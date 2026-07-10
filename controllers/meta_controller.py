# -*- coding: utf-8 -*-
from __future__ import annotations

from database.connection import get_session
from models.meta_presupuesto import MetaPresupuesto
from services.meta_import_service import MetaImportError, MetaImportService

__all__ = ["MetaController", "MetaImportError"]


class MetaController:
    @staticmethod
    def importar_metas(ruta_archivo: str) -> int:
        with get_session() as session:
            return MetaImportService.importar(ruta_archivo, session)

    @staticmethod
    def contar() -> int:
        with get_session() as session:
            return session.query(MetaPresupuesto).count()
