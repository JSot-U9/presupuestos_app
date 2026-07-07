# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.auditoria import Auditoria
from models.proyecto import Proyecto
from utils.validators import ValidationError, require_not_empty, validar_codigo_proyecto


class ProyectoService:
    @staticmethod
    def listar(session: Session, texto_busqueda: str = "", estado: Optional[str] = None) -> list[Proyecto]:
        query = session.query(Proyecto)
        if texto_busqueda:
            like = f"%{texto_busqueda.strip()}%"
            query = query.filter(or_(Proyecto.codigo.ilike(like), Proyecto.nombre.ilike(like)))
        if estado:
            query = query.filter(Proyecto.estado == estado)
        return query.order_by(Proyecto.codigo).all()

    @staticmethod
    def obtener(session: Session, proyecto_id: int) -> Proyecto:
        proyecto = session.get(Proyecto, proyecto_id)
        if proyecto is None:
            raise ValidationError(f"No existe el proyecto con id={proyecto_id}.")
        return proyecto

    @staticmethod
    def crear(
        session: Session,
        codigo: str,
        nombre: str,
        sector: str = "",
        pliego: str = "",
        programa: str = "",
        meta: str = "",
        usuario_actual: str = "sistema",
    ) -> Proyecto:
        codigo = validar_codigo_proyecto(codigo)
        nombre = require_not_empty(nombre, "Nombre")
        if session.query(Proyecto).filter_by(codigo=codigo).one_or_none():
            raise ValidationError(f"Ya existe un proyecto con código '{codigo}'.")

        proyecto = Proyecto(
            codigo=codigo, nombre=nombre, sector=sector or None,
            pliego=pliego or None, programa=programa or None, meta=meta or None,
        )
        session.add(proyecto)
        session.flush()
        session.add(Auditoria(usuario=usuario_actual, accion="CREAR", entidad="Proyecto",
                               detalle=f"codigo={codigo}"))
        return proyecto

    @staticmethod
    def editar(session: Session, proyecto_id: int, usuario_actual: str = "sistema", **campos) -> Proyecto:
        proyecto = ProyectoService.obtener(session, proyecto_id)
        if "nombre" in campos:
            campos["nombre"] = require_not_empty(campos["nombre"], "Nombre")
        for clave, valor in campos.items():
            if hasattr(proyecto, clave):
                setattr(proyecto, clave, valor or None)
        session.add(Auditoria(usuario=usuario_actual, accion="EDITAR", entidad="Proyecto",
                               detalle=f"id={proyecto_id}"))
        return proyecto

    @staticmethod
    def eliminar(session: Session, proyecto_id: int, usuario_actual: str = "sistema") -> None:
        proyecto = ProyectoService.obtener(session, proyecto_id)
        session.delete(proyecto)
        session.add(Auditoria(usuario=usuario_actual, accion="ELIMINAR", entidad="Proyecto",
                               detalle=f"id={proyecto_id} codigo={proyecto.codigo}"))
