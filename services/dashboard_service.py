# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.presupuesto import Presupuesto
from models.proyecto import Proyecto


@dataclass
class DashboardKPIs:
    num_proyectos: int = 0
    pim_total: float = 0.0
    certificado_total: float = 0.0
    comprometido_total: float = 0.0
    devengado_total: float = 0.0
    saldo_total: float = 0.0
    porcentaje_ejecucion: float = 0.0


class DashboardService:
    @staticmethod
    def calcular_kpis(session: Session) -> DashboardKPIs:
        num_proyectos = session.query(func.count(Proyecto.id)).scalar() or 0

        agregados = session.query(
            func.coalesce(func.sum(Presupuesto.pim), 0.0),
            func.coalesce(func.sum(Presupuesto.certificacion), 0.0),
            func.coalesce(func.sum(Presupuesto.compromiso), 0.0),
            func.coalesce(func.sum(Presupuesto.devengado), 0.0),
        ).one()

        pim, certificado, comprometido, devengado = agregados
        saldo = pim - devengado
        porcentaje = (devengado / pim * 100.0) if pim else 0.0

        return DashboardKPIs(
            num_proyectos=num_proyectos,
            pim_total=pim,
            certificado_total=certificado,
            comprometido_total=comprometido,
            devengado_total=devengado,
            saldo_total=saldo,
            porcentaje_ejecucion=round(porcentaje, 2),
        )

    @staticmethod
    def ejecucion_por_proyecto(session: Session, top_n: int = 10) -> list[tuple[str, float, float]]:
        """Devuelve (codigo_proyecto, pim, devengado) para los N proyectos con mayor PIM."""
        filas = (
            session.query(
                Proyecto.codigo,
                func.coalesce(func.sum(Presupuesto.pim), 0.0),
                func.coalesce(func.sum(Presupuesto.devengado), 0.0),
            )
            .join(Presupuesto, Presupuesto.proyecto_id == Proyecto.id)
            .group_by(Proyecto.codigo)
            .order_by(func.sum(Presupuesto.pim).desc())
            .limit(top_n)
            .all()
        )
        return filas
