# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.proyecto import Proyecto


class Presupuesto(Base):
    """Una fila de partida presupuestal (clasificador de gasto) importada
    desde el reporte SIAF, asociada a un Proyecto.

    Los nombres de columna replican 1:1 los campos que produce
    `services/excel_import_service.py` (adaptado de pruebas_presupuesto.py)
    para que la importación sea una simple inserción sin transformación
    adicional.
    """

    __tablename__ = "presupuestos"

    id: Mapped[int] = mapped_column(primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(ForeignKey("proyectos.id"), nullable=False, index=True)

    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    rubro: Mapped[str | None] = mapped_column(String(200), nullable=True)
    programa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta: Mapped[str | None] = mapped_column(String(300), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True)
    clasificador: Mapped[str | None] = mapped_column(String(60), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)

    pia: Mapped[float] = mapped_column(Float, default=0.0)
    pim: Mapped[float] = mapped_column(Float, default=0.0)
    certificacion: Mapped[float] = mapped_column(Float, default=0.0)
    compromiso: Mapped[float] = mapped_column(Float, default=0.0)
    devengado: Mapped[float] = mapped_column(Float, default=0.0)
    saldo_certificacion: Mapped[float] = mapped_column(Float, default=0.0)
    saldo_compromiso: Mapped[float] = mapped_column(Float, default=0.0)
    saldo_devengado: Mapped[float] = mapped_column(Float, default=0.0)
    porcentaje_avance: Mapped[float] = mapped_column(Float, default=0.0)

    fecha_importacion: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, nullable=False
    )
    archivo_origen: Mapped[str | None] = mapped_column(String(255), nullable=True)

    proyecto: Mapped["Proyecto"] = relationship(back_populates="presupuestos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Presupuesto {self.clasificador} PIM={self.pim}>"
