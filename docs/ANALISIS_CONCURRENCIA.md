# Análisis de concurrencia e infraestructura — SIEVA

**Servidor:** `vps88099.inmotionhosting.com` (198.46.86.154)
**Dominio:** `sieva.drehuanuco.gob.pe`
**Fecha:** 20 de octubre de 2026
**Alcance:** capacidad de la infraestructura para sostener un volumen alto de usuarios concurrentes.

---

## 1. Veredicto

**El hardware es de sobra. La configuración de la cadena de serving no lo es.**

La máquina (16 vCPU, 32 GB RAM, 453 GB SSD) está utilizando entre el 1% y el 10% de su capacidad.
Sin embargo, las pruebas de carga muestran que **el sistema se degrada con 20 peticiones
simultáneas a la misma URL**: la latencia pasa de 10 ms a 2–5 segundos y el throughput cae de
~1.000 req/s (backend directo) a ~40 req/s (a través de nginx + Apache).

| Capa | Techo medido / estimado | Estado |
|---|---|---|
| CPU / RAM / disco | 16 vCPU, 32 GB, 75 GB libres | Holgado (uso real < 10%) |
| Backend FastAPI directo | 965 req/s (endpoint trivial) | Correcto |
| Apache directo | 1.090 req/s | Correcto |
| **Cadena completa (URL repetida)** | **40–70 req/s, p95 2–5 s** | **Crítico** |
| **Login (bcrypt)** | **~3 logins/s** | **Crítico** |
| Base de datos | 250 conexiones, 7 MB de datos | Sin presión hoy |

Con la configuración actual el sistema aguanta bien una **piloto de 40–60 usuarios
simultáneos**. A partir de ~200 usuarios concurrentes empieza a degradarse de forma visible, y
con 500+ el inicio de sesión y las pantallas de exámenes se encolan durante minutos.

---

## 2. Inventario real del servidor

```
SO            AlmaLinux 8.10 (kernel 4.18 Virtuozzo, VPS Parallels)
CPU           16 vCPU  Intel Xeon Gold 6338 @ 2.00 GHz  (cgroup: 16 cores, sin steal)
RAM           32 GB (3,4 GB en uso, 29 GB disponibles)  — SIN swap
Disco         453 GB, 359 GB usados (83%), 75 GB libres
Panel         cPanel/WHM · 28 dominios alojados
Web           nginx 1.31.7 (imh-nginx) delante de Apache 2.4.69 (MPM worker)
Backend       gunicorn 2 workers UvicornWorker · Python 3.11 · 190 MB por worker
Base de datos MariaDB 10.6.27 (misma máquina, 1,2 GB RSS)
Otros         clamd (1 GB), spamd, exim, dovecot, PHP-FPM 7.4/8.0/8.1/8.2
```

Datos de la aplicación: 35 exámenes, 541 preguntas, 230 estudiantes, 772 sesiones de acceso.
Base de datos total: ~7 MB. Tráfico del día (20/10): 3.093 peticiones, 21 IPs únicas
(incluyendo las pruebas de este análisis). El sistema está en etapa piloto.

---

## 3. Recorrido de una petición (el problema de fondo)

```
Navegador
   │  TLS 1.3
   ▼
nginx :443  (8 workers × 768 conexiones)
   │  ── proxy_cache_lock ON ──┐
   │  TLS NUEVO en cada request (proxy_ssl_session_reuse off)
   │  sin keepalive hacia el upstream (HTTP/1.0)
   ▼
Apache :8443  (MPM worker, ~137 hilos, mod_security)
   │  .htaccess → RewriteRule [P] (mod_rewrite + mod_proxy)
   ▼
gunicorn :8000  (2 workers, event loop Python)
   │
   ▼
MariaDB :3306  (pool 5 + 10 por worker)
```

Cuatro saltos, dos terminaciones TLS y dos proxys inversos para servir una API.
Cada petición además atraviesa **mod_security** y las reglas de reescritura de `.htaccess`.

---

## 4. Mediciones (reproducibles)

### 4.1 Backend directo (sin proxies)

```
ab -n 500 -c 25 http://127.0.0.1:8000/api/health
  → 965 req/s · p95 74 ms
```

