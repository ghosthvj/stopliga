# StopLiga

StopLiga keeps a UniFi policy-based route named `StopLiga` in sync with the status and IP list published by [`r4y7s/laliga-ip-list`](https://github.com/r4y7s/laliga-ip-list).

This repo is meant to run with Docker.

## What It Does

StopLiga manages a UniFi policy route that matches the destination IPs/CIDRs published in the LaLiga feed.

On every sync it:

1. checks whether the feed says blocking is active or not
2. downloads the latest destination IP list
3. compares that with the UniFi route
4. enables or disables the route
5. updates the route destination list if needed

Those IPs are the public destinations published by [`r4y7s/laliga-ip-list`](https://github.com/r4y7s/laliga-ip-list). StopLiga does not discover them by itself.

## Before You Start

You need:

- a UniFi gateway/controller reachable from the container
- a local UniFi API key
- a VPN client network already configured in UniFi if you want this route to send matching traffic through a VPN

Important:

- StopLiga does not create or configure the VPN tunnel itself
- it manages the UniFi policy route that uses that VPN
- if the route already exists, StopLiga only updates its destination IP list and enabled state
- if the route does not exist yet, StopLiga can bootstrap it, but it still needs an existing VPN client network inside UniFi

## Quick Start

1. Copy the example environment file.
2. Set your UniFi host and API key.
3. Start the container with Docker Compose.

```bash
cp .env.example .env
docker compose pull
docker compose up -d
```

For the API key, open UniFi Network and go to `Settings > Control Plane > Integrations`, then create or copy a local Network API key and paste it into `UNIFI_API_KEY` in `.env`.

Official reference: [Getting Started with the Official UniFi API](https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-the-Official-UniFi-API)

## Configuration

These are the same variables that appear in [`.env.example`](/Users/jonatan/Nextcloud/AI/Claude/Apps/StopLiga/.env.example:1).

Required:

```dotenv
UNIFI_HOST=10.0.1.1
UNIFI_API_KEY=replace-me
UNIFI_SITE=default
UNIFI_VERIFY_TLS=false
```

Core runtime settings:

```dotenv
STOPLIGA_RUN_MODE=loop
STOPLIGA_SYNC_INTERVAL_SECONDS=300
STOPLIGA_ROUTE_NAME=StopLiga
STOPLIGA_MAX_RESPONSE_BYTES=2097152
```

What they mean:

- `UNIFI_API_KEY` is required. Authentication is API-key only.
- `UNIFI_SITE=default` is the normal value unless your UniFi setup uses a different site.
- `UNIFI_VERIFY_TLS=false` is only for local setups with a self-signed UniFi certificate.
- `STOPLIGA_RUN_MODE=loop` keeps the container running continuously.
- `STOPLIGA_SYNC_INTERVAL_SECONDS` controls how often StopLiga runs a full sync.
- `STOPLIGA_ROUTE_NAME` must match the exact UniFi policy route name that StopLiga should manage.
- `STOPLIGA_MAX_RESPONSE_BYTES` is a safety limit for feed/API response size.

Optional route bootstrap:

```dotenv
# STOPLIGA_VPN_NAME=Mullvad DE
# STOPLIGA_TARGETS=apple-tv,ps5,aa:bb:cc:dd:ee:ff
```

Use those only if the route does not already exist and you want StopLiga to create it for you with an existing UniFi VPN client network and a set of target devices.

Optional notifications:

```dotenv
# STOPLIGA_GOTIFY_URL=https://gotify.example.com
# STOPLIGA_GOTIFY_TOKEN=replace-me
# STOPLIGA_GOTIFY_PRIORITY=5
# STOPLIGA_GOTIFY_ALLOW_PLAIN_HTTP=false
# STOPLIGA_GOTIFY_VERIFY_TLS=true
# STOPLIGA_TELEGRAM_BOT_TOKEN=123456:replace-me
# STOPLIGA_TELEGRAM_CHAT_ID=123456789
```

## VPN And Route Setup

The usual setup is:

1. Create or verify your VPN client network in UniFi.
2. Create the policy route in UniFi, or let StopLiga create it for you.
3. Point StopLiga at that route name with `STOPLIGA_ROUTE_NAME`.

What the policy route does:

- it matches destination IPs/CIDRs from the published feed
- it applies only to the clients/targets configured in that UniFi route
- it sends that matching traffic through the VPN network attached to the route

## Sync Cycle

In loop mode, every cycle does the same sequence:

1. download the current blocking status
2. download the current IP/CIDR list
3. compare that feed against the UniFi route
4. enable or disable the route
5. update the destination IP list if it changed

With `STOPLIGA_SYNC_INTERVAL_SECONDS=300`, that full cycle runs every 5 minutes.

## Docker Compose

The repo includes a working [`docker-compose.yml`](/Users/jonatan/Nextcloud/AI/Claude/Apps/StopLiga/docker-compose.yml:1):

```yaml
services:
  stopliga:
    image: ghcr.io/jcastro/stopliga:latest
    container_name: stopliga
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/data
    healthcheck:
      disable: true
```

The container mode comes from `STOPLIGA_RUN_MODE` in `.env`.

Useful commands:

```bash
docker compose up -d
docker compose logs -f
docker compose pull && docker compose up -d
```

## Docker Run

If you do not want Compose:

```bash
docker run -d \
  --name stopliga \
  --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/data:/data" \
  ghcr.io/jcastro/stopliga:latest
```

## Sources

- Data source: [`r4y7s/laliga-ip-list`](https://github.com/r4y7s/laliga-ip-list)
- Thanks to the maintainers of that repository for publishing and keeping the feed updated
