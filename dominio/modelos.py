"""Modelos de negocio inmutables."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal


EstadoTurno = Literal["reservado", "cancelado"]


@dataclass(frozen=True)
class Turno:
    """Reserva de un cliente para un momento determinado."""

    id: int | None
    cliente_id: int
    profesional_id: int
    servicio_id: int
    inicio: datetime
    fin: datetime
    estado: EstadoTurno


@dataclass(frozen=True)
class Cliente:
    """Persona que reserva un turno."""

    id: int
    nombre: str
    telefono: str


@dataclass(frozen=True)
class Profesional:
    """Prestador de los servicios del negocio."""

    id: int
    nombre: str
    activo: bool


@dataclass(frozen=True)
class Servicio:
    """Servicio reservable y su duracion."""

    id: int
    nombre: str
    duracion: timedelta
    activo: bool


@dataclass(frozen=True)
class Feriado:
    """Fecha sin atencion."""

    fecha: date
    motivo: str


@dataclass(frozen=True)
class FranjaHoraria:
    """Horario de atencion de un dia de la semana."""

    dia_semana: int
    apertura: time
    cierre: time