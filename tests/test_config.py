from app.config import Settings, validate_for_production


def test_produccion_rechaza_configuracion_insegura():
    s = Settings(
        environment="production",
        secret_key="cambiar-esta-clave-en-produccion",
        integration_api_key="cambiar-api-key-integracion",
        admin_password="Admin2026*",
        database_url="sqlite:///x.db",
        seed_demo_users=True,
    )
    problemas = validate_for_production(s)
    assert len(problemas) == 5  # clave, api key, password admin, sqlite, usuarios demo


def test_produccion_acepta_configuracion_robusta():
    s = Settings(
        environment="production",
        secret_key="x" * 48,
        integration_api_key="k" * 24,
        admin_password="UnaClaveLarga#2026",
        database_url="postgresql+psycopg2://u:p@db:5432/salesx",
        seed_demo_users=False,
    )
    assert validate_for_production(s) == []
