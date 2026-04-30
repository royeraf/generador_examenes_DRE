# AGENTS.md — LectoSistem DRE (SIEVA)

Sistema Integrado de Evaluación de Aula para la Dirección Regional de Educación Huánuco, Perú. Genera evaluaciones con IA (Gemini / OpenAI) para docentes y permite que estudiantes rindan exámenes en línea.

Producción: `https://sieva.drehuanuco.gob.pe`

---

## Estructura del repositorio

```
lectosistem_dre/
├── backend/               FastAPI + SQLAlchemy async
│   ├── app/
│   │   ├── main.py        Entry point
│   │   ├── core/          database.py, config.py, security.py, permissions.py
│   │   ├── models/        usuario.py, db_models.py, enums.py, ubigeo.py
│   │   ├── routes/        auth, admin, lectosistem, matsistem, examenes,
│   │   │                  organizacion, registro, estudiantes, metricas, ubigeo
│   │   ├── repositories/  base_repository.py, usuario_repository.py
│   │   ├── schemas/       usuario.py, pagination.py, token.py, ubigeo.py
│   │   ├── services/      usuario_service.py, lectosistem_service.py,
│   │   │                  matsistem_service.py, ai_base.py, ai_factory.py,
│   │   │                  gemini_service.py, chatgpt_service.py, word_generator.py
│   │   └── api/           dependencies.py (auth guards, require_role, require_modulo)
│   ├── alembic/           Migrations
│   ├── scripts/           load_desempenos.py, load_matematica.py,
│   │                      seed_test_users.py, load_ubigeo.py
│   ├── init_data.py       Run after first deploy to seed curriculum + first admin
│   ├── requirements.txt
│   └── .env               (never commit — copy from .env.example)
├── frontend/              Vue 3 + TypeScript + Vite + Tailwind CSS 4
│   └── src/
│       ├── modules/       One folder per domain (auth, home, lectosistem, matsistem,
│       │                  generador, asignaciones, codigos_clase, metricas,
│       │                  estudiante, admin)
│       ├── shared/        components/, composables/, services/, types/, utils/
│       ├── stores/        auth.ts (Pinia)
│       └── router/        index.ts
├── DESIGN.md              Visual identity tokens + prose (read before touching UI)
├── USUARIOS_PRUEBA.md     Test credentials for all 7 roles
└── AGENTS.md              This file
```

---

## Entorno de desarrollo

### Backend

```bash
cd backend
cp .env.example .env          # fill GOOGLE_API_KEY, OPENAI_API_KEY, SECRET_KEY
python -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/alembic upgrade head          # apply migrations
./venv/bin/python init_data.py           # seed curriculum + first admin (run once)
./venv/bin/python -m scripts.seed_test_users  # seed test users for all 7 roles
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/api/docs`

Default admin after `init_data.py`:
- DNI: `00000000` — Password: `admin123` — Role: `especialista_dre_comunicacion`

### Frontend

```bash
cd frontend
bun install
bun dev              # http://localhost:5173
bun run build        # runs vue-tsc + vite build — MUST pass before considering done
```

The frontend build (`bun run build`) is the TypeScript check. Run it after every change.
TypeScript strict mode is enabled (`strict: true`, `noUnusedLocals`, `noUnusedParameters`). The build will fail on any type error.

---

## Variables de entorno requeridas (backend)

```env
DATABASE_URL=sqlite+aiosqlite:///./desempenos.db   # dev default
SECRET_KEY=change-me
GOOGLE_API_KEY=...       # Gemini — primary AI
OPENAI_API_KEY=...       # OpenAI — fallback AI
```

---

## Comandos de verificación

After any backend change:
```bash
cd backend && ./venv/bin/python -c "from app.main import app; print('OK')"
```

After any frontend change:
```bash
cd frontend && bun run build
```

After modifying DB models, always generate a migration:
```bash
cd backend && ./venv/bin/alembic revision --autogenerate -m "description"
./venv/bin/alembic upgrade head
```

---

## Sistema de roles

7 roles fijos con jerarquía estricta. Cada rol accede a un scope distinto de datos.

| Rol | Código | Scope |
|---|---|---|
| Especialista DRE Comunicación | `especialista_dre_comunicacion` | Global |
| Especialista DRE Matemática | `especialista_dre_matematica` | Global |
| Responsable UGEL | `responsable_ugel` | Su UGEL + IEs |
| Director | `director` | Su IE |
| Auxiliar | `auxiliar` | Su IE |
| Docente | `docente` | Sus propios exámenes/asignaciones |
| Estudiante | `estudiante` | Sus exámenes asignados |

