# Church Bible Study Attendance System

Web-based attendance for church Bible Study Groups (BSGs), driven by face recognition
on a group photo posted to a leaders' Telegram group, with an Angular dashboard for
setup, member registration, visitor review, and reporting.

## Stack & why

| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | **Python + FastAPI** | The proven face-recognition libraries (InsightFace/ArcFace) are Python-native. One language for API + recognition + Telegram bot — no separate microservice. |
| DB | **PostgreSQL + pgvector** | Stores 512-d ArcFace embeddings; group-scoped vector matching without a separate vector DB. |
| Face recognition | **InsightFace** (`buffalo_l`, ArcFace 512-d) | Strong open model; behind a `FaceEngine` seam so it can be swapped. |
| Telegram | **aiogram v3** | Async bot sharing the same models/recognition code. |
| Frontend | **Angular 17** (standalone) | Web-only dashboard. |

## Architecture

```
Telegram group ──photo──▶ bot ─┐
                                ├─▶ recognition_pipeline ─▶ Postgres (attendance, visitors)
Angular  ──test endpoint──▶ API ┘                         (embeddings, never full photos)
Angular  ◀── login / setup / members / VISITOR REVIEW / reports ── API
```

- **Recognition is group-scoped:** a photo is matched only against the *sender's* group's
  members. Visiting members fall through as visitors and are resolved in the app.
- **Privacy:** full meeting photos are never persisted. Member profiles store embeddings.
  Visitor face crops are held **only until reviewed**, then deleted (no time-based retention).

## Data model

`Church → BibleStudyGroup → BSGMember → FacialProfilePhoto(embedding)`,
`User`(login: mobile+password, role admin|leader) ↔ `BSGLeader`(Telegram id),
`Meeting`(group+date) → `AttendanceRecord`(present-once, `is_guest`) / `VisitorEntry`(pending crop),
`BSGMembershipHistory`(group moves). See `backend/app/db/models/`.

## Telegram flow

1. Leader links Telegram once: dashboard issues a code → leader DMs the bot `/link <CODE>`.
   This captures their Telegram id (private chat id == user id == group-message sender id).
2. Leader posts a group photo → bot reads `message.from.id` → resolves leader → their BSG.
3. Recognition runs against that group's members. Matches → marked present immediately.
   Unmatched real faces → `VisitorEntry` (crop stored). Low-quality faces → discarded.
4. Bot replies (minimal): `Group: X | Recognized Members: N | Visitors: M (pending review) | Saved Successfully`.
   **Visitors are reviewed in the Angular app, not announced in the group.**
   Unregistered senders are ignored.

## Visitor review (Angular)

For each pending face the leader can:
- **Map to a member** (own group → present; other group → *Guest* attendance only, or
  *Move here* to reassign their home group + log history),
- **Register as new member** (own group; crop becomes first reference photo),
- **Keep as visitor**.
The crop is deleted on every outcome; the row is retained for stats.

## Configuration — all OPEN-DECISION knobs are env-driven (`backend/.env`)

| Var | Meaning |
|-----|---------|
| `FACE_MATCH_THRESHOLD` | cosine similarity to count as a match |
| `FACE_DET_SCORE_MIN`, `FACE_MIN_PIXELS`, `FACE_MAX_YAW_DEG`, `FACE_BLUR_VAR_MIN` | quality gate (discard tiny/side/blurry) |
| `TELEGRAM_MATCH_FIELD` | `user_id` (default) vs `chat_id` — isolated in `leader_resolver.py` (OPEN DECISION #5) |
| `TELEGRAM_REPLY_MODE` | `minimal` / `silent` / `private` |
| `BOOTSTRAP_ADMIN_*` | first admin created on startup |

No visitor-retention window exists by design (held until reviewed).
Open decisions still marked with `# TODO` in code: cross-group enabled in review, forward-only
re-recognition, and confirming the Telegram sender id against a real group message.

## Run with Docker

```bash
cp backend/.env.example backend/.env   # set TELEGRAM_BOT_TOKEN, JWT_SECRET, admin creds
docker compose up --build
# API:    http://localhost:8000  (docs at /docs)
# first run downloads the InsightFace model (~300MB) into the facemodels volume
```

Frontend:
```bash
cd frontend && npm install && npm start   # http://localhost:4200
```

## Run locally (without Docker)

```bash
# Postgres with pgvector must be running and match DATABASE_URL.
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows; use bin/activate on *nix
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload                       # API
python -m app.telegram.bot                          # bot (separate terminal)
```

## Validate accuracy early (Build step 4)

Use **Test Recognition** in the dashboard (or `POST /api/v1/recognition/test`) to run the
exact pipeline on an uploaded photo without Telegram. Defaults to a dry-run (`persist=false`);
tick "Save" to also write attendance + visitors. Tune thresholds in `.env` from the results.

## Build order (delivered)

1. ✅ Data model + Alembic migrations (pgvector)
2. ✅ Angular: setup + member registration with face profiles
3. ✅ Face recognition service (detection, matching, configurable threshold)
4. ✅ Test endpoint (no Telegram)
5. ✅ Telegram bot (sender-id lookup, intake, recognition, summary)
6. ✅ Visitor review wired to recognition output
7. ✅ Reporting
