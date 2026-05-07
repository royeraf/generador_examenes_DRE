#!/bin/bash
# vps_setup.sh — Instalación inicial del backend en el VPS (CentOS/AlmaLinux)
# Ejecutar UNA SOLA VEZ como el usuario del dominio:
#   bash ~/sieva_repo/vps_setup.sh

set -e

REPO="$HOME/sieva_repo"
BACKEND="$REPO/backend"
VPS_USER=$(whoami)

fail() { echo "ERROR: $1"; exit 1; }
info() { echo ""; echo ">>> $1"; }

# ─── 1. Python ────────────────────────────────────────────────────────────────
info "Verificando Python 3.11..."
if command -v python3.11 &>/dev/null; then
    PY=python3.11
elif command -v python3.10 &>/dev/null; then
    PY=python3.10
elif command -v python3.9 &>/dev/null; then
    PY=python3.9
    echo "AVISO: Python 3.9 puede tener problemas. Se recomienda 3.10+."
    echo "Para instalar Python 3.11: sudo dnf install python3.11 -y"
else
    fail "No se encontró Python 3.9+. Instala con: sudo dnf install python3.11 -y"
fi
echo "Usando: $($PY --version)"

# ─── 2. Venv + dependencias ──────────────────────────────────────────────────
info "Creando entorno virtual..."
cd "$BACKEND"
$PY -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencias instaladas."

# ─── 3. Archivo .env ─────────────────────────────────────────────────────────
info "Configurando .env de producción..."
if [ ! -f "$BACKEND/.env" ]; then
    cp "$BACKEND/.env.example" "$BACKEND/.env"
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s|cambia-esta-clave-secreta-en-produccion-usa-openssl-rand-hex-32|$SECRET|g" "$BACKEND/.env"
    echo ""
    echo "Se creó .env con SECRET_KEY generada automáticamente."
    echo "IMPORTANTE: Edita $BACKEND/.env y agrega tus API keys:"
    echo "  GOOGLE_API_KEY=tu_clave_aqui"
    echo "  OPENAI_API_KEY=tu_clave_aqui"
    echo ""
    read -p "Presiona ENTER para abrir el editor (nano) o Ctrl+C para hacerlo manualmente... "
    nano "$BACKEND/.env"
else
    echo ".env ya existe, se omite."
fi

# ─── 4. Base de datos + migraciones ─────────────────────────────────────────
info "Ejecutando migraciones Alembic..."
cd "$BACKEND"
source venv/bin/activate
alembic upgrade head
echo "Migraciones OK."

# ─── 5. Servicio systemd ─────────────────────────────────────────────────────
info "Instalando servicio systemd..."
SERVICE_SRC="$BACKEND/lectosistem.service"
SERVICE_DST="/etc/systemd/system/lectosistem.service"

sed "s/__USER__/$VPS_USER/g; s|/home/__USER__/sieva.drehuanuco.gob.pe/sieva_repo|$REPO|g" \
    "$SERVICE_SRC" | sudo tee "$SERVICE_DST" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable lectosistem
sudo systemctl start lectosistem
sleep 2
sudo systemctl status lectosistem --no-pager

# ─── 6. Verificar que escucha en 8000 ────────────────────────────────────────
info "Verificando puerto 8000..."
if curl -sf http://127.0.0.1:8000/api/docs > /dev/null 2>&1; then
    echo "Backend respondiendo en :8000"
else
    echo "AVISO: El backend no responde aún. Revisa: sudo journalctl -u lectosistem -n 30"
fi

# ─── 7. Snippet de Nginx ─────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  PASO FINAL: Agrega este bloque a tu config de Nginx"
echo "  (dentro del server {} del dominio sieva.drehuanuco.gob.pe)"
echo "============================================================"
echo ""
cat << 'NGINX_SNIPPET'
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
NGINX_SNIPPET
echo ""
echo "Luego: sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "============================================================"
echo "  Setup completado."
echo "============================================================"
