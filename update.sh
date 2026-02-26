#!/bin/bash
# ===============================================
# Update Script — Run from your Mac
# Usage: ./update.sh
# ===============================================
set -e

SERVER="root@185.129.48.250"
REMOTE_DIR="/home/logist_zp"

echo "=== 1/4: Uploading updated files ==="
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
    --exclude '.git' --exclude 'dist' --exclude '.env' \
    -e ssh \
    /Users/shukhrat/Desktop/logist_zp/ ${SERVER}:${REMOTE_DIR}/

echo "=== 2/4: Installing backend dependencies ==="
ssh ${SERVER} << 'REMOTE'
cd /home/logist_zp/backend
source venv/bin/activate
pip install -r requirements.txt -q
REMOTE

echo "=== 3/4: Running database migration ==="
ssh ${SERVER} << 'REMOTE'
PGPASSWORD=logist_secret psql -h localhost -U logist logist_zp -f /home/logist_zp/manual_migration.sql
REMOTE

echo "=== 4/4: Rebuilding frontend & restarting backend ==="
ssh ${SERVER} << 'REMOTE'
cd /home/logist_zp/frontend
npm install --silent
npx vite build
systemctl restart logist-backend
echo "Done! Backend restarted."
REMOTE

echo ""
echo "============================================="
echo "  Update complete!"
echo "  Site: https://qazair.inbrain.kz"
echo "============================================="
