#!/bin/bash
# deploy.sh — Deploy frontend Vue de SIEVA al VPS
# Repo vive en ~/sieva.drehuanuco.gob.pe/sieva_repo/
# Build se copia a ~/sieva.drehuanuco.gob.pe/
# Uso: bash ~/sieva.drehuanuco.gob.pe/sieva_repo/deploy.sh

REPO="$HOME/sieva.drehuanuco.gob.pe/sieva_repo"
WEB="$HOME/sieva.drehuanuco.gob.pe"
FRONTEND="$REPO/frontend"

fail() { echo "✖  Error: $1"; exit 1; }

echo "▸ Pulling latest changes..."
cd "$REPO" && git pull || fail "git pull falló"

echo "▸ Installing dependencies..."
cd "$FRONTEND" && npm install || fail "npm install falló"

echo "▸ Building frontend..."
cd "$FRONTEND" && npm run build || fail "npm build falló"

echo "▸ Deploying to web root..."
cp -r "$FRONTEND/dist/"* "$WEB/" || fail "cp dist falló"

echo "▸ Limpiando caché de nginx..."
sudo rm -rf /var/nginx/cache/drehua5/* 2>/dev/null && echo "  Nginx cache limpiado" || echo "  Sin permisos para limpiar nginx cache"
curl -sk -A "Mozilla/5.0" "https://sieva.drehuanuco.gob.pe/purge/" > /dev/null && echo "  Nginx purge OK"

echo ""
echo "✔  Deploy SIEVA completado."
