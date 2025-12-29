# Deployment Checklist: bookshelf.lindsaybrunner.com

Quick checklist to get your API live before building the frontend.

## Pre-Deployment

- [ ] **Domain configured**
  - [ ] DNS A record points to your server IP
  - [ ] DNS has propagated (check with `dig bookshelf.lindsaybrunner.com`)

- [ ] **Server ready**
  - [ ] VPS/cloud instance created
  - [ ] SSH access working
  - [ ] Firewall configured (SSH, HTTP, HTTPS)

- [ ] **Dataset ready**
  - [ ] `datasets/lindsay/books.csv` is up to date
  - [ ] Data validated (`python scripts/validate_books_csv.py --dataset datasets/lindsay`)

## Deployment Steps

### Option A: Simple VPS (Recommended)

- [ ] Install dependencies (Python, nginx, certbot)
- [ ] Clone/upload code to server
- [ ] Create virtual environment and install requirements
- [ ] Set `BOOKS_DATASET=datasets/lindsay` environment variable
- [ ] Create systemd service file
- [ ] Start and enable service
- [ ] Configure nginx reverse proxy
- [ ] Test API locally (`curl http://localhost:8000/`)
- [ ] Configure DNS
- [ ] Set up SSL with Let's Encrypt
- [ ] Test production URL (`curl https://bookshelf.lindsaybrunner.com/`)

### Option B: Docker

- [ ] Install Docker and Docker Compose on server
- [ ] Build Docker image
- [ ] Configure docker-compose.yml with correct dataset
- [ ] Start containers
- [ ] Configure nginx reverse proxy (if not using Docker for nginx)
- [ ] Set up SSL
- [ ] Test production URL

### Option C: Platform-as-a-Service

- [ ] Create account (Railway, Render, Fly.io, etc.)
- [ ] Connect repository
- [ ] Set environment variables (`BOOKS_DATASET=datasets/lindsay`)
- [ ] Deploy
- [ ] Configure custom domain
- [ ] Test production URL

## Post-Deployment Verification

- [ ] **API is accessible**
  - [ ] Root endpoint: `https://bookshelf.lindsaybrunner.com/`
  - [ ] API docs: `https://bookshelf.lindsaybrunner.com/docs`
  - [ ] Books endpoint: `https://bookshelf.lindsaybrunner.com/api/books?limit=5`

- [ ] **SSL working**
  - [ ] HTTPS redirects HTTP
  - [ ] Certificate is valid (check browser padlock)

- [ ] **CORS configured** (if frontend on different domain)
  - [ ] Test from browser console or frontend

- [ ] **Data is correct**
  - [ ] Books endpoint returns your data
  - [ ] Stats endpoint shows correct counts
  - [ ] Search endpoint works

## Before Building Frontend

- [ ] API is stable and accessible
- [ ] All endpoints tested via Swagger UI (`/docs`)
- [ ] CORS configured for frontend domain
- [ ] Environment variables documented
- [ ] Update process documented (how to update books.csv)

## Quick Test Commands

```bash
# Test API locally
curl http://localhost:8000/

# Test API via domain
curl https://bookshelf.lindsaybrunner.com/

# Test books endpoint
curl "https://bookshelf.lindsaybrunner.com/api/books?limit=5"

# Test search
curl "https://bookshelf.lindsaybrunner.com/api/books/search?q=test"

# Test stats
curl https://bookshelf.lindsaybrunner.com/api/stats
```

## Next Steps After Deployment

1. ✅ API is live and tested
2. Build frontend (can use production API or local dev server)
3. Deploy frontend (same domain or subdomain)
4. Test end-to-end

