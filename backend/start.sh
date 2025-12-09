#!/bin/bash
set -e

# Configuración de despliegue para Render
# Nos aseguramos de estar en el directorio del backend donde se encuentra este script
cd "$(dirname "$0")"

echo "📂 Directorio de trabajo: $(pwd)"
echo "🔄 Iniciando script de arranque..."

# 1. Generar la base de datos local y cargar datos iniciales
# Ejecutamos el script que crea las tablas y carga los datos desde el Excel
echo "📊 Generando y cargando base de datos de desempeños..."
python -m scripts.load_desempenos

# 2. Iniciar el servidor FastAPI (que también sirve el frontend Vue compilado)
# Render inyecta la variable de entorno PORT automáticamente
echo "🚀 Iniciando servidor Uvicorn en el puerto ${PORT:-10000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
