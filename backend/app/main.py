from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Include routers
app.include_router(preguntas.router, prefix="/api/preguntas", tags=["Preguntas"])
app.include_router(desempenos.router, prefix="/api/desempenos", tags=["Desempeños"])




@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Mount frontend static files
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Absolute path to frontend/dist relative to this file
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend/dist")

# Ensure the directory exists
if os.path.exists(frontend_dist):
    # 1. Mount assets specifically (CSS, JS, Images from Vite build)
    # This assumes Vite puts assets in 'assets' folder
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 2. Catch-all route for SPA (Vue Router support)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If it starts with api/, it's a 404 for the API (since API routes are defined above)
        if full_path.startswith("api"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
            
        # Check if a specific file exists (like favicon.ico, robots.txt)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Otherwise, serve index.html for client-side routing
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    print(f"⚠️ ADVERTENCIA: No se encontró la carpeta del frontend en: {frontend_dist}")
    print("El frontend no se servirá. Asegúrate de ejecutar 'npm run build' y que la ruta sea correcta.")
