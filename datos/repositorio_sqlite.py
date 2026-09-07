"""Implementacion SQLite del repositorio de turnos."""

import sqlite3
from datetime import datetime
from pathlib import Path

from dominio.modelos import Turno


class RepositorioTurnosSqlite:
    """Almacena turnos usando SQLite."""

    def __init__(self, ruta_base_datos: Path | str) -> None:
        self._ruta_base_datos = str(ruta_base_datos)
        self._crear_tabla()

    def _conexion(self) -> sqlite3.Connection:
        return sqlite3.connect(self._ruta_base_datos)

    def _crear_tabla(self) -> None:
        with self._conexion() as conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    profesional_id INTEGER NOT NULL,
                    servicio_id INTEGER NOT NULL,
                    inicio TEXT NOT NULL,
                    fin TEXT NOT NULL,
                    estado TEXT NOT NULL
                )
                """
            )

    def existe_en_horario(self, inicio: datetime) -> bool:
        with self._conexion() as conexion:
            fila = conexion.execute(
                "SELECT 1 FROM turnos WHERE inicio = ?", (inicio.isoformat(),)
            ).fetchone()
        return fila is not None

    def guardar(self, turno: Turno) -> Turno:
        with self._conexion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO turnos (cliente_id, profesional_id, servicio_id, inicio, fin, estado)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    turno.cliente_id,
                    turno.profesional_id,
                    turno.servicio_id,
                    turno.inicio.isoformat(),
                    turno.fin.isoformat(),
                    turno.estado,
                ),
            )
        return Turno(
            id=cursor.lastrowid,
            cliente_id=turno.cliente_id,
            profesional_id=turno.profesional_id,
            servicio_id=turno.servicio_id,
            inicio=turno.inicio,
            fin=turno.fin,
            estado=turno.estado,
        )

    def listar_por_cliente(self, cliente_id: int, desde: datetime) -> list[Turno]:
        with self._conexion() as conexion:
            filas = conexion.execute(
                """
                SELECT id, cliente_id, profesional_id, servicio_id, inicio, fin, estado
                FROM turnos
                WHERE cliente_id = ? AND inicio >= ?
                ORDER BY inicio
                """,
                (cliente_id, desde.isoformat()),
            ).fetchall()
        return [self._convertir_fila(fila) for fila in filas]

    def obtener(self, turno_id: int) -> Turno | None:
        with self._conexion() as conexion:
            fila = conexion.execute(
                """
                SELECT id, cliente_id, profesional_id, servicio_id, inicio, fin, estado
                FROM turnos WHERE id = ?
                """,
                (turno_id,),
            ).fetchone()
        return self._convertir_fila(fila) if fila else None

    def eliminar(self, turno_id: int) -> None:
        with self._conexion() as conexion:
            conexion.execute("DELETE FROM turnos WHERE id = ?", (turno_id,))

    @staticmethod
    def _convertir_fila(fila: tuple[object, ...]) -> Turno:
        return Turno(
            id=int(fila[0]),
            cliente_id=int(fila[1]),
            profesional_id=int(fila[2]),
            servicio_id=int(fila[3]),
            inicio=datetime.fromisoformat(str(fila[4])),
            fin=datetime.fromisoformat(str(fila[5])),
            estado=str(fila[6]),
        )