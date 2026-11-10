# Agente IA DSpace-CRIS (Versión 3.0)

Sistema de soporte a la decisión de curaduría institucional y enriquecimiento determinista de metadatos para **DSpace-CRIS de la VRIIC (Universidad de Santiago de Chile)**.

El sistema opera de forma totalmente desacoplada, identificando deficiencias de metadatos, consultando fuentes científicas globales, clasificando publicaciones mediante inferencia semántica con un modelo de lenguaje local (LLM) y generando propuestas atomizadas por campo sometidas a validación humana antes de su ingesta masiva.

---

## 🏛️ Arquitectura de Microservicios (4 Servicios Desacoplados)

El sistema aísla las cargas de trabajo intensivas de I/O de red, cómputo de IA, autenticación y orquestación institucional:

```
                   +---------------------------------------------+
                   |          DSpace-CRIS REST API (VRIIC)        |
                   +----------------------+----------------------+
                                          |
                                          v
+------------------+         +------------+------------+         +------------------+
| MS1: Recuperación| <=====> |   MS4: Orquestación     | <=====> |  MS3: Usuarios   |
|   de Metadatos   | RabbitMQ|    e Integración        |  REST   |  RBAC & Auditoría|
|  (Puerto 8001)   |         |    (Puerto 8000)        |         |  (Puerto 8003)   |
+------------------+         +------------+------------+         +------------------+
                                          |
                                          | RabbitMQ
                                          v
                             +------------+------------+
                             | MS2: Clasificación LLM  |
                             |   FORD OCDE & ODS ONU   |
                             |      (Puerto 8002)      |
                             +-------------------------+
                                          |
                                          v
                                   Ollama (Local)
                              Llama 3.2 (3B) - T = 0.0
```

### Delimitación Estricta de Propiedad de Tablas (Tercera Forma Normal - 3NF)

Cada una de las **13 tablas relacionales** tiene un único microservicio autorizado para escribir en ella:

* **MS1 (Recuperación)**: `Candidate_Match`, `External_API_Source`.
* **MS2 (Clasificación)**: `LLM_Classification_Log`, `Category`.
* **MS3 (Usuarios & Auditoría)**: `User`, `Role`, `Audit_Log` (*INSERT-only*).
* **MS4 (Orquestación & Integración)**: `Item_Enrichment`, `Field_Proposal`, `Item_Category`, `Status`, `Job`, `DSpace_Sync_Log`.

---

## 🔄 Ciclo de Vida Formal del Dato Enriquecido (12 Estados Unívocos)

1. **`Detectada`**: El monitoreo detecta campos vacíos en DSpace-CRIS y verifica ausencia de propuesta previa (*idempotencia temprana*).
2. **`En_recuperacion`**: Consultas asíncronas concurrentes a Crossref, OpenAlex, Unpaywall, Europe PMC y Semantic Scholar.
3. **`Coincidencia_dudosa`**: La similitud textual (Levenshtein) no alcanza el umbral de certeza (85% con DOI, 70%-94% sin DOI).
4. **`En_clasificacion`**: Inferencia semántica con Ollama local para asignar categorías FORD OCDE y metas ODS.
5. **`En_reintento`**: Manejo de fallas transitorias con espera exponencial (*Exponential Backoff*).
6. **`En_revision`**: Propuesta consolidada con trazabilidad atómica por campo disponible en el panel de curaduría.
7. **`Invalidada`**: El registro original en DSpace-CRIS fue alterado externamente antes o durante la curaduría.
8. **`Rechazada`**: El curador desestimó la propuesta registrando el motivo en la bitácora histórica.
9. **`Aprobada`**: El curador aprobó o editó los valores propuestos.
10. **`Exportada`**: Metadatos aprobados agrupados en lote CSV seguro con **CERO celdas vacías**.
11. **`Cargada`**: El ciclo de monitoreo confirma que los metadatos aprobados se reflejan en DSpace-CRIS.
12. **`Cerrada`**: Propuesta finalizada exitosamente en su ciclo de vida institucional.

---

## 🛡️ Protocolo de Exportación Segura por CSV (Cero Celdas Vacías)

La ingesta masiva en DSpace-CRIS reemplaza los valores de cada columna incluida; si una celda está vacía en una columna presente, DSpace elimina el metadato del repositorio. Para prevenir pérdida de datos:
1. **Revalidación de concurrencia**: Compara `last_modified_dspace`. Si el ítem cambió en el repositorio desde que el curador lo aprobó, transita a `Invalidada` y se excluye.
2. **Agrupación por subconjunto de columnas**: Clasifica las propuestas aprobadas por conjuntos idénticos de campos a actualizar, generando archivos CSV independientes donde **todas las celdas tienen valor obligatorio**.
3. **Verificación en dos pasos**: Transición `Exportada` $\rightarrow$ `Cargada` $\rightarrow$ `Cerrada` tras verificación vía API REST.

---

## 🚀 Despliegue con Docker Compose

El stack completo se levanta mediante contenedores aislados:

```bash
# 1. Crear archivos de secretos en ./secrets/ (reemplazar con credenciales reales)
mkdir -p secrets
echo "postgres" > secrets/db_password.txt
echo "user=admin@usach.cl\npassword=secret" > secrets/dspace_credentials.txt

# 2. Levantar los 4 microservicios + PostgreSQL + RabbitMQ + Ollama:
docker compose up -d --build
```

### Puertos y Servicios Expuestos:
* **MS4 (Gateway Principal)**: `http://localhost:8000`
* **MS1 (Recuperación de Metadatos)**: `http://localhost:8001`
* **MS2 (Clasificación LLM)**: `http://localhost:8002`
* **MS3 (Usuarios & Auditoría)**: `http://localhost:8003`
* **RabbitMQ Dashboard**: `http://localhost:15672` (guest / guest)
* **Ollama Server**: `http://localhost:11434`

---

## 💻 Ejecución Local y Desarrollo

### 1. Entorno Virtual e Instalación
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Inicialización de Base de Datos y Catálogos Oficiales (Seeding)
Crea las 13 tablas relacionales y siembra los 12 estados, 5 fuentes científicas, roles y catálogos completos FORD OCDE (2007) y ODS ONU (2015):
```bash
python seed_db.py
```

### 3. Ejecución del Pipeline Batch
```bash
python procesar_dois.py
```

### 4. Suite de Pruebas de Integración Continua (Sección 5.4)
Ejecuta las pruebas automatizadas que verifican los requerimientos críticos de la especificación técnica:
```bash
python -m unittest tests/test_integration_v3.py
```

Pruebas verificadas:
* `test_double_detection`: Idempotencia temprana (omisión de llamadas redundantes ante propuestas activas).
* `test_external_change_invalidation`: Invalidación y exclusión inmediata si el registro cambia en DSpace.
* `test_csv_zero_empty_cells`: Verificación estricta de CERO celdas vacías en los lotes CSV generados.
* `test_partial_source_failure`: Resiliencia ante caídas de fuentes científicas individuales.
* `test_max_retries_exhaustion`: Tránsito a revisión con error registrado en `Job` al agotar 3 reintentos.
* `test_rbac_permissions_isolation`: Rechazo HTTP 403 para usuarios con rol `Academico` que intenten curaduría.
