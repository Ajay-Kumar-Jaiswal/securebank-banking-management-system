import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "SecureBank - Banking Management System"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="mysql+pymysql://username:password@localhost:3306/banking_db",
        description="Database connection URL configured via environment variables (.env).",
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="banking-super-secret-production-grade-jwt-key-2026-securebank",
        description="Secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Email / SMTP Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@securebank.com"
    SMTP_FROM_NAME: str = "SecureBank Management System"
    SMTP_TLS: bool = True
    EMAILS_ENABLED: bool = False

    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("EMAILS_ENABLED", mode="before")
    @classmethod
    def assemble_emails_enabled(cls, v, info):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        if v is True:
            return True
        # Automatically enable if SMTP_HOST is configured
        values = info.data if hasattr(info, "data") else {}
        smtp_host = values.get("SMTP_HOST") or os.getenv("SMTP_HOST", "")
        return bool(smtp_host and str(smtp_host).strip())

    @field_validator("SMTP_FROM_EMAIL", mode="before")
    @classmethod
    def assemble_from_email(cls, v, info):
        if v and str(v).strip():
            return str(v).strip()
        values = info.data if hasattr(info, "data") else {}
        username = values.get("SMTP_USERNAME") or os.getenv("SMTP_USERNAME", "")
        if username and "@" in str(username):
            return str(username).strip()
        return "no-reply@securebank.com"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
