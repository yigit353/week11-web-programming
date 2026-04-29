# ByteBooks — Full-Stack Bookstore Demo

A teaching project for a web programming course (Week 11). A small bookstore
app — list books, register/login, add to your library — built as a
production-grade full-stack application and deployed live on Vercel + Railway.

| Component | Tech | Live URL |
|---|---|---|
| Frontend | React 19 + Vite + React Router | https://bytebooks-frontend-mu.vercel.app |
| Backend | FastAPI + SQLModel + JWT auth | https://week11-web-programming-production.up.railway.app |
| Database | PostgreSQL (managed by Railway) | — |
| Docs | Swagger UI auto-generated | [/docs](https://week11-web-programming-production.up.railway.app/docs) |

> 📖 **Deploying this yourself, or curious how the deployment was done?** See
> **[GUIDE.md](./GUIDE.md)** — a field guide built from the actual Claude Code
> sessions that deployed this app, including the platform-UI hallucinations
> Claude made and how they were fixed.

---

## Repository Layout

```
week11-web-programming/
├── bytebooks-api/          FastAPI backend
│   ├── main.py             Routes + lifespan handler (creates tables, seeds data)
│   ├── database.py         Engine config, env-driven (SQLite local / Postgres prod)
│   ├── models.py           SQLModel ORM models (Author, Book, User)
│   ├── schemas.py          Pydantic request/response schemas
│   ├── services.py         Business logic (CRUD)
│   ├── auth_utils.py       JWT issue/verify
│   ├── external_api.py     Open Library integration
│   ├── config.py           SECRET_KEY + JWT settings (env-driven)
│   ├── Procfile            Railway start command
│   ├── requirements.txt    pinned in production
│   └── .env.example        documents required env vars
│
├── bytebooks-frontend/     React + Vite frontend
│   ├── src/                components, contexts, utils
│   ├── vercel.json         SPA rewrites
│   ├── .env.development    VITE_API_URL=http://localhost:8000
│   └── .env.production.example
│
├── prompts/                Original Claude Code prompts for sessions 1 & 2
├── GUIDE.md                Deployment guide (Vercel + Railway, with hallucination playbook)
└── README.md               You are here
```

---

## Quickstart (Local Development)

### Backend

```bash
cd bytebooks-api
python -m venv venv
source venv/bin/activate                # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API at http://127.0.0.1:8000 — Swagger UI at http://127.0.0.1:8000/docs.
On first run the local SQLite file `bytebooks.db` is created and seeded with
sample authors and books.

### Frontend

```bash
cd bytebooks-frontend
npm install
npm run dev
```

App at http://localhost:5173. The dev build reads `VITE_API_URL` from
`.env.development`, which points at `http://localhost:8000`.

### Environment variables

Copy `bytebooks-api/.env.example` to `bytebooks-api/.env` if you want to use
PostgreSQL locally. Without `.env`, the backend falls back to SQLite — fine
for development.

```env
DATABASE_URL=postgresql://localhost/bytebooks_dev
SECRET_KEY=replace-with-openssl-rand-hex-32-output
FRONTEND_URL=http://localhost:5173
```

---

## API Endpoints (Summary)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/books` | — | List books with author |
| GET | `/books/{id}` | — | Get one book |
| POST | `/books` | JWT | Create book |
| PUT | `/books/{id}` | JWT | Update book |
| DELETE | `/books/{id}` | JWT | Delete book |
| GET | `/authors` | — | List authors |
| POST | `/authors` | JWT | Create author |
| GET | `/books/search-external?q=...` | — | Search Open Library |
| POST | `/books/import-external` | JWT | Import a book by ISBN |
| POST | `/auth/register` | — | Create user |
| POST | `/auth/login` | — | Get JWT |

Full interactive docs at `/docs`.

---

## Deployment

The live deployment uses:

- **Vercel** for the frontend (auto-deploys on `git push origin main` from
  `bytebooks-frontend/`).
- **Railway** for the backend + managed PostgreSQL (auto-deploys on
  `git push origin main` from `bytebooks-api/`).

For the full step-by-step — including which buttons to click on each
platform, which CLI commands to run, what to verify after each step, and
how to recognize when Claude Code has hallucinated a UI element that no
longer exists — see **[GUIDE.md](./GUIDE.md)**.

**Cost shape:** Vercel hobby tier is free, Railway is ~$5/mo for a small
app after the trial credit. Total under $10/mo — beats $100+/mo for
traditional VPS hosting.

---

## Course Context

This project covers Week 11 of a web programming course — production
deployment of full-stack apps. Two prompts drove the work:

- [`prompts/session1-prompt.md`](./prompts/session1-prompt.md) — frontend to Vercel
- [`prompts/session2-prompt.md`](./prompts/session2-prompt.md) — backend + Postgres to Railway, frontend wiring

Both sessions were run with Claude Code. The narrative of how those sessions
went — what Claude got right on the first try, what it hallucinated, and how
those hallucinations were corrected — is preserved in [GUIDE.md](./GUIDE.md).
That document is the more useful artifact than this README if you want to
**learn the workflow**, not just the project.

---

## Further Reading

- **[GUIDE.md](./GUIDE.md)** — full deployment walkthrough + hallucination playbook + verification recipes
- **[bytebooks-api/STARTUP.md](./bytebooks-api/STARTUP.md)** — local API testing scenarios
- **[bytebooks-api/test_scenarios.md](./bytebooks-api/test_scenarios.md)** — endpoint test cases
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Vite docs](https://vitejs.dev/)
- [Railway docs](https://docs.railway.com/)
- [Vercel docs](https://vercel.com/docs)
