# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

# El catálogo oficial usa espacios como separador de grupo, p.ej.
# "2.3.1 1.1 1" (grupos "2.3.1", "1.1", "1"). Los reportes SIAF exportan
# el mismo código con espaciado irregular por celdas de ancho fijo, p.ej.
# "2.3. 1  1. 1  1".
#
# IMPORTANTE: no se deben ELIMINAR los espacios, solo reemplazarlos por
# un separador. Eliminarlos fusiona números adyacentes de forma ambigua
# (p.ej. "1 1" se convertía en "11", indistinguible de un "11" real como
# en "2.3.1 6.1 99"). En su lugar, cada espacio se reemplaza por un punto
# y luego se colapsan los puntos duplicados que resultan de los puntos ya
# existentes en el texto original. Así "2.3. 1  1. 1  1" y "2.3.1 1.1 1"
# normalizan ambos, sin ambigüedad, a "2.3.1.1.1.1".
_ESPACIOS_RE = re.compile(r"\s+")
_PUNTOS_DUPLICADOS_RE = re.compile(r"\.{2,}")


def normalizar_codigo(codigo: str) -> str:
    texto = str(codigo or "").strip()
    texto = _ESPACIOS_RE.sub(".", texto)
    texto = _PUNTOS_DUPLICADOS_RE.sub(".", texto)
    return texto.strip(".")


class Clasificador(Base):
    """Catálogo oficial de clasificadores de gasto (MEF), por año.

    Es la fuente de verdad para validar y enriquecer con la descripción
    canónica cada partida de `Presupuesto` importada desde un reporte SIAF.
    """

    __tablename__ = "clasificadores"
    __table_args__ = (UniqueConstraint("anio", "codigo_normalizado", name="uq_clasificador_anio_codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)  # formato original del catálogo
    codigo_normalizado: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion_detallada: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Clasificador {self.anio} {self.codigo}>"
