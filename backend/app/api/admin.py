from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_BaseDeDatos
from app.models import models
from app.api.auth import obtener_usuario_actual  # Dependencia que valida el token del usuario logueado
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin", tags=["Administración"])

class RolUpdate(BaseModel):
    nuevo_rol: str

@router.put("/usuarios/{usuario_id}/rol")
def cambiar_rol_usuario(
    usuario_id: int, 
    datos: RolUpdate,
    db: Session = Depends(get_BaseDeDatos), 
    usuario_actual: models.Usuario = Depends(obtener_usuario_actual)
):
    if not usuario_actual.rol or usuario_actual.rol.nombre.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    usuario_objetivo = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario_objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    rol_db = db.query(models.Rol).filter(models.Rol.nombre.ilike(datos.nuevo_rol)).first()
    if not rol_db:
        raise HTTPException(status_code=400, detail="El rol especificado no es válido.")
    
    usuario_objetivo.id_rol = rol_db.id
    db.commit()
    
    return {"mensaje": f"El rol de {usuario_objetivo.nombre} fue actualizado a {rol_db.nombre}."}

@router.get("/usuarios")
def listar_todos_los_usuarios(
    db: Session = Depends(get_BaseDeDatos), 
    usuario_actual: models.Usuario = Depends(obtener_usuario_actual)
):
    # Verificar que el usuario actual sea Administrador
    if not usuario_actual.rol or usuario_actual.rol.nombre.lower() != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren privilegios de Administrador."
        )
    
    usuarios = db.query(models.Usuario).all()
    # Mapeamos para devolver información limpia al frontend
    resultado = []
    for u in usuarios:
        resultado.append({
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "rol": u.rol.nombre if u.rol else "Sin Rol",
            "aprobado": u.aprobado
        })
    return resultado

@router.put("/usuarios/{usuario_id}/aprobar")
def aprobar_usuario(
    usuario_id: int, 
    db: Session = Depends(get_BaseDeDatos), 
    usuario_actual: models.Usuario = Depends(obtener_usuario_actual)
):
    if not usuario_actual.rol or usuario_actual.rol.nombre.lower() != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado."
        )
    
    usuario_objetivo = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario_objetivo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    usuario_objetivo.aprobado = True
    db.commit()
    
    return {"mensaje": f"El usuario {usuario_objetivo.nombre} ha sido aprobado correctamente."}

@router.put("/usuarios/{usuario_id}/rol")
def actualizar_rol_usuario(
    usuario_id: int, 
    datos: RolUpdate,
    db: Session = Depends(get_BaseDeDatos), 
    usuario_actual: models.Usuario = Depends(obtener_usuario_actual)
):
    if not usuario_actual.rol or usuario_actual.rol.nombre.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    usuario_objetivo = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario_objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    rol_db = db.query(models.Rol).filter(models.Rol.nombre.ilike(datos.nuevo_rol)).first()
    if not rol_db:
        raise HTTPException(status_code=400, detail="El rol especificado no existe.")
    
    usuario_objetivo.id_rol = rol_db.id
    db.commit()
    
    return {"mensaje": f"Rol actualizado correctamente a {rol_db.nombre}"}