# CodeJudge AI — AI-powered coding assessment & personalised learning platform (Aavishkar)

FastAPI + SQLAlchemy + Jinja2 (no Node build step). Upgrade of the original Online Judge; all original
features (judge, AI Code Doctor, workspace, extensions, bookmarks, import-from-image/PDF) still work.

## Features
| Area | What is implemented |
|---|---|
| Judge | Python, C, C++, Java · public + hidden test cases (weighted, partial scoring) · custom stdin runs · "Run samples" · submission history with filters · hidden test data never shown |
| AI | Tutor chat (persisted) · 3-level progressive hints · line-by-line explanation · error explanation · optimisation · weakness detection · personalised roadmap · recommendations. Uses Claude when `ANTHROPIC_API_KEY` is set, otherwise rule-based logic using the student's real code/verdicts |
| Integrity | Winnowing-based similarity (renamed variables/comments don't hide copies), flagged pairs with side-by-side compare |
| Students | Dashboard, streak + 26-week heatmap, XP/levels, 12 badges, rank, public profile, progress per topic |
| Contests | Admin-created, timer, penalty scoring, live leaderboard (polled every 8s), history, contest-only problems |
| Faculty/Admin | Analytics dashboard, topic weakness report, at-risk students, student/class **PDF** reports, user roles (student/faculty/admin), problem + test-case + contest management |
| UI | Design system with dark/light mode, responsive nav, toasts, spinners, error pages |
| Security | bcrypt, signed HttpOnly+SameSite cookies, role checks, input validation, rate limiting, CSRF (Origin check), security headers, hardened sandbox (see below) |

## Setup
```bash
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py          # creates tables/migrates, admin account, sample problems (prints admin password once)
uvicorn app.main:app --reload     # http://127.0.0.1:8000
```
Toolchains for other languages: `gcc`, `g++`, JDK (`javac`+`java`). Python needs nothing extra.

**Existing database:** just start the app. `app/migrations.py` adds the new columns/tables on startup
(idempotent, never deletes data). Existing admins become role `admin`.

## Configuration (environment variables)
See `.env.example`. In production set `JUDGE_ENV=production` — the app refuses to start with the default secret key.

## Code-execution sandbox
Docker is **not** used. Each run uses a hardened local sandbox: scrubbed environment (API keys/secrets are not visible
to user code), rlimits (CPU time, memory, file size, open files, processes, no core dumps), separate process group killed
on timeout, output captured to size-capped files, network namespace via `unshare -n` (when the kernel permits — check
`/health` → `network_isolation`), a source-size limit, and a static scan that rejects `os.system`, `subprocess`, sockets,
`fork`, `#include "/..."`, `Runtime.exec`, reflection etc. (`app/services/executor.py`).
**Limits of this design:** it is not a VM/container boundary. Run the server as an unprivileged OS user on a dedicated
machine, keep `judge.db`/`.env` out of that user's reach where possible, and put the app behind nginx + HTTPS.
For a public internet deployment of untrusted code, a container/VM boundary is still the stronger option.

## Roles
`student` (default on sign-up) · `faculty` (analytics, reports, plagiarism, create problems/contests) · `admin` (everything: users, delete, extensions).
Admins promote users at **Admin → Users**.

## Tests
`cd tests && python -m pytest -q` — 23 end-to-end tests (see TESTING_REPORT.md).

## Deployment (Linux)
```bash
export JUDGE_ENV=production JUDGE_SECRET_KEY=... JUDGE_ADMIN_PASSWORD=...
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
```
Put nginx in front (TLS, `proxy_set_header X-Forwarded-For $remote_addr; proxy_set_header Host $host;`). Rate limits are
per-process in memory; with several workers each worker counts separately. Use a systemd unit to keep it running.
SQLite is fine for a college deployment; set `JUDGE_DATABASE_URL` for PostgreSQL if needed.

## Project layout
`app/routers/*` HTTP routes · `app/services/*` judge, executor, AI, analytics, gamification, similarity, contests, PDF ·
`app/migrations.py` safe schema upgrade · `app/security.py` rate-limit/CSRF · `app/templates`, `app/static` UI · `tests/`.
