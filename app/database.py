from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtenemos la URL de la base de datos, con un valor por defecto
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# Crear el motor (engine) de SQLAlchemy
engine = create_engine(DATABASE_URL)

# Crear la clase base para las sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para que los modelos ORM hereden de ella
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos y cerrarla automáticamente
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
