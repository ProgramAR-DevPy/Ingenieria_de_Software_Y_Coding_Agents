"""Excepciones de las reglas de negocio."""


class ErrorDeNegocio(Exception):
    """Error base para reglas de negocio incumplidas."""


class HorarioInvalido(ErrorDeNegocio):
    """El turno no se encuentra dentro del horario de atencion."""


class DuracionInvalida(ErrorDeNegocio):
    """La duracion solicitada no es positiva."""


class FechaPasada(ErrorDeNegocio):
    """El turno solicitado ya ocurrio."""


class TurnoNoDisponible(ErrorDeNegocio):
    """El horario solicitado ya esta reservado."""


class TurnoInexistente(ErrorDeNegocio):
    """El turno solicitado no existe."""


class TurnoNoAutorizado(ErrorDeNegocio):
    """El cliente no puede modificar el turno solicitado."""