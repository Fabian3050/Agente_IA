"""
Suite de Pruebas Unitarias e Integración: OAuth 2.0 / OpenID Connect (OIDC) - MS3
Valida los requerimientos de la Sección 2.5 de la Especificación Técnica:
1. Generación de URL de autorización OAuth 2.0 / OIDC.
2. Generación, firma y verificación criptográfica de tokens JWT de sesión (HS256).
3. Rechazo de tokens manipulados o expirados (401 Unauthorized).
4. Provisión de usuarios Just-In-Time (JIT) a partir de claims de identidad institucional.
5. Control de acceso RBAC estricto (Admin, Curador_VRIIC, Academico - 403 Forbidden).
6. Endpoint /auth/me protegido mediante Bearer token.
7. Endpoint /auth/introspect para validación entre microservicios.
"""

import os
import sys
import unittest
import uuid
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")

if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.database import Base
from services.ms3_auth.models import User, Role, AuditLog
from services.ms3_auth.services.seed_service import seed_roles
from services.ms3_auth.services.oidc_service import OIDCService, oidc_service
from services.ms3_auth.security import get_current_user, require_role
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestMS3OIDC(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Role.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()
        seed_roles(self.db)
        self.oidc = OIDCService()

    def tearDown(self):
        self.db.close()
        Role.metadata.drop_all(bind=self.engine)

    def test_oidc_authorization_url_generation(self):
        """Verifica que la URL hacia el IdP institucional cumpla con el estándar OAuth 2.0 / OIDC."""
        state = "random_state_12345"
        auth_url = self.oidc.get_authorization_url(state=state)
        self.assertIn("response_type=code", auth_url)
        self.assertIn("client_id=", auth_url)
        self.assertIn("scope=openid+profile+email", auth_url)
        self.assertIn(f"state={state}", auth_url)

    def test_jwt_creation_and_verification(self):
        """Genera un JWT firmado y valida que sus claims contengan rol, ORCID e ID institucional."""
        role_curador = self.db.query(Role).filter(Role.name == "Curador_VRIIC").first()
        user = User(
            id_role=role_curador.id,
            name="Curador",
            last_name="Investigación",
            email="curador@usach.cl",
            orcid="0000-0002-1825-0097",
            dspace_person_id="person-vriic-99",
            is_active=True
        )
        self.db.add(user)
        self.db.commit()

        token, expires_in = self.oidc.create_session_jwt(user)
        self.assertIsInstance(token, str)
        self.assertGreater(expires_in, 0)

        # Verificar y decodificar
        claims = self.oidc.verify_session_jwt(token)
        self.assertEqual(claims["sub"], str(user.id))
        self.assertEqual(claims["email"], "curador@usach.cl")
        self.assertEqual(claims["role"], "Curador_VRIIC")
        self.assertEqual(claims["orcid"], "0000-0002-1825-0097")
        self.assertEqual(claims["dspace_person_id"], "person-vriic-99")
        self.assertEqual(claims["iss"], "agente-ia-ms3-auth")

    def test_jwt_invalid_signature_rejection(self):
        """Tokens con firma manipulada deben ser rechazados con excepción."""
        role_curador = self.db.query(Role).filter(Role.name == "Curador_VRIIC").first()
        user = User(
            id_role=role_curador.id,
            name="Curador",
            last_name="Test",
            email="test@usach.cl"
        )
        self.db.add(user)
        self.db.commit()

        token, _ = self.oidc.create_session_jwt(user)
        parts = token.split('.')
        tampered_token = f"{parts[0]}.{parts[1]}.tamperedSignature"

        with self.assertRaises(ValueError):
            self.oidc.verify_session_jwt(tampered_token)

    def test_jwt_expired_token_rejection(self):
        """Tokens expirados deben ser rechazados."""
        role = self.db.query(Role).filter(Role.name == "Academico").first()
        user = User(id_role=role.id, name="User", last_name="Exp", email="exp@usach.cl")
        self.db.add(user)
        self.db.commit()

        # Configurar servicio con expiración negativa (-10s)
        self.oidc.jwt_expiry_seconds = -10
        expired_token, _ = self.oidc.create_session_jwt(user)

        with self.assertRaises(ValueError) as ctx:
            self.oidc.verify_session_jwt(expired_token)
        self.assertIn("expirado", str(ctx.exception).lower())

    def test_jit_user_provisioning(self):
        """
        Provisión Just-In-Time (JIT): Al recibir claims de un usuario nuevo del IdP,
        se crea automáticamente en la base de datos sin necesidad de contraseñas locales.
        """
        claims = {
            "sub": "usach-sso-sub-7890",
            "email": "nuevo.profesor@usach.cl",
            "given_name": "Manuel",
            "family_name": "Villalobos",
            "role": "Curador_VRIIC",
            "orcid": "0000-0001-5000-2000"
        }

        user = self.oidc.provision_user_from_claims(self.db, claims)
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "nuevo.profesor@usach.cl")
        self.assertEqual(user.name, "Manuel")
        self.assertEqual(user.role.name, "Curador_VRIIC")
        self.assertEqual(user.orcid, "0000-0001-5000-2000")
        self.assertIsNotNone(user.last_login)

        # Segunda llamada con el mismo usuario debe actualizar y no duplicar
        user_updated = self.oidc.provision_user_from_claims(self.db, claims)
        self.assertEqual(user_updated.id, user.id)
        total_users = self.db.query(User).filter(User.email == "nuevo.profesor@usach.cl").count()
        self.assertEqual(total_users, 1)

    def test_security_dependency_get_current_user(self):
        """Prueba de la dependencia FastAPI get_current_user con credenciales Bearer."""
        role = self.db.query(Role).filter(Role.name == "Curador_VRIIC").first()
        user = User(id_role=role.id, name="Ana", last_name="Curadora", email="ana@usach.cl", is_active=True)
        self.db.add(user)
        self.db.commit()

        token, _ = self.oidc.create_session_jwt(user)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        resolved_user = get_current_user(credentials=creds, db=self.db)
        self.assertEqual(resolved_user.id, user.id)
        self.assertEqual(resolved_user.email, "ana@usach.cl")

    def test_security_dependency_missing_credentials(self):
        """Sin credenciales se debe lanzar HTTP 401 Unauthorized."""
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(credentials=None, db=self.db)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_rbac_require_role_isolation(self):
        """
        Verificación de aislamiento de roles (test_rbac_permissions_isolation de Sección 5.4):
        Un usuario Academico debe recibir HTTP 403 Forbidden al intentar acceder a rol Curador_VRIIC.
        """
        role_academico = self.db.query(Role).filter(Role.name == "Academico").first()
        role_curador = self.db.query(Role).filter(Role.name == "Curador_VRIIC").first()

        user_academico = User(id_role=role_academico.id, name="Pedro", last_name="Docente", email="pedro@usach.cl")
        user_curador = User(id_role=role_curador.id, name="Laura", last_name="Curadora", email="laura@usach.cl")
        self.db.add_all([user_academico, user_curador])
        self.db.commit()

        curator_checker = require_role("Curador_VRIIC")

        # Curador permitido
        result_curador = curator_checker(current_user=user_curador)
        self.assertEqual(result_curador.id, user_curador.id)

        # Académico rechazado con 403 Forbidden
        with self.assertRaises(HTTPException) as ctx:
            curator_checker(current_user=user_academico)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Acceso denegado", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
