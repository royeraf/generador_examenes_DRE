"""
Load test del flujo "estudiante rinde examen": login -> iniciar -> (pensar) -> finalizar.

Requiere haber corrido primero:
    cd backend && ./venv/bin/python -m loadtest.seed_loadtest_data --n-estudiantes 50

Uso:
    cd backend
    LOADTEST_ASIGNACION_LECTURA=<id> \
    LOADTEST_ASIGNACION_MATEMATICA=<id> \
    LOADTEST_N_ESTUDIANTES=50 \
    ./venv/bin/locust -f loadtest/locustfile.py --host http://localhost:8000

Luego abrir http://localhost:8089 y configurar cantidad de usuarios / spawn rate.

Incluye dos escenarios (ver clases al final):
  - EstudianteExamenUser: flujo normal, cada "usuario" virtual usa un estudiante
    LOADT#### distinto (round-robin) -> mide throughput/latencia real del flujo.
  - DobleEnvioUser: dispara DOS "iniciar" EN PARALELO sobre el MISMO estudiante/
    asignación para intentar reproducir la race condition TOCTOU detectada en el
    código — doble clic / reintento de red. Cuenta cuántas veces la segunda llamada
    concurrente devuelve 500 en vez de un error controlado (400/409). Usa un
    sub-pool de estudiantes separado del escenario normal para no contaminar las
    métricas de uno con el otro.
"""
import os
import random

import gevent
from locust import HttpUser, task, between, events

PASSWORD = os.environ.get("LOADTEST_PASSWORD", "LoadTest2026!")
CODIGO_PREFIX = os.environ.get("LOADTEST_CODIGO_PREFIX", "LOADT")
N_ESTUDIANTES = int(os.environ.get("LOADTEST_N_ESTUDIANTES", "50"))
ASIG_LECTURA = os.environ.get("LOADTEST_ASIGNACION_LECTURA")
ASIG_MATEMATICA = os.environ.get("LOADTEST_ASIGNACION_MATEMATICA")

if not ASIG_LECTURA and not ASIG_MATEMATICA:
    raise RuntimeError(
        "Define LOADTEST_ASIGNACION_LECTURA y/o LOADTEST_ASIGNACION_MATEMATICA "
        "(ids impresos por seed_loadtest_data.py)"
    )

ASIGNACIONES = [a for a in (ASIG_LECTURA, ASIG_MATEMATICA) if a]

