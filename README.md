# Agente_IA
Despliegue de prototipo agente de IA 

## Despliegue Local y Prueba de `procesar_dois.py`

Para ejecutar localmente el script `procesar_dois.py` y probar la completitud de metadatos, sigue estos pasos:

### 1. Requisitos Previos
- **Python 3.8+**
- **PostgreSQL** corriendo localmente (o mediante Docker).
- **Ollama** corriendo localmente con el modelo Llama 3.2 o el que soporte el dispositivo en donde se quiera probar el sistema (necesario para la clasificación de las áreas OCDE/ODS).

### 2. Configurar el Entorno
Crea un entorno virtual e instala las dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuración de la Base de Datos
Por defecto, la aplicación se conecta a `postgresql://postgres:postgres@localhost:5432/postgres`.
Puedes levantar una base de datos PostgreSQL de prueba rápidamente con Docker:
```bash
docker run --name postgres-agente -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```
*(Si usas otra configuración, crea un archivo `.env` en la raíz del proyecto y define tu variable de entorno: `DATABASE_URL=postgresql://usuario:password@localhost:5432/tubd`)*

### 4. Poblar Base de Datos de Ejemplo (Seed)
Para que `procesar_dois.py` funcione, necesita registros en la tabla `doi_records`. Puedes inicializar las tablas y agregar DOIs de prueba creando y ejecutando el siguiente script (`seed_db.py`) en la raíz del proyecto:

```python
from app.database import engine, Base, SessionLocal
from app.models.db_models import DoiRecord

# 1. Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# 2. Insertar DOIs de prueba
db = SessionLocal()
dois_de_prueba = [
    "10.1038/s41586-020-2649-2", # Ejemplo 1
    "10.1126/science.1249098"    # Ejemplo 2
]

for doi in dois_de_prueba:
    existe = db.query(DoiRecord).filter(DoiRecord.doi == doi).first()
    if not existe:
        nuevo_registro = DoiRecord(doi=doi)
        db.add(nuevo_registro)

db.commit()
db.close()
print("Base de datos inicializada con DOIs de prueba.")
```

Ejecuta el script:
```bash
python seed_db.py
```

### 5. Ejecutar `procesar_dois.py`
Una vez que tengas la base de datos lista y con datos de prueba, ejecuta el script de procesamiento:

```bash
python procesar_dois.py
```

El script iterará sobre los DOIs de la base de datos, consultará OpenAlex para obtener sus metadatos y utilizará el servicio de clasificación LLM para categorizarlos en áreas de la OCDE y ODS. Los resultados de la completitud se guardarán en la tabla `document_metadata`.
