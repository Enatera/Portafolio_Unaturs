from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr
from app.models.models import EstadoProyecto, VisibilidadProyecto

class RolPermitido(str, Enum):
    ESTUDIANTE = "estudiante"
    PROFESOR = "profesor"

class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolPermitido  # Solo aceptará "estudiante" o "profesor"

# Esquemas para Usuario
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolPermitido

class CambiarRolUsuario(BaseModel):
    id_rol: int    

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    id_rol: Optional[int] = None

    model_config = {"from_attributes": True}

# Esquemas para Tokens JWT
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# --- ESQUEMAS PARA ROLES Y CARRERAS ---
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class RolOut(RolBase):
    id: int
    class Config:
        from_attributes = True

class CarreraBase(BaseModel):
    nombre: str

class CarreraCreate(BaseModel):
    nombre: str

class CarreraOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Optional[str] = "Estudiante"  # Valor por defecto

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    id_rol: Optional[int] = None

    model_config = {"from_attributes": True}

# --- ESQUEMAS PARA PROYECTOS ---
class ProyectoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    id_carrera: int
    # Opcionales al crear: si no los envían, toman el valor por defecto
    estado: Optional[EstadoProyecto] = EstadoProyecto.borrador
    visibilidad: Optional[VisibilidadProyecto] = VisibilidadProyecto.estudiantes

class ProyectoOut(BaseModel):
    id: int
    titulo: str
    slug: str  # 👈 Añade esta línea si te faltaba
    descripcion: Optional[str] = None
    archivo_ruta: Optional[str] = None
    estado: EstadoProyecto
    visibilidad: VisibilidadProyecto
    id_carrera: int
    id_autor: int
    id_rol: Optional[int] = None

    class Config:
        from_attributes = True