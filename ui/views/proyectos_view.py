# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
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

from controllers.proyecto_controller import ProyectoController
from models.proyecto import Proyecto
from utils.logger import get_logger
from utils.validators import ValidationError

logger = get_logger(__name__)


class ProyectoDialog(QDialog):
    """Formulario de creación/edición de Proyecto con validación."""

    def __init__(self, proyecto: Proyecto | None = None, parent=None):
        super().__init__(parent)
        self.proyecto = proyecto
        self.setWindowTitle("Editar proyecto" if proyecto else "Nuevo proyecto")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_codigo = QLineEdit(proyecto.codigo if proyecto else "")
        self.input_codigo.setEnabled(proyecto is None)  # el código no se edita luego de creado
        self.input_nombre = QLineEdit(proyecto.nombre if proyecto else "")
        self.input_sector = QLineEdit(proyecto.sector or "" if proyecto else "")
        self.input_pliego = QLineEdit(proyecto.pliego or "" if proyecto else "")
        self.input_programa = QLineEdit(proyecto.programa or "" if proyecto else "")
        self.input_meta = QLineEdit(proyecto.meta or "" if proyecto else "")

        form.addRow("Código *", self.input_codigo)
        form.addRow("Nombre *", self.input_nombre)
        form.addRow("Sector", self.input_sector)
        form.addRow("Pliego", self.input_pliego)
        form.addRow("Programa", self.input_programa)
        form.addRow("Meta", self.input_meta)
        layout.addLayout(form)

        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("SecondaryButton")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._guardar)
        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addLayout(botones)

    def _guardar(self) -> None:
        self.datos = dict(
            codigo=self.input_codigo.text(),
            nombre=self.input_nombre.text(),
            sector=self.input_sector.text(),
            pliego=self.input_pliego.text(),
            programa=self.input_programa.text(),
            meta=self.input_meta.text(),
        )
        self.accept()


class ProyectosView(QWidget):
    COLUMNAS = ["ID", "Código", "Nombre", "Sector", "Programa", "Estado"]

    def __init__(self, usuario_actual: str, parent=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self._construir_ui()
        self.cargar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titulo = QLabel("Proyectos")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        header.addWidget(titulo)
        header.addStretch()

        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por código o nombre...")
        self.input_busqueda.setFixedWidth(280)
        self.input_busqueda.textChanged.connect(self.cargar_datos)
        header.addWidget(self.input_busqueda)

        btn_nuevo = QPushButton("+ Nuevo proyecto")
        btn_nuevo.clicked.connect(self._crear_proyecto)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        self.tabla = QTableWidget(0, len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.setColumnHidden(0, True)
        layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        btn_editar = QPushButton("Editar")
        btn_editar.setObjectName("SecondaryButton")
        btn_editar.clicked.connect(self._editar_proyecto)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setObjectName("SecondaryButton")
        btn_eliminar.clicked.connect(self._eliminar_proyecto)
        acciones.addWidget(btn_editar)
        acciones.addWidget(btn_eliminar)
        acciones.addStretch()
        layout.addLayout(acciones)

    def cargar_datos(self) -> None:
        texto = self.input_busqueda.text()
        try:
            proyectos = ProyectoController.listar(texto)
        except Exception:  # noqa: BLE001
            logger.exception("Error listando proyectos")
            return

        self.tabla.setRowCount(len(proyectos))
        for fila, p in enumerate(proyectos):
            valores = [str(p.id), p.codigo, p.nombre, p.sector or "-", p.programa or "-", p.estado]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.UserRole, p.id)
                self.tabla.setItem(fila, col, item)

    def _fila_seleccionada_id(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        return int(self.tabla.item(fila, 0).text())

    def _crear_proyecto(self) -> None:
        dialogo = ProyectoDialog(parent=self)
        if dialogo.exec() == QDialog.Accepted:
            try:
                ProyectoController.crear(self.usuario_actual, **dialogo.datos)
            except ValidationError as exc:
                QMessageBox.warning(self, "Datos inválidos", str(exc))
                return
            except Exception:  # noqa: BLE001
                logger.exception("Error creando proyecto")
                QMessageBox.critical(self, "Error", "No se pudo crear el proyecto.")
                return
            self.cargar_datos()

    def _editar_proyecto(self) -> None:
        proyecto_id = self._fila_seleccionada_id()
        if proyecto_id is None:
            QMessageBox.information(self, "Selección requerida", "Seleccione un proyecto.")
            return
        proyecto = ProyectoController.obtener(proyecto_id)
        dialogo = ProyectoDialog(proyecto=proyecto, parent=self)
        if dialogo.exec() == QDialog.Accepted:
            datos = dict(dialogo.datos)
            datos.pop("codigo", None)  # inmutable tras creación
            try:
                ProyectoController.editar(proyecto_id, self.usuario_actual, **datos)
            except ValidationError as exc:
                QMessageBox.warning(self, "Datos inválidos", str(exc))
                return
            except Exception:  # noqa: BLE001
                logger.exception("Error editando proyecto")
                QMessageBox.critical(self, "Error", "No se pudo editar el proyecto.")
                return
            self.cargar_datos()

    def _eliminar_proyecto(self) -> None:
        proyecto_id = self._fila_seleccionada_id()
        if proyecto_id is None:
            QMessageBox.information(self, "Selección requerida", "Seleccione un proyecto.")
            return
        respuesta = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Eliminar el proyecto y todos sus registros de presupuesto asociados?",
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            ProyectoController.eliminar(proyecto_id, self.usuario_actual)
        except Exception:  # noqa: BLE001
            logger.exception("Error eliminando proyecto")
            QMessageBox.critical(self, "Error", "No se pudo eliminar el proyecto.")
            return
        self.cargar_datos()
