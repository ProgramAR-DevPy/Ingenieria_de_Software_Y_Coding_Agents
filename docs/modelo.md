# Modelo de dominio

## 1. Entidades

```python
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

EstadoTurno = Literal["reservado", "cancelado"]


@dataclass(frozen=True)
class Cliente:
    id: int
    nombre: str
    telefono: str


@dataclass(frozen=True)
class Profesional:
    id: int
    nombre: str
    activo: bool


@dataclass(frozen=True)
class Servicio:
    id: int
    nombre: str
    duracion: timedelta
    activo: bool


@dataclass(frozen=True)
class Turno:
    id: int
    cliente_id: int
    profesional_id: int
    servicio_id: int
    inicio: datetime
    fin: datetime
    estado: EstadoTurno


@dataclass(frozen=True)
class Feriado:
    fecha: date
    motivo: str


@dataclass(frozen=True)
class FranjaHoraria:
    dia_semana: int
    apertura: time
    cierre: time
```

## 2. Funciones Puras Del Dominio

- `calcular_fin_turno(inicio: datetime, servicio: Servicio) -> datetime`  
  Calcula el horario de finalización según la duración del servicio.

- `obtener_franja_atencion(fecha: date) -> FranjaHoraria | None`  
  Devuelve la franja de atención para esa fecha, o `None` si el negocio está cerrado por día semanal.

- `es_fecha_feriado(fecha: date, feriados: list[Feriado]) -> bool`  
  Indica si una fecha está cargada como cerrada manualmente.

- `validar_turno_en_horario_atencion(inicio: datetime, fin: datetime, feriados: list[Feriado]) -> None`  
  Valida que el turno entre completo dentro del horario permitido y no caiga en feriado.

- `turnos_solapados(un_inicio: datetime, un_fin: datetime, otro_inicio: datetime, otro_fin: datetime) -> bool`  
  Indica si dos rangos horarios se pisan total o parcialmente.

- `validar_profesional_disponible(profesional_id: int, inicio: datetime, fin: datetime, turnos_existentes: list[Turno]) -> None`  
  Valida que el profesional no tenga otro turno reservado superpuesto.

- `contar_turnos_futuros_cliente(cliente_id: int, ahora: datetime, turnos_existentes: list[Turno]) -> int`  
  Cuenta los turnos futuros reservados de un cliente.

- `validar_limite_turnos_futuros_cliente(cliente_id: int, ahora: datetime, turnos_existentes: list[Turno]) -> None`  
  Valida que el cliente no supere el máximo de 2 turnos futuros activos.

- `validar_cancelacion_permitida(turno: Turno, ahora: datetime) -> None`  
  Valida que el cliente pueda cancelar al menos 2 horas antes del inicio.

- `crear_turno(id_turno: int, cliente_id: int, profesional_id: int, servicio: Servicio, inicio: datetime, ahora: datetime, turnos_existentes: list[Turno], feriados: list[Feriado]) -> Turno`  
  Construye un turno reservado si cumple horario, disponibilidad profesional y límite del cliente.

- `cancelar_turno(turno: Turno, ahora: datetime) -> Turno`  
  Devuelve una copia del turno con estado cancelado si la cancelación está permitida.

## 3. Decisiones De Diseño Más Riesgosas

1. **Guardar `inicio` y `fin` en `Turno`**

   Alternativa descartada: guardar solo `inicio` y calcular siempre el `fin` desde el servicio.  
   La descarté porque si en el futuro cambia la duración de un servicio, los turnos históricos podrían reinterpretarse mal. Guardar `fin` congela la reserva tal como fue tomada.

2. **Representar feriados como fechas cerradas completas**

   Alternativa descartada: modelar cierres parciales o excepciones horarias desde el inicio.  
   La descarté porque la regla actual dice "fechas cerradas". Meter excepciones parciales ahora agrega complejidad prematura, aunque deja una posible migración futura.

3. **Pasar `turnos_existentes` y `feriados` a funciones puras**

   Alternativa descartada: que el dominio consulte repositorios directamente.  
   La descarté porque rompería la arquitectura: `dominio/` no debería saber de SQLite ni de persistencia. El costo es que la capa de aplicación/datos tendrá que traer el contexto correcto antes de validar.

## 4. Preguntas Pendientes

- ¿Los servicios son fijos en código o se administran desde la base de datos?
- ¿Un cliente se identifica por `telefono`, `telegram_user_id` o una entidad propia con `id` interno?
- ¿Los profesionales tienen horarios individuales o todos usan el horario general del negocio?
- ¿Se permite reservar un turno que empieza antes del cierre pero termina después?
- ¿Qué pasa si un cliente intenta cancelar un turno ya cancelado?
- ¿Hay que permitir elegir profesional, o el sistema puede asignar cualquiera disponible?
- ¿Los feriados aplican a todo el negocio o podrían aplicar solo a ciertos profesionales?
- ¿Qué zona horaria se usa al recibir fechas desde Telegram: siempre `America/Argentina/Buenos_Aires`?
