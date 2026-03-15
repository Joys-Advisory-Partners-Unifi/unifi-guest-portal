# UniFi Guest Portal

A captive portal for UniFi guest WiFi networks using Authentik OIDC authentication.

## Overview

This portal replaces the built-in UniFi captive portal with a custom web app that:
- Authenticates guests via Authentik OIDC
- Supports multiple UniFi sites (JFMT, JFHR)
- Authorizes guest MAC addresses via the UniFi API
- Supports per-user session duration overrides via Authentik user attributes

## Architecture
```
Guest connects to WiFi
  → UniFi redirects to portal (/portal?site=jfmt&mac=xx:xx&...)
  → Portal initiates Authentik OIDC login
  → Guest authenticates (password + optional MFA)
  → Portal calls UniFi API to authorize guest MAC
  → Guest redirected to original URL
```

## Setup

### 1. Copy environment file
```bash
cp .env.example .env
```
Edit `.env` with your Authentik and UniFi credentials.

### 2. Add static assets
Place the following in `app/static/`:
- `pup.jpg` — the Shiba Inu photo
- `jfmt-pdx-logo.svg` — the JFMT-PDX logo

### 3. Configure Authentik
Create an OIDC provider in Authentik for the portal:
- Redirect URI: `https://portal.jfmt-pdx.net/callback`
- Note the Client ID and Client Secret for your `.env`

### 4. Configure UniFi
In UniFi Hotspot Portal:
- Enable **External Portal Server**
- Set URL to `https://portal.jfmt-pdx.net/portal`

### 5. Run
```bash
docker compose up -d
```

## Per-User Session Duration

By default guests get 24 hours (1440 minutes). To override for a specific user,
set the following attribute on their Authentik user profile:
```
guest_wifi_duration_minutes: 480
```

## Dependencies

- [unifi-utils-python](https://pypi.org/project/unifi-utils-python/) — UniFi API client
- [FastAPI](https://fastapi.tiangolo.com/)
- [Authentik](https://goauthentik.io/)

## License

Apache License 2.0
