# Frontend Deployment: Netlify Setup

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│   Netlify       │         │   Railway/Render  │
│   (Frontend)    │ ──────> │   (API Backend)   │
│                 │  HTTPS  │                   │
│ bookshelf.      │         │ bookshelf.        │
│ lindsaybrunner. │         │ lindsaybrunner.    │
│ com             │         │ com/api           │
└─────────────────┘         └──────────────────┘
```

**Frontend**: Static site (React/Vue/etc.) → Deploys to **Netlify**  
**Backend**: Python API → Deploys to **Railway** or **Render**

Both can use the same domain:
- `bookshelf.lindsaybrunner.com` → Frontend (Netlify)
- `bookshelf.lindsaybrunner.com/api` → API (Railway/Render)

Or use subdomains:
- `bookshelf.lindsaybrunner.com` → Frontend (Netlify)
- `api.bookshelf.lindsaybrunner.com` → API (Railway/Render)

## Quick Answer: Can We Build Frontend Now?

**Yes, but you have two options:**

### Option 1: Deploy API First (Recommended - 5 minutes)
1. Deploy API to Railway (super quick - see SIMPLE_DEPLOYMENT.md)
2. Build frontend to connect to production API
3. Deploy frontend to Netlify
4. Done!

**Why this is better:**
- You can test with real data immediately
- No switching between dev/prod URLs later
- Frontend works from day one

### Option 2: Build Frontend Now, Deploy API Later
1. Build frontend to connect to `http://localhost:8000` (local API)
2. Run API locally: `uvicorn api.server:app --reload`
3. Test frontend locally
4. Later: Deploy API, update frontend config, deploy to Netlify

**Why this works:**
- You can start building UI immediately
- Just need to change API URL later (one config value)

## Recommended Path: Deploy API First

Since Railway deployment takes ~5 minutes and is super easy:

1. **Deploy API to Railway** (5 min)
   - Follow `docs/SIMPLE_DEPLOYMENT.md`
   - Get your API URL: `https://bookshelf.lindsaybrunner.com` (or Railway's auto URL)

2. **Build Frontend** (connect to production API)
   - Create frontend in `frontend/` directory
   - Set API URL: `https://bookshelf.lindsaybrunner.com` (or your Railway URL)
   - Build and test locally

3. **Deploy Frontend to Netlify**
   - Connect GitHub repo
   - Build command: `npm run build` (or whatever your framework uses)
   - Publish directory: `dist/` or `build/` (depends on framework)
   - Add environment variable: `VITE_API_URL=https://bookshelf.lindsaybrunner.com` (if using Vite)

4. **Configure Domain**
   - Netlify: Add `bookshelf.lindsaybrunner.com` (or subdomain)
   - Railway: Add same domain (or `api.bookshelf.lindsaybrunner.com`)

## Frontend Configuration

Your frontend will need to know where the API is. Use environment variables:

### For Vite (React/Vue)
```env
# .env.development
VITE_API_URL=http://localhost:8000

# .env.production
VITE_API_URL=https://bookshelf.lindsaybrunner.com
```

### For Next.js
```env
# .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# .env.production
NEXT_PUBLIC_API_URL=https://bookshelf.lindsaybrunner.com
```

### In Your Frontend Code
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'https://bookshelf.lindsaybrunner.com';

// Then use it
fetch(`${API_URL}/api/books?limit=10`)
```

## Netlify Configuration

Create `netlify.toml` in your project root:

```toml
[build]
  command = "cd frontend && npm run build"
  publish = "frontend/dist"

[[redirects]]
  from = "/api/*"
  to = "https://bookshelf.lindsaybrunner.com/api/:splat"
  status = 200
  force = true

# Or if API is on subdomain:
# [[redirects]]
#   from = "/api/*"
#   to = "https://api.bookshelf.lindsaybrunner.com/api/:splat"
#   status = 200
#   force = true
```

This makes `/api/*` requests proxy to your Railway API.

## Domain Setup Options

### Option A: Same Domain (Recommended)
- `bookshelf.lindsaybrunner.com` → Netlify (frontend)
- Netlify redirects `/api/*` → Railway API
- User sees one domain, seamless experience

### Option B: Subdomain
- `bookshelf.lindsaybrunner.com` → Netlify (frontend)
- `api.bookshelf.lindsaybrunner.com` → Railway (API)
- Frontend calls `api.bookshelf.lindsaybrunner.com/api/books`

## Testing Locally

1. **Start API locally:**
   ```bash
   export BOOKS_DATASET=datasets/lindsay
   uvicorn api.server:app --reload
   ```

2. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Frontend connects to:** `http://localhost:8000`

## Deployment Checklist

- [ ] API deployed to Railway/Render
- [ ] API accessible at production URL
- [ ] Frontend built with production API URL
- [ ] Frontend tested locally
- [ ] Frontend deployed to Netlify
- [ ] Domain configured on Netlify
- [ ] Domain configured on Railway (if using subdomain)
- [ ] CORS configured on API (already done!)
- [ ] Test end-to-end: Visit `https://bookshelf.lindsaybrunner.com`

## Quick Start: Deploy API First

Since you know Netlify, Railway will feel familiar:

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. New Project → Deploy from GitHub → Select `books-project`
4. Add env var: `BOOKS_DATASET=datasets/lindsay`
5. Wait 2 minutes
6. Copy your API URL
7. **Now build frontend** pointing to that URL
8. Deploy frontend to Netlify

**Total time: ~10 minutes to get API live, then you can build frontend!**

