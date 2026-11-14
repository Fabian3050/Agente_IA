import os
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    # Parámetros OIDC / OAuth 2.0 Institucional (USACH SSO)
    OIDC_ISSUER_URL: str = os.getenv("OIDC_ISSUER_URL", "https://sso.usach.cl/auth/realms/usach")
    OIDC_CLIENT_ID: str = os.getenv("OIDC_CLIENT_ID", "agente-ia-dspace-cris")
    OIDC_CLIENT_SECRET: str = os.getenv("OIDC_CLIENT_SECRET", "usach-oidc-secret-token")
    OIDC_REDIRECT_URI: str = os.getenv("OIDC_REDIRECT_URI", "http://localhost:8003/auth/callback")
    OIDC_SCOPES: str = os.getenv("OIDC_SCOPES", "openid profile email")

    # Tokens JWT de sesión interna
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "agente-ia-vriic-usach-jwt-secret-key-2026-v3")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # Modo Mock/Sandbox para pruebas y desarrollo desacoplado
    MOCK_OIDC_ENABLED: bool = os.getenv("MOCK_OIDC_ENABLED", "true").lower() in ("true", "1", "yes")

    class Config:
        env_file = ".env"
        extra = "allow"


auth_config = AuthConfig()

