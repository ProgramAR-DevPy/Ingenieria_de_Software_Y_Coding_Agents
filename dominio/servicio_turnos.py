"""Casos de uso de reservas."""

import logging
from datetime import datetime

from dominio.agenda import reservar_turno
from dominio.errores import ErrorDeNegocio, TurnoInexistente, TurnoNoAutorizado
from dominio.modelos import Turno
from dominio.repositorio import RepositorioDeTurnos

logger = logging.getLogger(__name__)


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
        try:
            turno = reservar_turno(
                cliente_id,
                cliente_nombre,
                inicio,
                ahora,
                self._repositorio.existe_en_horario,
            )
            turno = self._repositorio.guardar(turno)
        except ErrorDeNegocio as error:
            logger.info("Turno rechazado. cliente_id=%s motivo=%s", cliente_id, error)
            raise
        logger.info("Turno reservado. id=%s cliente_id=%s", turno.id, cliente_id)
        return turno

    def listar_proximos(self, cliente_id: int, ahora: datetime) -> list[Turno]:
        return self._repositorio.listar_por_cliente(cliente_id, ahora)

    def cancelar(self, turno_id: int, cliente_id: int) -> None:
        turno = self._repositorio.obtener(turno_id)
        if turno is None:
            logger.info(
                "Cancelacion rechazada. turno_id=%s cliente_id=%s motivo=turno inexistente",
                turno_id,
                cliente_id,
            )
            raise TurnoInexistente("No existe un turno con ese identificador.")
        if turno.cliente_id != cliente_id:
            logger.info(
                "Cancelacion rechazada. turno_id=%s cliente_id=%s motivo=no autorizado",
                turno_id,
                cliente_id,
            )
            raise TurnoNoAutorizado("No podes cancelar el turno de otro cliente.")
        self._repositorio.eliminar(turno_id)
        logger.info("Turno cancelado. id=%s cliente_id=%s", turno_id, cliente_id)