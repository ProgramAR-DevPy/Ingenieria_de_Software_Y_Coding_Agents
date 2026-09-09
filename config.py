"""Configuración de la aplicación leída desde variables de entorno.

Único módulo del proyecto autorizado a leer `os.environ`.
"""

import os
from pathlib import Path


def _cargar_env(ruta: Path = Path(".env")) -> None:
    """Carga variables de un archivo .env sin pisar las ya definidas en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip())


class Config:
    """Agrupa toda la configuración dependiente del entorno de ejecución."""

    def __init__(self) -> None:
        _cargar_env()
        self.telegram_token = self._requerida(
            "TELEGRAM_TOKEN",
            "Definila con el token que te da @BotFather, por ejemplo:\n"
            '  PowerShell: $env:TELEGRAM_TOKEN = "tu_token"\n'
            "  bash: export TELEGRAM_TOKEN=tu_token",
        )
        self.db_path = Path(os.environ.get("TURNOSBOT_DB_PATH", "turnos.db"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        log_file = os.environ.get("LOG_FILE")
        self.log_file = Path(log_file) if log_file else None

    @staticmethod
    def _requerida(nombre: str, ayuda: str) -> str:
        """Lee una variable de entorno obligatoria o corta la ejecución."""
        valor = os.environ.get(nombre)
        if not valor:
            raise RuntimeError(
                f"Falta la variable de entorno obligatoria '{nombre}'.\n{ayuda}"
            )
        return valor


config = Config()
