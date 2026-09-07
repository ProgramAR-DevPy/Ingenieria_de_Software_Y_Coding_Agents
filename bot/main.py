"""Punto de entrada del bot de Telegram."""

import os
from datetime import datetime
from pathlib import Path

import telebot
from telebot.types import Message

from datos.repositorio_sqlite import RepositorioTurnosSqlite
from dominio.agenda import ZONA_HORARIA
from dominio.errores import ErrorDeNegocio
from dominio.servicio_turnos import ServicioDeTurnos


def ahora_argentina() -> datetime:
    """Devuelve el instante actual en la zona horaria del negocio."""
    return datetime.now(ZONA_HORARIA)


def interpretar_inicio(texto: str) -> datetime:
    """Interpreta el formato de fecha que se expone al usuario."""
    fecha = datetime.strptime(texto, "%Y-%m-%d %H:%M")
    return fecha.replace(tzinfo=ZONA_HORARIA)


def crear_bot(token: str, servicio: ServicioDeTurnos) -> telebot.TeleBot:
    """Crea y registra los comandos del bot."""
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start", "ayuda"])
    def mostrar_ayuda(mensaje: Message) -> None:
        bot.reply_to(
            mensaje,
            "Reserva turnos de lunes a viernes, de 09:00 a 18:00.\n\n"
            "/reservar AAAA-MM-DD HH:MM\n"
            "/mis_turnos\n"
            "/cancelar ID",
        )

    @bot.message_handler(commands=["reservar"])
    def reservar(mensaje: Message) -> None:
        partes = mensaje.text.split(maxsplit=1) if mensaje.text else []
        if len(partes) != 2:
            bot.reply_to(mensaje, "Usa: /reservar AAAA-MM-DD HH:MM")
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
            bot.reply_to(mensaje, "Usa la fecha con formato AAAA-MM-DD HH:MM.")
            return
        except ErrorDeNegocio as error:
            bot.reply_to(mensaje, str(error))
            return
        bot.reply_to(mensaje, f"Turno reservado. ID: {turno.id}. Fecha: {turno.inicio:%d/%m/%Y %H:%M}.")

    @bot.message_handler(commands=["mis_turnos"])
    def listar_turnos(mensaje: Message) -> None:
        turnos = servicio.listar_proximos(mensaje.from_user.id, ahora_argentina())
        if not turnos:
            bot.reply_to(mensaje, "No tenes turnos proximos.")
            return
        texto = "\n".join(
            f"ID {turno.id}: {turno.inicio:%d/%m/%Y %H:%M}" for turno in turnos
        )
        bot.reply_to(mensaje, texto)

    @bot.message_handler(commands=["cancelar"])
    def cancelar(mensaje: Message) -> None:
        partes = mensaje.text.split(maxsplit=1) if mensaje.text else []
        try:
            turno_id = int(partes[1])
            servicio.cancelar(turno_id, mensaje.from_user.id)
        except (IndexError, ValueError):
            bot.reply_to(mensaje, "Usa: /cancelar ID")
            return
        except ErrorDeNegocio as error:
            bot.reply_to(mensaje, str(error))
            return
        bot.reply_to(mensaje, "Turno cancelado.")

    return bot


def ejecutar() -> None:
    """Inicia el polling con el token de entorno."""
    
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Defini la variable de entorno TELEGRAM_TOKEN antes de iniciar el bot.")
    repositorio = RepositorioTurnosSqlite(Path("turnos.db"))
    bot = crear_bot(token, ServicioDeTurnos(repositorio))
    print("Bot iniciado")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    ejecutar()