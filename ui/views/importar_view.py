# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.presupuesto_controller import ExcelImportError, PresupuestoController
from utils.logger import get_logger
from utils.validators import ValidationError, require_not_empty, validar_codigo_proyecto

logger = get_logger(__name__)


class ImportWorker(QObject):
    progreso = Signal(int, str)
    finalizado = Signal(object)  # ImportResult
    error = Signal(str)

    def __init__(self, ruta: str, anio: int, mes: int, codigo: str, nombre: str):
        super().__init__()
        self.ruta = ruta
        self.anio = anio
        self.mes = mes
        self.codigo = codigo
        self.nombre = nombre

    def ejecutar(self) -> None:
        try:
            resultado = PresupuestoController.importar_excel(
                ruta_archivo=self.ruta,
                anio=self.anio,
                mes=self.mes,
                proyecto_codigo=self.codigo,
                proyecto_nombre=self.nombre,
                progress_cb=lambda pct, msg: self.progreso.emit(pct, msg),
            )
        except ExcelImportError as exc:
            self.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado durante la importación")
            self.error.emit(f"Error inesperado: {exc}")
        else:
            self.finalizado.emit(resultado)


class ImportarView(QWidget):
    """Importa reportes SIAF (celdas combinadas) usando
    services/excel_import_service.py, con barra de progreso en hilo aparte
    para no congelar la interfaz."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hilo: QThread | None = None
        self._worker: ImportWorker | None = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Importar Excel de Presupuesto (formato SIAF)")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Admite reportes con celdas combinadas (columnas PIA/PIM/Certificación/"
            "Compromiso/Devengado/Saldos/% Avance). El sistema detecta y corrige "
            "automáticamente columnas fantasma y cabeceras repetidas."
        )
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: #605E5C;")
        layout.addWidget(subtitulo)

        form = QFormLayout()
        fila_archivo = QHBoxLayout()
        self.input_archivo = QLineEdit()
        self.input_archivo.setReadOnly(True)
        btn_examinar = QPushButton("Examinar...")
        btn_examinar.setObjectName("SecondaryButton")
        btn_examinar.clicked.connect(self._seleccionar_archivo)
        fila_archivo.addWidget(self.input_archivo)
        fila_archivo.addWidget(btn_examinar)
        form.addRow("Archivo *", fila_archivo)

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Ej: 0035-0066")
        form.addRow("Código de proyecto *", self.input_codigo)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre descriptivo (opcional)")
        form.addRow("Nombre de proyecto", self.input_nombre)

        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2000, 2100)
        self.spin_anio.setValue(datetime.now().year)
        form.addRow("Año", self.spin_anio)

        self.combo_mes = QComboBox()
        self.combo_mes.addItem("(No especificar)", None)
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                 "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        for i, mes in enumerate(meses, start=1):
            self.combo_mes.addItem(mes, i)
        form.addRow("Mes de corte", self.combo_mes)

        layout.addLayout(form)

        self.btn_importar = QPushButton("Iniciar importación")
        self.btn_importar.clicked.connect(self._iniciar_importacion)
        layout.addWidget(self.btn_importar)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setValue(0)
        layout.addWidget(self.barra_progreso)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("El registro de la importación aparecerá aquí...")
        layout.addWidget(self.log, stretch=1)

    def _seleccionar_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar reporte SIAF", "", "Excel (*.xlsx *.xls)"
        )
        if ruta:
            self.input_archivo.setText(ruta)

    def _iniciar_importacion(self) -> None:
        ruta = self.input_archivo.text()
        try:
            require_not_empty(ruta, "Archivo")
            codigo = validar_codigo_proyecto(self.input_codigo.text())
        except ValidationError as exc:
            QMessageBox.warning(self, "Datos incompletos", str(exc))
            return

        self.btn_importar.setEnabled(False)
        self.barra_progreso.setValue(0)
        self.log.clear()
        self._log("Iniciando importación...")

        self._hilo = QThread(self)
        self._worker = ImportWorker(
            ruta=ruta,
            anio=self.spin_anio.value(),
            mes=self.combo_mes.currentData(),
            codigo=codigo,
            nombre=self.input_nombre.text(),
        )
        self._worker.moveToThread(self._hilo)

        self._hilo.started.connect(self._worker.ejecutar)
        self._worker.progreso.connect(self._on_progreso)
        self._worker.finalizado.connect(self._on_finalizado)
        self._worker.error.connect(self._on_error)
        self._worker.finalizado.connect(self._hilo.quit)
        self._worker.error.connect(self._hilo.quit)
        self._hilo.finished.connect(self._on_hilo_finalizado)

        self._hilo.start()

    def _on_progreso(self, pct: int, mensaje: str) -> None:
        self.barra_progreso.setValue(pct)
        self._log(mensaje)

    def _on_finalizado(self, resultado) -> None:
        self._log("--- Importación completada ---")
        self._log(f"Filas importadas: {resultado.filas_importadas}")
        self._log(f"Proyectos nuevos: {resultado.proyectos_detectados}")
        self._log(f"Columnas fusionadas por celdas combinadas: {len(resultado.columnas_fusionadas)}")
        self._log(f"Filas de encabezado duplicadas eliminadas: {resultado.filas_encabezado_eliminadas}")
        QMessageBox.information(
            self, "Importación exitosa",
            f"Se importaron {resultado.filas_importadas} partidas presupuestales.",
        )

    def _on_error(self, mensaje: str) -> None:
        self._log(f"ERROR: {mensaje}")
        QMessageBox.critical(self, "Error de importación", mensaje)

    def _on_hilo_finalizado(self) -> None:
        self.btn_importar.setEnabled(True)

    def _log(self, mensaje: str) -> None:
        self.log.append(mensaje)
