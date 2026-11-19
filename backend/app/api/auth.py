from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import hashlib
import os
import bcrypt

from app.db.session import get_BaseDeDatos
import app.models.models as models
import app.schemas.schemas as schemas
from app.models.models import Usuario, Rol

router = APIRouter(tags=["Autenticación"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SECRET_KEY = "clave_secreta_super_segura_unaturs"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def obtener_password_hash(password: str) -> str:
    """Genera un hash PBKDF2-HMAC-SHA256 con salt para una contraseña."""
    salt = os.urandom(16)
    pwd_bytes = password.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt, 100000)
    # Formato limpio: salt_hex:key_hex
    return f"{salt.hex()}:{key.hex()}"


def verificar_password(password_plano: str, password_encriptado: str) -> bool:
    """Verifica una contraseña contra su hash (admite formatos bcrypt y PBKDF2)."""
    # 1. Intentar verificar si fue generado con Bcrypt
    try:
        pwd_bytes = password_plano.encode("utf-8")[:72]
        hash_bytes = password_encriptado.encode("utf-8")
        if bcrypt.checkpw(pwd_bytes, hash_bytes):
            return True
    except Exception:
        pass  # Si falla o no es formato bcrypt, continúa probando PBKDF2

    # 2. Intentar verificar si fue generado con PBKDF2 (salt:key o salt$key)
    try:
        if ":" in password_encriptado:
            salt_hex, key_hex = password_encriptado.split(":", 1)
        elif "$" in password_encriptado:
            partes = [p for p in password_encriptado.split("$") if p]
            if len(partes) != 2:
                return False
            salt_hex, key_hex = partes[0], partes[1]
        else:
            return False

        salt = bytes.fromhex(salt_hex)
        pwd_bytes = password_plano.encode("utf-8")
        nueva_key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt, 100000)

        # Se usa hmac.compare_digest para prevenir ataques de tiempo (timing attacks)
        import hmac

        return hmac.compare_digest(nueva_key.hex(), key_hex)
    except Exception:
        return False

def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expiracion})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_BaseDeDatos)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
    return usuario
        

def es_administrador(usuario_actual: models.Usuario = Depends(get_current_user)):
    # Asumiendo que id_rol = 3 es Administrador
    if usuario_actual.id_rol != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción."
        )
    return usuario_actual

    # Endpoint para obtener el perfil del usuario autenticado
@router.get("/me", response_model=schemas.UsuarioOut)
def obtener_perfil_me(id_autor: models.Usuario = Depends(get_current_user)):
    return id_autor

@router.get("/me", response_model=schemas.UsuarioOut)
def obtener_usuario_actual(usuario_actual: models.Usuario = Depends(get_current_user)):
    """Devuelve la información del usuario autenticado actualmente a través del token JWT."""
    return usuario_actual

@router.get("/me")
def obtener_perfil_actual(usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    return {
        "id": usuario_actual.id,
        "nombre": usuario_actual.nombre,
        "email": usuario_actual.email,
        "rol": usuario_actual.rol.nombre if usuario_actual.rol else "Usuario"
    }    

@router.post("/registro", response_model=schemas.UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_BaseDeDatos)):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )
    
    rol_nombre = usuario.rol.value if isinstance(usuario.rol, schemas.RolPermitido) else usuario.rol

    # 🔒 1. RESTRICCIÓN DE SEGURIDAD: Nadie puede registrarse como Administrador libremente
    if rol_nombre.lower() in ["administrador", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No está permitido registrarse directamente como Administrador."
        )

    rol_db = db.query(models.Rol).filter(models.Rol.nombre == rol_nombre).first()
    if not rol_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El rol '{rol_nombre}' no es admitido por la aplicación."
        )  

    # 🔒 2. VALIDACIÓN DE PROFESOR: Si es profesor, nace inactivo/no aprobado en espera del Admin
    cuenta_aprobada = True
    if rol_nombre.lower() == "profesor":
        cuenta_aprobada = False

    password_hash = obtener_password_hash(usuario.password)

    nuevo_usuario = models.Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=password_hash,
        id_rol=rol_db.id,
        aprobado=cuenta_aprobada # 👈 Asignamos el estado de aprobación
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_BaseDeDatos)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    
    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 🔒 3. COMPROBAR SI EL PROFESOR ESTÁ APROBADO
    if hasattr(usuario, 'aprobado') and usuario.aprobado is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta de profesor está pendiente de autorización por un Administrador."
        )
    
    access_token = crear_token_acceso(data={"sub": usuario.email, "user_id": usuario.id})
    return {"access_token": access_token, "token_type": "bearer"}