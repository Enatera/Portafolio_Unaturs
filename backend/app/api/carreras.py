from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_BaseDeDatos
import app.models.models as models
import app.schemas.schemas as schemas
from app.api.auth import get_current_user

router = APIRouter(prefix="/carreras", tags=["Carreras"])

@router.get("", response_model=List[schemas.CarreraOut])
def listar_carreras(db: Session = Depends(get_BaseDeDatos)):
    """Obtiene la lista de todas las carreras disponibles para los desplegables del frontend."""
    carreras = db.query(models.Carrera).all()
    return carreras

@router.post("", response_model=schemas.CarreraOut, status_code=status.HTTP_201_CREATED)
def crear_carrera(
    carrera: schemas.CarreraCreate,
    db: Session = Depends(get_BaseDeDatos),
    usuario_actual: models.Usuario = Depends(get_current_user)
):
    """Permite registrar una nueva carrera (ideal para administradores)."""
    # Verificar si ya existe una carrera con el mismo nombre
    carrera_existente = db.query(models.Carrera).filter(models.Carrera.nombre == carrera.nombre).first()
    if carrera_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una carrera registrada con ese nombre."
        )

    nueva_carrera = models.Carrera(nombre=carrera.nombre)
    db.add(nueva_carrera)
    db.commit()
    db.refresh(nueva_carrera)
    
    return nueva_carrera