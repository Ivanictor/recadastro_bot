from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: SecretStr
    phone_number: str
    whatsapp_service_url: str = "http://127.0.0.1:3000"
    port: str
    email: str
    senha_app: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instância global de configurações
settings = Settings()