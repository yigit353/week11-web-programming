You are deploying the ByteBooks FastAPI backend to Railway with a managed PostgreSQL database. The app currently uses SQLite for local development. Migrate to PostgreSQL, configure for production, and deploy to Railway.

## Part 1: Prepare Backend for Production Deployment

1. Switch Database from SQLite to PostgreSQL:
   - Open `database.py` (or wherever database connection is configured)
   - Current setup likely uses SQLite:
     ```python
     SQLALCHEMY_DATABASE_URL = "sqlite:///./bytebooks.db"
     ```
   - Update to use environment variable:
     ```python
     import os

     # Use DATABASE_URL from environment, fallback to SQLite for local dev
     SQLALCHEMY_DATABASE_URL = os.getenv(
         "DATABASE_URL",
         "sqlite:///./bytebooks.db"
     )

     # Railway provides postgres:// but SQLAlchemy needs postgresql://
     if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
         SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
             "postgres://", "postgresql://", 1
         )

     engine = create_engine(
         SQLALCHEMY_DATABASE_URL,
         connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
     )
     ```
   - Add comment explaining why we check for `postgres://` vs `postgresql://` (Railway quirk)

2. Install PostgreSQL Driver (psycopg2):
   - Update `requirements.txt` to include:
     ```
     fastapi
     uvicorn[standard]
     sqlalchemy
     psycopg2-binary
     python-multipart
     pydantic
     passlib[bcrypt]
     python-jose[cryptography]
     ```
   - The `psycopg2-binary` package is the PostgreSQL adapter for SQLAlchemy
   - Run `pip install psycopg2-binary` locally to verify it installs

