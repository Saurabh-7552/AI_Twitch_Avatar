import asyncio
import json
import logging
import os
import time
from pathlib import Path

import aiohttp
import websockets

from event_normalizer import normalize_event

logging.getLogger(__name__)

WS_URL = "wss://eventsub.wss.twitch.tv/ws"

DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / "debug-60b19a.log"


def debug_log(hypothesis_id: str, location: str, message: str, data: dict | None = None, run_id: str = "run1") -> None:
    """Write a single NDJSON debug line to the shared debug log."""
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts_ms = int(time.time() * 1000)
        payload = {
            "sessionId": "60b19a",
            "id": f"log_{ts_ms}",
            "timestamp": ts_ms,
            "location": location,
            "message": message,
            "data": data or {},
            "runId": run_id,
            "hypothesisId": hypothesis_id,
        }
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        # Never let debug logging crash the client
        pass


async def _get_app_access_token(session: aiohttp.ClientSession) -> str | None:
    """Fetch an access token for EventSub.

    Prefer a user access token from TWITCH_ACCESS_TOKEN (with proper scopes),
    otherwise fall back to an app token via client credentials.
    """
    user_token = os.getenv("TWITCH_ACCESS_TOKEN")
    if user_token:
        debug_log(
            "H2",
            "websocket_client._get_app_access_token",
            "using_user_access_token_from_env",
            {},
        )
        return user_token
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        logging.warning("Missing TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET for EventSub setup.")
        debug_log("H2", "websocket_client._get_app_access_token", "missing_client_credentials", {})
        return None

    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    try:
        async with session.post(url, data=data) as resp:
            body = await resp.json()
            if resp.status != 200:
                logging.warning("Failed to get app token: %s - %s", resp.status, body)
                debug_log(
                    "H2",
                    "websocket_client._get_app_access_token",
                    "token_error",
                    {"status": resp.status, "body": body},
                )
                return None
            token = body.get("access_token")
            debug_log(
                "H2",
                "websocket_client._get_app_access_token",
                "token_ok",
                {"has_token": bool(token), "source": "client_credentials"},
            )
            return token
    except Exception as exc:  # noqa: BLE001
        logging.warning("Error fetching app access token: %s", exc)
        debug_log(
            "H2",
            "websocket_client._get_app_access_token",
            "token_exception",
            {"error": str(exc)},
        )
        return None


async def _get_broadcaster_id(session: aiohttp.ClientSession, token: str) -> str | None:
    """Resolve broadcaster user ID from TWITCH_CHANNEL login name."""
    client_id = os.getenv("TWITCH_CLIENT_ID")
    channel_login = os.getenv("TWITCH_CHANNEL")
    if not client_id or not channel_login:
        logging.warning("Missing TWITCH_CLIENT_ID or TWITCH_CHANNEL for EventSub setup.")
        debug_log("H2", "websocket_client._get_broadcaster_id", "missing_config", {})
        return None

    url = "https://api.twitch.tv/helix/users"
    params = {"login": channel_login}
    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {token}",
    }
    try:
        async with session.get(url, params=params, headers=headers) as resp:
            body = await resp.json()
            if resp.status != 200:
                logging.warning("Failed to get broadcaster ID: %s - %s", resp.status, body)
                debug_log("H2", "websocket_client._get_broadcaster_id", "users_error", {"status": resp.status, "body": body})
                return None
            data = body.get("data") or []
            if not data:
                logging.warning("No user found for channel login: %s", channel_login)
                debug_log("H2", "websocket_client._get_broadcaster_id", "no_user", {"channel": channel_login})
                return None
            user_id = data[0].get("id")
            debug_log("H2", "websocket_client._get_broadcaster_id", "user_ok", {"user_id": user_id})
            return user_id
    except Exception as exc:  # noqa: BLE001
        logging.warning("Error fetching broadcaster ID: %s", exc)
        debug_log("H2", "websocket_client._get_broadcaster_id", "users_exception", {"error": str(exc)})
        return None


