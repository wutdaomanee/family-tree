# Family Tree — Deployment Guide

## Prerequisites
- Docker Desktop (Windows/Mac/Linux) **or** Python 3.11+
- Git (optional, for cloning)

---

## Option A — Local Python (Windows / Mac / Linux)

```bash
# 1. Install dependency
pip install openpyxl

# 2. Run
python web_ui.py
```

Browser opens automatically at **http://localhost:8888**  
Default login: `admin` / `admin1234`

To change the port:
```bash
PORT=9000 python web_ui.py          # Mac/Linux
set PORT=9000 && python web_ui.py   # Windows CMD
```

---

## Option B — Docker (single container, dev/test)

```bash
# 1. Build
docker build -t family-tree .

# 2. Run (data persists in Docker volume)
docker run -d \
  --name family-tree \
  -p 8888:8888 \
  -v family_tree_data:/data \
  -e NO_BROWSER=1 \
  family-tree
```

Open **http://localhost:8888**

Stop / remove:
```bash
docker stop family-tree && docker rm family-tree
```

---

## Option C — Docker Compose (dev, single service)

```bash
# Start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Data volume: `family_data` (survives `down`, removed by `down -v`)

---

## Option D — Docker Compose + Nginx (production)

```bash
# Start (app on :8888 behind nginx on :80)
docker compose -f docker-compose.prod.yml up -d

# Reload nginx config without downtime
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Stop
docker compose -f docker-compose.prod.yml down
```

To enable HTTPS, replace the `nginx.conf` server block with a Certbot/SSL section:
```nginx
listen 443 ssl;
ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

---

## Option E — Render.com (cloud PaaS)

1. Push code to GitHub/GitLab.
2. Go to [render.com](https://render.com) → **New** → **Blueprint**.
3. Connect your repository — Render detects `render.yaml` automatically.
4. Click **Apply** — Render builds the Docker image and provisions a 1 GB disk at `/data`.
5. After deploy, open the service URL; first login: `admin` / `admin1234`.

> **Note:** The free plan sleeps after 15 min of inactivity. Use the `starter` plan for always-on.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8888` | HTTP listen port |
| `DB_PATH` | `./family_tree.db` | SQLite database file path |
| `PHOTO_DIR` | `./photos` | Directory for uploaded photos |
| `NO_BROWSER` | _(unset)_ | Set to `1` to disable auto browser open |

---

## Backup & Restore

```bash
# Backup (while running)
docker cp family-tree:/data/family_tree.db ./backup_$(date +%Y%m%d).db
docker cp family-tree:/data/photos ./backup_photos_$(date +%Y%m%d)

# Restore
docker cp ./backup_2025xxxx.db family-tree:/data/family_tree.db
docker restart family-tree
```

With Docker Compose, the volume name is `family-tree_family_data` (prefix = project dir name).

---

## Upgrade

```bash
# Rebuild image with latest code
docker compose pull          # if using registry
docker compose up -d --build # rebuild from local Dockerfile

# Data volume is untouched — no migration needed for v0.x series
```
