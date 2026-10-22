#!/usr/bin/env bash
# Waypoint engine: one-shot server setup for Ubuntu (Hetzner).
# Installs Docker, writes docker-compose.yml + .env with fresh secrets,
# and starts n8n + Postgres + Cloudflare Tunnel.
# Usage (as root):  bash bootstrap.sh
set -euo pipefail

APP_DIR=/opt/waypoint
N8N_HOST=n8n.noahhofmann.com

echo "==> 1/5 System update + firewall"
apt-get update -y && apt-get upgrade -y
apt-get install -y ufw curl openssl
ufw allow OpenSSH
ufw --force enable

echo "==> 2/5 Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> 3/5 Files in $APP_DIR"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

cat > docker-compose.yml <<'YAML'
services:
  postgres:
    image: postgres:16.15
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

  n8n:
    image: docker.n8n.io/n8nio/n8n:2.43.5
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: ${POSTGRES_DB}
      DB_POSTGRESDB_USER: ${POSTGRES_USER}
      DB_POSTGRESDB_PASSWORD: ${POSTGRES_PASSWORD}
      N8N_HOST: ${N8N_HOST}
      N8N_PROTOCOL: https
      N8N_PORT: 5678
      WEBHOOK_URL: https://${N8N_HOST}/
      N8N_PROXY_HOPS: 1
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
      N8N_RUNNERS_ENABLED: "true"
      N8N_DIAGNOSTICS_ENABLED: "false"
      N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS: "true"
      GENERIC_TIMEZONE: Europe/Berlin
      TZ: Europe/Berlin
      EXECUTIONS_DATA_PRUNE: "true"
      EXECUTIONS_DATA_MAX_AGE: 336
    volumes:
      - n8n_data:/home/node/.n8n

  cloudflared:
    image: cloudflare/cloudflared:2026.10.0
    restart: unless-stopped
    command: tunnel --no-autoupdate run
    environment:
      TUNNEL_TOKEN: ${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - n8n

volumes:
  postgres_data:
  n8n_data:
YAML

if [ ! -f .env ]; then
  read -rsp "Paste your Cloudflare Tunnel token (hidden): " TOKEN; echo
  cat > .env <<ENV
N8N_HOST=$N8N_HOST
POSTGRES_USER=n8n
POSTGRES_PASSWORD=$(openssl rand -hex 32)
POSTGRES_DB=n8n
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
CLOUDFLARE_TUNNEL_TOKEN=$TOKEN
ENV
  chmod 600 .env
fi

echo "==> Block the Hetzner metadata service (169.254.169.254) from containers (SSRF, audit 19 Oct)"
cat > /etc/systemd/system/block-metadata.service <<'UNIT'
[Unit]
Description=Block Hetzner metadata (169.254.169.254) from Docker containers
After=docker.service
Requires=docker.service
[Service]
Type=oneshot
ExecStart=/bin/sh -c 'iptables -C DOCKER-USER -d 169.254.169.254 -j DROP 2>/dev/null || iptables -I DOCKER-USER -d 169.254.169.254 -j DROP'
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload && systemctl enable --now block-metadata.service

echo "==> 4/5 Start containers"
docker compose up -d

echo "==> 5/5 Status"
sleep 15
docker compose ps
echo
echo "N8N_ENCRYPTION_KEY (save this in your password manager NOW):"
grep N8N_ENCRYPTION_KEY .env | cut -d= -f2
echo
echo "Done. Open https://$N8N_HOST and create the owner account."