async def _ensure_subscriptions(session: aiohttp.ClientSession, token: str, broadcaster_id: str, session_id: str) -> None:
    """Ensure basic EventSub WebSocket subscriptions exist for this session."""
    client_id = os.getenv("TWITCH_CLIENT_ID")
    bot_user_id = os.getenv("TWITCH_BOT_NUMERIC_USERNAME")


    if not client_id:
        debug_log("H2", "websocket_client._ensure_subscriptions", "missing_client_id", {})
        return

    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Start with the most relevant types; some may be rejected depending on scopes / support.
    sub_types = [
        "channel.chat.message",
        # "channel.subscribe",
        "channel.raid",
        # "channel.follow",  # 410 Gone in current API; skip by default
    ]

    for sub_type in sub_types:
        if sub_type == "channel.chat.message":
            # user_id must be broadcaster or moderator; token must be for that user with user:read:chat
            user_id = bot_user_id or broadcaster_id
            condition = {
                "broadcaster_user_id": broadcaster_id,
                "user_id": bot_user_id,
            }
            debug_log(
                "H1",
                "websocket_client._ensure_subscriptions",
                "chat_subscription_condition",
                {"broadcaster_user_id": broadcaster_id, "user_id": user_id, "bot_user_id": bot_user_id},
            )
        elif sub_type == "channel.subscribe":
            condition = {
                "broadcaster_user_id": broadcaster_id,
            }
        elif sub_type == "channel.raid":
            condition = {
                "to_broadcaster_user_id": broadcaster_id,
            }
        elif sub_type == "channel.follow":
            condition = {
                "broadcaster_user_id": broadcaster_id,
                "moderator_user_id": broadcaster_id,
            }
        else:
            continue

        payload = {
            "type": sub_type,
            "version": "1",
            "condition": condition,
            "transport": {
                "method": "websocket",
                "session_id": session_id,
            },
        }
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                body = await resp.json()
                debug_log(
                    "H1",
                    "websocket_client._ensure_subscriptions",
                    "subscribe_response",
                    {"type": sub_type, "status": resp.status, "body": body, "success": resp.status in (200, 202)},
                )
                if resp.status not in (200, 202):
                    logging.warning("Failed to subscribe %s: %s - %s", sub_type, resp.status, body)
        except Exception as exc:  # noqa: BLE001
            logging.warning("Error creating subscription %s: %s", sub_type, exc)
            debug_log(
                "H2",
                "websocket_client._ensure_subscriptions",
                "subscribe_exception",
                {"type": sub_type, "error": str(exc)},
            )



async def start_websocket() -> None:
    """Start the EventSub WebSocket client with automatic reconnects."""
    backoff = 1
    while True:
        try:
            await _run_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            logging.warning(
                "WebSocket error: %s. Reconnecting in %s seconds...", exc, backoff
            )
            debug_log(
                "H1",
                "websocket_client.start_websocket",
                "websocket_error",
                {"error": str(exc), "backoff": backoff},
            )
            await asyncio.sleep(backoff)
            # Cap backoff at 10 seconds to avoid long waits
            backoff = min(backoff * 2, 10)
        else:
            backoff = 1
            logging.info("WebSocket closed cleanly. Reconnecting in 5 seconds...")
            debug_log(
                "H1",
                "websocket_client.start_websocket",
                "websocket_closed_cleanly",
                {},
            )
            await asyncio.sleep(5)


async def _run_once() -> None:
    """Connect once to the Twitch EventSub WebSocket and process messages."""
    async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
        logging.info("Connected to Twitch EventSub WebSocket.")
        debug_log("H1", "websocket_client._run_once", "connected", {"url": WS_URL})

        async for raw in ws:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logging.warning("Received non-JSON message: %s", raw)
                debug_log("H1", "websocket_client._run_once", "non_json_message", {"raw": str(raw)[:200]})
                continue

            metadata = message.get("metadata", {}) or {}
            msg_type = metadata.get("message_type")
            payload = message.get("payload", {}) or {}

            debug_log(
                "H1",
                "websocket_client._run_once",
                "received_message",
                {"message_type": msg_type, "has_payload": bool(payload)},
            )

            if msg_type == "session_welcome":
                logging.info("Received session_welcome.")
                debug_log("H1", "websocket_client._run_once", "session_welcome", {})

                # Auto-create subscriptions for this session
                session_info = payload.get("session") or {}
                session_id = session_info.get("id")
                if session_id:
                    debug_log(
                        "H2",
                        "websocket_client._run_once",
                        "session_id_obtained",
                        {"session_id": session_id},
                    )
                    async with aiohttp.ClientSession() as http:
                        token = await _get_app_access_token(http)
                        if token:
                            broadcaster_id = os.getenv("TWITCH_BOT_CASTER_USERNAME")
                            if not broadcaster_id:
                                broadcaster_id = await _get_broadcaster_id(http, token)
                                debug_log(
                                    "H2",
                                    "websocket_client._run_once",
                                    "broadcaster_id_from_api",
                                    {"broadcaster_id": broadcaster_id, "source": "TWITCH_CHANNEL"},
                                )
                            else:
                                debug_log(
                                    "H2",
                                    "websocket_client._run_once",
                                    "broadcaster_id_from_env",
                                    {"broadcaster_id": broadcaster_id, "source": "TWITCH_BOT_CASTER_USERNAME"},
                                )
                            if broadcaster_id:
                                await _ensure_subscriptions(http, token, broadcaster_id, session_id)
                            else:
                                debug_log(
                                    "H1",
                                    "websocket_client._run_once",
                                    "skip_subscriptions_no_broadcaster",
                                    {},
                                )
            elif msg_type == "notification":
                subscription = payload.get("subscription") or {}
                event = payload.get("event") or {}
                debug_log(
                    "H1",
                    "websocket_client._run_once",
                    "notification",
                    {"subscription_type": subscription.get("type")},
                )
                normalized = normalize_event(subscription, event)
                if normalized:
                    print(normalized.model_dump_json())
                    debug_log(
                        "H1",
                        "websocket_client._run_once",
                        "normalized_event_emitted",
                        {"event_type": normalized.event_type},
                    )
                else:
                    debug_log(
                        "H1",
                        "websocket_client._run_once",
                        "notification_ignored_or_unhandled",
                        {"subscription_type": subscription.get("type")},
                    )
            else:
                # Ignore keepalives and other message types
                continue

