#!/bin/bash
# ===============================================
# Server Setup Script - Run this ONCE on the server
# ssh root@185.129.48.250
# Then paste this and run
# ===============================================
set -e

echo "=== 1/6: Creating swap file (2GB) ==="
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap created"
else
    echo "Swap already exists"
fi

echo "=== 2/6: Installing system packages ==="
apt update -y
apt install -y postgresql postgresql-contrib python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl git

# Install Node.js 20
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi

echo "Node: $(node -v)"
echo "Python: $(python3 --version)"

echo "=== 3/6: Setting up PostgreSQL ==="
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='logist'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER logist WITH PASSWORD 'logist_secret';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='logist_zp'" | grep -q 1 || \
    sudo -u postgres createdb -O logist logist_zp
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE logist_zp TO logist;"
echo "PostgreSQL configured"

echo "=== 4/6: Creating project directory ==="
mkdir -p /home/logist_zp

echo "=== 5/6: Creating production .env ==="
cat > /home/logist_zp/.env << 'EOF'
POSTGRES_USER=logist
POSTGRES_PASSWORD=logist_secret
POSTGRES_DB=logist_zp
DATABASE_URL=postgresql+asyncpg://logist:logist_secret@localhost:5432/logist_zp
SECRET_KEY=qazair-prod-8Km3xPz7YwL2nR9cJbF4
ACCESS_TOKEN_EXPIRE_DAYS=30
BACKEND_CORS_ORIGINS=https://qazair.inbrain.kz,http://qazair.inbrain.kz
EOF
echo ".env created"

echo "=== 6/6: Configuring Nginx ==="
cat > /etc/nginx/sites-available/qazair << 'NGINX'
server {
    listen 80;
    server_name qazair.inbrain.kz;

    # Frontend (Vue SPA)
    location / {
        root /home/logist_zp/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy — strips /api prefix
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/qazair /etc/nginx/sites-enabled/qazair
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
echo "Nginx configured"

echo ""
echo "============================================="
echo "  Server setup complete!"
echo "  Now run deploy.sh from your Mac."
echo "============================================="

