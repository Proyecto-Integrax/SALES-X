from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"  # development | production
    database_url: str = "sqlite:///./sales_x.db"

    secret_key: str = "cambiar-esta-clave-en-produccion"
    token_expire_minutes: int = 480
    integration_api_key: str = "cambiar-api-key-integracion"

    iva_rate: float = 0.19
    business_tz: str = "America/Bogota"

    admin_email: str = "admin@salesx.local"
    admin_password: str = "Admin2026*"
    admin_name: str = "Administrador SALES-X"
    seed_demo_users: bool = True

    catalogo_provider: str = "simulado"  # simulado | rest
    clientes_api_url: str = "http://localhost:8001/api/clientes"
    productos_api_url: str = "http://localhost:8002/api/productos"
    integration_timeout_seconds: float = 5.0

    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


INSECURE_DEFAULTS = {"cambiar-esta-clave-en-produccion", "cambiar-api-key-integracion", "Admin2026*"}


def validate_for_production(s: Settings) -> list[str]:
    """Devuelve los problemas de configuración que impiden arrancar en producción."""
    problems = []
    if s.secret_key in INSECURE_DEFAULTS or len(s.secret_key) < 32:
        problems.append("SECRET_KEY debe tener al menos 32 caracteres y no ser el valor por defecto")
    if s.integration_api_key in INSECURE_DEFAULTS or len(s.integration_api_key) < 16:
        problems.append("INTEGRATION_API_KEY debe tener al menos 16 caracteres y no ser el valor por defecto")
    if s.admin_password in INSECURE_DEFAULTS or len(s.admin_password) < 10:
        problems.append("ADMIN_PASSWORD debe tener al menos 10 caracteres y no ser el valor por defecto")
    if s.database_url.startswith("sqlite"):
        problems.append("En producción debe usarse PostgreSQL (DATABASE_URL), no SQLite")
    if s.seed_demo_users:
        problems.append("SEED_DEMO_USERS debe ser false en producción")
    return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
