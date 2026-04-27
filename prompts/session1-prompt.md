You are deploying the ByteBooks React frontend (built with Vite) to Vercel. The app currently connects to a local FastAPI backend at http://localhost:8000. Prepare the app for production deployment and deploy it to Vercel.

## Part 1: Prepare Frontend for Deployment

1. Update API Configuration for Environment Variables:
   - Find all instances where the frontend makes API calls to the backend (likely in fetch() calls or axios requests)
   - Replace hardcoded `http://localhost:8000` URLs with an environment variable
   - Create a config file (src/config.js) that exports:
     ```javascript
     export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
     ```
   - Update all API calls to use this config:
     ```javascript
     import { API_URL } from './config';
     fetch(`${API_URL}/books`)
     ```
   - Explain in comments why environment variables are critical (different URLs for dev/prod, security, flexibility)

2. Create Environment Files:
   - Create `.env.development` file with:
     ```
     VITE_API_URL=http://localhost:8000
     ```
   - Create `.env.production.example` file (template for production, not committed with real values):
     ```
     VITE_API_URL=https://your-backend-url.railway.app
     ```
   - Add `.env.production` to `.gitignore` (never commit production secrets)

3. Configure for SPA Routing (if using React Router):
   - Create a `vercel.json` file in the project root:
     ```json
     {
       "rewrites": [
         { "source": "/(.*)", "destination": "/index.html" }
       ]
     }
     ```
   - This ensures all routes serve index.html (required for client-side routing)

4. Test Production Build Locally:
   - Run `npm run build` to create optimized production assets
   - Check the `dist` folder is created with index.html, JS bundles, CSS, assets
   - Optionally run `npm run preview` to test the production build locally
   - Verify the build completes without errors or warnings

5. Update `.gitignore`:
   - Ensure these are included:
     ```
     node_modules
     dist
     .env.production
     .vercel
     ```

## Part 2: Deploy to Vercel

6. Install Vercel CLI:
   - Run `npm install -g vercel` (install globally)
   - Verify installation: `vercel --version`

7. Deploy to Vercel:
   - Navigate to the frontend project directory
   - Run `vercel` command
   - Follow the interactive prompts:
     * Log in or create Vercel account (browser will open)
     * Set up and deploy project? Yes
     * Which scope? (select your account)
     * Link to existing project? No (first deployment)
     * Project name? (use default or customize)
     * Directory? ./ (current directory)
     * Override settings? No (Vercel auto-detects Vite)
   - Vercel will:
     * Upload files
     * Build the project (runs `npm run build`)
     * Deploy to a preview URL like `bytebooks-abc123.vercel.app`
   - Note the preview URL provided

8. Set Environment Variables in Vercel Dashboard:
   - Visit the Vercel dashboard (vercel.com/dashboard)
   - Navigate to your project
   - Go to Settings → Environment Variables
   - Add a new environment variable:
     * Key: `VITE_API_URL`
     * Value: `http://localhost:8000` (temporary, will update after backend deployment)
     * Select "Production" environment
   - Save the variable

9. Deploy to Production:
   - Run `vercel --prod` to deploy to the production URL
   - This creates a permanent URL like `bytebooks.vercel.app`
   - Visit the URL and verify the app loads (API calls will fail until backend is deployed)

10. Set Up GitHub Integration for Automatic Deployments (optional but recommended):
    - In Vercel dashboard, go to project Settings → Git
    - Connect your GitHub repository
    - Enable automatic deployments:
      * Push to `main` → deploys to production
      * Push to other branches or PRs → creates preview deployments
    - Test it: Make a small change (e.g., update homepage text), commit, and push to GitHub
    - Vercel will automatically trigger a new deployment
    - Check the Deployments tab to see the build progress

## Verification Checklist

- [ ] Production build runs successfully (`npm run build` completes)
- [ ] `vercel.json` exists with SPA routing configuration
- [ ] API calls use `VITE_API_URL` environment variable, not hardcoded localhost
- [ ] `.env.development` and `.env.production.example` files exist
- [ ] `.env.production` and `.vercel` are in `.gitignore`
- [ ] Vercel CLI installed and deployment successful
- [ ] App is live at a `.vercel.app` URL
- [ ] Environment variable `VITE_API_URL` set in Vercel dashboard
- [ ] GitHub repository connected for automatic deployments (if applicable)

## Expected Output

When complete, students should have:
- A live, publicly accessible React app at a Vercel URL
- Environment variables properly configured for dev and prod
- Understanding of the Vercel deployment flow
- Knowledge of how to trigger automatic deployments via GitHub
- A production-ready frontend (even though backend isn't deployed yet)

## Common Issues and Solutions

**Issue: Build fails with "Module not found" error**
- Ensure all dependencies are in package.json (not just devDependencies)
- Run `npm install` locally to verify dependencies resolve
- Check import paths are correct (case-sensitive on Linux servers)

**Issue: Environment variables not working**
- Vite requires `VITE_` prefix for env vars to be exposed to client
- Redeploy after setting env vars (changes don't apply to existing deployments)
- Check env vars are set for "Production" environment, not just "Preview"

**Issue: 404 errors on refresh for routes like /books/1**
- Missing `vercel.json` with rewrite rules
- Create vercel.json as specified above and redeploy

**Issue: CORS errors when calling API**
- Expected at this stage (backend not deployed yet)
- Will be fixed in Session 2 when backend CORS is configured

**Issue: Deployment succeeds but app shows blank page**
- Check browser console for JavaScript errors
- Verify build output in Vercel logs (click on deployment → see build logs)
- Ensure base URL is correct in vite.config.js (usually not needed unless deploying to subdirectory)

## Explanation to Students

This session demonstrates modern frontend deployment:
- **Environment variables** allow different configurations for dev/prod without changing code
- **Vercel's build process** optimizes your React app (minification, tree-shaking, code splitting)
- **CDN deployment** means your app is served from data centers worldwide (fast load times globally)
- **Automatic deployments** from GitHub enable continuous deployment (push code → live in minutes)
- **Preview deployments** for PRs let you test changes before merging to main

This is how professional teams deploy frontend apps in 2024. The same approach works for personal projects and billion-dollar companies.
