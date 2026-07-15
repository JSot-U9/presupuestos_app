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
    "Proyecto", "Rubro", "Meta", "Programa", "Producto", "Actividad / AI / Obra",
    "Clasif. Presu.", "Clasificador de gasto", "Descripción", "Función", "División Funcional", "Grupo Funcional",
    "PIM", "Certificado", "Devengado", "% Avance",
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

        # Filtros distribuidos en 2 filas
        filtros_container = QVBoxLayout()
        filtros_container.setSpacing(8)

        # --- Fila 1: identificación del proyecto (Meta, Programa, Producto, Actividad) ---
        fila1 = QHBoxLayout()
        fila1.setSpacing(12)
        fila1.addWidget(QLabel("🔍 Filtros:"))

        # Meta (prioritario)
        self.combo_meta = QComboBox()
        self.combo_meta.setFixedWidth(140)
        self.combo_meta.currentIndexChanged.connect(self.cargar_datos)
        fila1.addWidget(QLabel("Meta:"))
        fila1.addWidget(self.combo_meta)

        self.combo_programa = QComboBox()
        self.combo_programa.setFixedWidth(120)
        self.combo_programa.currentIndexChanged.connect(self.cargar_datos)
        fila1.addWidget(QLabel("Programa:"))
        fila1.addWidget(self.combo_programa)

        self.combo_producto = QComboBox()
        self.combo_producto.setFixedWidth(140)
        self.combo_producto.currentIndexChanged.connect(self.cargar_datos)
        fila1.addWidget(QLabel("Producto:"))
        fila1.addWidget(self.combo_producto)

        self.combo_actividad = QComboBox()
        self.combo_actividad.setFixedWidth(140)
        self.combo_actividad.currentIndexChanged.connect(self.cargar_datos)
        fila1.addWidget(QLabel("Act/AI/Obra:"))
        fila1.addWidget(self.combo_actividad)

        fila1.addStretch()

        # --- Fila 2: clasificación funcional y presupuestal + acciones ---
        fila2 = QHBoxLayout()
        fila2.setSpacing(12)

        self.combo_funcion = QComboBox()
        self.combo_funcion.setFixedWidth(100)
        self.combo_funcion.currentIndexChanged.connect(self.cargar_datos)
        fila2.addWidget(QLabel("Función:"))
        fila2.addWidget(self.combo_funcion)

        self.combo_division_funcional = QComboBox()
        self.combo_division_funcional.setFixedWidth(120)
        self.combo_division_funcional.currentIndexChanged.connect(self.cargar_datos)
        fila2.addWidget(QLabel("División Funcional:"))
        fila2.addWidget(self.combo_division_funcional)

        self.combo_grupo_funcional = QComboBox()
        self.combo_grupo_funcional.setFixedWidth(120)
        self.combo_grupo_funcional.currentIndexChanged.connect(self.cargar_datos)
        fila2.addWidget(QLabel("Grupo Funcional:"))
        fila2.addWidget(self.combo_grupo_funcional)

        self.combo_rubro = QComboBox()
        self.combo_rubro.setFixedWidth(200)
        self.combo_rubro.currentIndexChanged.connect(self.cargar_datos)
        fila2.addWidget(QLabel("Rubro:"))
        fila2.addWidget(self.combo_rubro)

        self.combo_clasi_presu = QComboBox()
        self.combo_clasi_presu.setFixedWidth(100)
        self.combo_clasi_presu.currentIndexChanged.connect(self.cargar_datos)
        fila2.addWidget(QLabel("Clasif. Presu.:"))
        fila2.addWidget(self.combo_clasi_presu)

        btn_limpiar = QPushButton("🔄 Limpiar Filtros")
        btn_limpiar.setFixedWidth(130)
        btn_limpiar.clicked.connect(self._limpiar_filtros)
        fila2.addWidget(btn_limpiar)

        fila2.addStretch()

        # Indicador de filtros activos
        self.label_filtros_activos = QLabel()
        self.label_filtros_activos.setStyleSheet("color: #ff7700; font-weight: 600;")
        self.label_filtros_activos.setWordWrap(True)
        fila2.addWidget(self.label_filtros_activos)

        filtros_container.addLayout(fila1)
        filtros_container.addLayout(fila2)
        layout.addLayout(filtros_container)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._mostrar_detalles)
        self.tabla.itemSelectionChanged.connect(self._actualizar_totales_seleccion)
        layout.addWidget(self.tabla)

        self.label_totales = QLabel("Seleccione un clasificador para ver el total de todas las filas.")
        self.label_totales.setStyleSheet("color: #333; font-weight: 600;")
        layout.addWidget(self.label_totales)

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

    def _limpiar_filtros(self) -> None:
        """Limpia todos los filtros y muestra todos los registros."""
        self.combo_proyecto.setCurrentIndex(0)
        self.combo_meta.setCurrentIndex(0)
        self.combo_programa.setCurrentIndex(0)
        self.combo_producto.setCurrentIndex(0)
        self.combo_actividad.setCurrentIndex(0)
        self.combo_funcion.setCurrentIndex(0)
        self.combo_division_funcional.setCurrentIndex(0)
        self.combo_grupo_funcional.setCurrentIndex(0)
        self.combo_rubro.setCurrentIndex(0)
        self.combo_clasi_presu.setCurrentIndex(0)
        self.input_busqueda.clear()
        self.cargar_datos()

    def _refrescar_filtros(self) -> None:
        filtros = {
            "proyecto_id": self._proyecto_id_actual(),
            "texto_busqueda": self.input_busqueda.text(),
            "meta": self.combo_meta.currentData(),
            "programa": self.combo_programa.currentData(),
            "producto": self.combo_producto.currentData(),
            "actividad_codigo": self.combo_actividad.currentData(),
            "funcion": self.combo_funcion.currentData(),
            "division_funcional": self.combo_division_funcional.currentData(),
            "grupo_funcional": self.combo_grupo_funcional.currentData(),
            "rubro": self.combo_rubro.currentData(),
            "clasi_presu": self.combo_clasi_presu.currentData(),
        }

        def actualizar(combo: QComboBox, etiqueta_todos: str, campo: str) -> None:
            actual = filtros[campo]
            filtros_para_opciones = {k: v for k, v in filtros.items() if k != campo}
            valores = PresupuestoController.listar_valores_filtro(campo, **filtros_para_opciones)
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(etiqueta_todos, None)
            for valor in valores:
                combo.addItem(valor, valor)
            indice = combo.findData(actual)
            combo.setCurrentIndex(indice if indice >= 0 else 0)
            combo.blockSignals(False)

        # Cada selector conserva su valor, pero sus alternativas se limitan a
        # los registros compatibles con todos los demás clasificadores activos.
        actualizar(self.combo_meta, "Todas las metas", "meta")
        actualizar(self.combo_programa, "Todos los prog.", "programa")
        actualizar(self.combo_producto, "Todos los productos", "producto")
        actualizar(self.combo_actividad, "Todas las actividades", "actividad_codigo")
        actualizar(self.combo_funcion, "Todas", "funcion")
        actualizar(self.combo_division_funcional, "Todas", "division_funcional")
        actualizar(self.combo_grupo_funcional, "Todos", "grupo_funcional")
        actualizar(self.combo_rubro, "Todos los rubros", "rubro")
        actualizar(self.combo_clasi_presu, "Todas", "clasi_presu")

    def cargar_datos(self) -> None:
        self._refrescar_combo_proyectos()
        self._refrescar_filtros()
        try:
            registros = PresupuestoController.listar(
                proyecto_id=self._proyecto_id_actual(),
                texto_busqueda=self.input_busqueda.text(),
                meta=self.combo_meta.currentData(),
                programa=self.combo_programa.currentData(),
                producto=self.combo_producto.currentData(),
                actividad_codigo=self.combo_actividad.currentData(),
                funcion=self.combo_funcion.currentData(),
                division_funcional=self.combo_division_funcional.currentData(),
                grupo_funcional=self.combo_grupo_funcional.currentData(),
                rubro=self.combo_rubro.currentData(),
                categoria=None,
                clasi_presu=self.combo_clasi_presu.currentData(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("Error listando presupuesto")
            return

        self._registros_actuales = registros
        self.tabla.setRowCount(len(registros))
        for fila, r in enumerate(registros):
            valores = [
                r.proyecto.codigo if r.proyecto else "-",
                r.rubro or "-",
                r.meta or "-",
                r.programa or "-",
                r.producto or "-",
                r.actividad_codigo or "-",
                r.clasi_presu or "-",
                r.clasificador or "-",
                r.descripcion or "-",
                r.funcion or "-",
                r.division_funcional or "-",
                r.grupo_funcional or "-",
                f"{r.pim:,.2f}",
                f"{r.certificacion:,.2f}",
                f"{r.devengado:,.2f}",
                f"{r.porcentaje_avance * 100:.2f}%",
            ]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))

        # Actualizar indicador de filtros activos
        self._actualizar_indicador_filtros(len(registros))
        self._actualizar_totales_seleccion()

    def _actualizar_indicador_filtros(self, total_registros: int) -> None:
        """Actualiza el indicador visual de filtros activos."""
        filtros_activos = []

        if self.combo_meta.currentData() is not None:
            filtros_activos.append(f"Meta: {self.combo_meta.currentText()}")
        if self.combo_programa.currentData() is not None:
            filtros_activos.append(f"Programa: {self.combo_programa.currentText()}")
        if self.combo_producto.currentData() is not None:
            filtros_activos.append(f"Producto: {self.combo_producto.currentText()}")
        if self.combo_actividad.currentData() is not None:
            filtros_activos.append(f"Actividad: {self.combo_actividad.currentText()}")
        if self.combo_funcion.currentData() is not None:
            filtros_activos.append(f"Función: {self.combo_funcion.currentText()}")
        if self.combo_division_funcional.currentData() is not None:
            filtros_activos.append(f"Div. Funcional: {self.combo_division_funcional.currentText()}")
        if self.combo_grupo_funcional.currentData() is not None:
            filtros_activos.append(f"\nGrupo Func.: {self.combo_grupo_funcional.currentText()}")
        if self.combo_rubro.currentData() is not None:
            filtros_activos.append(f"Rubro: {self.combo_rubro.currentText()[:20]}")
        if self.combo_clasi_presu.currentData() is not None:
            filtros_activos.append(f"Clasif. Presu.: {self.combo_clasi_presu.currentText()}")
        if self.input_busqueda.text().strip():
            filtros_activos.append(f"Búsqueda: '{self.input_busqueda.text()}'")

        if filtros_activos:
            texto = "  |  ".join(filtros_activos) + f"  →  {total_registros} registro(s)"
            self.label_filtros_activos.setText(texto)
            self.label_filtros_activos.setStyleSheet("color: #ff7700; font-weight: 600;")
        else:
            self.label_filtros_activos.setText(f"Mostrando {total_registros} registro(s)")
            self.label_filtros_activos.setStyleSheet("color: #666; font-weight: 500;")

    def _actualizar_totales_seleccion(self) -> None:
        """Actualiza el texto de totales cuando se selecciona un clasificador."""
        seleccion = self.tabla.selectionModel().selectedRows()
        if not seleccion:
            self.label_totales.setText("Seleccione un clasificador para ver el total de todas las filas.")
            return

        total_pim = 0.0
        total_certificado = 0.0
        total_devengado = 0.0
        for registro in self._registros_actuales:
            total_pim += registro.pim or 0.0
            total_certificado += registro.certificacion or 0.0
            total_devengado += registro.devengado or 0.0

        self.label_totales.setText(
            f"Total de todas las filas → PIM: {total_pim:,.2f} | Certificado: {total_certificado:,.2f} | Devengado: {total_devengado:,.2f}"
        )

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
