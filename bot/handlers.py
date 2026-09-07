"""Handlers del bot de Telegram para clientes y turnos."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import telebot
from telebot import types

from dominio.errores import ErrorDeNegocio

estados: dict[int, dict[str, Any]] = {}


def _mensaje_error(error: Exception) -> str:
    """Convierte una excepción de dominio en un mensaje de usuario."""
    if isinstance(error, ErrorDeNegocio):
        return str(error)
    return "No pudimos procesar tu solicitud en este momento."


def _llamar_servicio(servicio: Any, nombre: str, *args: Any, **kwargs: Any) -> Any:
    """Invoca una operación del servicio de dominio si está disponible."""
    metodo = getattr(servicio, nombre, None)
    if metodo is None:
        raise AttributeError(f"Falta la operación de dominio '{nombre}'.")
    return metodo(*args, **kwargs)


def _estado(chat_id: int) -> dict[str, Any]:
    """Devuelve el estado del chat, creando uno si no existe."""
    if chat_id not in estados:
        estados[chat_id] = {}
    return estados[chat_id]


def _menu_principal() -> types.ReplyKeyboardMarkup:
    """Crea el menú principal del bot."""
    teclado = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    teclado.row("/reservar", "/misturnos")
    teclado.row("/cancelar", "/start")
    return teclado


def _inline_inicio_flijo() -> types.InlineKeyboardMarkup:
    """Crea teclado de inicio para la reserva."""
    teclado = types.InlineKeyboardMarkup()
    teclado.add(types.InlineKeyboardButton("Elegir servicio", callback_data="reservar:servicio"))
    return teclado


def start(message: types.Message) -> None:
    """Da de alta al cliente y muestra el menú principal."""
    chat_id = message.chat.id
    usuario = message.from_user
    estado = _estado(chat_id)
    estado["usuario_id"] = usuario.id if usuario else chat_id
    estado["nombre"] = usuario.first_name if usuario and usuario.first_name else "Cliente"
    estado["fase"] = "idle"

    texto = (
        f"Hola {estado['nombre']} 👋\n\n"
        "Podés reservar turnos, ver tus turnos y cancelarlos desde aquí."
    )
    message.bot.send_message(chat_id, texto, reply_markup=_menu_principal())


def reservar(message: types.Message) -> None:
    """Inicia el flujo de reserva: servicio → profesional → día → horario → confirmación."""
    chat_id = message.chat.id
    estado = _estado(chat_id)
    estado["fase"] = "reservar"
    estado["paso"] = "servicio"

    try:
        servicios = _llamar_servicio(message.bot, "servicios", message.from_user.id)
    except AttributeError:
        message.reply("Todavía no está disponible el catálogo de servicios del dominio.")
        return
    except Exception as error:  # pragma: no cover - manejo de errores de integración
        message.reply(_mensaje_error(error))
        return

    if not servicios:
        message.reply("No hay servicios disponibles en este momento.")
        return

    teclado = types.InlineKeyboardMarkup()
    for servicio in servicios:
        callback = f"reservar:servicio:{servicio.id}"
        teclado.add(types.InlineKeyboardButton(servicio.nombre, callback_data=callback))

    message.reply("Elegí un servicio:", reply_markup=teclado)


def misturnos(message: types.Message) -> None:
    """Lista los turnos futuros del cliente actual."""
    chat_id = message.chat.id
    usuario_id = message.from_user.id if message.from_user else chat_id
    try:
        turnos = _llamar_servicio(message.bot, "listar_mis_turnos", usuario_id, datetime.now())
    except AttributeError:
        message.reply("Todavía no está disponible la consulta de turnos del dominio.")
        return
    except ErrorDeNegocio as error:
        message.reply(_mensaje_error(error))
        return
    except Exception as error:  # pragma: no cover - manejo de errores de integración
        message.reply(_mensaje_error(error))
        return

    if not turnos:
        message.reply("No tenés turnos futuros. ")
        return

    texto = "Tus turnos futuros:\n"
    for turno in turnos:
        texto += f"- {turno.inicio:%d/%m/%Y %H:%M} ({turno.estado})\n"
    message.reply(texto.strip())


def cancelar(message: types.Message) -> None:
    """Presenta la lista de turnos futuros para elegir cuál cancelar."""
    chat_id = message.chat.id
    usuario_id = message.from_user.id if message.from_user else chat_id
    try:
        turnos = _llamar_servicio(message.bot, "listar_mis_turnos", usuario_id, datetime.now())
    except AttributeError:
        message.reply("Todavía no está disponible la cancelación por dominio.")
        return
    except ErrorDeNegocio as error:
        message.reply(_mensaje_error(error))
        return
    except Exception as error:  # pragma: no cover - manejo de errores de integración
        message.reply(_mensaje_error(error))
        return

    if not turnos:
        message.reply("No tenés turnos futuros para cancelar.")
        return

    estado = _estado(chat_id)
    estado["fase"] = "cancelar"
    estado["turnos_a_cancelar"] = [turno.id for turno in turnos]

    teclado = types.InlineKeyboardMarkup()
    for turno in turnos:
        texto = f"{turno.inicio:%d/%m/%Y %H:%M}"
        teclado.add(types.InlineKeyboardButton(texto, callback_data=f"cancelar:turno:{turno.id}"))
    message.reply("Elegí el turno que querés cancelar:", reply_markup=teclado)


def callback_query(call: types.CallbackQuery) -> None:
    """Procesa callbacks del flujo de reserva y cancelación."""
    chat_id = call.message.chat.id
    estado = _estado(chat_id)
    data = call.data or ""
    bot = call.bot

    if not data:
        bot.answer_callback_query(call.id, "Acción no válida.")
        return

    partes = data.split(":")
    accion = partes[0]

    try:
        if accion == "reservar":
            self_state = estado.setdefault("reservar", {})
            if partes[1] == "servicio":
                servicio_id = int(partes[2])
                self_state["servicio_id"] = servicio_id
                profesionales = _llamar_servicio(bot, "profesionales_por_servicio", servicio_id)
                teclado = types.InlineKeyboardMarkup()
                for profesional in profesionales:
                    payload = f"reservar:profesional:{profesional.id}"
                    teclado.add(types.InlineKeyboardButton(profesional.nombre, callback_data=payload))
                bot.edit_message_text(
                    "Elegí un profesional:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=teclado,
                )
                return

            if partes[1] == "profesional":
                profesional_id = int(partes[2])
                self_state["profesional_id"] = profesional_id
                fechas = _llamar_servicio(bot, "dias_disponibles", profesional_id, self_state["servicio_id"])
                teclado = types.InlineKeyboardMarkup()
                for fecha in fechas:
                    payload = f"reservar:dia:{fecha.isoformat()}"
                    teclado.add(types.InlineKeyboardButton(fecha.strftime("%d/%m/%Y"), callback_data=payload))
                bot.edit_message_text(
                    "Elegí un día:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=teclado,
                )
                return

            if partes[1] == "dia":
                fecha = datetime.fromisoformat(partes[2])
                self_state["dia"] = fecha
                horarios = _llamar_servicio(bot, "horarios_disponibles", self_state["profesional_id"], self_state["servicio_id"], fecha)
                teclado = types.InlineKeyboardMarkup()
                for horario in horarios:
                    payload = f"reservar:horario:{horario.isoformat()}"
                    teclado.add(types.InlineKeyboardButton(horario.strftime("%H:%M"), callback_data=payload))
                bot.edit_message_text(
                    "Elegí un horario:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=teclado,
                )
                return

            if partes[1] == "horario":
                inicio = datetime.fromisoformat(partes[2])
                self_state["inicio"] = inicio
                texto = (
                    f"Confirmás este turno:\n"
                    f"Servicio: {self_state['servicio_id']}\n"
                    f"Profesional: {self_state['profesional_id']}\n"
                    f"Inicio: {inicio:%d/%m/%Y %H:%M}"
                )
                teclado = types.InlineKeyboardMarkup()
                teclado.add(types.InlineKeyboardButton("Confirmar", callback_data="reservar:confirmar"))
                teclado.add(types.InlineKeyboardButton("Cancelar", callback_data="reservar:cancelar"))
                bot.edit_message_text(texto, chat_id, call.message.message_id, reply_markup=teclado)
                return

            if partes[1] == "confirmar":
                inicio = self_state["inicio"]
                turno = _llamar_servicio(
                    bot,
                    "confirmar_turno",
                    estado["usuario_id"],
                    estado["nombre"],
                    self_state["servicio_id"],
                    self_state["profesional_id"],
                    inicio,
                )
                bot.edit_message_text(
                    f"Turno confirmado. ID: {turno.id}. Fecha: {turno.inicio:%d/%m/%Y %H:%M}",
                    chat_id,
                    call.message.message_id,
                )
                estado["fase"] = "idle"
                return

            if partes[1] == "cancelar":
                bot.edit_message_text("Reserva cancelada.", chat_id, call.message.message_id)
                estado["fase"] = "idle"
                return

        if accion == "cancelar":
            if partes[1] == "turno":
                turno_id = int(partes[2])
                try:
                    _llamar_servicio(bot, "cancelar_turno", turno_id, estado["usuario_id"])
                except ErrorDeNegocio as error:
                    bot.answer_callback_query(call.id, _mensaje_error(error))
                    return
                bot.edit_message_text("Turno cancelado correctamente.", chat_id, call.message.message_id)
                return

        bot.answer_callback_query(call.id, "Acción no soportada.")
    except AttributeError:
        bot.answer_callback_query(call.id, "Falta una operación del dominio para continuar este flujo.")
    except ErrorDeNegocio as error:
        bot.answer_callback_query(call.id, _mensaje_error(error))
    except Exception as error:  # pragma: no cover - manejo de errores de integración
        bot.answer_callback_query(call.id, _mensaje_error(error))


def registrar_handlers(bot: telebot.TeleBot, servicio: Any) -> None:
    """Registra todos los handlers del bot."""
    bot.register_message_handler(start, commands=["start"])
    bot.register_message_handler(reservar, commands=["reservar"])
    bot.register_message_handler(misturnos, commands=["misturnos"])
    bot.register_message_handler(cancelar, commands=["cancelar"])
    bot.register_callback_query_handler(callback_query, func=lambda call: True)

    bot.servicio = servicio
