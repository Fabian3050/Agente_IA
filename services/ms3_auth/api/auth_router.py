import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

try:
    from common.database import get_db
except ImportError:
    from services.common.database import get_db

try:
    from services.ms3_auth.models import (
        User, Role, UserDTO, TokenResponseDTO,
        OIDCTokenExchangeRequest, MockLoginRequest,
        TokenIntrospectRequest, TokenIntrospectResponse,
        CreateUserRequest
    )
    from services.ms3_auth.services.audit_service import MS3AuditWorker
    from services.ms3_auth.services.oidc_service import oidc_service
    from services.ms3_auth.security import get_current_user
except ImportError:
    from models import (
        User, Role, UserDTO, TokenResponseDTO,
        OIDCTokenExchangeRequest, MockLoginRequest,
        TokenIntrospectRequest, TokenIntrospectResponse,
        CreateUserRequest
    )
    from services.audit_service import MS3AuditWorker
    from services.oidc_service import oidc_service
    from security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
audit_worker = MS3AuditWorker()


# -----------------------------------------------------------------------------
# 1. FLUJO OAUTH 2.0 / OPENID CONNECT (AUTHORIZATION CODE)
# -----------------------------------------------------------------------------

@router.get("/login")
def login(
    state: Optional[str] = Query(None, description="Estado de seguridad anti-CSRF"),
    redirect_uri: Optional[str] = Query(None, description="URI de redirección post-login"),
    auto_redirect: bool = Query(False, description="Redirigir automáticamente (HTTP 307) o retornar URL JSON")
):
    """
    Inicia el flujo de autenticación OpenID Connect (OIDC) con el proveedor institucional (USACH SSO).
    Retorna la URL de autorización hacia el IdP o ejecuta la redirección HTTP directa.
    """
    auth_url = oidc_service.get_authorization_url(state=state, redirect_uri=redirect_uri)
    if auto_redirect:
        return RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return {
        "authorization_url": auth_url,
        "protocol": "OpenID Connect 1.0 / OAuth 2.0",
        "response_type": "code",
        "scope": oidc_service.scopes
    }


@router.get("/callback", response_model=TokenResponseDTO)
async def auth_callback(
    code: str = Query(..., description="Código de autorización emitido por el IdP"),
    state: Optional[str] = Query(None, description="Estado anti-CSRF retornado"),
    redirect_uri: Optional[str] = Query(None, description="URI de redirección configurada"),
    db: Session = Depends(get_db)
):
    """
    Callback del flujo Authorization Code de OIDC:
    1. Intercambia el código por tokens con el IdP institucional.
    2. Valida las claims del ID Token (sub, email, nombre, rol, ORCID).
    3. Aprovisiona o actualiza el usuario en la BD de MS3 (Just-in-Time).
    4. Emite un JWT firmado de sesión interna para el Agente IA.
    """
    try:
        token_payload = await oidc_service.exchange_code_for_tokens(code=code, redirect_uri=redirect_uri)
        id_token = token_payload.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proveedor OIDC no retornó un id_token válido"
            )

        claims = oidc_service.parse_id_token_unverified(id_token)
        user = oidc_service.provision_user_from_claims(db, claims)
        jwt_token, expires_in = oidc_service.create_session_jwt(user)

        user_dto = UserDTO(
            id=user.id,
            name=user.name,
            last_name=user.last_name,
            email=user.email,
            role_name=user.role.name if user.role else "Academico",
            sub=user.sub,
            orcid=user.orcid,
            dspace_person_id=user.dspace_person_id,
            is_active=user.is_active,
            last_login=user.last_login
        )

        return TokenResponseDTO(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_dto
        )

    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo en callback OIDC: {str(ex)}")


