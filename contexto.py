"""Id corto de correlación para seguir una interacción de punta a punta en los logs."""

import contextvars
import secrets

_id_correlacion: contextvars.ContextVar[str] = contextvars.ContextVar(
    "id_correlacion", default="-"
)


def nuevo_id() -> str:
    """Genera y fija un nuevo id de correlación para el contexto actual."""
    id_ = secrets.token_hex(4)
    _id_correlacion.set(id_)
    return id_


def id_actual() -> str:
    """Devuelve el id de correlación vigente en el contexto actual."""
    return _id_correlacion.get()
