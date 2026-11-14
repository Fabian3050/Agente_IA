import os
import json
import logging
from sqlalchemy.orm import Session

try:
    from services.ms3_auth.models import Role, User
except ImportError:
    from models import Role, User

logger = logging.getLogger(__name__)


def seed_roles(db: Session) -> int:
    """Siembra los 3 roles formales de RBAC en MS3 si no existen."""
    roles_data = [
        ("Admin", "Administrador de la plataforma y gobierno de datos."),
        ("Curador_VRIIC", "Curador autorizado de la Vicerrectoría de Investigación, Innovación y Creación."),
        ("Academico", "Investigador o académico de la Universidad de Santiago de Chile.")
    ]
    created = 0
    for name, desc in roles_data:
        r = db.query(Role).filter(Role.name == name).first()
        if not r:
            db.add(Role(name=name, description=desc))
            created += 1
    db.commit()
    return created


def seed_initial_users(db: Session) -> int:
    """
    Carga o sincroniza usuarios iniciales durante el arranque del despliegue:
    1. Lee variables de entorno (INITIAL_ADMIN_*, INITIAL_CURATOR_*).
    2. Si existe un archivo JSON en INITIAL_USERS_FILE o variable INITIAL_USERS_JSON, los carga.
    3. Si la base de datos está limpia y no se pasaron variables, carga usuarios institucionales base por defecto.
    Garantiza idempotencia (no duplica si el email ya existe).
    """
    roles_map = {r.name: r for r in db.query(Role).all()}
    if not roles_map:
        seed_roles(db)
        roles_map = {r.name: r for r in db.query(Role).all()}

    users_to_seed = []

    # Opción A: Archivo JSON montado (ej. /app/config/initial_users.json)
    json_path = os.getenv("INITIAL_USERS_FILE", "")
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    users_to_seed.extend(data)
        except Exception as e:
            logger.warning(f"[MS3] Error leyendo INITIAL_USERS_FILE: {e}")

    # Opción B: JSON serializado en variable de entorno
    json_env = os.getenv("INITIAL_USERS_JSON", "").strip()
    if json_env:
        try:
            parsed = json.loads(json_env)
            if isinstance(parsed, list):
                users_to_seed.extend(parsed)
        except Exception as e:
            logger.warning(f"[MS3] Error parseando INITIAL_USERS_JSON: {e}")

    # Opción C: Variables de entorno explícitas (INITIAL_ADMIN_* e INITIAL_CURATOR_*)
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
    if admin_email:
        users_to_seed.append({
            "email": admin_email.strip().lower(),
            "name": os.getenv("INITIAL_ADMIN_NAME", "Administrador"),
            "last_name": os.getenv("INITIAL_ADMIN_LAST_NAME", "VRIIC"),
            "role": "Admin",
            "orcid": os.getenv("INITIAL_ADMIN_ORCID", None),
            "dspace_person_id": os.getenv("INITIAL_ADMIN_DSPACE_ID", None)
        })

    curator_email = os.getenv("INITIAL_CURATOR_EMAIL")
    if curator_email:
        users_to_seed.append({
            "email": curator_email.strip().lower(),
            "name": os.getenv("INITIAL_CURATOR_NAME", "Curador"),
            "last_name": os.getenv("INITIAL_CURATOR_LAST_NAME", "VRIIC"),
            "role": "Curador_VRIIC",
            "orcid": os.getenv("INITIAL_CURATOR_ORCID", "0000-0002-1825-0097"),
            "dspace_person_id": os.getenv("INITIAL_CURATOR_DSPACE_ID", None)
        })

    # Si no se configuró nada, asegurar usuarios institucionales representativos por defecto
    if not users_to_seed:
        users_to_seed = [
            {
                "email": "fabian.escobedo@usach.cl",
                "name": "Administrador",
                "last_name": "VRIIC",
                "role": "Admin",
                "orcid": None,
                "dspace_person_id": "admin-person-001"
            },
            {
                "email": "curador.vriic@usach.cl",
                "name": "Curador",
                "last_name": "VRIIC",
                "role": "Curador_VRIIC",
                "orcid": "0000-0002-1825-0097",
                "dspace_person_id": "curator-person-002"
            },
            {
                "email": "investigador@usach.cl",
                "name": "Académico",
                "last_name": "Investigador",
                "role": "Academico",
                "orcid": "0000-0001-5000-2000",
                "dspace_person_id": "academic-person-003"
            }
        ]

    created = 0
    for u_data in users_to_seed:
        email = u_data.get("email", "").strip().lower()
        if not email:
            continue

        existing = db.query(User).filter(User.email == email).first()
        role_name = u_data.get("role", "Academico")
        target_role = roles_map.get(role_name) or roles_map.get("Academico")

        if not existing:
            new_user = User(
                id_role=target_role.id,
                name=u_data.get("name", "Usuario"),
                last_name=u_data.get("last_name", "Institucional"),
                email=email,
                sub=u_data.get("sub", f"usach-seed-{email}"),
                orcid=u_data.get("orcid"),
                dspace_person_id=u_data.get("dspace_person_id"),
                is_active=True
            )
            db.add(new_user)
            created += 1
            logger.info(f"[MS3 Seed] Usuario inicial creado: {email} ({role_name})")
        else:
            # Asegurar que tenga el rol indicado si es el seed oficial
            if target_role and existing.id_role != target_role.id:
                existing.id_role = target_role.id

    db.commit()
    return created