### 4.2 Apache directo (sin nginx)

```
ab -n 100 -c 10 https://sieva.drehuanuco.gob.pe:8443/api/health
  → 1.090 req/s · p95 12 ms
```

### 4.3 Cadena completa, MISMA URL (caso real: 40 alumnos abriendo la misma pantalla)

| Concurrencia | Throughput | p95 |
|---|---|---|
| 1 | 95 req/s | 12 ms |
| 5 | 30 req/s | 518 ms |
| 10 | 37 req/s | 1.541 ms |
| 20 | 59 req/s | **5.079 ms** |
| 40 | 69 req/s | 3.515 ms |

100 peticiones con 20 en paralelo a la misma URL: **4,24 s de pared**, p95 2,2 s, máx 4,2 s.
El log de nginx lo confirma: `upstream_time` = 2–3 ms pero `request_time` = 2.000–5.000 ms.
**El tiempo no se pierde en el backend: se pierde esperando en nginx.**

### 4.4 Cadena completa, URLs distintas (mismo volumen)

100 peticiones con 20 en paralelo, cada una con query distinta: **100% en menos de 1 s**,
p95 100 ms. Es decir, **la cadena sí puede hacer ≥100 req/s**; lo que la tumba es la
repetição de la misma URL.

### 4.5 Login (bcrypt)

- Coste de una verificación bcrypt con el hash actual (`$2b$12$`): **342 ms**.
- 8 logins concurrentes: **2,82 s de pared** (los dos primeros a 0,73 s, el resto a 2,2–2,8 s).
- Capacidad efectiva: **~3 inicios de sesión por segundo** para toda la región.

---

## 5. Cuellos de botella, por impacto

### 5.1 `proxy_cache_lock on` aplicado a `/api` — CRÍTICO

El vhost generado por el Nginx Manager de cPanel tiene, a nivel de `server`:

```nginx
proxy_cache drehua5;
proxy_cache_valid 200 14400s;
proxy_cache_lock on;
proxy_cache_key "$scheme$request_method$host$request_uri";
```

La API responde `Cache-Control: no-store` y `X-Accel-Expires: 0`, así que **nunca se cachea**
(los logs muestran `ucs=MISS` siempre). Pero `proxy_cache_lock` igual se aplica: mientras una
petición está en vuelo, las demás que piden **la misma URL** esperan hasta
`proxy_cache_lock_timeout` (5 s por defecto). Resultado:

- 40 alumnos cargando `/api/estudiante/examenes` a la vez → el último espera ~5 s.
- 300 alumnos → olas de 5 s por endpoint.
- El problema crece **linealmente** con el número de usuarios que comparten pantalla.

Es el hallazgo de mayor impacto y el más barato de corregir.

### 5.2 bcrypt dentro del event loop — CRÍTICO

`app/routes/auth.py` es `async def` y llama `verify_password()` (bcrypt) de forma síncrona.
Con `rounds=12` cada verificación bloquea el worker **342 ms**, y solo hay 2 workers.

- Techo: ~3 logins/s.
- Un arranque de exámenes con 500 estudiantes = **~3 minutos** para el último.
- Durante ese bloqueo, cualquier otra petición asignada a ese worker espera hasta 342 ms.

Además `get_dummy_hash()` (para usuarios inexistentes) también se ejecuta en el loop.

### 5.3 Solo 2 workers de gunicorn — ALTO

`-w 2` en un servidor de 16 núcleos: se usa el 12% de la CPU disponible.
Cada worker es un proceso Python de un solo hilo para ejecución de código: todo lo que sea
CPU (bcrypt, parseo de JSON grandes, reparación de LaTeX, OCR, DOCX) se serializa por worker.
Subir a 8 workers multiplica por 4 esa capacidad sin tocar código. RAM: 8 × 190 MB = 1,5 GB
(sobran 29 GB).

### 5.4 Cadena nginx → Apache → gunicorn — ALTO

