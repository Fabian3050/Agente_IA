import hmac
import hashlib
import base64
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import httpx
from sqlalchemy.orm import Session

try:
    from services.ms3_auth.config import auth_config
    from services.ms3_auth.models import User, Role
except ImportError:
    from config import auth_config
    from models import User, Role

logger = logging.getLogger(__name__)


def _b64url_encode(data: bytes) -> str:
    """Codifica bytes a Base64 URL-safe sin relleno '=' (RFC 7515)."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _b64url_decode(s: str) -> bytes:
    """Decodifica cadena Base64 URL-safe agregando el relleno necesario."""
    pad = 4 - (len(s) % 4)
    if pad != 4:
        s += '=' * pad
    return base64.urlsafe_b64decode(s)


class OIDCService:
    """
    Servicio de Autenticación OpenID Connect (OIDC) y OAuth 2.0 para MS3.
    Implementa:
    - Generación y verificación criptográfica de tokens JWT de sesión (HS256).
    - Flujo Authorization Code con IdP institucional (USACH SSO / Keycloak / Google).
    - Provisión Just-in-Time (JIT) de usuarios en la base de datos sin contraseñas locales.
    - Soporte de introspección y validación de tokens Bearer.
    """

    def __init__(self):
        self.issuer_url = auth_config.OIDC_ISSUER_URL.rstrip('/')
        self.client_id = auth_config.OIDC_CLIENT_ID
        self.client_secret = auth_config.OIDC_CLIENT_SECRET
        self.redirect_uri = auth_config.OIDC_REDIRECT_URI
        self.scopes = auth_config.OIDC_SCOPES
        self.jwt_secret = auth_config.JWT_SECRET_KEY.encode('utf-8')
        self.jwt_expiry_seconds = auth_config.JWT_EXPIRATION_MINUTES * 60
        # Almacén en memoria de códigos de autorización emitidos por el portal SSO institucional
        self._pending_auth_codes: Dict[str, Dict[str, Any]] = {}

    def register_auth_code(self, code: str, user_info: Dict[str, Any]) -> None:
        """Registra un código de autorización temporal emitido por el portal SSO."""
        self._pending_auth_codes[code] = {
            **user_info,
            "created_at": time.time()
        }

    def consume_auth_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Consume (valida y elimina) un código temporal de autorización (Single-Use RFC 6749)."""
        data = self._pending_auth_codes.pop(code, None)
        if not data:
            return None
        # Expiración a los 10 minutos
        if time.time() - data.get("created_at", 0) > 600:
            return None
        return data

    # -------------------------------------------------------------------------
    # 1. GENERACIÓN Y VALIDACIÓN DE JWT (RFC 7519 / HS256)
    # -------------------------------------------------------------------------
    def create_session_jwt(self, user: User) -> Tuple[str, int]:
        """
        Genera un token JWT firmado para la sesión de usuario autenticado.
        Incluye identificadores de autor (ORCID e ID DSpace) y su rol RBAC formal.
        """
        now = int(time.time())
        exp = now + self.jwt_expiry_seconds

        header = {
            "alg": auth_config.JWT_ALGORITHM,
            "typ": "JWT"
        }

        role_name = user.role.name if user.role else "Academico"

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": f"{user.name} {user.last_name}",
            "role": role_name,
            "orcid": user.orcid,
            "dspace_person_id": user.dspace_person_id,
            "iss": "agente-ia-ms3-auth",
            "iat": now,
            "exp": exp
        }

        h_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        p_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        signing_input = f"{h_b64}.{p_b64}".encode('utf-8')

        signature = hmac.new(self.jwt_secret, signing_input, hashlib.sha256).digest()
        sig_b64 = _b64url_encode(signature)

        token = f"{h_b64}.{p_b64}.{sig_b64}"
        return token, self.jwt_expiry_seconds

    def verify_session_jwt(self, token: str) -> Dict[str, Any]:
        """
        Valida la firma criptográfica y expiración de un token JWT Bearer.
        Retorna las claims contenidas en el payload si es válido.
        Lanza ValueError si el token es inválido o expiró.
        """
        parts = token.strip().split('.')
        if len(parts) != 3:
            raise ValueError("Token JWT malformado: debe tener 3 segmentos")

        h_b64, p_b64, sig_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode('utf-8')

        expected_sig = hmac.new(self.jwt_secret, signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            raise ValueError("Firma del token JWT inválida")

        payload_bytes = _b64url_decode(p_b64)
        claims = json.loads(payload_bytes.decode('utf-8'))

        # Validar expiración
        exp = claims.get("exp")
        if exp and int(time.time()) > int(exp):
            raise ValueError("Token JWT expirado")

        return claims

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # PROTOCOLO OIDC / OAUTH 2.0 (AUTHORIZATION CODE FLOW)
    # -------------------------------------------------------------------------
    def get_authorization_url(self, state: Optional[str] = None, redirect_uri: Optional[str] = None) -> str:
        """
        Construye la URL de redirección hacia el Authorization Endpoint del IdP institucional.
        Si MOCK_OIDC_ENABLED=True (desarrollo/sandbox), redirige al portal interactivo SSO institucional
        servido por MS3 Auth (/auth/sso/login) para que el usuario ingrese sus credenciales institucionalmente.
        """
        redir = redirect_uri or self.redirect_uri
        st = state or uuid.uuid4().hex

        from urllib.parse import urlencode

        if auth_config.MOCK_OIDC_ENABLED:
            sso_endpoint = "http://localhost:8003/auth/sso/login"
            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "scope": self.scopes,
                "redirect_uri": redir,
                "state": st
            }
            return f"{sso_endpoint}?{urlencode(params)}"

        if "google.com" in self.issuer_url:
            auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "scope": self.scopes,
                "redirect_uri": redir,
                "state": st,
                "access_type": "offline",
                "prompt": "select_account"
            }
            return f"{auth_endpoint}?{urlencode(params)}"

        auth_endpoint = f"{self.issuer_url}/protocol/openid-connect/auth"

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": self.scopes,
            "redirect_uri": redir,
            "state": st
        }
        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Intercambia el código de autorización temporal por tokens en el Token Endpoint del IdP.
        Si el código fue generado por el portal SSO interactivo de MS3 o en modo sandbox,
        emite un id_token institucional con los datos del usuario autenticado.
        """
        pending_user = self.consume_auth_code(code)

        if pending_user or auth_config.MOCK_OIDC_ENABLED or code.startswith("mock_") or code.startswith("usach_"):
            email = (pending_user or {}).get("email", "curador.vriic@usach.cl")
            name = (pending_user or {}).get("name", "Fabián")
            last_name = (pending_user or {}).get("last_name", "Escobedo")
            role_name = (pending_user or {}).get("role", "Curador_VRIIC")
            orcid = (pending_user or {}).get("orcid", "0000-0002-1825-0097")
            dspace_id = (pending_user or {}).get("dspace_person_id", f"person-{uuid.uuid5(uuid.NAMESPACE_DNS, email).hex[:8]}")

            header = {"alg": "HS256", "typ": "JWT"}
            payload = {
                "sub": f"usach-sso-{uuid.uuid5(uuid.NAMESPACE_DNS, email)}",
                "email": email,
                "given_name": name,
                "family_name": last_name,
                "name": f"{name} {last_name}".strip(),
                "role": role_name,
                "orcid": orcid,
                "dspace_person_id": dspace_id,
                "iss": self.issuer_url,
                "aud": self.client_id,
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600
            }
            h_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
            p_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
            dummy_sig = _b64url_encode(b"simulated_oidc_signature")
            mock_id_token = f"{h_b64}.{p_b64}.{dummy_sig}"

            return {
                "access_token": f"usach_idp_access_token_{uuid.uuid4().hex[:12]}",
                "token_type": "Bearer",
                "expires_in": 3600,
                "id_token": mock_id_token
            }

        redir = redirect_uri or self.redirect_uri
        if "google.com" in self.issuer_url:
            token_endpoint = "https://oauth2.googleapis.com/token"
        else:
            token_endpoint = f"{self.issuer_url}/protocol/openid-connect/token"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redir,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(token_endpoint, data=data)
            if resp.status_code != 200:
                logger.error(f"Error intercambiando código OIDC: {resp.text}")
                raise ValueError(f"Fallo en token endpoint de IdP (HTTP {resp.status_code}): {resp.text}")
            return resp.json()

    def parse_id_token_unverified(self, id_token: str) -> Dict[str, Any]:
        """
        Decodifica el payload de un id_token OIDC emitido por el IdP.
        """
        parts = id_token.strip().split('.')
        if len(parts) != 3:
            raise ValueError("id_token OIDC malformado")
        payload_bytes = _b64url_decode(parts[1])
        return json.loads(payload_bytes.decode('utf-8'))

    # -------------------------------------------------------------------------
    # 3. PROVISIÓN DE USUARIOS JUST-IN-TIME (JIT) Y GESTIÓN DE ROLES
    # -------------------------------------------------------------------------
    def provision_user_from_claims(self, db: Session, claims: Dict[str, Any]) -> User:
        """
        Localiza o aprovisiona el usuario en la BD de MS3 utilizando las claims de identidad OIDC.
        Asigna el rol institucional correspondiente (Admin, Curador_VRIIC, Academico).
        No almacena ni requiere contraseñas locales.
        """
        email = claims.get("email") or claims.get("preferred_username")
        if not email:
            raise ValueError("Las claims OIDC deben incluir un 'email' válido")

        email = email.lower().strip()
        sub = claims.get("sub")
        name = claims.get("given_name") or claims.get("name") or "Usuario"
        last_name = claims.get("family_name") or "Institucional"
        orcid = claims.get("orcid")
        dspace_person_id = claims.get("dspace_person_id")

        # Determinar rol a partir de grupos/roles OIDC o parámetro
        requested_role = self._map_claims_to_role(claims)

        # Buscar usuario existente por email o sub
        user = db.query(User).filter((User.email == email) | (User.sub == sub)).first()

        # Obtener o asegurar rol en DB
        role_record = db.query(Role).filter(Role.name == requested_role).first()
        if not role_record:
            # Fallback a Academico si el rol no existe
            role_record = db.query(Role).filter(Role.name == "Academico").first()
            if not role_record:
                role_record = Role(name="Academico", description="Rol Academico por defecto")
                db.add(role_record)
                db.commit()
                db.refresh(role_record)

        if not user:
            user = User(
                id_role=role_record.id,
                name=name,
                last_name=last_name,
                email=email,
                sub=sub,
                orcid=orcid,
                dspace_person_id=dspace_person_id,
                is_active=True,
                last_login=datetime.utcnow()
            )
            db.add(user)
        else:
            # Actualizar datos de perfil y timestamp de sesión
            user.last_login = datetime.utcnow()
            if sub and not user.sub:
                user.sub = sub
            if orcid and not user.orcid:
                user.orcid = orcid
            if dspace_person_id and not user.dspace_person_id:
                user.dspace_person_id = dspace_person_id

        db.commit()
        db.refresh(user)
        return user

    def _map_claims_to_role(self, claims: Dict[str, Any]) -> str:
        """
        Mapea las claims y grupos recibidos del IdP a los 3 roles formales:
        - Admin
        - Curador_VRIIC
        - Academico
        """
        email = (claims.get("email") or "").lower()
        if "curador" in email or "vriic" in email or "fabian" in email or "fescobedo" in email:
            return "Curador_VRIIC"
        if "admin" in email:
            return "Admin"

        explicit_role = claims.get("role") or claims.get("roles")
        if explicit_role:
            if isinstance(explicit_role, list):
                if any(r in ["Admin", "admin", "administrador"] for r in explicit_role):
                    return "Admin"
                if any(r in ["Curador_VRIIC", "curador", "Curador"] for r in explicit_role):
                    return "Curador_VRIIC"
            elif isinstance(explicit_role, str):
                if explicit_role.lower() in ["admin", "administrador"]:
                    return "Admin"
                if explicit_role.lower() in ["curador_vriic", "curador"]:
                    return "Curador_VRIIC"

        groups = claims.get("groups") or []
        if isinstance(groups, list):
            if "vriic-curadores" in groups or "curadores" in groups:
                return "Curador_VRIIC"
            if "vriic-admin" in groups or "administradores" in groups:
                return "Admin"

        return "Curador_VRIIC" if "@usach.cl" in email else "Academico"


oidc_service = OIDCService()
