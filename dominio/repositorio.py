"""Contrato de persistencia requerido por el dominio."""

from datetime import datetime
from typing import Protocol

from dominio.modelos import Turno


class RepositorioDeTurnos(Protocol):
    """Operaciones de almacenamiento que necesita el servicio."""

    def existe_en_horario(self, inicio: datetime) -> bool: ...

    def guardar(self, turno: Turno) -> Turno: ...

    def listar_por_cliente(self, cliente_id: int, desde: datetime) -> list[Turno]: ...

    def obtener(self, turno_id: int) -> Turno | None: ...

    def eliminar(self, turno_id: int) -> None: ...