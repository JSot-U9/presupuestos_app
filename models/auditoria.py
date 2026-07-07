# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Auditoria(Base):
    """Registro de auditoría: quién hizo qué y cuándo."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[str] = mapped_column(String(50), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)  # CREAR/EDITAR/ELIMINAR/IMPORTAR/LOGIN
    entidad: Mapped[str] = mapped_column(String(50), nullable=False)  # Proyecto, Presupuesto, etc.
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, nullable=False)