El scoping se aplica en:
- `GET /examenes/asignaciones` — director ve toda su IE
- `GET /metricas/resumen` — scoped automáticamente por rol
- `GET /admin/docentes` — scoped por `ugel_id` o `institucion_educativa_id`
- `GET /organizacion/instituciones/{id}/analytics` — validado por rol

La jerarquía de creación de usuarios está en `backend/app/core/permissions.py`. Un director no puede crear otros directores.

Los módulos accesibles por rol vienen de `ROLE_MODULOS_DEFAULT` en `app/models/enums.py`, sobreescribibles por `permisos_modulos` en el usuario.

---

## Convenciones de backend (FastAPI)

- Toda la lógica de base de datos usa **SQLAlchemy async**: `await db.execute(select(...))`.
- No usar `db.query()` (síncrono) — siempre `select()` de SQLAlchemy 2.x.
- Rutas que modifican datos usan `await db.flush()` + el `get_db()` hace `commit()` al salir.
- Auth guards en `app/api/dependencies.py`:
  - `get_current_active_user` — cualquier usuario autenticado y activo
  - `require_role(*roles)` — uno de los roles indicados
  - `require_modulo("nombre")` — usuario tiene ese módulo habilitado
  - `get_current_superuser` — solo especialistas DRE
- Schemas Pydantic en `app/schemas/` — separados de los modelos SQLAlchemy.
- Los modelos SQLAlchemy viven en `app/models/`. `Usuario` en `usuario.py`; el resto en `db_models.py`.
- Nunca importar `Docente` de `app/models/docente.py` en código nuevo — ese archivo es legacy. Usar `Usuario` de `app/models/usuario.py`.

---

## Convenciones de frontend (Vue 3)

- **Siempre** `<script setup lang="ts">` — nunca Options API.
- Composables en `src/modules/<modulo>/composables/use<Feature>.ts`.
- Tipos en `src/shared/types/index.ts` (comunicación), `matematica.ts` (mat), `admin.ts` (admin).
- Servicios API en `src/shared/services/api.ts` — exporta servicios por dominio (`organizacionService`, `asignacionesService`, etc.).
- El store de auth es `src/stores/auth.ts` (Pinia). Expone `userRole`, `modulosEfectivos`, `homeRoute`.
- Navegación: `useRouter().push('/ruta')` — nunca `emit` para navegar entre módulos.
- El `Header` compartido tiene slot `#actions-before` para el botón Home.

---

## Design system (leer DESIGN.md antes de tocar UI)

Reglas críticas que nunca se rompen:

- **Sin emojis** en templates — siempre Lucide Icons (`lucide-vue-next`).
- **Dark mode** obligatorio en cada elemento: toda clase de color/bg/border necesita contraparte `dark:`.
- **Border radius**:
  - Tarjetas principales → `rounded-2xl`
  - Botones, inputs, selects → `rounded-xl`
  - Badges, pills → `rounded-full`
  - Contenedores de ícono decorativos → `rounded-lg`
- **Colores por módulo** — consistentes en toda la vista:
  - LectoSistem / Comunicación → teal (`from-teal-400 to-emerald-500`)
  - MatSistem / Matemática → indigo (`from-indigo-400 to-purple-500`)
  - Asignaciones → violet (`from-violet-500 to-indigo-600`)
- **Font weights en botones**: siempre `font-bold` o `font-semibold`, nunca `font-medium`.
- **Tipografía**: Fredoka para `h1–h6` (via CSS global), Nunito para todo lo demás.
- El build de TypeScript valida el frontend — correr `bun run build` es el test.

---

## Base de datos

- **Desarrollo**: SQLite en `backend/desempenos.db` (creado automáticamente).
- **Producción**: PostgreSQL vía `DATABASE_URL`.
- Migraciones con Alembic — **nunca** modificar el schema manualmente.
- Para agregar una columna: editar el modelo, generar migración, aplicarla.

Usuarios de prueba disponibles en `USUARIOS_PRUEBA.md` — contraseña: `Test2024!`.

---

## Guía para pull requests

- Títulos: `feat:`, `fix:`, `style:`, `refactor:`, `docs:` — seguir Conventional Commits.
- Correr `bun run build` en frontend antes de hacer PR — debe pasar sin errores.
- Probar en modo oscuro si el cambio toca UI.
- Las rutas del backend nuevas deben registrarse en `backend/app/routes/__init__.py`.
- Los endpoints nuevos en `estudiantes.py` o `organizacion.py` que cambien scope de datos deben actualizar también `metricas.py` si aplica.
