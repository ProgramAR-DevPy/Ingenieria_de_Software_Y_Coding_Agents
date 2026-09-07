from datetime import datetime, timedelta

import pytest

from dominio.agenda import ZONA_HORARIA, hay_disponibilidad
from dominio.errores import DuracionInvalida
from dominio.modelos import Turno


def _turno(
    *,
    profesional_id: int = 1,
    inicio: datetime | None = None,
    fin: datetime | None = None,
    estado: str = "reservado",
) -> Turno:
    if inicio is None:
        inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)
    if fin is None:
        fin = inicio + timedelta(minutes=30)

    return Turno(
        id=1,
        cliente_id=1,
        profesional_id=profesional_id,
        servicio_id=1,
        inicio=inicio,
        fin=fin,
        estado=estado,
    )


def test_hay_disponibilidad_cuando_el_turno_esta_dentro_del_horario_y_no_hay_solapamiento() -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is True


def test_no_hay_disponibilidad_si_comienza_antes_del_horario_de_apertura() -> None:
    inicio = datetime(2026, 8, 31, 8, 30, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is False


def test_no_hay_disponibilidad_si_termina_despues_del_horario_de_cierre() -> None:
    inicio = datetime(2026, 8, 31, 17, 45, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is False


@pytest.mark.parametrize(
    ("inicio_solicitado", "turnos_existentes"),
    [
        (
            datetime(2026, 8, 31, 9, 15, tzinfo=ZONA_HORARIA),
            [_turno(profesional_id=7, inicio=datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA))],
        ),
        (
            datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA),
            [_turno(profesional_id=7, inicio=datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA))],
        ),
        (
            datetime(2026, 8, 31, 9, 15, tzinfo=ZONA_HORARIA),
            [_turno(profesional_id=7, inicio=datetime(2026, 8, 31, 9, 15, tzinfo=ZONA_HORARIA))],
        ),
    ],
)
def test_no_hay_disponibilidad_si_se_solapa_con_el_mismo_profesional(
    inicio_solicitado: datetime,
    turnos_existentes: list[Turno],
) -> None:
    assert hay_disponibilidad(turnos_existentes, 7, inicio_solicitado, 30) is False


def test_hay_disponibilidad_si_existe_turno_en_el_mismo_horario_pero_de_otro_profesional() -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)
    turnos_existentes = [_turno(profesional_id=2, inicio=inicio, fin=inicio + timedelta(minutes=30))]

    assert hay_disponibilidad(turnos_existentes, 7, inicio, 30) is True


def test_hay_disponibilidad_si_el_turno_empieza_exactamente_cuando_termina_el_anterior_del_mismo_profesional() -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)
    turno_existente = _turno(profesional_id=5, inicio=inicio, fin=inicio + timedelta(minutes=30))

    assert hay_disponibilidad([turno_existente], 5, inicio + timedelta(minutes=30), 30) is True


def test_hay_disponibilidad_si_el_turno_termina_exactamente_cuando_comienza_el_siguiente_del_mismo_profesional() -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)
    turno_siguiente = _turno(
        profesional_id=5,
        inicio=inicio + timedelta(minutes=30),
        fin=inicio + timedelta(minutes=60),
    )

    assert hay_disponibilidad([turno_siguiente], 5, inicio, 30) is True


def test_hay_disponibilidad_cuando_dos_turnos_se_to_can_exactamente_en_el_minuto() -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)
    turno_existente = _turno(profesional_id=5, inicio=inicio, fin=inicio + timedelta(minutes=30))

    assert hay_disponibilidad([turno_existente], 5, inicio + timedelta(minutes=30), 30) is True


def test_no_hay_disponibilidad_si_un_turno_arranca_justo_en_el_horario_de_cierre() -> None:
    inicio = datetime(2026, 8, 31, 18, 0, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is False


def test_no_hay_disponibilidad_si_un_turno_cruza_el_cierre_por_5_minutos() -> None:
    inicio = datetime(2026, 8, 31, 17, 55, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is False


@pytest.mark.parametrize("duracion", [0, -15])
def test_hay_disponibilidad_rechaza_duracion_no_positiva(duracion: int) -> None:
    inicio = datetime(2026, 8, 31, 9, 0, tzinfo=ZONA_HORARIA)

    with pytest.raises(DuracionInvalida):
        hay_disponibilidad([], 1, inicio, duracion)


def test_no_hay_disponibilidad_si_el_turno_es_un_domingo() -> None:
    inicio = datetime(2026, 8, 30, 10, 0, tzinfo=ZONA_HORARIA)

    assert hay_disponibilidad([], 1, inicio, 30) is False