def seed_initial_users(db: Session) -> int:
    """
    Carga o sincroniza usuarios iniciales durante el arranque del despliegue:
    1. Lee variables de entorno (INITIAL_ADMIN_*, INITIAL_CURATOR_*).
    2. Si existe un archivo JSON en INITIAL_USERS_FILE o variable INITIAL_USERS_JSON, los carga.
    3. Si la base de datos está limpia y no se pasaron variables, carga usuarios institucionales base por defecto.
    Garantiza idempotencia (no duplica si el email ya existe).
    """
    roles_map = {r.name: r for r in db.query(Role).all()}
    if not roles_map:
        seed_roles(db)
        roles_map = {r.name: r for r in db.query(Role).all()}

    users_to_seed = []

    # Opción A: Archivo JSON montado (ej. /app/config/initial_users.json)
    json_path = os.getenv("INITIAL_USERS_FILE", "")
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    users_to_seed.extend(data)
        except Exception as e:
            logger.warning(f"[MS3] Error leyendo INITIAL_USERS_FILE: {e}")

    # Opción B: JSON serializado en variable de entorno
    json_env = os.getenv("INITIAL_USERS_JSON", "").strip()
    if json_env:
        try:
            parsed = json.loads(json_env)
            if isinstance(parsed, list):
                users_to_seed.extend(parsed)
        except Exception as e:
            logger.warning(f"[MS3] Error parseando INITIAL_USERS_JSON: {e}")

    # Opción C: Variables de entorno explícitas (INITIAL_ADMIN_* e INITIAL_CURATOR_*)
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL")
    if admin_email:
        users_to_seed.append({
            "email": admin_email.strip().lower(),
            "name": os.getenv("INITIAL_ADMIN_NAME", "Administrador"),
            "last_name": os.getenv("INITIAL_ADMIN_LAST_NAME", "VRIIC"),
            "role": "Admin",
            "orcid": os.getenv("INITIAL_ADMIN_ORCID", None),
            "dspace_person_id": os.getenv("INITIAL_ADMIN_DSPACE_ID", None)
        })

    curator_email = os.getenv("INITIAL_CURATOR_EMAIL")
    if curator_email:
        users_to_seed.append({
            "email": curator_email.strip().lower(),
            "name": os.getenv("INITIAL_CURATOR_NAME", "Curador"),
            "last_name": os.getenv("INITIAL_CURATOR_LAST_NAME", "VRIIC"),
            "role": "Curador_VRIIC",
            "orcid": os.getenv("INITIAL_CURATOR_ORCID", "0000-0002-1825-0097"),
            "dspace_person_id": os.getenv("INITIAL_CURATOR_DSPACE_ID", None)
        })

    # Si no se configuró nada, asegurar usuarios institucionales representativos por defecto
    if not users_to_seed:
        users_to_seed = [
            {
                "email": "admin.vriic@usach.cl",
                "name": "Administrador",
                "last_name": "VRIIC",
                "role": "Admin",
                "orcid": None,
                "dspace_person_id": "admin-person-001"
            },
            {
                "email": "curador.vriic@usach.cl",
                "name": "Curador",
                "last_name": "VRIIC",
                "role": "Curador_VRIIC",
                "orcid": "0000-0002-1825-0097",
                "dspace_person_id": "curator-person-002"
            },
            {
                "email": "investigador@usach.cl",
                "name": "Académico",
                "last_name": "Investigador",
                "role": "Academico",
                "orcid": "0000-0001-5000-2000",
                "dspace_person_id": "academic-person-003"
            }
        ]

    created = 0
    for u_data in users_to_seed:
        email = u_data.get("email", "").strip().lower()
        if not email:
            continue

        existing = db.query(User).filter(User.email == email).first()
        role_name = u_data.get("role", "Academico")
        target_role = roles_map.get(role_name) or roles_map.get("Academico")

        if not existing:
            new_user = User(
                id_role=target_role.id,
                name=u_data.get("name", "Usuario"),
                last_name=u_data.get("last_name", "Institucional"),
                email=email,
                sub=u_data.get("sub", f"usach-seed-{email}"),
                orcid=u_data.get("orcid"),
                dspace_person_id=u_data.get("dspace_person_id"),
                is_active=True
            )
            db.add(new_user)
            created += 1
            logger.info(f"[MS3 Seed] Usuario inicial creado: {email} ({role_name})")
        else:
            # Asegurar que tenga el rol indicado si es el seed oficial
            if target_role and existing.id_role != target_role.id:
                existing.id_role = target_role.id

    db.commit()
    return created
