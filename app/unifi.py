from unifi_utils import UnifiUtils, UnifiAPI
from app.config import SiteConfig

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging
logger = logging.getLogger(__name__)


def authorize_guest(site: SiteConfig, mac: str, duration_minutes: int) -> bool:
    """Authorize a guest MAC address on the UniFi controller."""
    try:
        unifi = UnifiUtils(
            endpoint=site.unifi_host,
            api_key=site.unifi_api_key,
            site=site.unifi_site,
        )
        unifi.session.verify = False
        response = unifi.make_api_call(
            UnifiAPI.ClientAuthorizeGuestPost,
            json_body={
                "cmd": "authorize-guest",
                "mac": mac,
                "minutes": duration_minutes,
            },
        )
        logger.info("Authorized guest %s on site %s for %d minutes", mac, site.id, duration_minutes)
        logger.debug("UniFi response: %s", response)
        return True
    except Exception as e:
        logger.error("Failed to authorize guest %s on site %s: %s", mac, site.id, str(e))
        return False


def unauthorize_guest(site: SiteConfig, mac: str) -> bool:
    """Revoke guest access for a MAC address."""
    try:
        unifi = UnifiUtils(
            endpoint=site.unifi_host,
            api_key=site.unifi_api_key,
            site=site.unifi_site,
        )
        response = unifi.make_api_call(
            UnifiAPI.ClientUnauthorizeGuestPost,
            json_body={
                "cmd": "unauthorize-guest",
                "mac": mac,
            },
        )
        logger.info("Unauthorized guest %s on site %s", mac, site.id)
        logger.debug("UniFi response: %s", response)
        return True
    except Exception as e:
        logger.error("Failed to unauthorize guest %s on site %s: %s", mac, site.id, str(e))
        return False
