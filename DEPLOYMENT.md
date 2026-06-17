# Production Deployment — Hostinger VPS + Coolify

Target domains:
- **Dashboard (Angular):** `https://bsg.rmoffice.online`
- **API (FastAPI):** `https://bsgapi.rmoffice.online`

Stack deployed as one Docker Compose resource: `db` (Postgres+pgvector), `api`, `bot`, `frontend`.

---

## 0. Prerequisites
- Hostinger VPS with Coolify installed and reachable (you can open the Coolify dashboard).
- Your code in a Git repository (GitHub/GitLab/Gitea) that Coolify can pull. Private is fine (add a deploy key / GitHub App in Coolify).
- Note your VPS public IPv4 address (Coolify → Server, or `curl ifconfig.me` on the VPS).

---

## 1. DNS (do this first; propagation takes minutes)
In your DNS provider for `rmoffice.online`, add two **A records** pointing at the VPS IP:

| Type | Name     | Value (VPS IP)   | TTL |
|------|----------|------------------|-----|
| A    | `bsg`    | `YOUR.VPS.IP`    | Auto |
| A    | `bsgapi` | `YOUR.VPS.IP`    | Auto |

Verify (from your PC): `nslookup bsg.rmoffice.online` and `nslookup bsgapi.rmoffice.online` should both return the VPS IP before continuing — Let's Encrypt needs this to issue SSL.

---

## 2. Create the project in Coolify
1. Coolify → **Projects → + New** → name it `bsg-attendance` → choose your Server and an environment (Production).
2. Inside the project → **+ New Resource → Docker Compose**
   - Source: your Git repository + branch.
   - **Compose file path:** `docker-compose.prod.yml`
   - Save. Coolify parses the file and shows the 4 services.

> Coolify builds the images from the repo (`backend/Dockerfile`, `frontend/Dockerfile`) — you don't push images anywhere.

---

## 3. Environment variables (secrets)
Open the resource → **Environment Variables** and add the values from `.env.production.example`. Generate strong secrets:
- `JWT_SECRET` → `openssl rand -hex 32`
- `POSTGRES_PASSWORD` → a long random string
- `BOOTSTRAP_ADMIN_MOBILE`, `BOOTSTRAP_ADMIN_PASSWORD` → your first admin login
- `CORS_ORIGINS=https://bsg.rmoffice.online`
- `MAX_PHOTO_AGE_DAYS=7`
- `TELEGRAM_BOT_TOKEN` → leave empty (set later in the in-app Settings page) or paste it.

Mark password/secret/token entries as **Secret**.

---

## 4. Assign domains (Coolify wires Traefik + SSL automatically)
In the resource, each service is listed. Set the public domain + internal port:

- **api** → Domain `https://bsgapi.rmoffice.online`, Port `8000`
- **frontend** → Domain `https://bsg.rmoffice.online`, Port `80`
- **db**, **bot** → no domain (leave internal).

Coolify generates the proxy route and requests a Let's Encrypt certificate for each domain (this is why DNS must resolve first).

---

## 5. Persistent storage (important)
The compose already declares named volumes — Coolify persists them across redeploys:
- `pgdata` — the database (attendance history, members, embeddings).
- `memberphotos` — member reference images (their facial profile images).
- `facemodels` — the downloaded InsightFace model (~300 MB; first boot downloads it).
- `visitorcrops` — transient visitor crops (deleted on review).

Do not delete these volumes; `pgdata` and `memberphotos` are your real data.

---

## 6. Deploy
Click **Deploy**. First deploy takes several minutes (Docker build + InsightFace model download). Watch the logs:
- `api` runs `alembic upgrade head` (creates all tables) then starts uvicorn — wait for `Application startup complete`.
- `db` becomes healthy first.
- `frontend` builds the Angular bundle and serves via nginx.
- `bot` starts; with no token it logs "No Telegram bot token set yet — waiting…" (expected).

Health check: open `https://bsgapi.rmoffice.online/health` → `{"status":"ok"}` and `https://bsgapi.rmoffice.online/docs` for the API docs.

---

## 7. First login + setup
1. Open `https://bsg.rmoffice.online` → log in with the bootstrap admin (mobile + password from step 3).
2. Setup → create **Church → Group(s) → Leader(s)**, add **Cities/Streets**.
3. **⚙️ Settings**: paste the **Telegram bot token** (from @BotFather) and Save. The bot picks it up within ~30s (it auto-restarts).
4. Register members + upload reference photos (web or mobile).

---

## 8. Telegram
1. Token set in Settings (step 7.3).
2. Add your bot to the existing leaders' group and **make it admin** (so it can read group photos).
3. Link each leader: Setup → Leaders → **Get link code**; the leader DMs the bot `/link <code>`.
4. Leaders post the group photo in the group → attendance is recorded; they review visitors in the app.

---

## 9. Mobile app (point it at production)
The Flutter app asks for a **Server URL** on the login screen — enter:
```
https://bsgapi.rmoffice.online
```
To build a release APK to share with leaders:
```bash
cd mobile
flutter build apk --release
# output: build/app/outputs/flutter-apk/app-release.apk
```
(Optionally set the default server URL in the login screen so leaders don't type it.)

---

## 10. Updates & maintenance
- **Deploy new code:** push to the branch → Coolify **Redeploy** (or enable auto-deploy on push / webhook). Migrations run automatically on each `api` start.
- **Backups:** schedule Postgres backups in Coolify (Database backups), and snapshot/back up the `memberphotos` volume. Embeddings live in Postgres, so a DB backup covers recognition data; `memberphotos` covers the displayable images.
- **Logs:** Coolify → resource → Logs (per service).
- **Scaling thresholds/policy:** all in the in-app ⚙️ Settings (match threshold, quality, `discard_low_quality`, photo-age window) — no redeploy needed.

---

## Troubleshooting
- **SSL pending / 502:** DNS not resolving yet, or you deployed before DNS propagated. Fix DNS, then redeploy / retry certificate.
- **CORS errors in browser console:** `CORS_ORIGINS` must equal exactly `https://bsg.rmoffice.online` (no trailing slash). Redeploy `api` after changing.
- **Bot not reacting to photos:** ensure it's a **group admin** (or privacy mode disabled in @BotFather), token saved in Settings, and the leader is linked.
- **"Photo older than N days":** EXIF capture date is too old (or adjust `MAX_PHOTO_AGE_DAYS`). Note many chat apps strip EXIF — then the photo is allowed.
- **First recognition slow:** the InsightFace model downloads on first use into the `facemodels` volume; subsequent calls are fast.
