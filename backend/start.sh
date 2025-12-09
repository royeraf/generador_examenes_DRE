#!/bin/bash
set -e

echo "🔄 Iniciando script de despliegue completo..."

# 1. Compilar el frontend de Vue.js
echo "🎨 Compilando frontend Vue.js..."
cd ../frontend
npm install
npm run build
echo "✅ Frontend compilado en ./dist"

# 2. Volver al directorio del backend
cd ../backend
echo "📂 Directorio de trabajo: $(pwd)"

# 3. Instalar dependencias de Python (por si acaso)
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

# 4. Generar la base de datos local y cargar datos iniciales
echo "📊 Generando y cargando base de datos de desempeños..."
python -m scripts.load_desempenos

# 5. Iniciar el servidor FastAPI (que también sirve el frontend Vue compilado)
echo "🚀 Iniciando servidor Uvicorn en el puerto ${PORT:-10000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}