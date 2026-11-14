import uuid
from typing import Optional, Callable
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

try:
    from common.database import get_db
except ImportError:
    from services.common.database import get_db

try:
    from services.ms3_auth.models import User, Role
    from services.ms3_auth.services.oidc_service import oidc_service
except ImportError:
    from models import User, Role
    from services.oidc_service import oidc_service

http_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de seguridad que extrae y valida el JWT Bearer token del encabezado Authorization.
    Retorna el modelo User autenticado y activo.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación no proporcionadas (Bearer token requerido)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        claims = oidc_service.verify_session_jwt(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_raw = claims.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene identificador de sujeto válido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuario en token no tiene formato UUID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario autenticado no existe en la base de datos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra inactiva",
        )

    return user


def require_role(required_role: str) -> Callable[[User], User]:
    """
    Fábrica de dependencias para validar roles RBAC específicos.
    El rol 'Admin' tiene acceso implícito a todas las funciones.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.name if current_user.role else "Academico"
        if user_role == "Admin":
            return current_user
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: El rol '{user_role}' no cuenta con permisos para esta operación. Se requiere '{required_role}'."
            )
        return current_user

    return role_checker


# Dependencias convenientes preconfiguradas
require_curator = require_role("Curador_VRIIC")
require_admin = require_role("Admin")
