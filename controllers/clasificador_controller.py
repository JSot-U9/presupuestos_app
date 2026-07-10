# -*- coding: utf-8 -*-
from __future__ import annotations

from database.connection import get_session
from services.clasificador_service import CatalogoImportError, ClasificadorService

__all__ = ["ClasificadorController", "CatalogoImportError"]


class ClasificadorController:
    @staticmethod
    def importar_catalogo(ruta_archivo: str) -> int:
        with get_session() as session:
            return ClasificadorService.importar_catalogo(ruta_archivo, session)

    @staticmethod
    def contar(anio: int | None = None) -> int:
        with get_session() as session:
            return ClasificadorService.contar(session, anio)
