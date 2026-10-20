#!/bin/bash
# vps_p0_concurrencia.sh — Aplica/garantiza el plan P0 del análisis de concurrencia.
#
#   sudo bash ~/sieva_repo/vps_p0_concurrencia.sh
#
# Qué hace:
#   1. nginx: garantiza el bloque `location ^~ /api/` (directo a gunicorn, sin
#      Apache ni cache) y desactiva cache_lock_enable en la config de ngxconf,
#      que es la fuente que regenera el vhost.
#   2. systemd: deja el unit de lectosistem con 8 workers y timeout 180 s.
#   3. MariaDB: thread_cache_size=64 y slow query log (>1 s), en caliente y
#      persistido en /etc/my.cnf.d/zz-sieva.cnf.
#   4. Instala un watchdog (timer systemd cada 30 s) que re-aplica el bloque
#      /api si ngxconf regenera el vhost. No hay que volver a ejecutar nada.
#
# Idempotente. Hace backup y rollback si `nginx -t` falla.

set -euo pipefail

VHOST="/etc/nginx/vhosts/drehua5__sieva_drehuanuco_gob_pe.conf"
UNIT="/etc/systemd/system/lectosistem.service"
YML="/home/drehua5/.imh/nginx/sieva_drehuanuco_gob_pe.yml"
PATCHER="/usr/local/sbin/sieva-api-direct.py"
WATCHDOG="/usr/local/sbin/sieva-api-direct.sh"
BACKUP_DIR="/var/backups/sieva"
MARK="# P0-concurrencia"
TS="$(date +%Y%m%d_%H%M%S)"

