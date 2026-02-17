# FloodGuard-AI Backend - Deployment Guide

## Hướng dẫn triển khai production

### Mục lục
1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
2. [Chuẩn bị môi trường](#chuẩn-bị-môi-trường)
3. [Triển khai với Docker](#triển-khai-với-docker)
4. [Triển khai manual](#triển-khai-manual)
5. [Cấu hình Nginx](#cấu-hình-nginx)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)

---

## Yêu cầu hệ thống

### Hardware Requirements (Production)
- **CPU**: 4+ cores
- **RAM**: 8GB+ (16GB khuyến nghị)
- **Storage**: 100GB+ SSD
- **Network**: Stable internet connection

### Software Requirements
- **OS**: Ubuntu 22.04 LTS hoặc mới hơn
- **Python**: 3.11+
- **Docker**: 24.0+ (nếu dùng containerization)
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Nginx**: 1.24+ (nếu dùng reverse proxy)

---

## Chuẩn bị môi trường

### 1. Update hệ thống
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Cài đặt dependencies
```bash
# Build tools
sudo apt install -y build-essential git curl wget

# Python development
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3-pip

# Geospatial libraries
sudo apt install -y gdal-bin libgdal-dev libgeos-dev libproj-dev

# Database
sudo apt install -y postgresql postgresql-contrib

# Redis
sudo apt install -y redis-server
```

### 3. Setup Google Earth Engine

**Tạo Service Account:**
1. Truy cập [Google Cloud Console](https://console.cloud.google.com)
2. Tạo project mới hoặc chọn project có sẵn
3. Enable Earth Engine API
4. Tạo Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Grant role: **Earth Engine Resource Writer**
5. Tạo key (JSON format)
6. Download và lưu tại: `./credentials/gee-key.json`

**Đăng ký Earth Engine:**
```bash
# Install Earth Engine
pip install earthengine-api

# Authenticate
earthengine authenticate

# Test connection
python -c "import ee; ee.Initialize(); print('GEE OK')"
```

### 4. Setup Google Gemini API

1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Lưu key vào file `.env`:
```env
GEMINI_API_KEY=your-api-key-here
```

### 5. Setup Email (Gmail)

1. Enable 2-Factor Authentication trên Gmail
2. Tạo App Password:
   - Google Account → Security → App passwords
   - Chọn "Mail" và "Other device"
   - Copy generated password
3. Cấu hình trong `.env`:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## Triển khai với Docker

### Bước 1: Clone repository
```bash
git clone https://github.com/your-org/floodguard-ai-backend.git
cd floodguard-ai-backend
```

### Bước 2: Cấu hình environment
```bash
# Copy và chỉnh sửa .env
cp .env.example .env
nano .env
```

**Cấu hình quan trọng:**
```env
# Production settings
DEBUG=False
ENVIRONMENT=production

# Database (sử dụng container)
DATABASE_URL=postgresql://floodguard_user:secure_password@postgres:5432/floodguard_db

# Redis (sử dụng container)
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=generate-a-secure-random-key-min-32-chars
```

### Bước 3: Chuẩn bị credentials
```bash
# Tạo thư mục credentials
mkdir -p credentials

# Copy GEE service account key
cp /path/to/your/gee-key.json credentials/

# Set permissions
chmod 600 credentials/gee-key.json
```

### Bước 4: Build và chạy
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

### Bước 5: Verify deployment
```bash
# Health check
curl http://localhost:8000/health

# Test API
curl http://localhost:8000/api/regions

# Check Swagger docs
open http://localhost:8000/docs
```

---

## Triển khai Manual

### Bước 1: Setup Python environment
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Bước 2: Setup PostgreSQL
```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE floodguard_db;
CREATE USER floodguard_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE floodguard_db TO floodguard_user;
\q
EOF

# Test connection
psql -U floodguard_user -d floodguard_db -h localhost
```

### Bước 3: Setup Redis
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Set bind address
bind 127.0.0.1

# Set password (optional but recommended)
requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

### Bước 4: Run application
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Bước 5: Setup systemd service
```bash
# Create service file
sudo nano /etc/systemd/system/floodguard.service
```

**Nội dung file:**
```ini
[Unit]
Description=FloodGuard-AI Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/floodguard-backend
Environment="PATH=/opt/floodguard-backend/venv/bin"
ExecStart=/opt/floodguard-backend/venv/bin/gunicorn \
    app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start floodguard
sudo systemctl enable floodguard
sudo systemctl status floodguard
```

---

## Cấu hình Nginx

### Install Nginx
```bash
sudo apt install -y nginx
```

### Configure reverse proxy
```bash
sudo nano /etc/nginx/sites-available/floodguard
```

**Nội dung cấu hình:**
```nginx
upstream floodguard_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.floodguard-ai.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://floodguard_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for future use)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if needed)
    location /static/ {
        alias /opt/floodguard-backend/static/;
        expires 7d;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://floodguard_backend/health;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/floodguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/TLS Setup

### Với Let's Encrypt (Certbot)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.floodguard-ai.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### Manual SSL configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.floodguard-ai.com;

    ssl_certificate /etc/ssl/certs/floodguard.crt;
    ssl_certificate_key /etc/ssl/private/floodguard.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.floodguard-ai.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring & Logging

### Setup log rotation
```bash
sudo nano /etc/logrotate.d/floodguard
```

```
/var/log/floodguard/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload floodguard > /dev/null 2>&1
    endscript
}
```

### Prometheus monitoring
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

---

## Backup & Recovery

### Database backup
```bash
# Daily backup script
cat > /opt/scripts/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/floodguard"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U floodguard_user floodguard_db | \
    gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/scripts/backup-db.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/scripts/backup-db.sh
```

### Application backup
```bash
# Backup application and configs
tar -czf /var/backups/floodguard/app_$(date +%Y%m%d).tar.gz \
    /opt/floodguard-backend \
    --exclude='venv' \
    --exclude='__pycache__'
```

### Recovery procedure
```bash
# Restore database
gunzip -c /var/backups/floodguard/db_backup_YYYYMMDD.sql.gz | \
    psql -U floodguard_user floodguard_db

# Restore application
tar -xzf /var/backups/floodguard/app_YYYYMMDD.tar.gz -C /
```

---

## Troubleshooting

### Check logs
```bash
# Application logs
docker-compose logs -f backend
# hoặc
sudo journalctl -u floodguard -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Common issues

**1. GEE Authentication Error**
```bash
# Re-authenticate
earthengine authenticate

# Check service account
python -c "import ee; ee.Initialize(); print('OK')"
```

**2. Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U floodguard_user -d floodguard_db -h localhost
```

**3. High Memory Usage**
```bash
# Check memory
free -h

# Restart services
docker-compose restart backend
# hoặc
sudo systemctl restart floodguard
```

---

## Security Checklist

- [ ] Firewall configured (UFW/iptables)
- [ ] SSH key-only authentication
- [ ] SSL/TLS certificates installed
- [ ] Database passwords strong and unique
- [ ] API keys stored in environment variables
- [ ] Regular security updates
- [ ] Backup strategy implemented
- [ ] Log monitoring active
- [ ] Rate limiting configured
- [ ] CORS properly configured

---

## Performance Tuning

### PostgreSQL
```sql
-- Edit postgresql.conf
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB
max_connections = 100
```

### Redis
```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Uvicorn/Gunicorn
```bash
# Optimal workers: (2 x CPU cores) + 1
gunicorn app.main:app \
    --workers 9 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 60 \
    --keep-alive 5
```

---

## Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Earth Engine](https://developers.google.com/earth-engine)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
