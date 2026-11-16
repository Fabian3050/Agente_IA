import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
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


# -----------------------------------------------------------------------------
# PORTAL INTERACTIVO SSO INSTITUCIONAL USACH (OIDC / OAUTH 2.0)
# -----------------------------------------------------------------------------

@router.get("/sso/login", response_class=HTMLResponse)
def sso_login_page(
    redirect_uri: str = Query("http://localhost:5173/", description="URI de redirección"),
    state: Optional[str] = Query(None, description="Estado de seguridad anti-CSRF"),
    client_id: Optional[str] = Query("agente-ia-dspace-cris", description="ID de cliente OAuth"),
    scope: Optional[str] = Query("openid profile email", description="Scopes solicitados")
):
    """
    Renderiza la interfaz web institucional del Servicio de Autenticación Centralizada (SSO USACH).
    Permite al usuario ingresar sus credenciales institucionales, seleccionar su rol en el sistema
    y autorizar el acceso del Agente IA (DSpace-CRIS) bajo el estándar OpenID Connect.
    """
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>USACH SSO · Servicio Central de Autenticación Unificada</title>
  <style>
    :root {{
      --usach-navy: #1a2332;
      --usach-teal: #00aea7;
      --usach-teal-dark: #008f89;
      --usach-orange: #ea7600;
      --usach-bg: #f8fafc;
      --usach-card: #ffffff;
      --usach-border: #e2e8f0;
      --usach-text: #1e293b;
      --usach-muted: #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
    body {{
      background: linear-gradient(135deg, #0d1522 0%, #1a2332 60%, #00363a 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      color: var(--usach-text);
    }}
    .sso-card {{
      background: var(--usach-card);
      width: 100%;
      max-width: 480px;
      border-radius: 18px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45);
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .sso-header {{
      background: var(--usach-navy);
      padding: 28px 24px;
      text-align: center;
      color: white;
      border-bottom: 4px solid var(--usach-teal);
      position: relative;
    }}
    .badge-env {{
      display: inline-block;
      background: rgba(0, 174, 167, 0.2);
      color: #5eead4;
      border: 1px solid rgba(0, 174, 167, 0.4);
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 20px;
      margin-bottom: 12px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}
    .sso-title {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 4px;
    }}
    .sso-subtitle {{
      font-size: 12px;
      color: #94a3b8;
      font-weight: 500;
    }}
    .sso-body {{
      padding: 24px;
    }}
    .consent-banner {{
      background: #f0fdfa;
      border: 1px solid #99f6e4;
      border-radius: 10px;
      padding: 12px 14px;
      margin-bottom: 20px;
      font-size: 12px;
      color: #115e59;
      line-height: 1.4;
    }}
    .consent-banner strong {{
      color: #042f2e;
    }}
    .scopes-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }}
    .scope-pill {{
      background: #ccfbf1;
      color: #0f766e;
      font-size: 10px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 6px;
    }}
    .quick-title {{
      font-size: 12px;
      font-weight: 700;
      color: var(--usach-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }}
    .profiles-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 18px;
    }}
    .profile-btn {{
      background: #f8fafc;
      border: 1px solid var(--usach-border);
      border-radius: 10px;
      padding: 10px 6px;
      font-size: 11px;
      cursor: pointer;
      text-align: center;
      transition: all 0.2s;
    }}
    .profile-btn:hover {{
      background: #f1f5f9;
      border-color: var(--usach-teal);
      transform: translateY(-2px);
    }}
    .profile-btn strong {{
      display: block;
      color: var(--usach-navy);
      font-size: 11px;
      margin-top: 3px;
    }}
    .profile-btn span {{
      display: block;
      font-size: 10px;
      color: var(--usach-muted);
    }}
    .form-group {{
      margin-bottom: 14px;
    }}
    .form-label {{
      display: block;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 5px;
      color: var(--usach-text);
    }}
    .form-input, .form-select {{
      width: 100%;
      padding: 10px 12px;
      font-size: 13px;
      border: 1px solid var(--usach-border);
      border-radius: 8px;
      background: #f8fafc;
      color: var(--usach-text);
      transition: border-color 0.2s;
    }}
    .form-input:focus, .form-select:focus {{
      outline: none;
      border-color: var(--usach-teal);
      background: white;
      box-shadow: 0 0 0 3px rgba(0, 174, 167, 0.15);
    }}
    .form-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .btn-submit {{
      width: 100%;
      padding: 12px;
      background: var(--usach-teal);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
      margin-top: 6px;
      box-shadow: 0 4px 12px rgba(0, 174, 167, 0.3);
    }}
    .btn-submit:hover {{
      background: var(--usach-teal-dark);
    }}
    .btn-submit:active {{
      transform: scale(0.99);
    }}
    .btn-cancel {{
      display: block;
      width: 100%;
      padding: 10px;
      background: transparent;
      color: var(--usach-muted);
      border: 1px solid var(--usach-border);
      border-radius: 10px;
      font-size: 12px;
      font-weight: 600;
      text-align: center;
      text-decoration: none;
      margin-top: 10px;
      cursor: pointer;
      transition: background 0.2s;
    }}
    .btn-cancel:hover {{
      background: #f1f5f9;
      color: var(--usach-text);
    }}
    .sso-footer {{
      padding: 14px 24px;
      background: #f8fafc;
      border-top: 1px solid var(--usach-border);
      text-align: center;
      font-size: 11px;
      color: var(--usach-muted);
    }}
  </style>
</head>
<body>
  <div class="sso-card">
    <div class="sso-header">
      <div class="badge-env">USACH SSO · OpenID Connect 1.0</div>
      <h1 class="sso-title">Identidad Institucional</h1>
      <p class="sso-subtitle">Universidad de Santiago de Chile · VRIIC</p>
    </div>

    <div class="sso-body">
      <div class="consent-banner">
        <strong>Conexión Institucional Solicitada</strong><br>
        La aplicación <strong>Agente IA (DSpace-CRIS)</strong> solicita verificar su identidad y obtener los siguientes permisos institucionales:
        <div class="scopes-list">
          <span class="scope-pill">✓ openid (identidad)</span>
          <span class="scope-pill">✓ profile (nombre)</span>
          <span class="scope-pill">✓ email (correo @usach.cl)</span>
          <span class="scope-pill">✓ role (RBAC VRIIC)</span>
          <span class="scope-pill">✓ orcid</span>
        </div>
      </div>

      <div class="quick-title">Selección Rápida de Identidad</div>
      <div class="profiles-grid">
        <button type="button" class="profile-btn" onclick="selectUser('curador.vriic@usach.cl', 'Fabián', 'Escobedo', 'Curador_VRIIC', '0000-0002-1825-0097')">
          🏛️
          <strong>Curador VRIIC</strong>
          <span>Fabián Escobedo</span>
        </button>
        <button type="button" class="profile-btn" onclick="selectUser('investigador@usach.cl', 'Juan', 'Pérez', 'Academico', '0000-0001-9876-5432')">
          📋
          <strong>Académico</strong>
          <span>Dr. Juan Pérez</span>
        </button>
        <button type="button" class="profile-btn" onclick="selectUser('admin.dspace@usach.cl', 'María', 'González', 'Admin', '0000-0003-4567-8901')">
          ⚙️
          <strong>Administrador</strong>
          <span>Dra. María González</span>
        </button>
      </div>

      <form method="GET" action="/auth/sso/authorize" id="ssoForm">
        <input type="hidden" name="redirect_uri" value="{redirect_uri}">
        <input type="hidden" name="state" value="{state or ''}">

        <div class="form-group">
          <label class="form-label">Correo Electrónico Institucional</label>
          <input type="email" id="email" name="email" class="form-input" value="curador.vriic@usach.cl" required>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Nombre</label>
            <input type="text" id="name" name="name" class="form-input" value="Fabián" required>
          </div>
          <div class="form-group">
            <label class="form-label">Apellido</label>
            <input type="text" id="last_name" name="last_name" class="form-input" value="Escobedo" required>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Rol en el Sistema (RBAC)</label>
          <select id="role" name="role" class="form-select">
            <option value="Curador_VRIIC" selected>Curador VRIIC (Revisión y Aprobación)</option>
            <option value="Academico">Académico / Investigador (Lectura y Consultas)</option>
            <option value="Admin">Administrador DSpace-CRIS (Control Total)</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Identificador ORCID</label>
          <input type="text" id="orcid" name="orcid" class="form-input" value="0000-0002-1825-0097">
        </div>

        <div class="form-group">
          <label class="form-label">Contraseña Institucional</label>
          <input type="password" class="form-input" value="••••••••••••" placeholder="Contraseña institucional">
        </div>

        <button type="submit" class="btn-submit">
          Iniciar Sesión y Autorizar Acceso al Sistema
        </button>

        <a href="{redirect_uri}{'&' if '?' in redirect_uri else '?'}error=access_denied" class="btn-cancel">
          Cancelar y Regresar al Sistema
        </a>
      </form>
    </div>

    <div class="sso-footer">
      Seguridad Institucional · Vicerrectoría de Investigación, Innovación y Creación · USACH
    </div>
  </div>

  <script>
    function selectUser(email, name, lastName, role, orcid) {{
      document.getElementById('email').value = email;
      document.getElementById('name').value = name;
      document.getElementById('last_name').value = lastName;
      document.getElementById('role').value = role;
      document.getElementById('orcid').value = orcid;
      // Auto-submit para flujo fluido con 1 clic
      document.getElementById('ssoForm').submit();
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@router.get("/sso/authorize")
def sso_authorize(
    redirect_uri: str = Query("http://localhost:5173/", description="URI de redirección post-login"),
    state: Optional[str] = Query(None, description="Estado de seguridad anti-CSRF"),
    email: str = Query("curador.vriic@usach.cl", description="Correo del usuario autenticado en SSO"),
    name: str = Query("Fabián", description="Nombre"),
    last_name: str = Query("Escobedo", description="Apellido"),
    role: str = Query("Curador_VRIIC", description="Rol institucional"),
    orcid: Optional[str] = Query(None, description="ORCID del investigador")
):
    """
    Endpoint de autorización del portal interactivo SSO de USACH.
    Emite un código de autorización temporal, registra la identidad autorizada en memoria
    y ejecuta la redirección HTTP 303 hacia el redirect_uri configurado por el frontend con ?code=...&state=...
    """
    auth_code = f"usach_code_{uuid.uuid4().hex}"
    oidc_service.register_auth_code(auth_code, {
        "email": email,
        "name": name,
        "last_name": last_name,
        "role": role,
        "orcid": orcid or "0000-0002-1825-0097",
    })

    sep = "&" if "?" in redirect_uri else "?"
    target_url = f"{redirect_uri}{sep}code={auth_code}"
    if state:
        target_url += f"&state={state}"

    return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)


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


@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: uuid.UUID,
    is_active: bool = Query(..., description="Estado de activación del usuario"),
    db: Session = Depends(get_db)
):
    """Activa o revoca el acceso de un usuario en el sistema."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "status": "Activo" if user.is_active else "Revocado"
    }