# Reservamos el último 10% del pool (mínimo 2) para el escenario de doble envío,
# para no competir por el mismo estudiante con el escenario de flujo normal.
N_RACE = max(2, N_ESTUDIANTES // 10)
N_NORMAL = max(1, N_ESTUDIANTES - N_RACE)


def _codigo(i: int) -> str:
    return f"{CODIGO_PREFIX}{i:04d}"


class _CicloEstudiantes:
    """Reparte códigos de estudiante de forma round-robin entre los usuarios
    virtuales que arrancan. Simple y suficiente para una corrida en un solo
    proceso de locust (uso local)."""

    def __init__(self, indices):
        self._indices = list(indices)
        self._pos = 0

    def siguiente(self) -> str:
        codigo = _codigo(self._indices[self._pos % len(self._indices)])
        self._pos += 1
        return codigo


_pool_normal = _CicloEstudiantes(range(1, N_NORMAL + 1))
_pool_race = _CicloEstudiantes(range(N_NORMAL + 1, N_NORMAL + N_RACE + 1))


def _login(client, codigo: str) -> str | None:
    with client.post(
        "/api/auth/login",
        data={"username": codigo, "password": PASSWORD},
        name="/api/auth/login",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"login falló para {codigo}: {resp.status_code} {resp.text[:200]}")
            return None
        resp.success()
        return resp.json()["access_token"]


def _respuestas_para(preguntas: list) -> list[dict]:
    out = []
    for p in preguntas:
        opciones = p.get("opciones") or []
        elegido = random.choice(opciones)["valor"] if opciones else "A"
        out.append({"pregunta_numero": p["numero"], "respuesta": elegido})
    return out


class EstudianteExamenUser(HttpUser):
    """Escenario principal: un estudiante distinto por usuario virtual,
    rindiendo el flujo completo repetidamente."""

    weight = 9
    wait_time = between(1, 3)

    def on_start(self):
        self.codigo = _pool_normal.siguiente()
        token = _login(self.client, self.codigo)
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        self.asignacion_id = None

    @task
    def rendir_examen(self):
        if not self.client.headers.get("Authorization"):
            return
        asignacion_id = random.choice(ASIGNACIONES)

        with self.client.post(
            f"/api/estudiante/examenes/{asignacion_id}/iniciar",
            name="/api/estudiante/examenes/[id]/iniciar",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                # "intentos agotados" (400) es esperable si N_ESTUDIANTES es chico
                # y la corrida es larga; cualquier otra cosa (500) es un fallo real.
                if resp.status_code == 400:
                    resp.success()
                else:
                    resp.failure(f"iniciar falló: {resp.status_code} {resp.text[:200]}")
                return
            resp.success()
            data = resp.json()

        intento_id = data["intento_id"]
        preguntas = data.get("preguntas", [])

        # Tiempo simulado "leyendo/respondiendo" antes de enviar.
        gevent.sleep(random.uniform(0.5, 2.0))

        payload = {"respuestas": _respuestas_para(preguntas)}
        with self.client.post(
            f"/api/estudiante/intentos/{intento_id}/finalizar",
            json=payload,
            name="/api/estudiante/intentos/[id]/finalizar",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"finalizar falló: {resp.status_code} {resp.text[:200]}")
            else:
                resp.success()


class DobleEnvioUser(HttpUser):
    """Escenario de estrés dirigido: intenta reproducir la race condition TOCTOU
    de iniciar_examen (backend/app/routes/estudiantes.py) disparando dos POST
    /iniciar concurrentes para el MISMO estudiante+asignación (simula doble
    clic o reintento de red del cliente)."""

    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        self.codigo = _pool_race.siguiente()
        token = _login(self.client, self.codigo)
        if token:
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    def _iniciar_una_vez(self, asignacion_id, resultados):
        with self.client.post(
            f"/api/estudiante/examenes/{asignacion_id}/iniciar",
            name="/api/estudiante/examenes/[id]/iniciar (doble envio)",
            catch_response=True,
        ) as resp:
            resultados.append(resp.status_code)
            if resp.status_code in (200, 400):
                resp.success()
            else:
                resp.failure(
                    f"iniciar concurrente devolvió {resp.status_code} (posible race "
                    f"condition TOCTOU): {resp.text[:200]}"
                )

    @task
    def doble_iniciar_concurrente(self):
        if not self.client.headers.get("Authorization"):
            return
        asignacion_id = random.choice(ASIGNACIONES)
        resultados: list[int] = []
        g1 = gevent.spawn(self._iniciar_una_vez, asignacion_id, resultados)
        g2 = gevent.spawn(self._iniciar_una_vez, asignacion_id, resultados)
        gevent.joinall([g1, g2])

        # Limpiar: si se creó un intento, finalizarlo para poder repetir el
        # escenario en la siguiente iteración (evita agotar intentos_permitidos
        # de forma innecesaria, aunque el seed lo deja muy alto).
        with self.client.post(
            f"/api/estudiante/examenes/{asignacion_id}/iniciar",
            name="/api/estudiante/examenes/[id]/iniciar (reanudar para limpiar)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
                intento_id = resp.json()["intento_id"]
                preguntas = resp.json().get("preguntas", [])
                self.client.post(
                    f"/api/estudiante/intentos/{intento_id}/finalizar",
                    json={"respuestas": _respuestas_para(preguntas)},
                    name="/api/estudiante/intentos/[id]/finalizar (limpieza)",
                )
            else:
                resp.success()


@events.quitting.add_listener
def _resumen(environment, **kwargs):
    print(
        "\nRevisa en la UI/reporte de Locust las filas '(doble envio)': "
        "cualquier status 500 ahí confirma la race condition TOCTOU de "
        "iniciar_examen bajo concurrencia real.\n"
    )
