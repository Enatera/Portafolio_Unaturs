import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class EstadoProyecto(str, enum.Enum):
    borrador = "borrador"
    en_revision = "en_revision"
    publico = "publico"

class VisibilidadProyecto(str, enum.Enum):
    publico = "publico"
    estudiantes = "estudiantes"
    profesores = "profesores"
    privado = "privado"

class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")
    proyectos = relationship("Proyecto", back_populates="rol")

class Carrera(Base):
    __tablename__ = "carreras"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)

    proyectos = relationship("Proyecto", back_populates="carrera")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    id_rol = Column(Integer, ForeignKey("roles.id"), nullable=True)
    
    rol = relationship("Rol", back_populates="usuarios")
    proyectos = relationship("Proyecto", back_populates="autor")
    aprobado = Column(Boolean, default=True) # True para estudiantes por defecto, False para profesores en espera

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, index=True, nullable=False) # 👈 Nuevo campo slug
    descripcion = Column(String(500), nullable=True)
    archivo_ruta = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    estado = Column(
        SQLEnum(EstadoProyecto), 
        default=EstadoProyecto.borrador, 
        nullable=False
    )
    
    visibilidad = Column(
        SQLEnum(VisibilidadProyecto), 
        default=VisibilidadProyecto.estudiantes, 
        nullable=False
    )

    id_carrera = Column(Integer, ForeignKey("carreras.id"), nullable=False)
    id_autor = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id"), nullable=True)

    autor = relationship("Usuario", back_populates="proyectos")
    carrera = relationship("Carrera", back_populates="proyectos")
    rol = relationship("Rol", back_populates="proyectos")