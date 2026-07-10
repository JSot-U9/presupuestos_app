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
from ui.views.presupuesto_detail_dialog import PresupuestoDetailDialog
from utils.logger import get_logger

logger = get_logger(__name__)

COLUMNAS = [
    "Proyecto", "Meta", "Programa", "Producto", "Actividad", "Clasificador", 
    "Descripción", "Función", "PIM", "Certificado", "Devengado", "% Avance",
]


class PresupuestoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._registros_actuales = []  # Guardar referencia a registros para abrir detalles
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
        self.combo_proyecto.currentIndexChanged.connect(self._on_filtro_cambiado)
        header.addWidget(self.combo_proyecto)

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar clasificador o descripción...")
        self.input_busqueda.setFixedWidth(260)
        self.input_busqueda.textChanged.connect(self._on_filtro_cambiado)
        header.addWidget(self.input_busqueda)

        btn_exportar = QPushButton("Exportar a Excel")
        btn_exportar.clicked.connect(self._exportar_excel)
        header.addWidget(btn_exportar)
        layout.addLayout(header)

        filtros = QHBoxLayout()
        self.combo_meta = QComboBox()
        self.combo_meta.setFixedWidth(120)
        self.combo_meta.currentIndexChanged.connect(self.cargar_datos)
        filtros.addWidget(QLabel("Meta:"))
        filtros.addWidget(self.combo_meta)

        self.combo_programa = QComboBox()
        self.combo_programa.setFixedWidth(120)
        self.combo_programa.currentIndexChanged.connect(self.cargar_datos)
        filtros.addWidget(QLabel("Programa:"))
        filtros.addWidget(self.combo_programa)

        self.combo_funcion = QComboBox()
        self.combo_funcion.setFixedWidth(100)
        self.combo_funcion.currentIndexChanged.connect(self.cargar_datos)
        filtros.addWidget(QLabel("Función:"))
        filtros.addWidget(self.combo_funcion)

        self.combo_rubro = QComboBox()
        self.combo_rubro.setFixedWidth(220)
        self.combo_rubro.currentIndexChanged.connect(self.cargar_datos)
        filtros.addWidget(QLabel("Rubro:"))
        filtros.addWidget(self.combo_rubro)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._mostrar_detalles)
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

    def _on_filtro_cambiado(self) -> None:
        self.cargar_datos()

    def _refrescar_filtros(self) -> None:
        proyecto_id = self._proyecto_id_actual()
        meta_actual = self.combo_meta.currentData()
        programa_actual = self.combo_programa.currentData()
        funcion_actual = self.combo_funcion.currentData()
        rubro_actual = self.combo_rubro.currentData()

        self.combo_meta.blockSignals(True)
        self.combo_meta.clear()
        self.combo_meta.addItem("Todas las metas", None)
        for m in PresupuestoController.listar_metas():
            self.combo_meta.addItem(m, m)
        idx = self.combo_meta.findData(meta_actual)
        self.combo_meta.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_meta.blockSignals(False)

        self.combo_programa.blockSignals(True)
        self.combo_programa.clear()
        self.combo_programa.addItem("Todos los prog.", None)
        for p in PresupuestoController.listar_programas(proyecto_id):
            self.combo_programa.addItem(str(p), p)
        idx = self.combo_programa.findData(programa_actual)
        if idx >= 0:
            self.combo_programa.setCurrentIndex(idx)
        self.combo_programa.blockSignals(False)

        self.combo_funcion.blockSignals(True)
        self.combo_funcion.clear()
        self.combo_funcion.addItem("Todas", None)
        for f in PresupuestoController.listar_funciones(proyecto_id):
            self.combo_funcion.addItem(str(f), f)
        idx = self.combo_funcion.findData(funcion_actual)
        if idx >= 0:
            self.combo_funcion.setCurrentIndex(idx)
        self.combo_funcion.blockSignals(False)

        self.combo_rubro.blockSignals(True)
        self.combo_rubro.clear()
        self.combo_rubro.addItem("Todos los rubros", None)
        for r in PresupuestoController.listar_rubros(proyecto_id):
            self.combo_rubro.addItem(r, r)
        idx = self.combo_rubro.findData(rubro_actual)
        if idx >= 0:
            self.combo_rubro.setCurrentIndex(idx)
        self.combo_rubro.blockSignals(False)

    def cargar_datos(self) -> None:
        self._refrescar_combo_proyectos()
        self._refrescar_filtros()
        try:
            registros = PresupuestoController.listar(
                proyecto_id=self._proyecto_id_actual(),
                texto_busqueda=self.input_busqueda.text(),
                meta=self.combo_meta.currentData(),
                rubro=self.combo_rubro.currentData(),
                categoria=None,  # Categoría deprecada, mantenida para compatibilidad
            )
        except Exception:  # noqa: BLE001
            logger.exception("Error listando presupuesto")
            return

        self._registros_actuales = registros
        self.tabla.setRowCount(len(registros))
        for fila, r in enumerate(registros):
            valores = [
                r.proyecto.codigo if r.proyecto else "-",
                r.meta or "-",
                r.programa or "-",
                r.producto or "-",
                f"{r.actividad_codigo or '-'} ({r.actividad_descripcion[:20] if r.actividad_descripcion else '-'})",
                r.clasificador or "-",
                r.descripcion or "-",
                r.funcion or "-",
                f"{r.pim:,.2f}",
                f"{r.certificacion:,.2f}",
                f"{r.devengado:,.2f}",
                f"{r.porcentaje_avance:.2f}%",
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))

    def _mostrar_detalles(self) -> None:
        """Muestra un diálogo con todos los detalles del presupuesto seleccionado."""
        fila_actual = self.tabla.currentRow()
        if fila_actual < 0 or fila_actual >= len(self._registros_actuales):
            return
        presupuesto = self._registros_actuales[fila_actual]
        dialogo = PresupuestoDetailDialog(presupuesto, parent=self)
        dialogo.exec()

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
