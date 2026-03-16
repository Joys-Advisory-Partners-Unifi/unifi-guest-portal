import httpx
from app.config import AppConfig
import logging
logger = logging.getLogger(__name__)


SCOPES = "openid email profile"


def get_authorization_url(config: AppConfig, state: str) -> str:
    params = {
        "client_id": config.authentik_client_id,
        "redirect_uri": f"{config.portal_base_url}/callback",
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    logger.info("Authorization URL: %s", url)
    return f"{config.authentik_host}/application/o/authorize/?{query}"


async def exchange_code_for_token(config: AppConfig, code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config.authentik_host}/application/o/token/",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{config.portal_base_url}/callback",
                "client_id": config.authentik_client_id,
                "client_secret": config.authentik_client_secret,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_userinfo(config: AppConfig, access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{config.authentik_host}/application/o/userinfo/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def get_guest_duration(userinfo: dict, site_default: int) -> int:
    """
    Check Authentik user attributes for a custom duration override.
    Falls back to site default (1440 minutes = 24 hours).
    """
    attributes = userinfo.get("attributes", {})
    return int(attributes.get("guest_wifi_duration_minutes", site_default))
