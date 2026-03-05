# Twitch Access Token Setup Guide

This guide explains how to obtain a Twitch access token for use in this project, based on the `tmp.py` script.

## 1. Prerequisites
- A Twitch account.
- A registered application on the [Twitch Developer Console](https://dev.twitch.tv/console).

## 2. Register Your Application
1. Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
2. Click **+ Register Your Application**.
3. Set the **Name** (e.g., "The Gaffer Orchestrator").
4. Set the **OAuth Redirect URLs** to: `http://localhost:3000/callback`.
5. Set the **Category** to `Chat Bot`.
6. Click **Create**.
7. Once created, click **Manage** to find your **Client ID** and generate a **Client Secret**.

## 3. Configuration
Ensure your `.env` or application configuration includes:
- `CLIENT_ID`: Your Twitch Client ID.
- `CLIENT_SECRET`: Your Twitch Client Secret.
- `REDIRECT_URI`: `http://localhost:3000/callback`

## 4. Obtain an Authorization Code
Twitch uses the **Authorization Code Grant Flow**. You first need a user to authorize your app.

1.  Construct the authorization URL (replace `<CLIENT_ID>`):
    ```text
    https://id.twitch.tv/oauth2/authorize?client_id=<CLIENT_ID>&redirect_uri=http://localhost:3000/callback&response_type=code&scope=user:read:chat+user:bot+moderator:read:followers+channel:read:subscriptions
    ```
2.  Paste this URL into your browser.
3.  Authorize the application.
4.  Twitch will redirect you to `http://localhost:3000/callback?code=<AUTHORIZATION_CODE>`.
5.  Copy the `<AUTHORIZATION_CODE>` from the URL.

## 5. Exchange Code for Access Token
Use the following `curl` command to exchange the code for a token:

```bash
curl -X POST https://id.twitch.tv/oauth2/token \
-d "client_id=<CLIENT_ID>" \
-d "client_secret=<CLIENT_SECRET>" \
-d "code=<AUTHORIZATION_CODE>" \
-d "grant_type=authorization_code" \
-d "redirect_uri=http://localhost:3000/callback"
```

The response will look like this:
```json
{
  "access_token": "your_new_access_token",
  "expires_in": 14064,
  "refresh_token": "your_refresh_token",
  "scope": ["user:read:chat", "user:bot", ...],
  "token_type": "bearer"
}
```

## 6. Validate Your Token
You can verify if your token is still valid using:
```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" https://id.twitch.tv/oauth2/validate
```

## 7. Troubleshooting
- **Invalid Redirect URI**: Ensure the `redirect_uri` in your code matches *exactly* what is registered in the Twitch console.
- **Scope Mismatch**: If you need more permissions, you must re-authorize the user with the updated scopes in the URL from step 4.
