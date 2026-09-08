from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    dspace_api_url: str
    dspace_username: str
    dspace_password: str

    # En Pydantic v2, esta es la forma recomendada y segura de cargar el .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
