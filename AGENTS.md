# TurnosBot

Bot de Telegram para reservar turnos en negocios de servicios
(peluquerías, consultorios, talleres).

## Stack
Python 3.11 · pyTelegramBotAPI (telebot) 4.x · SQLite (módulo `sqlite3`) · pytest.
Sin ORM, sin framework web, sin async.

## Arquitectura — regla dura
- `dominio/`  reglas de negocio puras. NO importa telebot ni sqlite3.
- `datos/`    único lugar del proyecto donde hay SQL.
- `bot/`      traduce mensajes de Telegram a llamadas de dominio. Cero reglas de negocio.
La dependencia va siempre  bot → dominio ← datos.  Nunca al revés.

## Convenciones
- Nombres de funciones, variables y tests en español. Type hints obligatorios.
- Fechas: `datetime` con timezone `America/Argentina/Buenos_Aires`. Nunca naive.
- Ninguna función de `dominio/` llama a `datetime.now()`.
  El "ahora" se recibe siempre como parámetro.
- Errores de negocio: excepciones propias en `dominio/errores.py`.
  Nunca devolver strings de error ni `None` para señalar una falla.
- El token sale de la variable de entorno `TELEGRAM_TOKEN`. Nunca hardcodeado.

## Cómo trabajar conmigo
- Si te falta un dato para decidir, preguntá antes de asumir.
- No agregues dependencias sin avisarme primero.
- Código nuevo viene con su test.
- Cuando termines, decime en dos líneas qué cambiaste y qué NO probaste.