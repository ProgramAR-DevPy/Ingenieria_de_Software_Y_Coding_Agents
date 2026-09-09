"""Punto de entrada del bot de Telegram."""

import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Callable

import requests
import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import Message

import contexto
from config import config
from datos.repositorio_sqlite import RepositorioTurnosSqlite
from dominio.agenda import ZONA_HORARIA
from dominio.errores import ErrorDeNegocio
from dominio.servicio_turnos import ServicioDeTurnos

UMBRAL_LENTITUD_SEGUNDOS = 5
MAX_INTENTOS_ENVIO = 3
ESPERA_BASE_SEGUNDOS = 1
CODIGOS_HTTP_TRANSITORIOS = (429, 500, 502, 503, 504)

logger = logging.getLogger(__name__)


class _FiltroCorrelacion(logging.Filter):
    """Agrega el id de correlación vigente a cada registro de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.id_correlacion = contexto.id_actual()
        return True


class _FormateadorConZonaHoraria(logging.Formatter):
    """Formatea la fecha y hora del log en la zona horaria del negocio."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        instante = datetime.fromtimestamp(record.created, tz=ZONA_HORARIA)
        return instante.strftime(datefmt or "%Y-%m-%d %H:%M:%S%z")


def configurar_logging() -> None:
    """Configura el logging de toda la aplicación. Se llama una sola vez, al arrancar."""
    formateador = _FormateadorConZonaHoraria(
        "%(asctime)s %(levelname)s [%(id_correlacion)s] %(name)s: %(message)s"
    )
    filtro = _FiltroCorrelacion()

    manejadores: list[logging.Handler] = [logging.StreamHandler()]
    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)
        manejadores.append(
            RotatingFileHandler(
                config.log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
        )

    for manejador in manejadores:
        manejador.setFormatter(formateador)
        manejador.addFilter(filtro)

    logging.basicConfig(level=config.log_level, handlers=manejadores, force=True)


def ahora_argentina() -> datetime:
    """Devuelve el instante actual en la zona horaria del negocio."""
    return datetime.now(ZONA_HORARIA)


def interpretar_inicio(texto: str) -> datetime:
    """Interpreta el formato de fecha que se expone al usuario."""
    fecha = datetime.strptime(texto, "%Y-%m-%d %H:%M")
    return fecha.replace(tzinfo=ZONA_HORARIA)


def _es_transitorio(error: Exception) -> bool:
    """Indica si el error de Telegram vale la pena reintentar."""
    if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(error, ApiTelegramException) and error.error_code in CODIGOS_HTTP_TRANSITORIOS:
        return True
    return False


def _responder(bot: telebot.TeleBot, mensaje: Message, texto: str) -> None:
    """Responde al usuario, reintentando con espera creciente ante fallas transitorias."""
    inicio = time.monotonic()
    intento = 1
    while True:
        try:
            bot.reply_to(mensaje, texto)
            break
        except Exception as error:
            if not _es_transitorio(error):
                raise
            if intento >= MAX_INTENTOS_ENVIO:
                logger.error(
                    "Se agotaron los %s intentos de responder por Telegram. chat_id=%s error=%s",
                    MAX_INTENTOS_ENVIO,
                    mensaje.chat.id,
                    error,
                )
                try:
                    bot.reply_to(mensaje, "Estamos con problemas para responderte. Probá de nuevo en un momento.")
                except Exception:
                    pass
                return
            espera = ESPERA_BASE_SEGUNDOS * (2 ** (intento - 1))
            logger.warning(
                "Reintento %s/%s respondiendo por Telegram tras error transitorio: %s",
                intento,
                MAX_INTENTOS_ENVIO,
                error,
            )
            time.sleep(espera)
            intento += 1
    duracion = time.monotonic() - inicio
    if duracion > UMBRAL_LENTITUD_SEGUNDOS:
        logger.warning("Llamada a Telegram lenta. duracion_seg=%.1f", duracion)


def _con_correlacion(manejador: Callable[[Message], None]) -> Callable[[Message], None]:
    """Arranca un id de correlación nuevo y loguea excepciones inesperadas con traceback."""

    def envoltorio(mensaje: Message) -> None:
        contexto.nuevo_id()
        try:
            manejador(mensaje)
        except Exception:
            logger.exception("Error inesperado procesando chat_id=%s", mensaje.chat.id)

    return envoltorio


def crear_bot(token: str, servicio: ServicioDeTurnos) -> telebot.TeleBot:
    """Crea y registra los comandos del bot."""
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start", "ayuda"])
    @_con_correlacion
    def mostrar_ayuda(mensaje: Message) -> None:
        _responder(
            bot,
            mensaje,
            "Reserva turnos de lunes a viernes, de 09:00 a 18:00.\n\n"
            "/reservar AAAA-MM-DD HH:MM\n"
            "/mis_turnos\n"
            "/cancelar ID",
        )

    @bot.message_handler(commands=["reservar"])
    @_con_correlacion
    def reservar(mensaje: Message) -> None:
        partes = mensaje.text.split(maxsplit=1) if mensaje.text else []
        if len(partes) != 2:
            _responder(bot, mensaje, "Usa: /reservar AAAA-MM-DD HH:MM")
            return
        try:
            inicio = interpretar_inicio(partes[1])
            turno = servicio.reservar(
                mensaje.from_user.id,
                mensaje.from_user.first_name,
                inicio,
                ahora_argentina(),
            )
        except ValueError:
            _responder(bot, mensaje, "Usa la fecha con formato AAAA-MM-DD HH:MM.")
            return
        except ErrorDeNegocio as error:
            _responder(bot, mensaje, str(error))
            return
        _responder(bot, mensaje, f"Turno reservado. ID: {turno.id}. Fecha: {turno.inicio:%d/%m/%Y %H:%M}.")

    @bot.message_handler(commands=["mis_turnos"])
    @_con_correlacion
    def listar_turnos(mensaje: Message) -> None:
        turnos = servicio.listar_proximos(mensaje.from_user.id, ahora_argentina())
        if not turnos:
            _responder(bot, mensaje, "No tenes turnos proximos.")
            return
        texto = "\n".join(
            f"ID {turno.id}: {turno.inicio:%d/%m/%Y %H:%M}" for turno in turnos
        )
        _responder(bot, mensaje, texto)

    @bot.message_handler(commands=["cancelar"])
    @_con_correlacion
    def cancelar(mensaje: Message) -> None:
        partes = mensaje.text.split(maxsplit=1) if mensaje.text else []
        try:
            turno_id = int(partes[1])
            servicio.cancelar(turno_id, mensaje.from_user.id)
        except (IndexError, ValueError):
            _responder(bot, mensaje, "Usa: /cancelar ID")
            return
        except ErrorDeNegocio as error:
            _responder(bot, mensaje, str(error))
            return
        _responder(bot, mensaje, "Turno cancelado.")

    return bot


def ejecutar() -> None:
    """Inicia el polling con la configuración leída del entorno."""
    configurar_logging()
    repositorio = RepositorioTurnosSqlite(config.db_path)
    bot = crear_bot(config.telegram_token, ServicioDeTurnos(repositorio))
    logger.info("Bot iniciado")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    ejecutar()