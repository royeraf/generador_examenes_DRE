from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from app.config import get_settings
from app.routes import preguntas, desempenos
from app.database import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para generar preguntas de evaluación usando IA (Gemini y ChatGPT)",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# ==========================================
# API ROUTES (PRIMERO - IMPORTANTE)
# ==========================================
app.include_router(preguntas.router, prefix="/api/preguntas", tags=["Preguntas"])
app.include_router(desempenos.router, prefix="/api/desempenos", tags=["Desempeños"])

@app.get("/api/health")  # Cambié a /api/health para consistencia
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# ==========================================
# FRONTEND STATIC FILES (AL FINAL)
# ==========================================
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend/dist")

if os.path.exists(frontend_dist):
    # Montar carpeta assets para archivos estáticos (CSS, JS, imágenes)
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # Servir archivos estáticos adicionales (favicon, etc.)
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = os.path.join(frontend_dist, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    # Catch-all para SPA (Vue Router) - DEBE IR AL FINAL
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Si es una ruta API que no existe, retornar 404
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        
        # Si existe un archivo específico, servirlo
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Para todo lo demás (rutas de Vue Router), servir index.html
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
else:
    print(f"⚠️ ADVERTENCIA: No se encontró la carpeta del frontend en: {frontend_dist}")
    print("El frontend no se servirá. Asegúrate de ejecutar 'npm run build' en la carpeta frontend.")