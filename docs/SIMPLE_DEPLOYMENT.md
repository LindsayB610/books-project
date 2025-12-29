# Simple Deployment Guide (Netlify-Style)

If you know how to use Netlify, this guide is for you! We'll use **Railway** or **Render** - they work just like Netlify but for Python backends.

## Choose Your Platform

Both are free to start and super simple:

- **Railway** (recommended) - Most similar to Netlify
- **Render** - Also very easy, good free tier

## Option 1: Railway (Recommended - Easiest)

Railway is like Netlify for backends. Here's how to deploy:

### Step 1: Sign Up
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (same as Netlify!)

### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `books-project` repository
4. Railway will automatically detect it's a Python project

### Step 3: Configure Environment Variables
1. Click on your project
2. Go to "Variables" tab
3. Add this variable:
   - **Name**: `BOOKS_DATASET`
   - **Value**: `datasets/lindsay`
4. Click "Add"

### Step 4: Deploy
1. Railway will automatically start deploying
2. Wait 2-3 minutes
3. Your API will be live at a URL like `https://your-project.up.railway.app`

### Step 5: Custom Domain (Like Netlify!)
1. Click "Settings" → "Networking"
2. Click "Custom Domain"
3. Enter: `bookshelf.lindsaybrunner.com`
4. Railway will give you DNS instructions (just like Netlify does)
5. Add the CNAME record in your DNS (same process as Netlify)
6. Wait a few minutes for DNS to propagate

### Step 6: Test It
Visit: `https://bookshelf.lindsaybrunner.com/docs`

You should see the API documentation page!

---

## Option 2: Render (Alternative)

Render is also very simple and has a good free tier.

### Step 1: Sign Up
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create New Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Select `books-project`

### Step 3: Configure
- **Name**: `books-api` (or whatever you want)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variable
1. Scroll down to "Environment Variables"
2. Click "Add Environment Variable"
3. **Key**: `BOOKS_DATASET`
4. **Value**: `datasets/lindsay`
5. Click "Save"

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait 3-5 minutes for first deployment
3. Your API will be live at `https://your-service.onrender.com`

### Step 6: Custom Domain
1. Go to "Settings" → "Custom Domains"
2. Add `bookshelf.lindsaybrunner.com`
3. Follow DNS instructions (same as Netlify)
4. Add the CNAME record in your DNS provider

---

## Updating Your Books Data

When you update `datasets/lindsay/books.csv`:

1. **Push to GitHub** (just like Netlify)
2. Railway/Render will automatically redeploy
3. Your new data will be live in a few minutes

Or if you want to update manually:
- **Railway**: Upload the file through their dashboard
- **Render**: You can SSH in, but pushing to GitHub is easier

---

## Troubleshooting

### API not working?
1. Check the "Deployments" or "Logs" tab (like Netlify's deploy logs)
2. Make sure `BOOKS_DATASET=datasets/lindsay` is set
3. Check that `datasets/lindsay/books.csv` exists in your repo

### Domain not working?
1. Check DNS propagation (same as Netlify - can take a few minutes)
2. Make sure you added the CNAME record correctly
3. Wait up to 48 hours (usually much faster)

### Need help?
- Railway: Great docs and Discord community
- Render: Good documentation and support

---

## Cost

**Free tier is usually enough:**
- Railway: $5/month free credit (plenty for personal use)
- Render: Free tier available (may sleep after inactivity)

Both are very affordable if you need to upgrade.

---

## Next Steps

Once your API is live at `https://bookshelf.lindsaybrunner.com`:

1. ✅ Test it: Visit `/docs` to see the API documentation
2. ✅ Test endpoints: Try `/api/books?limit=5`
3. ✅ **Build your frontend** (can deploy to Netlify!)
4. ✅ Connect frontend to your API

**Frontend goes on Netlify!** See `docs/FRONTEND_DEPLOYMENT.md` for details on:
- How to configure frontend to connect to your API
- How to deploy frontend to Netlify
- Domain setup options

---

## Quick Comparison to Netlify

| Netlify | Railway/Render |
|---------|---------------|
| Connect GitHub repo | ✅ Same |
| Automatic deploys | ✅ Same |
| Custom domain | ✅ Same |
| Environment variables | ✅ Same |
| Deploy logs | ✅ Same |
| Free tier | ✅ Same |

The only difference: Railway/Render runs Python backends, Netlify runs static sites. Everything else works the same way!