- `proxy_ssl_session_reuse off` → **handshake TLS nuevo en cada petición** hacia Apache.
- No hay `proxy_http_version 1.1` ni `Connection ""` → **sin keepalive** hacia el upstream.
- El `proxy_pass` apunta a `https://198.46.86.154:8443`, es decir, **sale a la IP pública y
  vuelve** (hairpin) en lugar de usar `127.0.0.1`.
- Apache añade mod_security (hoy generó 590 respuestas 406) y `.htaccess` con `[P]`.

Latencia de cadena medida: **10–54 ms** para un endpoint que en gunicorn tarda 1,7 ms.
Eliminar Apache del camino de `/api` es la segunda palanca más grande.

### 5.5 Rate limit por IP incompatible con redes escolares — ALTO (riesgo de negocio)

```nginx
limit_req_zone $perip_rl_key zone=perip:10m rate=5r/s;   # burst 20
limit_conn perip_conn 100;
```

Hallazgo adicional: en el vhost, el `limit_req zone=perip` está dentro de un
`location /` (prefijo), pero existe un `location ~ "^(/)"` (regex) que **gana siempre** en el
orden de matching de nginx. Es decir, **el rate limit por IP nunca se aplica al tráfico HTTPS**:
es configuración muerta. Lo que sí aplica es `limit_conn perip_conn 100` (contexto http).

El límite real que sí muerde es el del backend: **20 intentos fallidos por IP en 5 minutos**
(`LOGIN_MAX_IP_ATTEMPTS`). En un colegio, **todos los alumnos salen por la misma IP pública
(NAT)**: unos pocos que se equivoquen dejan bloqueada el aula entera durante 5 minutos.

### 5.6 MariaDB — MEDIO (hoy sin presión, mal preparada para crecer)

```
max_connections            250
thread_cache_size          4      ← muy bajo, churn de hilos
innodb_buffer_pool_size    4 GB
innodb_buffer_pool_instances 1
innodb_flush_log_at_trx_commit 2
slow_query_log             OFF    ← sin visibilidad
long_query_time            10 s
wait_timeout               600
max_used_connections       19
```

El pool de la app es 5 + 10 por worker (30 conexiones con 2 workers). Con 8 workers serían 120,
todavía por debajo de 250, pero conviene bajar el pool por worker (p. ej. 5 + 5) y subir
`max_connections` a 500 si se escala. Datos actuales: 7 MB, irrelevante. El riesgo es de
crecimiento y de falta de observabilidad (slow log apagado).

### 5.7 Operación — MEDIO

- **Sin swap** (0 B). Un pico de memoria (prompts grandes de IA, OCR) termina en OOM kill.
- **Disco al 83%** (75 GB libres) con 37 GB en dos tarros de backup viejos y 22 GB de correo.
- **Sin monitoreo de aplicación** (no hay APM, ni alertas de p95/5xx).
- **Migraciones Alembic en el arranque de cada worker** (`startup_event`): con más workers
  se ejecutan N migraciones concurrentes.
- Proceso uvicorn huérfano en `:8011` desde hace 22 h (sitio de test).
- Archivos de 8–11 GB con nombres aleatorios en el home y un `.bashrc.infected.bak`:
  indicios de un incidente de seguridad anterior. Revisar y limpiar.

### 5.8 Timeouts desalineados — MEDIO

`proxy_read_timeout` no está definido en el vhost → **60 s por defecto de nginx**, mientras que
el presupuesto de IA es 50 s y gunicorn corta a 120 s. Una generación lenta produce 504 en el
navegador aunque el backend termine. El `vps_setup.sh` recomendaba 300 s, pero ese bloque nunca
se aplicó al vhost de cPanel.

---

## 6. Capacidad estimada

| Escenario | Concurrentes | Con la config actual | Tras el plan P0 |
|---|---|---|---|
| Aula (1 IE) | 40 | Aceptable, con picos de 1–5 s y riesgo de 429 por NAT | Holgado |
| IE grande | 300 | Degradado: colas de 5 s por endpoint, logins lentos | Aceptable |
| UGEL | 1.000 | No soportado | Al límite; requiere P1 |
| Regional | 5.000+ | Se cae | Requiere P1 + P2 |

