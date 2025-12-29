# Quick Start: Get Everything Running

## The Fastest Path (Recommended)

### Step 1: Deploy API (5 minutes)
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `books-project` repository
5. Add environment variable:
   - Name: `BOOKS_DATASET`
   - Value: `datasets/lindsay`
6. Wait 2 minutes for deployment
7. Copy your API URL (something like `https://your-project.up.railway.app`)

**✅ API is now live!** Test it: Visit `https://your-api-url/docs`

### Step 2: Build Frontend (Now or Later)
You can build the frontend now and point it to your Railway API URL, or wait until later. Either works!

**If building now:**
- Set API URL to your Railway URL in frontend config
- Test locally: `npm run dev`
- When ready, deploy to Netlify

**If waiting:**
- Deploy API first (done in Step 1!)
- Build frontend later
- Deploy frontend to Netlify

### Step 3: Deploy Frontend to Netlify
1. Build your frontend (React, Vue, etc.)
2. Go to Netlify
3. Connect your GitHub repo
4. Set build command: `cd frontend && npm run build` (or whatever)
5. Set publish directory: `frontend/dist` (or `frontend/build`)
6. Add environment variable: `VITE_API_URL=https://your-railway-url` (if using Vite)
7. Deploy!

### Step 4: Configure Domains
- **Netlify**: Add `bookshelf.lindsaybrunner.com` (or subdomain)
- **Railway**: Add same domain (or `api.bookshelf.lindsaybrunner.com`)

## Architecture

```
Frontend (Netlify)  ──>  API (Railway)
bookshelf.              bookshelf.
lindsaybrunner.com      lindsaybrunner.com/api
```

Both can share the same domain, or use subdomains. Your choice!

## Questions?

- **API deployment**: See `docs/SIMPLE_DEPLOYMENT.md`
- **Frontend setup**: See `docs/FRONTEND_DEPLOYMENT.md`
- **Domain configuration**: Same process as your other Netlify sites!

