# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.presupuesto import Presupuesto


class PresupuestoService:
    @staticmethod
    def listar(
        session: Session,
        proyecto_id: Optional[int] = None,
        anio: Optional[int] = None,
        texto_busqueda: str = "",
    ) -> list[Presupuesto]:
        query = session.query(Presupuesto)
        if proyecto_id:
            query = query.filter(Presupuesto.proyecto_id == proyecto_id)
        if anio:
            query = query.filter(Presupuesto.anio == anio)
        if texto_busqueda:
            like = f"%{texto_busqueda.strip()}%"
            query = query.filter(
                or_(Presupuesto.clasificador.ilike(like), Presupuesto.descripcion.ilike(like))
            )
        return query.order_by(Presupuesto.clasificador).all()

    @staticmethod
    def eliminar(session: Session, presupuesto_id: int) -> None:
        registro = session.get(Presupuesto, presupuesto_id)
        if registro:
            session.delete(registro)