Tras aplicar P0 (desactivar cache lock en `/api`, 8 workers, bcrypt fuera del loop y en
rounds 10, rate limit por usuario) la capacidad estimada sube a **1.000–1.500 concurrentes**
y **~100 logins/s**, sin cambiar una línea de arquitectura.

---

## 7. Plan de acción

### P0 — esta semana (sin cambiar arquitectura)

**1. Quitar el cache lock de `/api`** (mayor impacto: 20–40× en endpoints repetidos).
En WHM → Nginx Manager, configuración personalizada del dominio (el vhost se regenera solo,
un edit manual se pierde):

```nginx
location ^~ /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_connect_timeout 10s;
    client_max_body_size 15m;
}
```

Esto además **saca a Apache del camino de la API** (un salto menos, sin mod_security, sin
hairpin, con keepalive y TLS innecesario eliminado). Si no se puede añadir un `location`,
como mínimo: `proxy_cache off; proxy_cache_lock off;` para `/api`.

**2. Subir workers de gunicorn** (4× capacidad de CPU):

```ini
ExecStart=.../gunicorn -k uvicorn.workers.UvicornWorker \
    -w 8 --max-requests 2000 --max-requests-jitter 200 \
    --timeout 180 --graceful-timeout 30 \
    --bind 127.0.0.1:8000 app.main:app
```

**3. Sacar bcrypt del event loop y bajar el coste** (8–24× en login):

```python
from starlette.concurrency import run_in_threadpool

credenciales_validas = await run_in_threadpool(
    verify_password, form_data.password, usuario.password_hash
)
# idem para verify_password(form_data.password, get_dummy_hash())
```

Además: `bcrypt.gensalt(rounds=10)` (85 ms en vez de 342 ms) con **rehash progresivo** en el
login exitoso cuando el hash guardado sea de rounds 12.

**4. Corregir el bloqueo de login por IP:**

`LOGIN_MAX_IP_ATTEMPTS` de 20 → 100 (un aula comparte IP; el límite por identificador de 5
sigue protegiendo contra fuerza bruta). Ya aplicado en `config.py`.

El `limit_req zone=perip` del vhost es configuración muerta (lo tapa el `location ~ "^(/)"`);
si más adelante se quiere rate limiting real, debe ir dentro de un `location` que sí matchee
(y conviene keyear por usuario autenticado, no por IP).

**5. Timeouts coherentes:** `proxy_read_timeout 300s` (incluido arriba) y `--timeout 180` en
gunicorn.

**6. Servir el SPA desde nginx** (deja Apache solo para los otros 27 dominios):

```nginx
root /home/drehua5/sieva.drehuanuco.gob.pe;
location /assets/ { expires 1y; add_header Cache-Control "public, immutable"; }
location / { try_files $uri $uri/ /index.html; add_header Cache-Control "no-cache"; }
```

### P1 — próximas 2–4 semanas

7. **Redis** para caché (catálogos, métricas), rate limiting compartido y sesiones.
8. **Cola de trabajos** (ARQ/Celery/RQ) para generación con IA, OCR y generación de DOCX:
   el request devuelve un `job_id` y el frontend consulta. Elimina requests de 50 s.
9. **MariaDB**: `thread_cache_size=64`, `slow_query_log=ON`, `long_query_time=1`,
   `innodb_buffer_pool_instances=4`, `max_connections=500`; revisar índices con EXPLAIN de
   las consultas de `metricas` y `monitoreo`.
10. **Quitar Alembic del arranque** (`init_db`) y ejecutarlo como paso de despliegue.
11. **Monitoreo**: Netdata o node_exporter + el módulo VTS que ya está instalado; alertas de
    p95, 5xx, conexiones a MariaDB y disco.
12. **Swap de 4–8 GB** como red de seguridad y backup automático por cron (hoy solo hay un
    `.sql` manual en `.sieva_db_backups`).
13. **Limpieza**: 37 GB de tarros viejos, proceso huérfano en `:8011`, y revisión de los
    archivos grandes con nombres aleatorios y `.bashrc.infected.bak`.

### P2 — mediano plazo

