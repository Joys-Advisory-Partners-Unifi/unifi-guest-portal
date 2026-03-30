import logging
import secrets

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import get_authorization_url, exchange_code_for_token, get_userinfo, get_guest_duration
from app.config import load_config
from app.unifi import authorize_guest

from app.unifi import authorize_guest, set_guest_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
config = load_config()

# In-memory state store (fine for single-instance deployment)
state_store: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Entry point — shown when no site/mac params are present."""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "message": "No guest session found. Please connect to the guest WiFi first."
    })


@app.get("/portal")
async def portal(request: Request, site: str, mac: str, ap: str = "", url: str = ""):
    """
    Entry point from UniFi captive portal redirect.
    Stores session params and initiates Authentik OIDC login.
    """
    if site not in config.sites:
        raise HTTPException(status_code=400, detail=f"Unknown site: {site}")

    state = secrets.token_urlsafe(32)
    state_store[state] = {
        "site": site,
        "mac": mac,
        "ap": ap,
        "url": url,
    }

    auth_url = get_authorization_url(config, state)
    return RedirectResponse(auth_url)


@app.get("/guest/s/{site_id}/")
async def unifi_portal(request: Request, site_id: str, ap: str = "", id: str = "", t: str = "", url: str = "", ssid: str = ""):
    """Handle UniFi's default captive portal redirect format."""
    site = next((s for s in config.sites.values() if s.ssid == ssid), None)
    if site is None:
        site = next(iter(config.sites.values()))

    state = secrets.token_urlsafe(32)
    state_store[state] = {
        "site": site.id,
        "mac": id,
        "ap": ap,
        "url": url,
    }

    auth_url = get_authorization_url(config, state)
    return RedirectResponse(auth_url)

@app.get("/enroll-success", response_class=HTMLResponse)
async def enroll_success(request: Request, username: str = ""):
    return templates.TemplateResponse("enroll-success.html", {
        "request": request,
        "username": username,
    })

@app.get("/callback")
async def callback(request: Request, code: str, state: str):
    """
    Authentik OIDC callback.
    Exchanges code for token, gets user info, authorizes guest MAC.
    """
    if state not in state_store:
        raise HTTPException(status_code=400, detail="Invalid or expired state.")

    session = state_store.pop(state)
    site_id = session["site"]
    mac = session["mac"]
    original_url = session.get("url", "http://detectportal.firefox.com")

    site = config.sites[site_id]

    try:
        token = await exchange_code_for_token(config, code)
        userinfo = await get_userinfo(config, token["access_token"])
    except Exception as e:
        logger.error("OIDC error: %s", str(e))
        raise HTTPException(status_code=500, detail="Authentication failed.")

    duration = get_guest_duration(userinfo, site.default_duration_minutes)
    success = authorize_guest(site, mac, duration)
    user_agent = request.headers.get("user-agent", "").lower()
    logger.info("User agent: %s", user_agent)
    set_guest_name(site, mac, userinfo.get("preferred_username", "Guest"), user_agent)

    if not success:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Failed to authorize your device. Please try again or ask for help."
        })


    try:
        template = templates.env.get_template("success.html")
        html = template.render(
            request=request,
            site={"id": site.id, "name": site.name},
            userinfo=userinfo,
            duration_hours=duration // 60,
            original_url=original_url,
            user_agent=user_agent,
        )
        return HTMLResponse(html)
    except Exception as e:
        logger.error("Success template error: %s", str(e))
        return RedirectResponse(original_url or "http://captive.apple.com/hotspot-detect.html")

