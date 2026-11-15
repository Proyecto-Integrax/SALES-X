from datetime import date, datetime, timezone

from app.timeutil import day_end, day_start, to_local


def test_rango_diario_en_zona_de_negocio_colombia():
    # 13/nov 23:48 hora Colombia = 14/nov 04:48 UTC: debe caer DENTRO del día 13 (regresión de reporte vacío).
    pedido_utc = datetime(2026, 11, 14, 4, 48, tzinfo=timezone.utc)
    assert day_start(date(2026, 11, 13)) <= pedido_utc <= day_end(date(2026, 11, 13))
    assert not (day_start(date(2026, 11, 14)) <= pedido_utc)


def test_to_local_acepta_fecha_sin_zona_de_sqlite():
    assert to_local(datetime(2026, 11, 14, 4, 48)).strftime("%Y-%m-%d %H:%M") == "2026-11-13 23:48"
