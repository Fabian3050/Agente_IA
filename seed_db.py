from app.database import engine, Base, SessionLocal
from app.models.db_models import DoiRecord

# 1. Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# 2. Insertar DOIs de prueba
db = SessionLocal()
dois_de_prueba = [
    "10.1177/16878140211010657",
    "10.1016/j.robot.2024.104661",
    "10.1155/2020/7816785",
    "10.1117/12.911931",
    "10.3390/ijms21217922",
    "10.22481/praxisedu.v21i52.17106",
    "10.5354/0719-2584.2025.74613"
]

for doi in dois_de_prueba:
    existe = db.query(DoiRecord).filter(DoiRecord.doi == doi).first()
    if not existe:
        nuevo_registro = DoiRecord(doi=doi)
        db.add(nuevo_registro)

db.commit()
db.close()
print("Base de datos inicializada con DOIs de prueba.")