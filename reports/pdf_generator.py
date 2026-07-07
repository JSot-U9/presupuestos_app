# -*- coding: utf-8 -*-
"""Generación de reportes PDF con reportlab: resumen de ejecución
presupuestal por proyecto."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import APP_NAME
from services.dashboard_service import DashboardKPIs


def generar_reporte_ejecucion(
    destino: str | Path,
    kpis: DashboardKPIs,
    filas_por_proyecto: list[tuple[str, float, float]],
) -> Path:
    destino = Path(destino)
    doc = SimpleDocTemplate(
        str(destino),
        pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(APP_NAME, estilos["Title"]),
        Paragraph("Reporte de Ejecución Presupuestal", estilos["Heading2"]),
        Spacer(1, 0.5 * cm),
    ]

    resumen_data = [
        ["Proyectos", "PIM Total (S/)", "Certificado (S/)", "Comprometido (S/)",
         "Devengado (S/)", "Saldo (S/)", "% Ejecución"],
        [
            str(kpis.num_proyectos),
            f"{kpis.pim_total:,.2f}",
            f"{kpis.certificado_total:,.2f}",
            f"{kpis.comprometido_total:,.2f}",
            f"{kpis.devengado_total:,.2f}",
            f"{kpis.saldo_total:,.2f}",
            f"{kpis.porcentaje_ejecucion:.2f}%",
        ],
    ]
    tabla_resumen = Table(resumen_data, hAlign="LEFT")
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph("Ejecución por Proyecto (Top 10 por PIM)", estilos["Heading3"]))

    detalle_data = [["Proyecto", "PIM (S/)", "Devengado (S/)", "% Avance"]]
    for codigo, pim, devengado in filas_por_proyecto:
        pct = (devengado / pim * 100.0) if pim else 0.0
        detalle_data.append([codigo, f"{pim:,.2f}", f"{devengado:,.2f}", f"{pct:.2f}%"])

    tabla_detalle = Table(detalle_data, hAlign="LEFT")
    tabla_detalle.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    elementos.append(tabla_detalle)

    doc.build(elementos)
    return destino
