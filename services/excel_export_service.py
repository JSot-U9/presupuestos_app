# -*- coding: utf-8 -*-
"""Exportación de datos de Presupuesto/Proyectos a Excel (openpyxl)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from models.presupuesto import Presupuesto
from models.proyecto import Proyecto

COLUMNAS_PRESUPUESTO = [
    "Proyecto", "Rubro", "Programa", "Meta", "Categoria", "Clasificador",
    "Descripcion", "PIA", "PIM", "Certificacion", "Compromiso", "Devengado",
    "Saldo_Certificacion", "Saldo_Compromiso", "Saldo_Devengado", "% Avance",
]


def exportar_presupuesto_excel(registros: list[Presupuesto], destino: str | Path) -> Path:
    filas = [
        {
            "Proyecto": r.proyecto.codigo if r.proyecto else "",
            "Rubro": r.rubro,
            "Programa": r.programa,
            "Meta": r.meta,
            "Categoria": r.categoria,
            "Clasificador": r.clasificador,
            "Descripcion": r.descripcion,
            "PIA": r.pia,
            "PIM": r.pim,
            "Certificacion": r.certificacion,
            "Compromiso": r.compromiso,
            "Devengado": r.devengado,
            "Saldo_Certificacion": r.saldo_certificacion,
            "Saldo_Compromiso": r.saldo_compromiso,
            "Saldo_Devengado": r.saldo_devengado,
            "% Avance": r.porcentaje_avance,
        }
        for r in registros
    ]
    df = pd.DataFrame(filas, columns=COLUMNAS_PRESUPUESTO)
    destino = Path(destino)
    df.to_excel(destino, index=False, engine="openpyxl")
    return destino


def exportar_proyectos_excel(proyectos: list[Proyecto], destino: str | Path) -> Path:
    filas = [
        {
            "Codigo": p.codigo,
            "Nombre": p.nombre,
            "Sector": p.sector,
            "Pliego": p.pliego,
            "Programa": p.programa,
            "Meta": p.meta,
            "Estado": p.estado,
            "Fecha Creacion": p.fecha_creacion,
        }
        for p in proyectos
    ]
    df = pd.DataFrame(filas)
    destino = Path(destino)
    df.to_excel(destino, index=False, engine="openpyxl")
    return destino