info() { echo ""; echo ">>> $1"; }
ok()   { echo "    OK: $1"; }
warn() { echo "    AVISO: $1"; }
fail() { echo "    ERROR: $1" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "Ejecuta con sudo: sudo bash $0"
[ -f "$VHOST" ] || fail "No existe $VHOST"
mkdir -p "$BACKUP_DIR"

# ─── Patcher reutilizable (lo usan el script y el watchdog) ─────────────────
cat > "$PATCHER" <<'PY'
#!/usr/bin/env python3
"""Inserta el bloque `location ^~ /api/` en el server{} 443 de sieva.

Idempotente: si el bloque ya está, no hace nada. Pensado para ejecutarse
también desde el watchdog cuando ngxconf regenera el vhost.
"""
import re
import sys

path = sys.argv[1]
lines = open(path).read().splitlines(keepends=True)

if any("location ^~ /api/" in l for l in lines):
    sys.exit(0)

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
print("insertado antes de la línea %d" % (destino + 1))
PY
chmod 750 "$PATCHER"

# ─── 1. nginx: bloque /api ──────────────────────────────────────────────────
info "1/4 nginx — /api/ directo a gunicorn:8000"

if grep -q "location ^~ /api/" "$VHOST"; then
    ok "bloque /api ya presente (sin cambios)"
else
    cp -a "$VHOST" "$BACKUP_DIR/vhost.$TS"
    python3 "$PATCHER" "$VHOST"
    ok "bloque insertado"

    if ! nginx -t 2>/tmp/nginx_t.err; then
        cat /tmp/nginx_t.err >&2
        cp -a "$BACKUP_DIR/vhost.$TS" "$VHOST"
        fail "nginx -t falló; vhost restaurado"
    fi
    systemctl reload nginx
    ok "nginx -t correcto y recargado"
fi

# ─── 2. ngxconf: desactivar cache_lock en el origen ─────────────────────────
info "2/4 ngxconf — cache_lock_enable: false (sobrevive regeneraciones)"

if [ -f "$YML" ]; then
    cp -a "$YML" "$BACKUP_DIR/yml.$TS"
    python3 - "$YML" <<'PY'
import re
import sys
import yaml

path = sys.argv[1]
texto = open(path).read()

if re.search(r"^cache_lock_enable:\s*false\s*$", texto, re.M):
    print("ya estaba en false")
elif re.search(r"^cache_lock_enable:\s*true\s*$", texto, re.M):
    texto = re.sub(r"^cache_lock_enable:\s*true\s*$", "cache_lock_enable: false", texto, flags=re.M)
    open(path, "w").write(texto)
    print("cambiado a false")
elif not re.search(r"^cache_lock_enable:", texto, re.M):
    open(path, "a").write("\ncache_lock_enable: false\n")
    print("añadido cache_lock_enable: false")
else:
    print("valor no booleano, se deja como está")

yaml.safe_load(open(path))
PY
    chown drehua5:drehua5 "$YML"
    chmod 664 "$YML"
    ok "config de ngxconf válida (se aplica en la próxima regeneración)"
    warn "no hace falta hacer nada más: el watchdog cubre el hueco del bloque /api"
    warn "validación opcional: sudo ngxconf --user drehua5 --force --reload --nofpm --skipfpmbuild --nohttpd --skiphttpdbuild"
else
    warn "no existe $YML; se omite (el watchdog sigue cubriendo el bloque /api)"
fi

# ─── 3. systemd: 8 workers persistentes ─────────────────────────────────────
info "3/4 systemd — lectosistem con 8 workers"

if grep -q -- "-w 8" "$UNIT"; then
    ok "ya estaba aplicado (sin cambios)"
else
    cp -a "$UNIT" "$BACKUP_DIR/unit.$TS"
    sed -i "s/-w 2/-w 8/; s/--timeout 120/--timeout 180 --graceful-timeout 30/" "$UNIT"
    systemctl daemon-reload
    ok "unit actualizado (se aplica en el próximo restart)"
fi

# ─── 4. MariaDB ─────────────────────────────────────────────────────────────
info "4/4 MariaDB — thread_cache_size y slow query log"

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

# ─── Watchdog: re-aplicar el bloque si ngxconf regenera el vhost ────────────
info "watchdog — re-aplicar /api si el vhost se regenera"

cat > "$WATCHDOG" <<'SH'
#!/bin/bash
# Re-aplica el bloque /api directo si ngxconf regeneró el vhost.
# Lo ejecuta sieva-api-direct.timer cada 30 s. Silencioso si todo está bien.
set -u

VHOST="/etc/nginx/vhosts/drehua5__sieva_drehuanuco_gob_pe.conf"
PATCHER="/usr/local/sbin/sieva-api-direct.py"
LOG="/var/log/sieva-api-direct.log"
BACKUP_DIR="/var/backups/sieva"
TS="$(date +%Y%m%d_%H%M%S)"

exec 9>/run/sieva-api-direct.lock
flock -n 9 || exit 0

[ -f "$VHOST" ] || exit 0
grep -q "location ^~ /api/" "$VHOST" && exit 0

# No parchear mientras ngxconf está escribiendo el archivo.
if [ $(( $(date +%s) - $(stat -c %Y "$VHOST") )) -lt 3 ]; then
    exit 0
fi

mkdir -p "$BACKUP_DIR"
cp -a "$VHOST" "$BACKUP_DIR/vhost.auto.$TS" 2>/dev/null || exit 0
python3 "$PATCHER" "$VHOST" >>"$LOG" 2>&1 || exit 0

if nginx -t >>"$LOG" 2>&1; then
    systemctl reload nginx >>"$LOG" 2>&1
    echo "$(date -Is) vhost regenerado: bloque /api re-aplicado" >>"$LOG"
else
    cp -a "$BACKUP_DIR/vhost.auto.$TS" "$VHOST"
    echo "$(date -Is) nginx -t falló tras re-aplicar; vhost restaurado" >>"$LOG"
fi

# Conservar solo los últimos 20 backups automáticos
ls -1t "$BACKUP_DIR"/vhost.auto.* 2>/dev/null | tail -n +21 | xargs -r rm -f
SH
chmod 750 "$WATCHDOG"

cat > /etc/systemd/system/sieva-api-direct.service <<'EOF'
[Unit]
Description=SIEVA - garantizar bloque /api directo a gunicorn

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/sieva-api-direct.sh
Nice=10
EOF

cat > /etc/systemd/system/sieva-api-direct.timer <<'EOF'
[Unit]
Description=SIEVA - revisar bloque /api cada 30 s

[Timer]
OnBootSec=45s
OnUnitActiveSec=30s
AccuracySec=5s
Unit=sieva-api-direct.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
if systemctl enable --now sieva-api-direct.timer >/dev/null 2>&1; then
    ok "timer activo: $(systemctl is-active sieva-api-direct.timer)"
    ok "si ngxconf regenera el vhost, se corrige solo en <=30 s"
else
    warn "no se pudo activar el timer; revisa: systemctl status sieva-api-direct.timer"
fi

# ─── Verificación ───────────────────────────────────────────────────────────
info "Verificación"
echo "    bloque /api en el vhost:  $(grep -c 'location ^~ /api/' "$VHOST")"
echo "    cache_lock en yml:        $(grep 'cache_lock_enable' "$YML" 2>/dev/null || echo 'n/a')"
echo "    procesos gunicorn:        $(pgrep -c -f 'bin/gunicorn' 2>/dev/null || echo '?') (1 master + 8 workers)"
echo "    unit:                     $(grep -o -- '-w [0-9]*' "$UNIT" | head -1)"
echo "    timer:                    $(systemctl is-enabled sieva-api-direct.timer 2>/dev/null)"
echo "    MariaDB:"
mysql --protocol=socket -N -e "SHOW VARIABLES WHERE Variable_name IN ('thread_cache_size','slow_query_log','long_query_time');" | sed "s/^/      /"
echo "    /api responde por nginx:"
curl -sk -A "Mozilla/5.0" -o /dev/null -w "      HTTP %{http_code} en %{time_total}s\n" https://sieva.drehuanuco.gob.pe/api/health

echo ""
echo "Listo. Ya no hay que volver a ejecutar este script:"
echo "  - el bloque /api se re-aplica solo cada 30 s si ngxconf regenera el vhost"
echo "  - cache_lock_enable: false se aplica en la próxima regeneración de ngxconf"
echo "  - log del watchdog: /var/log/sieva-api-direct.log"
