import os
import re
import unicodedata
import shutil
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from typing import Any, List, Optional

from app.db.session import get_BaseDeDatos
import app.models.models as models
from app.models.models import EstadoProyecto, VisibilidadProyecto  
import app.schemas.schemas as schemas
from app.api.auth import get_current_user

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "proyectos")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generar_slug(titulo: str) -> str:
    # Eliminar acentos y caracteres especiales
    titulo_normalizado = unicodedata.normalize('NFKD', titulo).encode('ascii', 'ignore').decode('utf-8')
    # Convertir a minúsculas, reemplazar espacios y caracteres no alfanuméricos por guiones
    slug = re.sub(r'[^a-z0-9]+', '-', titulo_normalizado.lower()).strip('-')
    return slug

@router.post("", response_model=schemas.ProyectoOut, status_code=status.HTTP_201_CREATED)
async def crear_proyecto(
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    id_carrera: int = Form(...),
    estado: Optional[EstadoProyecto] = Form(EstadoProyecto.borrador),
    visibilidad: Optional[VisibilidadProyecto] = Form(VisibilidadProyecto.estudiantes),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_BaseDeDatos),
    usuario_actual: models.Usuario = Depends(get_current_user)
):
    carrera = db.query(models.Carrera).filter(models.Carrera.id == id_carrera).first()
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La carrera con ID {id_carrera} no existe en la base de datos."
        )

    if usuario_actual.id_rol is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un rol asignado."
        )

    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos en formato PDF."
        )

    contenido = await archivo.read()
    if len(contenido) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo excede el tamaño máximo permitido de 10 MB."
        )

    extension = os.path.splitext(archivo.filename)[1]
    nombre_unico = f"{uuid.uuid4().hex}{extension}"
    ruta_fisica = os.path.join(UPLOAD_DIR, nombre_unico)

    with open(ruta_fisica, "wb") as f:
        f.write(contenido)

    slug_base = generar_slug(titulo)
    slug_final = slug_base
    contador = 1
    
    while db.query(models.Proyecto).filter(models.Proyecto.slug == slug_final).first():
        slug_final = f"{slug_base}-{contador}"
        contador += 1

    nuevo_proyecto = models.Proyecto(
        titulo=titulo,
        slug=slug_final,
        descripcion=descripcion,
        archivo_ruta=ruta_fisica,
        id_carrera=id_carrera,
        estado=estado,
        visibilidad=visibilidad,
        id_autor=usuario_actual.id,
        id_rol=usuario_actual.id_rol
    )

    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)

    return nuevo_proyecto

# 📌 RUTA DE LISTADO Y BÚSQUEDA (Siempre arriba de las rutas con {slug})
@router.get("", response_model=List[schemas.ProyectoOut])
def listar_proyectos(
    busqueda: Optional[str] = Query(None, description="Término para buscar en el título o descripción"),
    db: Session = Depends(get_BaseDeDatos)
):
    query = db.query(models.Proyecto)

    # Como es una ruta pública para el portafolio, filtramos por defecto los proyectos públicos o para estudiantes
    query = query.filter(
        models.Proyecto.estado == EstadoProyecto.publico,
        models.Proyecto.visibilidad.in_([
            VisibilidadProyecto.publico, 
            VisibilidadProyecto.estudiantes
        ])
    )

    if busqueda:
        termino = f"%{busqueda}%"
        query = query.filter(
            or_(
                models.Proyecto.titulo.like(termino),
                models.Proyecto.descripcion.like(termino)
            )
        )

    resultados = query.all()
    return resultados if resultados else []

@router.get("/{proyecto_id}/descargar")
def descargar_archivo_proyecto(proyecto_id: int, db: Session = Depends(get_BaseDeDatos)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
        
    if not proyecto.archivo_ruta or not os.path.exists(proyecto.archivo_ruta):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El archivo físico asociado no existe")
        
    extension = os.path.splitext(proyecto.archivo_ruta)[1]
    nombre_descarga = f"{proyecto.titulo}{extension}".replace(" ", "_")

    return FileResponse(
        path=proyecto.archivo_ruta,
        filename=nombre_descarga,
        media_type="application/pdf"
    )

@router.get("/{slug}", response_model=schemas.ProyectoOut)
def obtener_proyecto(slug: str, db: Session = Depends(get_BaseDeDatos)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.slug == slug).first()
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    return proyecto

@router.put("/{slug}", response_model=schemas.ProyectoOut)
def actualizar_proyecto(
    slug: str,
    titulo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    estado: Optional[EstadoProyecto] = Form(None),
    visibilidad: Optional[VisibilidadProyecto] = Form(None),
    db: Session = Depends(get_BaseDeDatos),
    usuario_actual: models.Usuario = Depends(get_current_user)
):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.slug == slug).first()
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")

    if proyecto.id_autor != usuario_actual.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar este proyecto.")

    if titulo is not None:
        proyecto.titulo = titulo
    if descripcion is not None:
        proyecto.descripcion = descripcion
    if estado is not None:
        proyecto.estado = estado
    if visibilidad is not None:
        proyecto.visibilidad = visibilidad

    db.commit()
    db.refresh(proyecto)
    return proyecto

@router.delete("/{slug}", status_code=status.HTTP_200_OK)
def eliminar_proyecto(
    slug: str,
    db: Session = Depends(get_BaseDeDatos),
    usuario_actual: models.Usuario = Depends(get_current_user)
):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.slug == slug).first()
    
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")

    if proyecto.id_autor != usuario_actual.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para eliminar este proyecto.")

    if proyecto.archivo_ruta and os.path.exists(proyecto.archivo_ruta):
        try:
            os.remove(proyecto.archivo_ruta)
        except Exception:
            pass

    db.delete(proyecto)
    db.commit()

    return {"mensaje": "Proyecto y archivo asociados eliminados exitosamente."}