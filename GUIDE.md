# GUIDE: Deploying a Full-Stack App with Claude Code, Vercel, and Railway

A field guide built from two real Claude Code sessions that took the **ByteBooks** app
(React + Vite frontend, FastAPI backend, SQLite → PostgreSQL) from "runs on my laptop"
to a live full-stack deployment on Vercel and Railway.

This guide is **not** "click here, click there." Vercel and Railway change their
dashboards every few months, so by the time you read this some buttons will have
moved. Instead, this guide teaches you the *workflow* — how to drive Claude Code
to do most of the work, how to spot and fix Claude's hallucinations about
platform UIs, and how to verify each step actually worked before moving on.

---

## Table of Contents

1. [Why This Guide Exists](#why-this-guide-exists)
2. [Prerequisites](#prerequisites)
3. [The Workflow Pattern (You + Claude Code)](#the-workflow-pattern-you--claude-code)
4. [Session 1: Frontend to Vercel](#session-1-frontend-to-vercel)
5. [Session 2: Backend + Postgres to Railway, Wiring Frontend](#session-2-backend--postgres-to-railway-wiring-frontend)
6. [Hallucination Playbook](#hallucination-playbook)
7. [Verification Patterns](#verification-patterns)
8. [Final State Reference](#final-state-reference)

---

## Why This Guide Exists

LLMs were trained on documentation that goes stale. Vercel and Railway redesign
their UIs faster than any model's training cutoff. When you ask Claude Code "how
do I set the Root Directory in Vercel?", it will confidently tell you "Settings
→ General" — and you'll spend 10 minutes searching a tab where it no longer
lives.

The skill you need is not memorizing Vercel's current dashboard. It's:

1. **Drive Claude Code to do all the local work** (code edits, env files,
   `.gitignore`, building, committing) — this is where it shines.
2. **Verify every claim with a real command** — `curl`, `vercel ls`, log
   inspection. Never trust "it should be deployed now."
3. **Recognize hallucinations** — when Claude points you at a button that
   doesn't exist, push back with screenshots and let it adapt.
4. **Use the platforms' CLIs** when the dashboard has moved — CLI flags are
   more stable than UI menus, and Claude can run them itself.

This guide walks through both sessions chronologically, showing exactly where
Claude got it wrong and what the fix was.

---

## Prerequisites

Before starting, install these locally and create the accounts:

| Tool | Install | Verify |
|---|---|---|
| Node.js (for Vite + Vercel CLI) | `brew install node` | `node --version` |
| Vercel CLI | `npm install -g vercel` | `vercel --version` |
| Vercel account | sign up at vercel.com | `vercel whoami` |
| Railway account | sign up at railway.app (use GitHub login) | (browser only) |
| Python 3.11+ | `brew install python` | `python --version` |
| Git + GitHub repo | repo must be **pushed to GitHub** for both platforms' auto-deploy | `git remote -v` |
| `openssl` | already on macOS | `openssl rand -hex 32` |
| Claude Code | follow Anthropic's install guide | `claude --version` |

**One thing to know up front:** both Vercel and Railway can deploy from a
**monorepo** (one Git repo with both `bytebooks-frontend/` and `bytebooks-api/`
side by side), but you must tell each platform which subdirectory to build.
That single setting is the source of more confusion in this guide than anything
else. Watch for it.

---

## The Workflow Pattern (You + Claude Code)

Both sessions followed the same shape:

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Read the prompt to Claude.                                       │
│    Ask: "what do I need to provide before you start?"               │
│                                                                      │
│ 2. Claude does Part 1 (local code) entirely on its own.             │
│    You: review the diff, push back if anything looks wrong.        │
│                                                                      │
│ 3. You do the platform-side setup that requires a human             │
│    (account creation, OAuth, picking project names, generating      │
│    secrets, attaching managed services).                            │
│                                                                      │
│ 4. Claude does Part 2 (deploy via CLI) and verifies with curl.      │
│                                                                      │
│ 5. Claude tries to verify end-to-end. If something looks wrong,     │
│    paste screenshots / log excerpts back into Claude. Iterate.      │
└──────────────────────────────────────────────────────────────────────┘
```

The "what do I need to provide before you start?" question is critical. In
session 1 it surfaced 7 specific items Claude needed (project name, install
state, deploy strategy, etc.) — it's faster to answer all of them at once than
to be interrupted mid-deploy.

---

## Session 1: Frontend to Vercel

### Goal
Deploy `bytebooks-frontend/` (Vite + React 19 + React Router) as a public site
at `https://<something>.vercel.app`.

### What Claude did locally (Part 1)

Files created/changed in commit `d124bc8`:

```
bytebooks-frontend/.env.development         # VITE_API_URL=http://localhost:8000
bytebooks-frontend/.env.production.example  # VITE_API_URL=https://your-backend.railway.app
bytebooks-frontend/vercel.json              # SPA rewrite rules
bytebooks-frontend/.gitignore               # added .env.production, .vercel
.gitignore (root)                           # added !.env.development, !.env.production.example
```

The `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Why: React Router uses client-side routes like `/books/1`. Without the rewrite,
Vercel returns 404 when someone refreshes that URL because there's no
`/books/1.html` file. The rewrite makes every path serve `index.html`, then
React Router takes over in the browser.

**Existing patterns Claude respected, didn't rewrite:**
The prompt asked for a `src/config.js` exporting `API_URL`. The codebase
already had `import.meta.env.VITE_API_URL` centralized in `src/utils/api.js`
and `src/contexts/AuthContext.jsx`. Claude flagged this and asked rather than
duplicating the pattern. **Lesson:** read the prompt critically; if your
codebase already does what the prompt asks, say so.

### What you do (Part 2)

You sign up at vercel.com (use GitHub login). Then Claude takes over the CLI
deploy.

### What Claude did via CLI

```bash
# 1. Build locally to verify
npm run build                                   # 240 KB JS, 18 KB CSS, 354 ms

# 2. Link the local folder to a Vercel project
vercel link --yes --project bytebooks-frontend

# 3. Preview deploy
vercel deploy --yes
# → https://bytebooks-frontend-ng3bx8jrz-yigit353s-projects.vercel.app

# 4. Set the env var (Vite bakes it in at BUILD time, so this must come before prod)
echo "http://localhost:8000" | vercel env add VITE_API_URL production

# 5. Production deploy
vercel deploy --prod --yes
# → aliased to https://bytebooks-frontend-mu.vercel.app

# 6. Verify SPA rewrites work for deep routes
curl -sI https://bytebooks-frontend-mu.vercel.app/books/1
# HTTP/2 200  ← important: not 404
```

> ⚠️ **Vite + env vars rule:** `import.meta.env.VITE_*` values are inlined
> into the JavaScript bundle **at build time**. Changing the env var in
> Vercel's dashboard does **not** affect existing deployments. You must
> trigger a fresh build (push a commit, run `vercel deploy --prod`, or
> use `vercel redeploy <url> --target=production`).

### 🪲 Hallucination 1: GitHub auto-connect via CLI

Claude tried:
```bash
vercel git connect https://github.com/yigit353/week11-web-programming.git
```

The command returned without error but **no GitHub integration was actually
set up** — pushing a commit didn't trigger a deploy. The reality: Vercel's
GitHub OAuth must be granted through the dashboard the first time. CLI
`vercel git connect` only works after the org-level OAuth grant exists.

**Fix:** the human (you) goes to
`https://vercel.com/<scope>/<project>/settings/git`, clicks Connect, authorizes
the GitHub app. Then future `git push origin main` triggers a deploy.

### 🪲 Hallucination 2: "Set Root Directory in Settings → General"

After GitHub auto-connect, the next push triggered a build that failed:
```
sh: line 1: vite: command not found
Error: Command "vite build" exited with 127
```

Cause: Vercel cloned the **repo root**, which has no `package.json`. It needed
to run the build inside `bytebooks-frontend/`.

Claude said: "Go to Settings → General → Root Directory."

User screenshotted the dashboard back: **there is no Root Directory in
General**. Vercel had moved it.

**The actual location (as of this writing):**
**Settings → Build and Deployment → Root Directory.** Set to `bytebooks-frontend`.

**Lesson:** when Claude tells you a UI path that doesn't exist, take a
screenshot, paste it back, and explicitly say "this menu doesn't have that
option." Claude will adapt — it can search current docs. Do not waste 20
minutes hunting through every tab.

### After fixing Root Directory

```bash
git commit --allow-empty -m "Trigger Vercel redeploy after root directory fix"
git push origin main
# Vercel auto-built from bytebooks-frontend/ → Ready in 9s
```

This commit (`b3bd2c7`) exists for *no other reason* than to retrigger a deploy
after fixing a dashboard setting. Don't be afraid of empty commits — they're
cheap and the audit trail is useful.

### Session 1 result

- `https://bytebooks-frontend-mu.vercel.app` returns 200
- SPA rewrites verified working
- `VITE_API_URL` set to `http://localhost:8000` (placeholder; will update in session 2)
- `git push origin main` → auto-deploys to production

---

## Session 2: Backend + Postgres to Railway, Wiring Frontend

### Goal
1. Migrate the FastAPI backend from SQLite to PostgreSQL.
2. Deploy `bytebooks-api/` to Railway with a managed Postgres instance.
3. Update Vercel's `VITE_API_URL` to point at the Railway URL.
4. Verify the full stack works end-to-end.

### Step 0: What I need from you (asked before any code)

Claude opened the session by listing what *only the human* could do:

| Action | Why |
|---|---|
| Sign up at railway.app with GitHub login | Lets Railway pull your repo |
| Create empty Railway project linked to your repo | Sets up the deployment target |
| **Set Railway service Root Directory to `bytebooks-api`** | Same monorepo problem as Vercel |
| Generate `SECRET_KEY` with `openssl rand -hex 32` | Claude can't (and shouldn't) generate your secret |
| Note the Vercel URL for `FRONTEND_URL` | Needed for CORS allow-list |

**`openssl rand -hex 32`** produces a 64-character hex string like
`a3f8c1d9e2b7460f8a1c3d5e7b9f2046a8c1e3d5f7b9046281c3a5e7d9f2b4c6`.
Treat it like a password. Never commit it. If you rotate it, all existing JWT
tokens become invalid (users get logged out — plan accordingly).

### Step 1: Attach Postgres on Railway (you do this)

The dashboard flow that worked:

1. **Create the app service first**, set its Root Directory to `bytebooks-api`
   (Settings → Source). The first build will fail — that's fine, ignore it.
2. In the project canvas, click **+ New → Database → Add PostgreSQL**.
3. A Postgres tile appears next to your app.
4. Click your **app service** tile → **Variables** tab. Some Railway versions
   auto-inject `DATABASE_URL`; if not, click **+ New Variable → Add Reference
   → Postgres → DATABASE_URL**. Railway sets it to `${{Postgres.DATABASE_URL}}`,
   a live reference that follows credential rotation.
5. Add `SECRET_KEY` and `FRONTEND_URL` (your Vercel URL, **including**
   `https://`, no trailing slash) as plain variables.

**You never paste the raw Postgres connection string anywhere.** Railway
injects `DATABASE_URL` into your app's runtime environment. `os.getenv("DATABASE_URL")`
in Python returns the right value at runtime.

### Step 2: Code changes (Claude does these)

Files changed in commit `b7b2236`:

#### `bytebooks-api/database.py` — env-driven, Postgres-aware

```python
import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bytebooks.db")

# Railway exposes Postgres URLs as `postgres://...`, but SQLAlchemy 1.4+
# requires the explicit `postgresql://` scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; Postgres does not.
_is_sqlite = DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(DATABASE_URL, echo=_is_sqlite, connect_args=_connect_args)
```

Three subtleties this code captures:

1. **`postgres://` → `postgresql://` rewrite.** Railway and Heroku both still
   emit the legacy scheme. SQLAlchemy ≥1.4 rejects it. One line fixes it.
2. **`connect_args` is conditional.** `check_same_thread=False` is a
   SQLite-only parameter; passing it to a Postgres engine errors out.
3. **`echo=True` only for local SQLite.** Logging every SQL statement to
   Railway's log stream is noisy and expensive.

#### `bytebooks-api/config.py` — `SECRET_KEY` from env

```python
import os
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",  # local dev only
)
```

#### `bytebooks-api/main.py` — env-driven CORS

```python
import os

FRONTEND_URL = os.getenv("FRONTEND_URL")
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Local dev origins stay in the list so the same backend code serves both
environments without a config flag.

#### `bytebooks-api/requirements.txt` — Postgres driver

Added: `psycopg2-binary` — the PostgreSQL adapter for SQLAlchemy. **Use
`psycopg2-binary`, not `psycopg2`.** The non-binary package needs `pg_config`
and a C compiler at build time; the binary package ships pre-compiled wheels
and works on Railway's build environment without any system deps.

#### `bytebooks-api/Procfile` — start command

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Three things must be exactly right:

- `--host 0.0.0.0` — binding to `127.0.0.1` would only accept local connections,
  so Railway's load balancer can't reach the app.
- `--port $PORT` — Railway injects `$PORT` at runtime; it changes per
  deployment. **Never hardcode 8000.**
- File location: at the **root of the deploy directory**. Because Railway's
  Root Directory is set to `bytebooks-api`, the Procfile lives at
  `bytebooks-api/Procfile`.

#### `bytebooks-api/.env.example` — documents required env vars

The whole point of this file is so a future developer can read it and know
what env vars they need to set, without exposing real values. We had to add
`!.env.example` to the root `.gitignore` because the existing `.env.*` rule
would otherwise block it.

### Step 3: Push and watch Railway build

```bash
git push origin main
# Railway auto-detects the new commit, rebuilds.
```

**What to look for in build logs:**
- `Successfully installed ... psycopg2-binary-2.x.x ...`
- No `error: pg_config executable not found` (would mean it picked the wrong package).

**What to look for in deploy logs:**
- `INFO: Started server process`
- `INFO: Uvicorn running on http://0.0.0.0:<some-port>`
- `INFO: Application startup complete`
- SQL `CREATE TABLE` statements (the lifespan handler runs against Postgres for the first time).

**Get the public URL:** Settings → Networking → Public Networking → Generate Domain.
Yields something like `week11-web-programming-production.up.railway.app`.

### Step 4: Verify Railway deployment is real

```bash
# /docs should return Swagger UI
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  https://week11-web-programming-production.up.railway.app/docs

# /books should return seeded data — proves Postgres tables were created and seeded
curl -sS https://week11-web-programming-production.up.railway.app/books | head -c 600
# [{"id":1,"title":"Clean Code", ...}]
```

If `/books` returns seeded sample books, three things are simultaneously true:
- Postgres connection works
- `create_db_and_tables()` ran successfully
- `_seed_data()` ran on the empty Postgres database
- Read endpoints work

This is a much stronger signal than a "deploy succeeded" log.

### Step 5: Update Vercel to point at Railway

```bash
cd bytebooks-frontend

# Vercel CLI has no in-place update; remove + re-add
vercel env rm VITE_API_URL production --yes
printf "https://week11-web-programming-production.up.railway.app" | \
  vercel env add VITE_API_URL production
```

### 🪲 Hallucination 3: `vercel --prod --yes` from the linked folder

Claude ran:
```bash
cd bytebooks-frontend && vercel --prod --yes
```

Got back:
```
Error: The provided path "~/.../bytebooks-frontend/bytebooks-frontend" does not exist.
```

Cause: Vercel's project Root Directory is configured to `bytebooks-frontend`.
When CLI runs from inside `bytebooks-frontend/`, it appends the configured
Root Directory again, doubling the path.

**Fix that worked:** redeploy a previous deployment, which re-runs the
build with current env vars but doesn't re-upload from local:
```bash
vercel ls   # find the latest Ready deployment URL
vercel redeploy https://bytebooks-frontend-dbgs19vki-yigit353s-projects.vercel.app \
  --target=production
```

### 🪲 Hallucination 4: `vercel redeploy --yes`

```bash
vercel redeploy <url> --target=production --yes
# Error: unknown or unexpected option: --yes
```

`--yes` works on `vercel deploy`, `vercel link`, `vercel env rm`, but **not**
on `vercel redeploy`. The `redeploy` subcommand has only `--no-wait` and
`--target`. (Confirmation is auto-skipped when an agent is detected.)

**General principle:** when a CLI flag fails, run `<cmd> --help` and show
Claude the actual flag list. CLI surfaces drift — what's true for one
subcommand isn't true for the next.

### Step 6: Verify the new bundle and CORS

```bash
# 1. Frontend reachable
curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://bytebooks-frontend-mu.vercel.app/

# 2. Railway URL baked into the JS bundle
for js in $(curl -sSL https://bytebooks-frontend-mu.vercel.app/ \
    | grep -oE '/assets/[^"]*\.js' | head -3); do
  echo "-- $js"
  curl -sS "https://bytebooks-frontend-mu.vercel.app$js" \
    | grep -oE '(railway\.app|localhost:8000)[^"]*' | sort -u | head -5
done
# Expected: week11-web-programming-production.up.railway.app
#           (NOT localhost:8000 — that means the rebuild didn't happen)

# 3. CORS preflight
curl -sS -o /dev/null -D - -X OPTIONS \
  -H "Origin: https://bytebooks-frontend-mu.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  https://week11-web-programming-production.up.railway.app/auth/register \
  | grep -i "access-control\|HTTP/"
# Expected:
#   HTTP/2 200
#   access-control-allow-origin: https://bytebooks-frontend-mu.vercel.app
```

If the bundle still contains `localhost:8000`, the redeploy didn't actually
rebuild — Vite's build was cached or the env var change didn't propagate.
Trigger a fresh deploy.

If the CORS preflight returns 400 or no `access-control-allow-origin` header,
the `FRONTEND_URL` you set on Railway doesn't match the **exact origin** the
browser is sending. URLs are case-sensitive and trailing-slash sensitive at
this layer.

### Step 7: Manual end-to-end test in the browser

Open DevTools → Network tab **before** doing anything:

1. Visit your Vercel URL.
2. Click Register → create a test account → see `POST /auth/register` → 200/201.
3. Login → `POST /auth/login` → JWT in response.
4. Add a book → `POST /books` → 201.
5. **Refresh the page** → books still there (proves persistence in Postgres,
   not just in-memory state).

If any step fails, the Network tab response is gold — paste it back to Claude.

---

## Hallucination Playbook

Catalog of things Claude got wrong in these sessions and the fixes that
worked. Use this as a checklist when something doesn't match Claude's
description.

| Symptom | Likely Hallucination | Fix |
|---|---|---|
| "Settings → General → Root Directory" but no such option exists | Vercel moved it | Look in **Settings → Build and Deployment → Root Directory**. Screenshot the actual UI back to Claude. |
| `vercel git connect <url>` returns success but pushes don't deploy | CLI can't grant first-time GitHub OAuth | Connect via dashboard at `vercel.com/<scope>/<project>/settings/git` |
| `vercel <subcommand> --yes` → `unknown or unexpected option: --yes` | Flag exists on some subcommands but not all | Run `vercel <subcommand> --help`; non-interactive mode is auto-detected when an agent is present |
| `vercel --prod` from inside the linked folder → "path doesn't exist" with the folder name doubled | Vercel project's Root Directory is set; CLI re-applies it | Use `vercel redeploy <url> --target=production` instead, or run from repo root |
| Vite app deployed but env var changes don't take effect | `import.meta.env.VITE_*` is baked at build time | Trigger a fresh deploy after changing the env var |
| Build fails: `sh: line 1: vite: command not found` | Build is running at repo root, not in the subdirectory | Set Root Directory in dashboard, push empty commit to retry |
| Postgres connect fails: `dialect "postgres" not supported` | URL scheme is `postgres://`, SQLAlchemy needs `postgresql://` | Rewrite the prefix in `database.py` |
| `pg_config executable not found` during `psycopg2` install | You used `psycopg2`, not `psycopg2-binary` | Switch to `psycopg2-binary` in `requirements.txt` |
| Railway app crashes on boot with `Address already in use` or won't bind | Hardcoded `--port 8000` | Use `--port $PORT` in Procfile |
| CORS errors in browser despite `FRONTEND_URL` being set on Railway | Origin mismatch (case, trailing slash, http vs https) | Match the exact origin shown in DevTools Network tab |
| `git rm --cached .idea` fails | Wrong flag order: `--cached` is a `git rm` flag, not a `git` flag | `git rm -rf --cached .idea` |

**Meta-rule:** when Claude describes a UI element, treat it as a *probability
distribution over recent versions of the UI*, not ground truth. If you don't
see what it described, that's data — share it.

---

## Verification Patterns

The single most valuable habit you can build: **never claim a step worked
because the command exited 0**. Always verify with an independent observation.

| Step | Bad verification | Good verification |
|---|---|---|
| "Vercel deploy succeeded" | `vercel --prod` exit code 0 | `curl -sI <url>` returns 200 |
| "SPA rewrites work" | `vercel.json` is in the repo | `curl -sI <url>/some/deep/route` returns 200 |
| "Postgres is connected" | "deploy succeeded" log | `curl <url>/books` returns seeded data |
| "Env var was updated" | `vercel env ls` shows the new value | New JS bundle contains the new URL (`grep` the bundle) |
| "CORS allows my frontend" | Backend code reads `FRONTEND_URL` | OPTIONS preflight returns matching `access-control-allow-origin` header |
| "Frontend talks to backend" | "it should work now" | Open DevTools Network tab, do a real action, see the request go to the right URL with 200 |

The patterns Claude used in these sessions:

```bash
# Pattern 1: Three-stage curl smoke test
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "$URL/"          # service alive
curl -sS "$URL/books" | head -c 600                              # data layer alive
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "$URL/docs"       # framework alive

# Pattern 2: Confirm env var made it into the production build
curl -sSL "https://<vercel-url>/" | grep -oE '/assets/[^"]*\.js' | head -1
curl -sS "https://<vercel-url>/<assets-path>.js" | grep -oE '<expected-domain>[^"]*'

# Pattern 3: CORS preflight
curl -sS -o /dev/null -D - -X OPTIONS \
  -H "Origin: <frontend-origin>" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  "<backend-url>/<endpoint>" | grep -i "access-control"
```

---

## Final State Reference

After both sessions, the project looked like this:

### Git history

```
b7b2236 Load config from env; add Procfile, .env.example         ← session 2 code changes
b3bd2c7 Trigger Vercel redeploy after root directory fix         ← empty commit, session 1
d124bc8 Configure ByteBooks frontend for Vercel deployment       ← session 1 local changes
f636cd5 Add ByteBooks v2 API and frontend app                    ← initial app
```

### Files added across both sessions

```
bytebooks-frontend/.env.development
bytebooks-frontend/.env.production.example
bytebooks-frontend/vercel.json
bytebooks-api/Procfile
bytebooks-api/.env.example
```

### Files modified

```
.gitignore                        # whitelist patterns for example env files
bytebooks-api/database.py         # DATABASE_URL from env, Postgres-aware
bytebooks-api/config.py           # SECRET_KEY from env
bytebooks-api/main.py             # FRONTEND_URL into CORS allow-list
bytebooks-api/requirements.txt    # added psycopg2-binary
bytebooks-frontend/.gitignore     # added .env.production, .vercel
```

### Live infrastructure

| Component | Location | Auto-deploy trigger |
|---|---|---|
| Frontend | Vercel — `https://bytebooks-frontend-mu.vercel.app` | `git push origin main` (Vercel watches `bytebooks-frontend/`) |
| Backend | Railway — `https://week11-web-programming-production.up.railway.app` | `git push origin main` (Railway watches `bytebooks-api/`) |
| Database | Railway managed Postgres | n/a (data persists across deploys) |
| Frontend env var | `VITE_API_URL` — production scope | Set via `vercel env`, requires redeploy to take effect |
| Backend env vars | `SECRET_KEY`, `FRONTEND_URL`, `DATABASE_URL` | Set in Railway dashboard, applies on next deploy |

### Cost shape (for context)

- Vercel: free for hobby projects, $20/mo for teams
- Railway: ~$5/mo for small apps after the free trial
- Total for a small full-stack project: under $10/mo, vs $100+/mo for traditional VPS

---

## When This Guide Goes Stale

Some parts of this guide will be wrong by the time you read it. Specifically:

- **Vercel's "Root Directory" location.** Right now it's in Build and Deployment.
  By 2027 it may have moved again.
- **Railway's variable-reference UI.** "Add Reference" used to be a separate
  button; in newer versions Postgres `DATABASE_URL` is auto-injected.
- **CLI flag names.** `vercel --yes` worked on some subcommands and not
  others as of this writing. That ratio drifts.

The workflow doesn't go stale, though:

1. Ask Claude what you need to provide before it starts.
2. Let it do all local code.
3. You handle account, OAuth, secrets, managed-service attachment.
4. Claude does CLI deploy + verification.
5. Verify each step with an independent command, not a log line.
6. When Claude points at a button that doesn't exist, screenshot back. Don't argue.

That pattern works no matter what the dashboards look like next year.
