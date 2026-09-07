# TurnosBot

Bot de Telegram para reservar turnos de lunes a viernes, de 09:00 a 18:00, en bloques de 30 minutos.

## Preparacion

Requiere Python 3.11 o posterior. Instala las dependencias:

```powershell
python -m pip install -e . pytest
```

Define el token creado con BotFather y ejecuta el bot:

```powershell
$env:TELEGRAM_TOKEN = "tu_token"
python -m bot.main
```

## Comandos

- `/start`: muestra la ayuda.
- `/reservar 2026-09-01 10:30`: reserva un horario.
- `/mis_turnos`: lista los próximos turnos personales.
- `/cancelar 3`: cancela un turno propio.

## Pruebas

```powershell
python -m pytest
```