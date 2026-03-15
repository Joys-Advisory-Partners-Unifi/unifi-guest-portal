import os
import json
from dataclasses import dataclass


@dataclass
class SiteConfig:
    id: str
    name: str
    unifi_host: str
    unifi_api_key: str
    unifi_site: str
    ssid: str
    default_duration_minutes: int = 1440


@dataclass
class AppConfig:
    authentik_host: str
    authentik_client_id: str
    authentik_client_secret: str
    portal_secret_key: str
    portal_base_url: str
    sites: dict[str, SiteConfig]


def load_config() -> AppConfig:
    sites_raw = json.loads(os.environ["SITES"])
    sites = {s["id"]: SiteConfig(**s) for s in sites_raw}

    return AppConfig(
        authentik_host=os.environ["AUTHENTIK_HOST"],
        authentik_client_id=os.environ["AUTHENTIK_CLIENT_ID"],
        authentik_client_secret=os.environ["AUTHENTIK_CLIENT_SECRET"],
        portal_secret_key=os.environ["PORTAL_SECRET_KEY"],
        portal_base_url=os.environ["PORTAL_BASE_URL"],
        sites=sites,
    )
