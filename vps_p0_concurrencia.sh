#!/bin/bash
# vps_p0_concurrencia.sh — Aplica el plan P0 del análisis de concurrencia.
#
#   sudo bash ~/sieva_repo/vps_p0_concurrencia.sh
#
# Qué hace:
#   1. nginx: manda /api/ directo a gunicorn (sin Apache, sin cache ni
#      proxy_cache_lock) y sube proxy_read_timeout a 300 s.
#   2. systemd: deja el unit de lectosistem con 8 workers y timeout 180 s
#      (se aplica en el próximo restart; ahora mismo ya hay 8 en caliente).
#   3. MariaDB: thread_cache_size=64 y slow query log (>1 s), en caliente y
#      persistido en /etc/my.cnf.d/zz-sieva.cnf.
#
# Es idempotente y hace backup + rollback si `nginx -t` falla.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VHOST="/etc/nginx/vhosts/drehua5__sieva_drehuanuco_gob_pe.conf"
UNIT="/etc/systemd/system/lectosistem.service"
MARK="# P0-concurrencia"
TS="$(date +%Y%m%d_%H%M%S)"

info() { echo ""; echo ">>> $1"; }
ok()   { echo "    OK: $1"; }
fail() { echo "    ERROR: $1" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "Ejecuta con sudo: sudo bash $0"
[ -f "$VHOST" ] || fail "No existe $VHOST"

# ─── 1. nginx: /api directo a gunicorn ──────────────────────────────────────
info "1/3 nginx — /api/ directo a gunicorn:8000"

if grep -q "$MARK" "$VHOST"; then
    ok "ya estaba aplicado (sin cambios)"
else
    cp -a "$VHOST" "$VHOST.bak.$TS"
    ok "backup: $VHOST.bak.$TS"

    python3 - "$VHOST" <<'PY'
import re
import sys

path = sys.argv[1]
lines = open(path).read().splitlines(keepends=True)

BLOQUE = """    # P0-concurrencia: /api va directo a gunicorn, sin Apache ni cache de nginx.
    # Evita el proxy_cache_lock (serializaba peticiones a la misma URL) y el
    # salto nginx -> Apache -> gunicorn (TLS nuevo por request, sin keepalive).
    location ^~ /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_connect_timeout 10s;
        client_max_body_size 15m;
    }

"""

# Localizar el server{} de HTTPS del dominio sieva.
inicio = None
for i, linea in enumerate(lines):
    if re.match(r"\s*listen\s+[0-9.]+:443\s+ssl\s*;", linea):
        for j in range(i, min(i + 15, len(lines))):
            if re.match(r"\s*server_name\s", lines[j]) and "sieva.drehuanuco.gob.pe" in lines[j]:
                inicio = i
                break
    if inicio is not None:
        break

if inicio is None:
    sys.exit("No se encontró el server{} 443 de sieva.drehuanuco.gob.pe")

# Insertar antes del primer location del bloque (el regex catch-all).
destino = None
for k in range(inicio, len(lines)):
    if re.match(r"\s*location\s", lines[k]):
        destino = k
        break
    if re.match(r"\s*server\s*\{", lines[k]) and k != inicio:
        break

if destino is None:
    sys.exit("No se encontró un location dentro del server{} 443")

lines.insert(destino, BLOQUE)
open(path, "w").writelines(lines)
print("    insertado antes de la línea %d" % (destino + 1))
PY

    if ! nginx -t 2>/tmp/nginx_t.err; then
        echo "    nginx -t FALLÓ, restaurando backup..." >&2
        cat /tmp/nginx_t.err >&2
        cp -a "$VHOST.bak.$TS" "$VHOST"
        fail "config restaurada, no se recargó nginx"
    fi
    ok "nginx -t correcto"
    systemctl reload nginx
    ok "nginx recargado"
fi

# ─── 2. systemd: 8 workers persistentes ─────────────────────────────────────
info "2/3 systemd — lectosistem con 8 workers"

if grep -q -- "-w 8" "$UNIT"; then
    ok "ya estaba aplicado (sin cambios)"
else
    cp -a "$UNIT" "$UNIT.bak.$TS"
    sed -i "s/-w 2/-w 8/; s/--timeout 120/--timeout 180 --graceful-timeout 30/" "$UNIT"
    systemctl daemon-reload
    ok "unit actualizado (se aplica en el próximo restart; en caliente ya hay 8)"
fi

# ─── 3. MariaDB: thread cache + slow query log ──────────────────────────────
info "3/3 MariaDB — thread_cache_size y slow query log"

mysql --protocol=socket -e "
    SET GLOBAL thread_cache_size = 64;
    SET GLOBAL slow_query_log = ON;
    SET GLOBAL long_query_time = 1;
" || fail "no se pudo aplicar en caliente"

cat > /etc/my.cnf.d/zz-sieva.cnf <<'EOF'
# SIEVA — ajustes de concurrencia (ver docs/ANALISIS_CONCURRENCIA.md)
[mysqld]
thread_cache_size = 64
slow_query_log = 1
long_query_time = 1
# Se aplica en el próximo reinicio de MariaDB
innodb_buffer_pool_instances = 4
EOF

ok "variables aplicadas y persistidas en /etc/my.cnf.d/zz-sieva.cnf"

# ─── Verificación ───────────────────────────────────────────────────────────
info "Verificación"
echo "    workers activos:"
ps -eo cmd | grep "[g]unicorn" | head -1 | sed "s/^/      /"
echo "    variables MariaDB:"
mysql --protocol=socket -N -e "SHOW VARIABLES WHERE Variable_name IN ('thread_cache_size','slow_query_log','long_query_time');" | sed "s/^/      /"
echo "    /api responde por nginx:"
curl -sk -A "Mozilla/5.0" -o /dev/null -w "      HTTP %{http_code} en %{time_total}s\n" https://sieva.drehuanuco.gob.pe/api/health

echo ""
echo "Listo. Para validar la concurrencia:"
echo "  ab -n 100 -c 20 -H 'User-Agent: Mozilla/5.0' https://sieva.drehuanuco.gob.pe/api/health"
echo ""
echo "NOTA: el vhost lo regenera el Nginx Manager de cPanel. Si se regenera,"
echo "vuelve a ejecutar este script (detecta el marcador '$MARK')."
