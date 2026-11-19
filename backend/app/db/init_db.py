from app.db.session import SessionLocal
import app.models.models as models

def cargar_datos_iniciales():
    db = SessionLocal()

    # Crear roles si no existen
    if not db.query(models.Rol).first():
        roles = ["Administrador", "Rector", "Docente", "Estudiante"]
        for r in roles:
            db.add(models.Rol(nombre=r))
        db.commit()

    # Crear carrera de prueba si no existe
    if not db.query(models.Carrera).first():
        carrera = models.Carrera(nombre="Ingeniería en Informática")
        db.add(carrera)
        db.commit()

    # Crear usuario de prueba si no existe
    if not db.query(models.Usuario).first():
        usuario = models.Usuario(
            email="estudiante@unetur.edu.ve",
            password_hash="123456",  # En etapas posteriores agregaremos hashing
            nombre="Estudiante Unetur",
            id_rol=4, # Estudiante
            id_carrera=1
        )
        db.add(usuario)
        db.commit()

    db.close()
    print("Datos iniciales cargados con éxito.")

if __name__ == "__main__":
    cargar_datos_iniciales()