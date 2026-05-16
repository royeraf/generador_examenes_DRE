#!/bin/bash
# deploy.sh — Deploy completo (frontend + backend) al VPS
# Repo: ~/sieva_repo/
# Web root: ~/sieva.drehuanuco.gob.pe/
# Uso: bash ~/sieva_repo/deploy.sh

REPO="$HOME/sieva_repo"
WEB="$HOME/sieva.drehuanuco.gob.pe"
FRONTEND="$REPO/frontend"
BACKEND="$REPO/backend"

fail() { echo "Error: $1"; exit 1; }

echo ">>> Pulling latest changes..."
cd "$REPO" && git pull || fail "git pull falló"

# ─── Frontend ────────────────────────────────────────────────────────────────
echo ">>> Installing frontend dependencies..."
cd "$FRONTEND" && pnpm install --no-frozen-lockfile || fail "pnpm install falló"

echo ">>> Building frontend..."
cd "$FRONTEND" && pnpm run build || fail "pnpm build falló"

echo ">>> Deploying frontend to web root..."
cp -a "$FRONTEND/dist/." "$WEB/" || fail "cp dist falló"

# ─── Backend ─────────────────────────────────────────────────────────────────
echo ">>> Updating backend dependencies..."
source "$BACKEND/venv/bin/activate"
pip install -r "$BACKEND/requirements.txt" -q

echo ">>> Running database migrations..."
cd "$BACKEND" && alembic upgrade head || fail "alembic upgrade falló"

echo ">>> Restarting backend service..."
sudo systemctl restart lectosistem || fail "No se pudo reiniciar lectosistem"
sleep 2
sudo systemctl is-active lectosistem && echo "Backend activo." || echo "AVISO: revisa con: sudo journalctl -u lectosistem -n 20"

# ─── Nginx cache ─────────────────────────────────────────────────────────────
echo ">>> Limpiando caché de nginx..."
sudo rm -rf /var/nginx/cache/drehua5/* 2>/dev/null || true
curl -sk -A "Mozilla/5.0" "https://sieva.drehuanuco.gob.pe/purge/" > /dev/null && echo "  Nginx purge OK" || true

echo ""
echo "Deploy completado."
