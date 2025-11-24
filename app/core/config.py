from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AppInfo(BaseModel):
    name: str = "smartpc-backend"
    version: str = "0.1.0"
    environment: str = "development"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # CORS / API
    cors_origin: str = "http://localhost:3000"

    # Security
    jwt_secret: str = "change_me_in_prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Database
    database_url: Optional[str] = None

    # Email/SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: EmailStr = "noreply@smartpc.pro-kom.eu"
    inquiry_email: EmailStr = "krystian.potaczek07@gmail.com"

    # reCAPTCHA
    recaptcha_secret_key: Optional[str] = None

    # App meta
    app: AppInfo = AppInfo()


settings = Settings()


