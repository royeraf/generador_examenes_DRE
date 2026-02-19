# Guía de Deployment en Render

## Problema: Las competencias y desempeños de Matemática no se muestran en producción

### Soluciones aplicadas:

1. **Corregidos los imports de base de datos**: Los scripts de carga (`load_desempenos.py`, `load_matematica.py`) ahora usan el path correcto `app.core.database`.

2. **Creado script maestro de inicialización**: Se agregó `backend/init_data.py` que ejecuta todos los scripts de carga de datos.

3. **Corregidos los joins de SQLAlchemy**: El endpoint `/matsistem/desempenos` en `matsistem.py` ahora usa joins correctamente para cargar relaciones.

### Pasos para configurar en Render:

Puesto que el proyecto tiene un **frontend (Vue)** y un **backend (FastAPI)**, y el backend sirve los archivos estáticos del frontend, la configuración recomendada es:

#### Configuración del Web Service (Backend)

1.  **Environment Variables**:
    *   `DATABASE_URL`: `postgresql+asyncpg://usuario:password@host:puerto/nombre_db` (Obtenlo de Render PostgreSQL)
    *   `GOOGLE_API_KEY`: Tu clave de Google AI.
    *   `SECRET_KEY`: Una cadena aleatoria larga para JWT.
    *   `PYTHON_VERSION`: `3.10` o superior (Render usa 3.7 por defecto si no se especifica).

2.  **Build Command**:
    ```bash
    pip install -r backend/requirements.txt && npm install --prefix frontend && npm run build --prefix frontend && cd backend && python init_data.py
    ```
    *Este comando instala dependencias, construye el frontend y carga los datos iniciales en PostgreSQL.*

3.  **Start Command**:
    ```bash
    cd backend && gunicorn -k uvicorn.workers.UvicornWorker app.main:app
    ```

#### Opción 2: Si ya tienes el deploy y solo quieres cargar datos manualmente
Si el sistema ya está arriba pero la base de datos está vacía, puedes ejecutar el script desde el **Shell** de Render:
```bash
cd backend
python init_data.py
```

### Verificación

Después de ejecutar los scripts, verifica que los datos se hayan cargado correctamente:

```bash
# Local testing
cd backend
python -m scripts.load_desempenos
python -m scripts.load_matematica
```

O ejecuta el script maestro:
```bash
cd backend
python init_data.py
```

### Logs esperados

Si todo funciona correctamente, deberías ver:
```
✅ Datos cargados exitosamente:
   - XX grados
   - XX capacidades
   - XXXX desempeños
```

### Endpoints a probar

Una vez desplegado, prueba estos endpoints para verificar los datos:

- `GET /api/matsistem/grados` - Debe retornar todos los grados
- `GET /api/matsistem/competencias` - Debe retornar 4 competencias
- `GET /api/matsistem/desempenos` - Debe retornar todos los desempeños
- `GET /api/matsistem/capacidades` - Debe retornar todas las capacidades

### Solución de problemas

Si aún no ves los datos:

1. **Verifica que los archivos de datos estén en Render**:
   - `backend/scripts/Copia de Desempeños Precisados_Ver.xlsx`
   - `capacidades_mat/COMPETENCIA MATEMATICA *.docx`

2. **Revisa los logs de Render** para errores de import o base de datos

3. **Asegúrate de que DATABASE_URL esté configurado** (si usan base de datos diferente a SQLite local)

4. **En caso de error de módulos**, verifica que `requirements.txt` tenga todas las dependencias necesarias

### Cambios realizados en el código

#### `backend/app/core/database.py`
- Sin cambios mayores, solo se mantiene la estructura async

#### `backend/app/routes/matsistem.py` (Línea 274-295)
**ANTES:**
```python
query = select(DesempenoMatematica).join(
    CapacidadMatematica
).join(
    CompetenciaMatematica, CapacidadMatematica.competencia
).options(...)
```

**DESPUÉS:**
```python
query = select(DesempenoMatematica).options(
    selectinload(DesempenoMatematica.capacidad).selectinload(CapacidadMatematica.competencia)
)
if competencia_id:
    query = query.join(CapacidadMatematica).where(CapacidadMatematica.competencia_id == competencia_id)
```

#### `backend/scripts/load_desempenos.py` (Línea 13-21)
**ANTES:**
```python
from app.database import engine, SessionLocal, Base
```

**DESPUÉS:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./desempenos.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
```

#### `backend/scripts/load_matematica.py` (Similar)
Se aplicaron los mismos cambios que en load_desempenos.py.

#### `backend/init_data.py` (Nuevo archivo)
Script maestro que ejecuta todos los scripts de carga de datos en secuencia.
