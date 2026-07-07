# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.proyecto import Proyecto


class Ejecucion(Base):
    """Registro mensual de avance físico/financiero de un proyecto."""

    __tablename__ = "ejecuciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(ForeignKey("proyectos.id"), nullable=False, index=True)

    fecha: Mapped[dt.date] = mapped_column(Date, nullable=False)
    avance_fisico: Mapped[float] = mapped_column(Float, default=0.0)  # % 0-100
    avance_financiero: Mapped[float] = mapped_column(Float, default=0.0)  # % 0-100
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    registrado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)

    proyecto: Mapped["Proyecto"] = relationship(back_populates="ejecuciones")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ejecucion proyecto={self.proyecto_id} {self.fecha}>"
