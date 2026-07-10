# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class MetaPresupuesto(Base):
    __tablename__ = "metas_presupuesto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nro_meta: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    meta: Mapped[str] = mapped_column(String(10), nullable=False)
    finalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(300), nullable=False)

    def __repr__(self) -> str:
        return f"<MetaPresupuesto {self.nro_meta} - {self.descripcion[:30]}>"
