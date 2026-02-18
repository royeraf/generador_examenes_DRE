# Generador de Preguntas DREHCO

Sistema de generación de preguntas de evaluación para docentes, basado en competencias y rúbricas, utilizando inteligencia artificial (Google Gemini y OpenAI ChatGPT).

## 🏗️ Arquitectura

Este es un proyecto monolítico con:
- **Backend**: FastAPI (Python)
- **Frontend**: Vue.js 3 + Vite + TypeScript

## 📁 Estructura del Proyecto

```
generador_preguntas_drehco/
├── backend/                    # API FastAPI
│   ├── venv/                   # Entorno virtual Python
│   ├── app/
│   │   ├── main.py            # Entrada principal
│   │   ├── config.py          # Configuración
│   │   ├── models/            # Modelos Pydantic
│   │   ├── services/          # Servicios de IA
│   │   └── routes/            # Endpoints API
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # App Vue.js
│   ├── src/
│   │   ├── views/             # Vistas principales
│   │   ├── services/          # Servicios API
│   │   └── types/             # Tipos TypeScript
│   └── package.json
└── README.md
```

## 🚀 Instalación y Ejecución

### 1. Configurar Backend

```bash
cd backend

# Activar entorno virtual
source venv/bin/activate

# Configurar API keys (copiar y editar .env)
cp .env.example .env
# Editar .env con tus API keys

# Ejecutar servidor
uvicorn app.main:app --reload
```

El backend estará disponible en: http://localhost:8000

### 2. Configurar Frontend

```bash
cd frontend

# Instalar dependencias (si no están instaladas)
npm install

# Ejecutar en modo desarrollo
npm run dev
```

El frontend estará disponible en: http://localhost:5173

## 🔑 Configuración de API Keys

Copia el archivo `.env.example` a `.env` en la carpeta `backend/` y configura:

```env
OPENAI_API_KEY=tu_api_key_de_openai
GOOGLE_API_KEY=tu_api_key_de_google
```

## 📡 Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/preguntas/generar` | Genera preguntas por competencias |
| POST | `/api/preguntas/generar-por-rubrica` | Genera preguntas por rúbricas |
| GET | `/api/preguntas/modelos` | Lista modelos de IA disponibles |
| GET | `/api/preguntas/tipos-preguntas` | Lista tipos de preguntas |

## 🎯 Funcionalidades

- ✅ Generación de preguntas por competencias
- ✅ Soporte para múltiples tipos de preguntas (múltiple, V/F, desarrollo)
- ✅ Selección de nivel de dificultad
- ✅ Integración con Gemini y ChatGPT
- ✅ Interfaz moderna con tema oscuro

## 📝 Licencia

DREHCO © 2026
