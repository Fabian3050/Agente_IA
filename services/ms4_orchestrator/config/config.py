import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    dspace_api_url: str = ""
    dspace_username: str = ""
    dspace_password: str = ""

    # Soporte para .env en múltiples ubicaciones (raíz del proyecto, contenedor Docker /app, etc.)
    model_config = SettingsConfigDict(
        env_file=(".env", "/app/.env", "../.env", "../../.env"),
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        self._load_fallback_secrets()

    def _load_fallback_secrets(self):
        """
        Carga credenciales desde secretos Docker (/run/secrets/dspace_credentials)
        o archivos de secretos locales si no fueron inyectados por variables de entorno.
        """
        secret_paths = [
            Path("/run/secrets/dspace_credentials"),
            Path("secrets/dspace_credentials.txt"),
            Path("/app/secrets/dspace_credentials.txt"),
            Path("../secrets/dspace_credentials.txt"),
            Path("../../secrets/dspace_credentials.txt"),
        ]
        for p in secret_paths:
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#") or "=" not in line:
                                continue
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k == "DSPACE_API_URL" and not self.dspace_api_url:
                                self.dspace_api_url = v
                            elif k == "DSPACE_USERNAME" and not self.dspace_username:
                                self.dspace_username = v
                            elif k == "DSPACE_PASSWORD" and not self.dspace_password:
                                self.dspace_password = v
                except Exception:
                    pass

        # Valor por defecto institucional si aún no se configuró
        if not self.dspace_api_url:
            self.dspace_api_url = os.getenv("DSPACE_API_URL", "https://sic.usach.cl/server/api")
        if not self.dspace_username:
            self.dspace_username = os.getenv("DSPACE_USERNAME", "agente-ia@usach.cl")
        if not self.dspace_password:
            self.dspace_password = os.getenv("DSPACE_PASSWORD", "")


settings = Settings()