@router.post("/oidc/token", response_model=TokenResponseDTO)
def exchange_oidc_id_token(
    payload: OIDCTokenExchangeRequest,
    db: Session = Depends(get_db)
):
    """
    Intercambio directo de un ID Token OIDC emitido por el IdP por un JWT de sesión del Agente IA.
    Utilizado por SPAs o aplicaciones móviles que manejan el flujo OIDC del lado del cliente.
    """
    try:
        claims = oidc_service.parse_id_token_unverified(payload.id_token)
        user = oidc_service.provision_user_from_claims(db, claims)
        jwt_token, expires_in = oidc_service.create_session_jwt(user)

        user_dto = UserDTO(
            id=user.id,
            name=user.name,
            last_name=user.last_name,
            email=user.email,
            role_name=user.role.name if user.role else "Academico",
            sub=user.sub,
            orcid=user.orcid,
            dspace_person_id=user.dspace_person_id,
            is_active=user.is_active,
            last_login=user.last_login
        )

        return TokenResponseDTO(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_dto
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token OIDC inválido: {str(ex)}")


# -----------------------------------------------------------------------------
# 2. AUTENTICACIÓN SIMULADA PARA DESARROLLO Y TESTING (SANDBOX OIDC)
# -----------------------------------------------------------------------------

@router.post("/mock-login", response_model=TokenResponseDTO)
def mock_login(
    payload: MockLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticación institucional simulada (Sandbox USACH SSO).
    Permite generar tokens JWT válidos para testing y desarrollo local sin requerir
    un IdP OIDC activo en red, asignando el rol especificado ('Curador_VRIIC', 'Academico', 'Admin').
    """
    simulated_claims = {
        "sub": f"usach-sso-{uuid.uuid5(uuid.NAMESPACE_DNS, payload.email)}",
        "email": payload.email,
        "name": payload.name,
        "family_name": payload.last_name,
        "role": payload.role_name,
        "orcid": payload.orcid,
        "dspace_person_id": payload.dspace_person_id
    }

    user = oidc_service.provision_user_from_claims(db, simulated_claims)
    jwt_token, expires_in = oidc_service.create_session_jwt(user)

    user_dto = UserDTO(
        id=user.id,
        name=user.name,
        last_name=user.last_name,
        email=user.email,
        role_name=user.role.name if user.role else "Academico",
        sub=user.sub,
        orcid=user.orcid,
        dspace_person_id=user.dspace_person_id,
        is_active=user.is_active,
        last_login=user.last_login
    )

    return TokenResponseDTO(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_dto
    )


# -----------------------------------------------------------------------------
# 3. PERFIL DE USUARIO Y VALIDACIÓN DE TOKEN (BEARER PROTECTED)
# -----------------------------------------------------------------------------

@router.get("/me", response_model=UserDTO)
def get_authenticated_profile(current_user: User = Depends(get_current_user)):
    """
    Retorna el perfil del usuario autenticado a partir del Bearer JWT Token.
    """
    return UserDTO(
        id=current_user.id,
        name=current_user.name,
        last_name=current_user.last_name,
        email=current_user.email,
        role_name=current_user.role.name if current_user.role else "Academico",
        sub=current_user.sub,
        orcid=current_user.orcid,
        dspace_person_id=current_user.dspace_person_id,
        is_active=current_user.is_active,
        last_login=current_user.last_login
    )


@router.post("/introspect", response_model=TokenIntrospectResponse)
def introspect_token(payload: TokenIntrospectRequest):
    """
    Punto de introspección de tokens para MS4 o Gateway API:
    Verifica si el Bearer token es válido y retorna su identidad, rol y tiempo de expiración.
    """
    try:
        claims = oidc_service.verify_session_jwt(payload.token)
        return TokenIntrospectResponse(
            active=True,
            user_id=claims.get("sub"),
            email=claims.get("email"),
            name=claims.get("name"),
            role=claims.get("role"),
            orcid=claims.get("orcid"),
            dspace_person_id=claims.get("dspace_person_id"),
            exp=claims.get("exp")
        )
    except Exception:
        return TokenIntrospectResponse(active=False)


@router.get("/verify-role")
def verify_role(
    user_id: uuid.UUID = Query(...),
    required_role: str = Query(...),
    db: Session = Depends(get_db)
):
    """Verifica si el usuario cuenta con el rol requerido (RBAC: Academico, Curador_VRIIC, Admin)."""
    allowed = audit_worker.verify_permission(db, user_id, required_role)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso denegado: El usuario no cuenta con el rol '{required_role}'."
        )
    return {"user_id": str(user_id), "role": required_role, "authorized": True}


@router.post("/users", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Registra manualmente un usuario en el sistema con su rol respectivo.
    """
    clean_email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario registrado con el correo '{clean_email}'."
        )

    role_record = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol '{payload.role_name}' inválido. Roles válidos: 'Admin', 'Curador_VRIIC', 'Academico'."
        )

    new_user = User(
        id_role=role_record.id,
        name=payload.name.strip(),
        last_name=payload.last_name.strip(),
        email=clean_email,
        sub=payload.sub or f"usach-sso-{clean_email}",
        orcid=payload.orcid,
        dspace_person_id=payload.dspace_person_id,
        is_active=payload.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserDTO(
        id=new_user.id,
        name=new_user.name,
        last_name=new_user.last_name,
        email=new_user.email,
        role_name=role_record.name,
        sub=new_user.sub,
        orcid=new_user.orcid,
        dspace_person_id=new_user.dspace_person_id,
        is_active=new_user.is_active,
        last_login=new_user.last_login
    )


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Lista todos los usuarios registrados y su rol asignado."""
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role.name if u.role else None,
            "sub": u.sub,
            "orcid": u.orcid,
            "dspace_person_id": u.dspace_person_id,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]
