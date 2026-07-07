# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.ejecucion import Ejecucion
    from models.presupuesto import Presupuesto
    from models.usuario import Usuario


class Proyecto(Base):
    __tablename__ = "proyectos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pliego: Mapped[str | None] = mapped_column(String(200), nullable=True)
    programa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False)
    fecha_creacion: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, nullable=False
    )

    creado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_por: Mapped["Usuario"] = relationship(foreign_keys=[creado_por_id])  # type: ignore[name-defined]  # noqa: F821

    presupuestos: Mapped[list["Presupuesto"]] = relationship(  # noqa: F821
        back_populates="proyecto", cascade="all, delete-orphan"
    )
    ejecuciones: Mapped[list["Ejecucion"]] = relationship(  # noqa: F821
        back_populates="proyecto", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Proyecto {self.codigo} - {self.nombre[:30]}>"
