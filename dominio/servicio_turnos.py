"""Casos de uso de reservas."""

from datetime import datetime

from dominio.agenda import reservar_turno
from dominio.errores import TurnoInexistente, TurnoNoAutorizado
from dominio.modelos import Turno
from dominio.repositorio import RepositorioDeTurnos


class ServicioDeTurnos:
    """Coordina las reglas de agenda con la persistencia."""

    def __init__(self, repositorio: RepositorioDeTurnos) -> None:
        self._repositorio = repositorio

    def reservar(
        self,
        cliente_id: int,
        cliente_nombre: str,
        inicio: datetime,
        ahora: datetime,
    ) -> Turno:
        turno = reservar_turno(
            cliente_id,
            cliente_nombre,
            inicio,
            ahora,
            self._repositorio.existe_en_horario,
        )
        return self._repositorio.guardar(turno)

    def listar_proximos(self, cliente_id: int, ahora: datetime) -> list[Turno]:
        return self._repositorio.listar_por_cliente(cliente_id, ahora)

    def cancelar(self, turno_id: int, cliente_id: int) -> None:
        turno = self._repositorio.obtener(turno_id)
        if turno is None:
            raise TurnoInexistente("No existe un turno con ese identificador.")
        if turno.cliente_id != cliente_id:
            raise TurnoNoAutorizado("No podes cancelar el turno de otro cliente.")
        self._repositorio.eliminar(turno_id)