# Quick Start: Deploy Your API

**If you know how to use Netlify, this will be easy!**

## The Simple Way (Recommended)

1. **Go to [Railway.app](https://railway.app)** (it's like Netlify for backends)
2. **Sign up with GitHub** (same as Netlify)
3. **Click "New Project" → "Deploy from GitHub"**
4. **Select your `books-project` repo**
5. **Add environment variable:**
   - Name: `BOOKS_DATASET`
   - Value: `datasets/lindsay`
6. **Wait 2 minutes** - it auto-deploys!
7. **Add custom domain** `bookshelf.lindsaybrunner.com` (same DNS process as Netlify)

**That's it!** Your API will be live.

## Full Instructions

See **[docs/SIMPLE_DEPLOYMENT.md](./docs/SIMPLE_DEPLOYMENT.md)** for step-by-step guide with screenshots and troubleshooting.

## Test It

Once deployed, visit:
- `https://bookshelf.lindsaybrunner.com/docs` - API documentation
- `https://bookshelf.lindsaybrunner.com/api/books?limit=5` - See your books

## Updating

Just push to GitHub (like Netlify) - it auto-deploys!

