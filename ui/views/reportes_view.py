# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.dashboard_controller import DashboardController
from controllers.presupuesto_controller import PresupuestoController
from utils.logger import get_logger

logger = get_logger(__name__)


class ReportesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        titulo = QLabel("Reportes")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(titulo)

        grid = QGridLayout()
        grid.setSpacing(14)

        botones = [
            ("Exportar Presupuesto a Excel", self._exportar_presupuesto_excel),
            ("Exportar Proyectos a Excel", self._exportar_proyectos_excel),
            ("Generar Reporte PDF de Ejecución", self._generar_pdf),
        ]
        for i, (texto, callback) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setMinimumHeight(60)
            btn.clicked.connect(callback)
            grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(grid)
        layout.addStretch()

    def _exportar_presupuesto_excel(self) -> None:
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar presupuesto", "presupuesto.xlsx", "Excel (*.xlsx)"
        )
        if not destino:
            return
        try:
            PresupuestoController.exportar_excel(destino)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error exportando presupuesto")
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {exc}")
            return
        QMessageBox.information(self, "Éxito", f"Archivo generado:\n{destino}")

    def _exportar_proyectos_excel(self) -> None:
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar proyectos", "proyectos.xlsx", "Excel (*.xlsx)"
        )
        if not destino:
            return
        try:
            DashboardController.exportar_proyectos_excel(destino)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error exportando proyectos")
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {exc}")
            return
        QMessageBox.information(self, "Éxito", f"Archivo generado:\n{destino}")

    def _generar_pdf(self) -> None:
        destino, _ = QFileDialog.getSaveFileName(
            self, "Generar reporte PDF", "reporte_ejecucion.pdf", "PDF (*.pdf)"
        )
        if not destino:
            return
        try:
            DashboardController.generar_pdf_ejecucion(destino)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error generando PDF")
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {exc}")
            return
        QMessageBox.information(self, "Éxito", f"Reporte generado:\n{destino}")
