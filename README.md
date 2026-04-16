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

If the UniFi route does not exist yet, StopLiga creates it automatically before continuing the sync.

In the normal zero-config path, StopLiga also:

- finds the first available UniFi network whose purpose is `vpn-client`
- creates the route named by `STOPLIGA_ROUTE_NAME`
- applies it to `ALL_CLIENTS` when UniFi allows it
- enables or disables the route according to the published blocking status

## Before You Start

You need:

- a UniFi gateway/controller reachable from the container
- a local UniFi API key
- at least one UniFi VPN Client network already configured in UniFi

Important:

- StopLiga does not create or configure the VPN tunnel itself
- it creates and manages the UniFi policy route automatically once a `vpn-client` network exists
- for most setups, the only values you need to change are `UNIFI_HOST` and `UNIFI_API_KEY`

## Quick Start

1. Copy the example environment file.
2. Set only your UniFi host and API key.
3. Start the container with Docker Compose.

```bash
cp .env.example .env
docker compose pull
docker compose up -d
```

Your `.env` can stay as simple as this:

```dotenv
UNIFI_HOST=10.0.1.1
UNIFI_API_KEY=replace-me
UNIFI_SITE=default
UNIFI_VERIFY_TLS=false
STOPLIGA_RUN_MODE=loop
STOPLIGA_SYNC_INTERVAL_SECONDS=300
STOPLIGA_ROUTE_NAME=StopLiga
STOPLIGA_MAX_RESPONSE_BYTES=2097152
```

After startup, follow the logs with:

```bash
docker compose logs -f
```

For the API key, open UniFi Network and go to `Settings > Control Plane > Integrations`, then create or copy a local Network API key and paste it into `UNIFI_API_KEY` in `.env`.

Official reference: [Getting Started with the Official UniFi API](https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-the-Official-UniFi-API)

## Configuration

These are the same variables that appear in [`.env.example`](/Users/jonatan/Nextcloud/AI/Claude/Apps/StopLiga/.env.example:1).

For most users, leave everything except `UNIFI_HOST` and `UNIFI_API_KEY` unchanged:

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

What those values do:

- `UNIFI_HOST`: UniFi host or IP address that the container should connect to.
- `UNIFI_API_KEY`: local UniFi API key used for authentication.
- `UNIFI_SITE`: UniFi site name. `default` is the normal value.
- `UNIFI_VERIFY_TLS`: whether to verify the UniFi TLS certificate. Set it to `false` only for local self-signed setups.
- `STOPLIGA_RUN_MODE`: `loop` keeps the service running continuously. `once` runs a single sync and exits.
- `STOPLIGA_SYNC_INTERVAL_SECONDS`: how often StopLiga runs a full sync. Each sync checks both blocking status and the IP list.
- `STOPLIGA_ROUTE_NAME`: exact UniFi policy route name that StopLiga should manage or create automatically.
- `STOPLIGA_MAX_RESPONSE_BYTES`: safety limit for HTTP response size, in bytes. It applies to feed downloads and UniFi API responses and helps avoid bad or unexpectedly large responses. In normal setups, leave the default.

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

## VPN Client Network Required

StopLiga can create the policy route automatically, but UniFi must already have at least one VPN Client network.

- StopLiga looks for UniFi networks whose purpose is `vpn-client`.
- If the route does not exist yet, it automatically picks the first available `vpn-client` network and creates the route.
- If no `vpn-client` network exists, StopLiga cannot continue and logs a clear error with a link to this section.
- After you create a VPN Client network in UniFi, restart the container.

## Automatic Setup

- if the route already exists, StopLiga updates its destination IP list and enabled state
- if the route does not exist, StopLiga creates it automatically
- in the normal case it applies the route to `ALL_CLIENTS`
- if UniFi rejects `ALL_CLIENTS`, StopLiga retries with a single detected client and keeps that degraded route disabled until you review it

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
