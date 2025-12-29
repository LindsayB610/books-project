# Deployment Guide: bookshelf.lindsaybrunner.com

> **👋 Not a developer?** Check out **[SIMPLE_DEPLOYMENT.md](./SIMPLE_DEPLOYMENT.md)** instead! It's like using Netlify - super easy.

This guide covers deploying the Books API to `bookshelf.lindsaybrunner.com`.

## Overview

The Books API is a FastAPI application that serves read-only data from `books.csv`. This guide covers deployment options and setup steps.

## Prerequisites

1. **Domain**: `bookshelf.lindsaybrunner.com` configured and pointing to your server
2. **Server**: A VPS or cloud instance (e.g., DigitalOcean, AWS EC2, Linode, etc.)
3. **Python 3.7+**: Installed on the server
4. **Dataset**: Your `datasets/lindsay/books.csv` file ready to deploy

## Deployment Options

### Option 1: Simple VPS with Systemd (Recommended for MVP)

**Pros:**
- Simple setup
- Full control
- Low cost ($5-10/month)
- Easy to debug

**Cons:**
- Manual SSL certificate management
- Manual updates

**Best for:** Personal projects, learning, MVP

### Option 2: Docker + Reverse Proxy (Recommended for Production)

**Pros:**
- Isolated environment
- Easy to update
- Can use Docker Compose
- Works with any reverse proxy (nginx, Caddy, Traefik)

**Cons:**
- Slightly more complex setup
- Requires Docker knowledge

**Best for:** Production deployments, multiple services

### Option 3: Platform-as-a-Service (Railway, Render, Fly.io)

**Pros:**
- Zero infrastructure management
- Automatic SSL
- Easy deployments
- Free tiers available

**Cons:**
- Less control
- Can be more expensive at scale
- Vendor lock-in

**Best for:** Quick deployment, minimal ops

## Recommended: Option 1 (Simple VPS)

### Step 1: Server Setup

1. **Create a VPS** (DigitalOcean, Linode, AWS EC2, etc.)
   - Ubuntu 22.04 LTS recommended
   - 1GB RAM minimum (2GB recommended)
   - Basic firewall rules: allow SSH (22), HTTP (80), HTTPS (443)

2. **SSH into your server:**
   ```bash
   ssh root@your-server-ip
   ```

3. **Create a non-root user:**
   ```bash
   adduser bookshelf
   usermod -aG sudo bookshelf
   su - bookshelf
   ```

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install nginx (for reverse proxy)
sudo apt install -y nginx

# Install certbot (for SSL)
sudo apt install -y certbot python3-certbot-nginx
```

### Step 3: Deploy Application

1. **Clone repository** (or upload files):
   ```bash
   cd /home/bookshelf
   git clone <your-repo-url> books-project
   cd books-project
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set environment variable:**
   ```bash
   # Create .env file
   echo "BOOKS_DATASET=datasets/lindsay" > .env
   ```

4. **Test the API locally:**
   ```bash
   uvicorn api.server:app --host 0.0.0.0 --port 8000
   # Visit http://your-server-ip:8000/docs to verify
   ```

### Step 4: Configure Systemd Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/books-api.service
```

Add this content:

```ini
[Unit]
Description=Books API Service
After=network.target

[Service]
Type=simple
User=bookshelf
WorkingDirectory=/home/bookshelf/books-project
Environment="PATH=/home/bookshelf/books-project/venv/bin"
Environment="BOOKS_DATASET=datasets/lindsay"
ExecStart=/home/bookshelf/books-project/venv/bin/uvicorn api.server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable books-api
sudo systemctl start books-api
sudo systemctl status books-api
```

### Step 5: Configure Nginx Reverse Proxy

Create nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/bookshelf
```

Add this content:

```nginx
server {
    listen 80;
    server_name bookshelf.lindsaybrunner.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/bookshelf /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### Step 6: Configure DNS

1. **Add A record** in your DNS provider:
   - Type: `A`
   - Name: `bookshelf` (or `@` if using subdomain)
   - Value: Your server's IP address
   - TTL: 300 (or default)

2. **Wait for DNS propagation** (can take a few minutes to 48 hours)

3. **Verify DNS:**
   ```bash
   dig bookshelf.lindsaybrunner.com
   ```

### Step 7: Set Up SSL with Let's Encrypt

```bash
sudo certbot --nginx -d bookshelf.lindsaybrunner.com
```

Follow the prompts. Certbot will:
- Obtain SSL certificate
- Configure nginx automatically
- Set up auto-renewal

### Step 8: Configure CORS (if frontend on different domain)

If your frontend will be on a different domain, update the FastAPI app to allow CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bookshelf.lindsaybrunner.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 9: Firewall Configuration

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Verification

1. **Check API is running:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Check nginx is proxying:**
   ```bash
   curl http://bookshelf.lindsaybrunner.com/
   ```

3. **Check SSL:**
   ```bash
   curl https://bookshelf.lindsaybrunner.com/
   ```

4. **Visit in browser:**
   - API docs: `https://bookshelf.lindsaybrunner.com/docs`
   - Root: `https://bookshelf.lindsaybrunner.com/`

## Updating the Application

1. **Pull latest changes:**
   ```bash
   cd /home/bookshelf/books-project
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Restart service:**
   ```bash
   sudo systemctl restart books-api
   ```

3. **Update books.csv:**
   ```bash
   # Upload new books.csv to datasets/lindsay/books.csv
   # The API will read it on next request (stateless)
   ```

## Monitoring

### Check service status:
```bash
sudo systemctl status books-api
```

### View logs:
```bash
sudo journalctl -u books-api -f
```

### Check nginx logs:
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### API not responding:
1. Check service status: `sudo systemctl status books-api`
2. Check logs: `sudo journalctl -u books-api -n 50`
3. Verify port: `sudo netstat -tlnp | grep 8000`

### Nginx 502 Bad Gateway:
1. Check API is running: `curl http://localhost:8000/`
2. Check nginx config: `sudo nginx -t`
3. Check nginx error log: `sudo tail -f /var/log/nginx/error.log`

### SSL issues:
1. Check certificate: `sudo certbot certificates`
2. Test renewal: `sudo certbot renew --dry-run`

## Next Steps

Once the API is deployed and working:

1. **Test all endpoints** via the Swagger UI at `/docs`
2. **Verify CORS** if frontend will be on different domain
3. **Build frontend** against the production API
4. **Set up monitoring** (optional: UptimeRobot, Pingdom, etc.)

## Alternative: Docker Deployment

If you prefer Docker, see `Dockerfile` and `docker-compose.yml` in the repo root.

## Security Considerations

- ✅ API is read-only (no write endpoints)
- ✅ Running behind nginx reverse proxy
- ✅ SSL/TLS encryption
- ✅ Firewall configured
- ⚠️ Consider rate limiting if public-facing
- ⚠️ Consider authentication if you want to restrict access

