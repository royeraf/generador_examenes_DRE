#!/bin/bash
# dev.sh — Arranca el entorno de desarrollo local
# Backend: FastAPI en :8000  |  Frontend: Vite en :5173
# Uso: bash dev.sh

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$REPO/backend"
FRONTEND="$REPO/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

cleanup() {
    echo -e "\n${YELLOW}Deteniendo servicios...${NC}"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    echo -e "${GREEN}Listo.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Verificar MariaDB ────────────────────────────────────────────────────────
echo -e "${CYAN}[1/3] Verificando MariaDB...${NC}"
if ! systemctl is-active --quiet mariadb; then
    echo -e "${YELLOW}  MariaDB no está corriendo, iniciando...${NC}"
    sudo systemctl start mariadb
fi
if mariadb -u lectosistem -plectosistem_dev_2026 lectosistem_dre -e "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}  MariaDB OK${NC}"
else
    echo -e "${RED}  Error: no se puede conectar a MariaDB. Verifica que la BD esté creada.${NC}"
    echo -e "${RED}  Ejecuta primero: sudo mariadb < scripts/create_dev_db.sql${NC}"
    exit 1
fi

# ─── Backend ─────────────────────────────────────────────────────────────────
echo -e "${CYAN}[2/3] Arrancando backend (puerto 8000)...${NC}"
cd "$BACKEND"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Esperar a que el backend responda
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/api/health &>/dev/null; then
        echo -e "${GREEN}  Backend listo en http://localhost:8000${NC}"
        break
    fi
    sleep 1
done

# ─── Frontend ────────────────────────────────────────────────────────────────
echo -e "${CYAN}[3/3] Arrancando frontend (puerto 5173)...${NC}"
cd "$FRONTEND"
bun run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Entorno local listo${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "  Frontend : ${CYAN}http://localhost:5173${NC}"
echo -e "  Backend  : ${CYAN}http://localhost:8000${NC}"
echo -e "  API docs : ${CYAN}http://localhost:8000/api/docs${NC}"
echo -e "  Admin    : DNI ${YELLOW}00000000${NC}  /  pass ${YELLOW}admin123${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "  Ctrl+C para detener todo"
echo ""

wait
