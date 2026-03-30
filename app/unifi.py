from unifi_utils import UnifiUtils, UnifiAPI
from app.config import SiteConfig
from unifi_utils import UnifiUtils, UnifiAPI, UnifiEndpointSymbolics

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

def set_guest_name(site: SiteConfig, mac: str, username: str, user_agent: str) -> None:
    """Set a friendly name on the guest device in UniFi."""
    try:
        unifi = UnifiUtils(
            endpoint=site.unifi_host,
            api_key=site.unifi_api_key,
            site=site.unifi_site,
        )
        unifi.session.verify = False

        # Determine device type from user agent
        ua = user_agent.lower()
        if "iphone" in ua:
            device_type = "iPhone"
        elif "ipad" in ua:
            device_type = "iPad"
        elif "android" in ua:
            device_type = "Android"
        elif "windows" in ua:
            device_type = "Windows"
        elif "mac" in ua:
            device_type = "Mac"
        else:
            device_type = "Device"

        friendly_name = f"{username} {device_type}"

        # Look up client by MAC to get _id
        clients = unifi.make_api_call(UnifiAPI.ActiveClientsGet)
        client = next((c for c in clients.get("data", []) if c.get("mac") == mac.lower()), None)

        if client is None:
            logger.warning("Could not find client %s to set name", mac)
            return

        client_id = client.get("_id")
        unifi.make_api_call(
            UnifiAPI.ClientModifyPut,
            json_body={"name": friendly_name},
            added_substitutions={UnifiEndpointSymbolics.ID: client_id},
        )
        logger.info("Set guest name '%s' for %s", friendly_name, mac)

    except Exception as e:
        logger.error("Failed to set guest name for %s: %s", mac, str(e))