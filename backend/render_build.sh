#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

echo "----------------------------------------"
echo "🛠️  Iniciando Custom Build Script para Render"
echo "----------------------------------------"

# Guardar directorio actual (debería ser backend/ o la raíz dependiendo de config, pero asumimos que el script está en backend/)
# Si Render Root Dir es "backend", estamos en .../repo/backend

# 1. Construir Frontend
echo "📂 Navegando al directorio Frontend..."
cd ../frontend

echo "📦 Instalando dependencias NPM..."
npm install

echo "🏗️  Ejecutando Build de Vue.js..."
npm run build

# Verificar que se creó la carpeta dist
if [ -d "dist" ]; then
    echo "✅ Build de Frontend exitoso. Carpeta 'dist' creada."
else
    echo "❌ Error: La carpeta 'dist' no se creó."
    exit 1
fi

# 2. Volver al Backend
cd ../backend

echo "🐍 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "----------------------------------------"
echo "✅ Build completado exitosamente."
echo "----------------------------------------"