14. **Separar SIEVA del hosting compartido cPanel**: 28 dominios, correo, clamd y 4 PHP-FPM
    comparten la máquina. Un nodo dedicado (o contenedores) aísla el ruido y permite escalar.
15. **Escalado horizontal**: gunicorn sin estado detrás de nginx en 2+ nodos, MariaDB
    gestionada o réplica de lectura, Redis, almacenamiento de objetos para archivos.
16. **Cloudflare delante** para absorber TLS y estáticos (el `real_ip` ya está configurado;
    verificar que `X-Real-IP` siga llegando con la IP real para no romper el throttling).
17. Endurecer seguridad del servidor y rotar credenciales si se confirma el incidente previo.

---

## 8. Cómo validar después

Repetir exactamente estas pruebas antes y después de P0:

```bash
# Misma URL, 20 en paralelo (antes: p95 2-5 s)
ab -n 100 -c 20 -H "User-Agent: Mozilla/5.0" https://sieva.drehuanuco.gob.pe/api/health

# URLs distintas, 20 en paralelo (debe mantenerse < 1 s)
seq 1 100 | xargs -P20 -I{} curl -sk -A "Mozilla/5.0" -o /dev/null \
  -w "%{time_total}\n" "https://sieva.drehuanuco.gob.pe/api/health?i={}" | sort -n

# Login concurrente (antes: 8 logins en 2,8 s)
for i in $(seq 1 8); do
  curl -sk -o /dev/null -w "%{time_total}\n" -X POST \
    https://sieva.drehuanuco.gob.pe/api/auth/login \
    -d "username=ZN000$i&password=x" &
done; wait

# Estado de nginx y logs
curl -s http://127.0.0.1/status
grep "sieva.drehuanuco.gob.pe" /var/log/nginx/access.log | tail -50
```

Criterio de aceptación de P0:
- misma URL / c=20 → p95 < 300 ms (hoy 2–5 s)
- 8 logins concurrentes → < 1 s (hoy 2,8 s)
- cero 429 en una simulación de 40 usuarios desde una misma IP

---

## 9. Resumen en una línea

**El servidor tiene 16 núcleos y 32 GB casi ociosos; lo que limita el sistema es un
`proxy_cache_lock` mal heredado de cPanel, 2 workers de gunicorn y bcrypt bloqueando el event
loop. Con tres cambios de configuración y uno de código, la capacidad pasa de ~50 a
~1.000–1.500 usuarios concurrentes sin comprar hardware.**

---

## 10. Estado de aplicación (20 oct 2026, 17:00)

### Aplicado en producción

| Cambio | Commit / medio | Estado |
|---|---|---|
| bcrypt fuera del event loop + rounds 10 + rehash progresivo | `191df9f` | Activo |
| `LOGIN_MAX_IP_ATTEMPTS` 20 → 100 (NAT escolar) | `f971705` | Activo |
| Gunicorn 2 → 8 workers (control socket) | `gunicornc worker add 6` | 8 activos |
| systemd con `-w 8`, `--timeout 180`, `--graceful-timeout 30` | script P0 | Persistido |
| nginx: `/api/` directo a gunicorn, `proxy_cache off`, timeout 300 s | script P0 | Activo |
| MariaDB: `thread_cache_size=64`, slow log a 1 s | script P0 | Activo + persistido |
| Persistencia ante regeneración de ngxconf | `489668a` | `cache_lock_enable: false` + timer de 30 s activo |
| Rehash de hashes viejos (12 → 10) | automático en login | Verificado (`$2b$10$`) |

Watchdog verificado: `sieva-api-direct.timer` corre cada 30 s, la última ejecución terminó
con `status=0/SUCCESS` y `/var/log/sieva-api-direct.log` aún no existe porque no hubo nada
que corregir. Cuando ngxconf regenere el vhost, la corrección tarda como máximo 30 s.

### Resultados medidos antes / después

