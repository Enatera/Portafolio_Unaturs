import os
from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, Base
import app.models.models as models
from app.api import proyectos, carreras, auth, admin

# Crear las tablas automáticamente
Base.metadata.create_all(bind=engine)


app = FastAPI(title="Portafolio Unaturs")

# 👈 Habilitar CORS para permitir peticiones desde el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen (ideal para desarrollo local)
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite cualquier encabezado (como Authorization)
)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "proyectos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Incluir las rutas de la API de forma limpia y sin duplicados
app.include_router(carreras.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(proyectos.router, prefix="/api/v1")
app.include_router(admin.router)

@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API del Sistema de Proyectos Unatur",
        "estado": "Servidor en línea"
    }