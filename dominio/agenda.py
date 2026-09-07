"""Reglas para crear turnos."""

from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dominio.errores import DuracionInvalida, FechaPasada, HorarioInvalido, TurnoNoDisponible
from dominio.modelos import Turno

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")
HORA_APERTURA = 9
HORA_CIERRE = 18
DURACION_TURNO_MINUTOS = 30


def turnos_solapados(
    un_inicio: datetime,
    un_fin: datetime,
    otro_inicio: datetime,
    otro_fin: datetime,
) -> bool:
    """Indica si dos intervalos semiabiertos comparten algun instante."""
    return un_inicio < otro_fin and otro_inicio < un_fin


def hay_disponibilidad(
    turnos_existentes: list[Turno],
    profesional_id: int,
    inicio: datetime,
    duracion_min: int,
) -> bool:
    """Indica si un profesional puede atender el rango solicitado."""
    if duracion_min <= 0:
        raise DuracionInvalida("La duracion del turno debe ser mayor que cero.")

    fin = inicio + timedelta(minutes=duracion_min)
    cierre = inicio.replace(hour=HORA_CIERRE, minute=0, second=0, microsecond=0)
    if inicio.weekday() >= 5 or inicio.hour < HORA_APERTURA or fin > cierre:
        return False

    return not any(
        turno.profesional_id == profesional_id
        and turno.estado != "cancelado"
        and turnos_solapados(inicio, fin, turno.inicio, turno.fin)
        for turno in turnos_existentes
    )


def validar_inicio(inicio: datetime, ahora: datetime) -> None:
    """Verifica que el inicio pueda reservarse segun las reglas del negocio."""
    if inicio.tzinfo != ZONA_HORARIA or ahora.tzinfo != ZONA_HORARIA:
        raise HorarioInvalido("Las fechas deben usar America/Argentina/Buenos_Aires.")
    if inicio <= ahora:
        raise FechaPasada("No se pueden reservar turnos en el pasado.")
    if inicio.weekday() >= 5:
        raise HorarioInvalido("Atendemos de lunes a viernes.")
    if inicio.minute not in (0, 30) or inicio.second != 0 or inicio.microsecond != 0:
        raise HorarioInvalido("Los turnos comienzan cada 30 minutos.")
    cierre = inicio.replace(hour=HORA_CIERRE, minute=0, second=0, microsecond=0)
    if inicio.hour < HORA_APERTURA or inicio + timedelta(minutes=DURACION_TURNO_MINUTOS) > cierre:
        raise HorarioInvalido("El horario de atencion es de 09:00 a 18:00.")


def reservar_turno(
    cliente_id: int,
    cliente_nombre: str,
    inicio: datetime,
    ahora: datetime,
    existe_turno: Callable[[datetime], bool],
) -> Turno:
    """Crea un turno validado cuando el horario esta libre."""
    validar_inicio(inicio, ahora)
    if existe_turno(inicio):
        raise TurnoNoDisponible("Ese horario ya fue reservado.")
    return Turno(
        id=None,
        cliente_id=cliente_id,
        profesional_id=1,
        servicio_id=1,
        inicio=inicio,
        fin=inicio + timedelta(minutes=DURACION_TURNO_MINUTOS),
        estado="reservado",
    )