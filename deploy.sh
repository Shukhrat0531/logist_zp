#!/bin/bash
# ===============================================
# Deploy Script — Run from your Mac
# Usage: ./deploy.sh
# ===============================================
set -e

SERVER="root@185.129.48.250"
REMOTE_DIR="/home/logist_zp"

echo "=== 1/5: Uploading project files ==="
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
    --exclude '.git' --exclude 'dist' --exclude '.env' \
    -e ssh \
    /Users/shukhrat/Desktop/logist_zp/ ${SERVER}:${REMOTE_DIR}/

echo "=== 2/5: Setting up backend Python venv ==="
ssh ${SERVER} << 'REMOTE'
cd /home/logist_zp/backend

# Create venv if it doesn't exist
if [ ! -d venv ]; then
    python3 -m venv venv
fi

# Install/upgrade dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Copy .env to backend
cp /home/logist_zp/.env /home/logist_zp/backend/.env

# Run database init (create tables + seed)
cd /home/logist_zp/backend
source venv/bin/activate
python3 -c "
import asyncio
from app.db.session import engine
from app.db.base import Base
from app.models import user, employee, reference, trip_invoice, machinery_session, payroll, audit_log, settings

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created')

asyncio.run(init())
"

# Run manual migration (safe — uses IF NOT EXISTS)
PGPASSWORD=logist_secret psql -h localhost -U logist logist_zp -f /home/logist_zp/manual_migration.sql 2>/dev/null || true

# Run seed
python3 -c "
import asyncio
from app.services.seed import run_seed
asyncio.run(run_seed())
" 2>/dev/null || true

echo "Backend setup complete"
REMOTE

echo "=== 3/5: Building frontend on server ==="
ssh ${SERVER} << 'REMOTE'
cd /home/logist_zp/frontend
npm install
npx vite build
echo "Frontend built"
REMOTE

echo "=== 4/5: Creating systemd service ==="
ssh ${SERVER} << 'REMOTE'
cat > /etc/systemd/system/logist-backend.service << 'SERVICE'
[Unit]
Description=Logist ZP Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/logist_zp/backend
EnvironmentFile=/home/logist_zp/.env
ExecStart=/home/logist_zp/backend/venv/bin/gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 127.0.0.1:8000 \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable logist-backend
systemctl restart logist-backend
echo "Backend service started"
REMOTE

echo "=== 5/5: Setting up SSL ==="
ssh ${SERVER} << 'REMOTE'
certbot --nginx -d qazair.inbrain.kz --non-interactive --agree-tos -m admin@inbrain.kz || echo "SSL setup failed (DNS might not be pointing to this server yet)"
systemctl restart nginx
REMOTE

echo ""
echo "============================================="
echo "  Deployment complete!"
echo "  Site: https://qazair.inbrain.kz"
echo "  API:  https://qazair.inbrain.kz/api/health"
echo "============================================="
