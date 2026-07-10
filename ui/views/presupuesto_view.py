# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.presupuesto_controller import PresupuestoController
from controllers.proyecto_controller import ProyectoController
from utils.logger import get_logger

logger = get_logger(__name__)

COLUMNAS = [
    "Proyecto", "Clasificador", "Descripción", "Meta", "PIA", "PIM",
    "Certificado", "Comprometido", "Devengado", "Saldo Devengado", "% Avance",
]


class PresupuestoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()
        self.cargar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titulo = QLabel("Presupuesto")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        header.addWidget(titulo)
        header.addStretch()

        self.combo_proyecto = QComboBox()
        self.combo_proyecto.setFixedWidth(220)
        self.combo_proyecto.currentIndexChanged.connect(self.cargar_datos)
        header.addWidget(self.combo_proyecto)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar clasificador o descripción...")
        self.input_busqueda.setFixedWidth(260)
        self.input_busqueda.textChanged.connect(self.cargar_datos)
        header.addWidget(self.input_busqueda)

        btn_exportar = QPushButton("Exportar a Excel")
        btn_exportar.clicked.connect(self._exportar_excel)
        header.addWidget(btn_exportar)
        layout.addLayout(header)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

    def _proyecto_id_actual(self) -> int | None:
        return self.combo_proyecto.currentData()

    def _refrescar_combo_proyectos(self) -> None:
        actual = self.combo_proyecto.currentData()
        self.combo_proyecto.blockSignals(True)
        self.combo_proyecto.clear()
        self.combo_proyecto.addItem("Todos los proyectos", None)
        for p in ProyectoController.listar():
            self.combo_proyecto.addItem(f"{p.codigo} - {p.nombre[:30]}", p.id)
        idx = self.combo_proyecto.findData(actual)
        self.combo_proyecto.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_proyecto.blockSignals(False)

    def cargar_datos(self) -> None:
        self._refrescar_combo_proyectos()
        try:
            registros = PresupuestoController.listar(
                proyecto_id=self._proyecto_id_actual(),
                texto_busqueda=self.input_busqueda.text(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("Error listando presupuesto")
            return

        self.tabla.setRowCount(len(registros))
        for fila, r in enumerate(registros):
            valores = [
                r.proyecto.codigo if r.proyecto else "-",
                r.clasificador or "-",
                r.descripcion or "-",
                r.meta or "-",
                f"{r.pia:,.2f}",
                f"{r.pim:,.2f}",
                f"{r.certificacion:,.2f}",
                f"{r.compromiso:,.2f}",
                f"{r.devengado:,.2f}",
                f"{r.saldo_devengado:,.2f}",
                f"{r.porcentaje_avance:.2f}%",
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))

    def _exportar_excel(self) -> None:
        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar presupuesto", "presupuesto_export.xlsx", "Excel (*.xlsx)"
        )
        if not destino:
            return
        try:
            PresupuestoController.exportar_excel(destino, proyecto_id=self._proyecto_id_actual())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error exportando presupuesto")
            QMessageBox.critical(self, "Error", f"No se pudo exportar: {exc}")
            return
        QMessageBox.information(self, "Exportación exitosa", f"Archivo generado:\n{destino}")
