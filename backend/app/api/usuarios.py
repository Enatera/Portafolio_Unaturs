from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_BaseDeDatos
import app.models.models as models
import app.schemas.schemas as schemas
from app.api.auth import es_administrador

router = APIRouter(prefix="/api/v1/usuarios", tags=["Gestión de Usuarios"])

@router.patch("/{usuario_id}/rol", response_model=schemas.UsuarioOut)
def cambiar_rol_usuario(
    usuario_id: int,
    datos_rol: schemas.CambiarRolUsuario,
    db: Session = Depends(get_BaseDeDatos),
    admin_actual: models.Usuario = Depends(es_administrador)  # Restringido solo a Admins
):
    # Validar existencia del usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    # Validar existencia del rol
    rol = db.query(models.Rol).filter(models.Rol.id == datos_rol.id_rol).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El rol especificado no existe."
        )

    usuario.id_rol = datos_rol.id_rol
    db.commit()
    db.refresh(usuario)
    return usuario