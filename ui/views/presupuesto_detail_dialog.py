# -*- coding: utf-8 -*-
"""Vista de detalles de partida presupuestal con estructura jerárquica."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class PresupuestoDetailDialog(QDialog):
    """Diálogo que muestra todos los detalles de un registro de Presupuesto."""

    def __init__(self, presupuesto, parent=None):
        super().__init__(parent)
        self.presupuesto = presupuesto
        self.setWindowTitle("Detalles de Partida Presupuestal")
        self.setMinimumWidth(600)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Formulario con los detalles
        form = QFormLayout()
        form.setSpacing(12)

        # Información básica
        form.addRow(QLabel("<b>PROYECTO</b>"), QLabel(""))
        proyecto_texto = f"{self.presupuesto.proyecto.codigo} - {self.presupuesto.proyecto.nombre}" if self.presupuesto.proyecto else "-"
        form.addRow(QLabel("Proyecto:"), QLabel(proyecto_texto))

        # Estructura presupuestal
        form.addRow(QLabel("<b>ESTRUCTURA PRESUPUESTAL</b>"), QLabel(""))
        form.addRow(QLabel("Rubro:"), QLabel(self.presupuesto.rubro or "-"))
        form.addRow(QLabel("Meta (0035):"), QLabel(self.presupuesto.meta or "-"))
        form.addRow(QLabel("Programa (0066):"), QLabel(self.presupuesto.programa or "-"))
        form.addRow(QLabel("Producto (3000001):"), QLabel(self.presupuesto.producto or "-"))

        # Actividad/AI/Obra
        form.addRow(QLabel("<b>ACTIVIDAD / AI / OBRA</b>"), QLabel(""))
        form.addRow(QLabel("Actividad / AI / Obra (código):"), QLabel(self.presupuesto.actividad_codigo or "-"))
        actividad_desc = self.presupuesto.actividad_descripcion or "-"
        form.addRow(QLabel("Descripción de actividad:"), QLabel(actividad_desc))

        # Clasificadores funcionales (MEF)
        form.addRow(QLabel("Función (22):"), QLabel(self.presupuesto.funcion or "-"))
        form.addRow(QLabel("División Funcional (048):"), QLabel(self.presupuesto.division_funcional or "-"))
        form.addRow(QLabel("Grupo Funcional (0109):"), QLabel(self.presupuesto.grupo_funcional or "-"))

        # Clasificador de gasto
        form.addRow(QLabel("<b>CLASIFICADOR DE GASTO</b>"), QLabel(""))
        form.addRow(QLabel("Código (normalizado):"), QLabel(self.presupuesto.clasificador or "-"))
        form.addRow(QLabel("Código (original):"), QLabel(self.presupuesto.clasificador_original or "-"))
        form.addRow(QLabel("Descripción:"), QLabel(self.presupuesto.descripcion or "-"))

        # Ejecución presupuestal
        form.addRow(QLabel("<b>EJECUCION PRESUPUESTAL</b>"), QLabel(""))
        form.addRow(QLabel("Año:"), QLabel(str(self.presupuesto.anio)))
        if self.presupuesto.mes:
            form.addRow(QLabel("Mes:"), QLabel(str(self.presupuesto.mes)))
        form.addRow(QLabel("PIA:"), QLabel(f"{self.presupuesto.pia:,.2f}"))
        form.addRow(QLabel("PIM:"), QLabel(f"{self.presupuesto.pim:,.2f}"))
        form.addRow(QLabel("Certificación:"), QLabel(f"{self.presupuesto.certificacion:,.2f}"))
        form.addRow(QLabel("Compromiso:"), QLabel(f"{self.presupuesto.compromiso:,.2f}"))
        form.addRow(QLabel("Devengado:"), QLabel(f"{self.presupuesto.devengado:,.2f}"))
        form.addRow(QLabel("Saldo Devengado:"), QLabel(f"{self.presupuesto.saldo_devengado:,.2f}"))
        form.addRow(QLabel("% Avance:"), QLabel(f"{self.presupuesto.porcentaje_avance * 100:.2f}%"))

        # Información de importación
        form.addRow(QLabel("<b>AUDITORIA</b>"), QLabel(""))
        form.addRow(QLabel("Fecha Importación:"), QLabel(self.presupuesto.fecha_importacion.strftime("%Y-%m-%d %H:%M:%S")))
        if self.presupuesto.archivo_origen:
            form.addRow(QLabel("Archivo Origen:"), QLabel(self.presupuesto.archivo_origen))

        layout.addLayout(form)

        # Botones
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
