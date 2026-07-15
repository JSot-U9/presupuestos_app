# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.presupuesto import Presupuesto


class PresupuestoService:
    @staticmethod
    def _aplicar_filtros(
        query,
        proyecto_id: Optional[int] = None,
        anio: Optional[int] = None,
        texto_busqueda: str = "",
        meta: Optional[str] = None,
        programa: Optional[str] = None,
        producto: Optional[str] = None,
        actividad_codigo: Optional[str] = None,
        funcion: Optional[str] = None,
        division_funcional: Optional[str] = None,
        grupo_funcional: Optional[str] = None,
        rubro: Optional[str] = None,
        categoria: Optional[str] = None,
        clasi_presu: Optional[str] = None,
    ):
        """Aplica los filtros comunes a consultas de presupuesto."""
        if proyecto_id:
            query = query.filter(Presupuesto.proyecto_id == proyecto_id)
        if anio:
            query = query.filter(Presupuesto.anio == anio)
        if meta:
            query = query.filter(Presupuesto.meta == meta)
        if programa:
            query = query.filter(Presupuesto.programa == programa)
        if producto:
            query = query.filter(Presupuesto.producto == producto)
        if actividad_codigo:
            query = query.filter(Presupuesto.actividad_codigo == actividad_codigo)
        if funcion:
            query = query.filter(Presupuesto.funcion == funcion)
        if division_funcional:
            query = query.filter(Presupuesto.division_funcional == division_funcional)
        if grupo_funcional:
            query = query.filter(Presupuesto.grupo_funcional == grupo_funcional)
        if rubro:
            query = query.filter(Presupuesto.rubro == rubro)
        if categoria:
            query = query.filter(Presupuesto.categoria == categoria)
        if clasi_presu:
            query = query.filter(Presupuesto.clasi_presu == clasi_presu)
        if texto_busqueda.strip():
            like = f"%{texto_busqueda.strip()}%"
            query = query.filter(
                or_(Presupuesto.clasificador.ilike(like), Presupuesto.descripcion.ilike(like))
            )
        return query

    @staticmethod
    def listar(
        session: Session,
        proyecto_id: Optional[int] = None,
        anio: Optional[int] = None,
        texto_busqueda: str = "",
        meta: Optional[str] = None,
        programa: Optional[str] = None,
        producto: Optional[str] = None,
        actividad_codigo: Optional[str] = None,
        funcion: Optional[str] = None,
        division_funcional: Optional[str] = None,
        grupo_funcional: Optional[str] = None,
        rubro: Optional[str] = None,
        categoria: Optional[str] = None,
        clasi_presu: Optional[str] = None,
    ) -> list[Presupuesto]:
        query = PresupuestoService._aplicar_filtros(
            session.query(Presupuesto), proyecto_id, anio, texto_busqueda,
            meta, programa, producto, actividad_codigo, funcion,
            division_funcional, grupo_funcional, rubro, categoria, clasi_presu,
        )
        return query.order_by(Presupuesto.clasificador).all()

    @staticmethod
    def listar_valores_filtro(
        session: Session,
        campo: str,
        **filtros,
    ) -> list[str]:
        """Devuelve los valores posibles de un filtro según los demás activos."""
        columna = getattr(Presupuesto, campo, None)
        if columna is None:
            raise ValueError(f"Campo de filtro no válido: {campo}")

        query = PresupuestoService._aplicar_filtros(
            session.query(columna), **filtros
        )
        return [str(valor[0]) for valor in query.distinct().order_by(columna).all()
                if valor[0] is not None]

    @staticmethod
    def eliminar(session: Session, presupuesto_id: int) -> None:
        registro = session.get(Presupuesto, presupuesto_id)
        if registro:
            session.delete(registro)
