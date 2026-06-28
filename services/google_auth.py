import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN,
    GOOGLE_SCOPES, TOKEN_PATH
)
from services.logger import get_logger

logger = get_logger("google_auth")


def get_credentials() -> Credentials:
    """Return valid Google OAuth2 credentials, refreshing if needed."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired credentials")
        creds.refresh(Request())
        _save_token(creds)
        return creds

    # Bootstrap from env vars if token file doesn't exist
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN:
        logger.info("Bootstrapping credentials from environment variables")
        creds = Credentials(
            token=None,
            refresh_token=GOOGLE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=GOOGLE_SCOPES,
        )
        creds.refresh(Request())
        _save_token(creds)
        return creds

    raise RuntimeError(
        "No valid Google credentials found. Run the auth setup flow:\n"
        "  python -m commands.cli auth\n"
        "Or set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in .env"
    )


def run_auth_flow(client_secrets_file: str) -> Credentials:
    """Run the OAuth2 authorization flow (one-time setup)."""
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, GOOGLE_SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    logger.info(f"Auth complete. Token saved to {TOKEN_PATH}")
    logger.info(f"Add this to your .env:\nGOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    return creds


def _save_token(creds: Credentials):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else GOOGLE_SCOPES,
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
