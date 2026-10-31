#!/bin/bash
# deploy.sh — Deploy completo (frontend + backend) al VPS
# Estructura: ~/sieva/app (repo) + ~/sieva/web (publicado)
# Uso: bash ~/sieva/deploy.sh
#
# Los symlinks ~/sieva_repo -> ~/sieva/app y
# ~/sieva.drehuanuco.gob.pe -> ~/sieva/web mantienen compatibilidad
# con systemd, cPanel y comandos históricos.

BASE="$HOME/sieva"
REPO="$BASE/app"
WEB="$BASE/web"
FRONTEND="$REPO/frontend"
BACKEND="$REPO/backend"

fail() { echo "Error: $1"; exit 1; }

echo ">>> Pulling latest changes..."
cd "$REPO" && git pull --ff-only || fail "git pull falló"

# ─── Frontend ────────────────────────────────────────────────────────────────
echo ">>> Installing frontend dependencies..."
rm -f "$FRONTEND/pnpm-lock.yaml"
cd "$FRONTEND" && pnpm install || fail "pnpm install falló"

echo ">>> Building frontend..."
cd "$FRONTEND" && pnpm run build || fail "pnpm build falló"

echo ">>> Publishing frontend (sin acumular builds viejos)..."
rsync -a --delete \
  --exclude='.htaccess' \
  --exclude='.well-known/' \
  "$FRONTEND/dist/" "$WEB/" || fail "rsync dist falló"

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
