from datetime import datetime, timezone
from typing import Optional

from models.event_schema import NormalizedEvent


def normalize_event(subscription: dict, event: dict) -> Optional[NormalizedEvent]:
    """Normalize a raw Twitch EventSub payload into a NormalizedEvent.

    Expects the EventSub notification's subscription and event dicts.
    """
    sub_type = subscription.get("type")
    if not sub_type or not event:
        return None

    event_type: Optional[str] = None
    message: Optional[str] = None
    username: Optional[str] = None

    if sub_type == "channel.chat.message":
        event_type = "ChatMessage"
        message = (event.get("message") or {}).get("text")
        username = event.get("chatter_user_name")
    elif sub_type == "channel.subscribe":
        event_type = "Subscription"
        username = event.get("user_name")
    elif sub_type == "channel.raid":
        event_type = "Raid"
        username = event.get("from_broadcaster_user_name")
    elif sub_type == "channel.follow":
        event_type = "Follow"
        username = event.get("user_name")
    else:
        return None

    if event_type is None:
        return None

    timestamp = event.get("created_at")
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()

    # channel.chat.message uses message_id; others use id
    raw_id = event.get("message_id") or event.get("id")
    if raw_id is None:
        return None
    event_id = str(raw_id)

    return NormalizedEvent(
        event_id=event_id,
        event_type=event_type,
        message=message,
        username=username,
        timestamp=timestamp,
    )