3. Configure Production Server (Gunicorn + Uvicorn):
   - Create a `Procfile` in the project root (Railway uses this to know how to run your app):
     ```
     web: uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - This tells Railway to:
     * Use the `web` process type (auto-assigned a public URL)
     * Run uvicorn with the app defined in `main.py`
     * Bind to all network interfaces (0.0.0.0)
     * Use the PORT environment variable Railway provides
   - Alternative for better production performance: use gunicorn with uvicorn workers:
     ```
     web: gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
     ```
   - If using gunicorn, add `gunicorn` to requirements.txt

4. Update CORS Configuration:
   - Open `main.py` (or wherever CORS middleware is configured)
   - Current CORS likely allows only localhost:
     ```python
     app.add_middleware(
         CORSMiddleware,
         allow_origins=["http://localhost:5173"],
         ...
     )
     ```
   - Update to allow production frontend URL:
     ```python
     import os

     # Get frontend URL from environment variable
     FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

     # Allow both localhost and production frontend
     allowed_origins = [
         "http://localhost:5173",
         "http://localhost:3000",
         FRONTEND_URL,
     ]

     app.add_middleware(
         CORSMiddleware,
         allow_origins=allowed_origins,
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```
   - Add comment explaining why CORS is necessary (browser security, different domains)

5. Create Environment Variable Template:
   - Create a `.env.example` file (template for production):
     ```
     DATABASE_URL=postgresql://user:password@host:port/dbname
     SECRET_KEY=your-secret-key-here-min-32-chars
     FRONTEND_URL=https://your-frontend.vercel.app
     ```
   - Add `.env` to `.gitignore` (if not already there)
   - This documents what env vars are needed without exposing real values

6. Update `.gitignore`:
   - Ensure these are included:
     ```
     __pycache__
     *.pyc
     .env
     *.db
     venv
     ```

7. Test Locally with PostgreSQL (Optional but Recommended):
   - Install PostgreSQL locally (macOS: `brew install postgresql`, Linux: `apt install postgresql`)
   - Create a local database: `createdb bytebooks_dev`
   - Create a `.env` file:
     ```
     DATABASE_URL=postgresql://localhost/bytebooks_dev
     SECRET_KEY=local-dev-secret-key-12345678
     FRONTEND_URL=http://localhost:5173
     ```
   - Run the app: `uvicorn main:app --reload`
   - Verify tables are created in PostgreSQL (not SQLite)
   - Test basic operations (create user, add book, login)

## Part 2: Deploy to Railway

8. Create Railway Account and New Project:
   - Visit https://railway.app and sign up (use GitHub login for easier integration)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub repositories
   - Select your ByteBooks backend repository

9. Add PostgreSQL Database:
   - In your Railway project, click "New" → "Database" → "Add PostgreSQL"
   - Railway will:
     * Provision a managed PostgreSQL instance
     * Automatically set `DATABASE_URL` environment variable in your app
     * Generate a random password and connection string
   - You don't need to manually configure DATABASE_URL (Railway does it automatically)

10. Set Additional Environment Variables:
    - In Railway project dashboard, click on your app service (not the database)
    - Go to "Variables" tab
    - Add these environment variables:
      * `SECRET_KEY`: Generate a secure key (use `openssl rand -hex 32` or similar)
      * `FRONTEND_URL`: The Vercel URL from Session 1 (e.g., `https://bytebooks.vercel.app`)
    - `DATABASE_URL` should already be set automatically (verify it's there)

11. Configure Build and Deploy:
    - Railway auto-detects Python and will:
      * Install dependencies from `requirements.txt`
      * Run the command specified in `Procfile`
    - If Railway doesn't auto-detect, manually set:
      * Build Command: `pip install -r requirements.txt`
      * Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
    - Click "Deploy" (or deployment may start automatically)

12. Monitor Deployment:
    - Watch the build logs in Railway dashboard
    - Deployment process:
      1. Pull code from GitHub
      2. Install Python dependencies
      3. Run Procfile command
      4. Assign public URL
    - If successful, you'll see "Success" and a public URL like `bytebooks-production.up.railway.app`
    - Click the URL to verify API is live (you should see FastAPI docs at `/docs`)

13. Initialize Database Schema:
    - Your database is empty (no tables yet)
    - Option A: Trigger table creation by making a request that uses the database
    - Option B: Add a startup event in `main.py`:
      ```python
      from database import Base, engine

      @app.on_event("startup")
      def startup():
          Base.metadata.create_all(bind=engine)
      ```
    - Redeploy if you add the startup event
    - Verify tables exist: Use Railway's PostgreSQL dashboard or connect via psql

14. Test the Deployed API:
    - Visit `https://your-app.railway.app/docs` (FastAPI interactive docs)
    - Test endpoints:
      * GET /books (should return empty array or error)
      * POST /auth/register (create a test user)
      * POST /auth/login (verify login works)
      * POST /books (add a test book)
    - Check Railway logs if any endpoint fails

## Part 3: Connect Frontend to Backend

15. Update Vercel Environment Variable:
    - Go to Vercel dashboard → Your project → Settings → Environment Variables
    - Update `VITE_API_URL`:
      * Old value: `http://localhost:8000`
      * New value: `https://your-app.railway.app` (your Railway URL)
    - Select "Production" environment
    - Save changes

16. Redeploy Frontend:
    - Vercel does NOT automatically redeploy when env vars change
    - Option A: Push a new commit to GitHub (triggers auto-deploy)
    - Option B: Go to Deployments tab → Click "..." on latest deployment → "Redeploy"
    - Wait for deployment to complete

17. Test Full Stack Deployment:
    - Visit your Vercel frontend URL
    - Test full user flow:
      * Register a new account (frontend → Railway API → PostgreSQL)
      * Login (verify JWT token flow works)
      * Add a book (verify CORS allows cross-origin requests)
      * View books list (verify data persists in PostgreSQL)
    - Open browser DevTools → Network tab to verify requests go to Railway URL

## Verification Checklist

- [ ] `database.py` uses `DATABASE_URL` environment variable with PostgreSQL support
- [ ] `psycopg2-binary` is in requirements.txt
- [ ] `Procfile` exists with correct uvicorn command
- [ ] CORS configuration allows production frontend URL
- [ ] `.env.example` documents required environment variables
- [ ] Railway project created with PostgreSQL database attached
- [ ] Environment variables set in Railway (SECRET_KEY, FRONTEND_URL, DATABASE_URL)
- [ ] Backend deployed successfully to Railway with public URL
- [ ] API docs accessible at `https://your-app.railway.app/docs`
- [ ] Database tables created (verify in Railway PostgreSQL dashboard)
- [ ] Vercel frontend updated with Railway API URL
- [ ] Full authentication flow works (register, login)
- [ ] Books can be added and retrieved from production database
- [ ] No CORS errors in browser console

## Expected Output

When complete, students should have:
- A fully deployed full-stack application:
  * Frontend: Vercel (React + Vite)
  * Backend: Railway (FastAPI)
  * Database: Railway PostgreSQL
- Public URLs for both frontend and backend
- Proper environment variable configuration (no secrets in Git)
- Understanding of production deployment workflow
- Experience with managed database services

## Common Issues and Solutions

**Issue: Build fails with "psycopg2-binary" installation error**
- Ensure requirements.txt has exact package name `psycopg2-binary` (not just `psycopg2`)
- Railway's Python environment should handle binary package correctly
- Check Railway build logs for specific error message

**Issue: "relation does not exist" database error**
- Tables haven't been created yet
- Add the startup event to create tables on app start (see step 13)
- Or manually connect to Railway PostgreSQL and run table creation

**Issue: CORS errors persisting after backend deployment**
- Verify FRONTEND_URL environment variable matches exact Vercel URL (including https://)
- Check Railway logs to see what origin the request is coming from
- Ensure CORS middleware includes the Vercel URL in allowed_origins
- Redeploy backend after changing CORS configuration

**Issue: "DATABASE_URL" not found error**
- Verify PostgreSQL database is attached to the Railway project (not a separate project)
- Check Variables tab shows DATABASE_URL (Railway sets this automatically)
- Restart the deployment if DATABASE_URL was added after initial deploy

**Issue: Frontend still connects to localhost**
- Environment variables in Vercel require redeployment to take effect
- Verify VITE_API_URL is set in Production environment (not just Preview)
- Check browser DevTools → Network tab to see which URL is being called
- Clear browser cache and hard refresh

**Issue: Authentication works locally but fails in production**
- Verify SECRET_KEY is set in Railway and is at least 32 characters
- Check that SECRET_KEY is the same across all backend instances (Railway should handle this)
- Ensure JWT tokens use HTTPS in production (usually automatic)

**Issue: Railway app crashes or "Application failed to respond"**
- Check Railway logs for Python errors
- Verify Procfile command is correct (`uvicorn main:app --host 0.0.0.0 --port $PORT`)
- Ensure all dependencies in requirements.txt are correct versions
- Check that $PORT variable is used (Railway injects this, don't hardcode port 8000)

**Issue: Database connection timeout**
- Railway PostgreSQL may take a few seconds to initialize on first connection
- Add connection retry logic (optional, usually not needed)
- Check DATABASE_URL format is correct (postgresql:// not postgres://)

## Explanation to Students

This session demonstrates modern full-stack deployment:
- **Managed databases** (Railway PostgreSQL) eliminate server administration burden
- **Environment variables** keep secrets out of Git and allow different configs per environment
- **Platform as a Service** (Railway, Vercel) abstracts infrastructure so you focus on code
- **CI/CD from GitHub** enables rapid iteration (push code → live in minutes)
- **CORS configuration** is critical for browser security when frontend and backend are on different domains

This is the same deployment pattern used by startups and large companies. You've now deployed a production-ready full-stack application with authentication, a real database, and automatic HTTPS. This is a significant milestone.

**Real-world perspective:**
- This same stack (React + FastAPI + PostgreSQL) powers many production apps
- Railway costs ~$5-10/month for small apps (generous free tier available)
- Vercel is free for personal projects, $20/month for teams
- This beats paying $100+/month for traditional VPS hosting
- The automatic scaling means your app can handle traffic spikes without manual intervention