| Prueba | Antes | Después | Mejora |
|---|---|---|---|
| Misma URL, c=20, sin keepalive | 40–70 req/s · p95 2–5 s | **325 req/s · p95 106 ms** | ~6× throughput / ~30× p95 |
| Misma URL, c=20, con keepalive | — | **3.336 req/s · p95 6 ms** | — |
| `/api/auth/me` (JWT + BD), c=20 keepalive | — | **434 req/s · p95 52 ms** | — |
| `/api/auth/me`, c=50 keepalive | — | 318 req/s · p95 285 ms | — |
| 8 logins concurrentes | 2,82 s | **0,39 s** | 7,2× |
| Login individual (real) | 0,37–0,53 s | **0,11 s** | ~4× |

Comprobaciones adicionales:

- `ucs=-` en el log de nginx: `/api` ya no pasa por la caché.
- El domlog de Apache no registra `/api` desde las 16:40: el backend ya no pasa por Apache.
- `X-Real-IP` llega correctamente (las sesiones se registran con `198.46.86.154`, no con
  `127.0.0.1`), así que el throttle de login sigue funcionando por IP real.
- CPU por worker durante las pruebas: ~1%. El cuello ya no es la aplicación.
- SPA y assets siguen sirviéndose por Apache sin cambios (HTTP 200).

### Cómo se aplicó

```bash
# 1. Código (bcrypt + límite por IP): deploy normal
git push && ssh sieva-vps 'cd ~/sieva_repo && git pull'
# 2. Recarga en caliente (sin downtime)
gunicornc -s ~/.gunicorn/gunicorn.ctl -c reload
gunicornc -s ~/.gunicorn/gunicorn.ctl -c "worker add 6"
# 3. Infraestructura (root, idempotente, con backup y rollback)
sudo bash ~/sieva_repo/vps_p0_concurrencia.sh
```

El script hizo backup del vhost y del unit con timestamp
(`*.conf.bak.20261020_165226`) y validó con `nginx -t` antes de recargar.

### Advertencias operativas

1. **El vhost lo regenera ngxconf (Nginx Manager de cPanel).** Ya no requiere intervención
   manual: el script instala dos capas de protección.

   - **Origen:** `cache_lock_enable: false` en `~/.imh/nginx/sieva_drehuanuco_gob_pe.yml`
     (archivo del usuario, no del root). Si ngxconf regenera el vhost, lo hará sin
     `proxy_cache_lock`, así que el problema crítico no vuelve aunque el bloque desaparezca.
   - **Watchdog:** `sieva-api-direct.timer` revisa cada 30 s si el bloque
     `location ^~ /api/` sigue en el vhost y lo re-aplica (con `nginx -t` y rollback) si
     ngxconf lo borró. Log: `/var/log/sieva-api-direct.log`.

   Verificación:

   ```bash
   grep -c "location ^~ /api/" /etc/nginx/vhosts/drehua5__sieva_drehuanuco_gob_pe.conf
   systemctl list-timers sieva-api-direct.timer
   ```

   Existe una alternativa oficial (`allow_user_includes` en `/opt/ngxconf/config.yaml` +
   include por dominio), pero **no se activó**: es una opción global que permite a cualquier
   cuenta cPanel inyectar directivas nginx que el master parsea como root. En un servidor
   compartido (aquí hay más cuentas y un `.bashrc.infected.bak`) es un vector de escalada.

2. **Los 8 workers en ejecución se añadieron en caliente.** El unit ya dice `-w 8`, así que
   un restart (o un crash con `Restart=always`) arranca con 8. No hace falta reiniciar ahora.

3. **El `limit_req zone=perip` del vhost sigue siendo configuración muerta.** No hay rate
   limiting real en HTTPS; el único límite es el del backend. Si se quiere protección contra
   abuso, implementarla por usuario en la app o en un `location` que sí matchee.

4. Los errores `unlink() ... failed` en `/var/log/nginx/error.log` son del gestor de caché de
   cPanel y son preexistentes (aparecían antes del cambio). No afectan las respuestas.

### Siguiente paso recomendado

Con P0 aplicado, el sistema está cómodo para ~1.000–1.500 concurrentes. Para pasar de ahí,
los siguientes movimientos son los de P1: **quitar Alembic del arranque**, **Redis** para
caché/sesiones y **cola de trabajos** para IA/OCR/DOCX. Antes de tocar nada más, conviene
monitorear una semana real con el slow query log ya activo.


