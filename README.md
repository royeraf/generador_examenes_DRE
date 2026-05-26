# LectoSistem DRE — Sistema Integrado de Evaluación de Aula

Sistema web educativo desarrollado para la **Dirección Regional de Educación (DRE) de Huánuco**, que permite a docentes, directores y especialistas generar, asignar y monitorear evaluaciones de comprensión lectora (LectoSistem) y matemática (MatSistem) alineadas al Currículo Nacional peruano, con el apoyo de inteligencia artificial generativa.

## Descripción General

LectoSistem DRE integra tres ejes funcionales en una sola plataforma:

- **Generación de evaluaciones con IA** — Los docentes seleccionan grado, área y desempeños del currículo; el sistema construye un examen completo (lectura, preguntas de opción múltiple, tabla de respuestas) usando Google Gemini o OpenAI ChatGPT como motores de generación.
- **Asignación y resolución en línea** — Los exámenes generados se asignan a grados/secciones; los estudiantes los resuelven desde su portal y obtienen retroalimentación inmediata con su nivel de logro.
- **Monitoreo y métricas** — Especialistas DRE, responsables UGEL y directores acceden a dashboards con promedios por grado, dominio de desempeños y progreso individual de estudiantes, cada uno con la visibilidad correspondiente a su rol.

## Arquitectura

Aplicación monolítica con frontend SPA y backend REST API desacoplados, desplegada en VPS de la DRE Huánuco.

```
lectosistem_dre/
├── backend/                  # FastAPI — API REST + lógica de negocio
│   └── app/
│       ├── main.py           # Punto de entrada (uvicorn :8000)
│       ├── core/             # Config, base de datos, seguridad
│       ├── models/           # 23 tablas SQLAlchemy (ORM)
│       ├── routes/           # 12 routers (~4600 líneas de endpoints)
│       ├── services/         # Lógica de IA, exámenes, Word, archivos
│       ├── schemas/          # Pydantic (request/response)
│       └── repositories/     # Capa de acceso a datos
├── frontend/                 # Vue 3 SPA
│   └── src/
│       ├── modules/          # 12 módulos: auth, home, lectosistem,
│       │   │                 # matsistem, asignaciones, estudiante,
│       │   │                 # metricas, admin, codigos_clase, …
│       ├── shared/           # Componentes, servicios y utils reutilizables
│       ├── stores/           # Pinia (auth)
│       └── router/           # Vue Router 4
├── diagrams/                 # PlantUML — diagramas C4, ER y flujos
├── deploy.sh                 # Script de despliegue al VPS
├── dev.sh                    # Script de desarrollo local
└── vps_setup.sh              # Configuración inicial del servidor
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI 0.110+, Python 3.11, SQLAlchemy (async) |
| Base de datos | MariaDB 11.8 (VPS producción) / SQLite (desarrollo) |
| Frontend | Vue 3.5 (Composition API), TypeScript, Vite 6, Tailwind CSS 4 |
| Estado global | Pinia 3 |
| Autenticación | JWT (python-jose) + bcrypt |
| IA generativa | Google Gemini API, OpenAI ChatGPT API |
| Exportación | python-docx (Word), PyMuPDF (lectura PDF) |
| Despliegue | Nginx (reverse proxy), systemd, VPS DRE Huánuco |

## Roles del Sistema

| Rol | Alcance |
|-----|---------|
| Especialista DRE Comunicación | Todo el sistema — módulo LectoSistem |
| Especialista DRE Matemática | Todo el sistema — módulo MatSistem |
| Responsable UGEL | Su UGEL y las IEs que la componen |
| Director | Su Institución Educativa |
| Auxiliar | Su Institución Educativa (acceso limitado) |
| Docente | Sus propias asignaciones y estudiantes |
| Estudiante | Sus exámenes asignados y su progreso |

## Instalación Local

### Prerrequisitos

- Python 3.11+
- Bun (o Node.js 20+)
- MariaDB / SQLite

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Configurar GOOGLE_API_KEY, OPENAI_API_KEY, DATABASE_URL, SECRET_KEY
uvicorn app.main:app --reload
```

API disponible en: `http://localhost:8000` | Documentación: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
bun install
bun run dev
```

Aplicación disponible en: `http://localhost:5173`

### Inicio rápido (ambos servicios)

```bash
./dev.sh
```

## Variables de Entorno

```env
# backend/.env
DATABASE_URL=mysql+aiomysql://usuario:password@localhost:3306/lectosistem_dre
SECRET_KEY=clave-secreta-jwt
GOOGLE_API_KEY=tu-api-key-gemini
OPENAI_API_KEY=tu-api-key-openai
```

## Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Autenticación (DNI o código estudiante) |
| GET | `/api/auth/me` | Perfil del usuario autenticado |
| POST | `/api/lectosistem/generar` | Generar examen de comprensión lectora |
| POST | `/api/matsistem/generar` | Generar examen de matemática |
| GET | `/api/examenes/lectura` | Historial de exámenes de lectura |
| POST | `/api/examenes/asignaciones` | Asignar examen a grado/sección |
| GET | `/api/metricas/dashboard` | Dashboard de métricas (scoped por rol) |
| GET | `/api/organizacion/ugeles` | Listar UGELes (DRE) |
| GET | `/api/organizacion/instituciones` | Listar Instituciones Educativas |
| GET | `/api/estudiantes` | Listar estudiantes (scoped) |

Documentación completa de la API en `/docs` (Swagger UI) al ejecutar el backend.

## Módulos Funcionales

### LectoSistem
Generación de exámenes de comprensión lectora alineados a los desempeños del área de Comunicación del Currículo Nacional. El docente selecciona el grado, las capacidades (literal, inferencial, crítico) y los desempeños precisados; la IA genera el texto de lectura y las preguntas de opción múltiple con su tabla de respuestas. El resultado puede descargarse en formato Word.

### MatSistem
Generación de exámenes y actividades de aprendizaje de Matemática, organizados por las 4 competencias del Currículo Nacional. Soporta 5 tipos de productos (exámenes con situación problemática, actividades de aprendizaje). Igualmente exportable a Word.

### Asignaciones
Los docentes y directores asignan exámenes guardados a grados y secciones, configurando fechas, duración, intentos permitidos y visibilidad de resultados.

### Portal Estudiante
Los estudiantes acceden con su código de estudiante, ven sus exámenes pendientes, los resuelven en línea con temporizador y reciben su resultado con nivel de logro (pre-inicio, inicio, proceso, satisfactorio, destacado).

### Métricas
Dashboard de analítica escolar con promedios por grado, dominio de desempeños, progreso individual y comparativas. Cada rol accede solo al ámbito que le corresponde.

### Administración
CRUD completo de usuarios (staff), UGELes, Instituciones Educativas, grados, capacidades y desempeños del currículo. La creación de cuentas docentes requiere un administrador; no hay registro público.

## Despliegue en VPS

El sistema se despliega en el servidor de la DRE Huánuco mediante el script `deploy.sh`:

```bash
./deploy.sh
```

El script realiza: `git pull` → build del frontend → copia de estáticos → instalación de dependencias Python → migraciones Alembic → reinicio del servicio systemd.

El servidor Nginx actúa como reverse proxy, sirviendo el frontend estático y redirigiendo `/api/*` al proceso FastAPI (Gunicorn + Uvicorn workers) en el puerto 8000.

## Licencia

DRE Huánuco © 2026 — Proyecto de uso institucional.
