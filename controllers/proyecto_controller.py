# -*- coding: utf-8 -*-
from __future__ import annotations

from database.connection import get_session
from models.proyecto import Proyecto
from services.proyecto_service import ProyectoService


class ProyectoController:
    @staticmethod
    def listar(texto_busqueda: str = "", estado: str | None = None) -> list[Proyecto]:
        with get_session() as session:
            proyectos = ProyectoService.listar(session, texto_busqueda, estado)
            for p in proyectos:
                session.expunge(p)
            return proyectos

    @staticmethod
    def crear(usuario_actual: str, **datos) -> Proyecto:
        with get_session() as session:
            proyecto = ProyectoService.crear(session, usuario_actual=usuario_actual, **datos)
            session.flush()
            proyecto_id = proyecto.id
        return ProyectoController.obtener(proyecto_id)

    @staticmethod
    def editar(proyecto_id: int, usuario_actual: str, **campos) -> Proyecto:
        with get_session() as session:
            ProyectoService.editar(session, proyecto_id, usuario_actual=usuario_actual, **campos)
        return ProyectoController.obtener(proyecto_id)

    @staticmethod
    def eliminar(proyecto_id: int, usuario_actual: str) -> None:
        with get_session() as session:
            ProyectoService.eliminar(session, proyecto_id, usuario_actual=usuario_actual)

    @staticmethod
    def obtener(proyecto_id: int) -> Proyecto:
        with get_session() as session:
            proyecto = ProyectoService.obtener(session, proyecto_id)
            session.expunge(proyecto)
            return proyecto
