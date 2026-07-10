# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.meta_controller import MetaController, MetaImportError
from utils.logger import get_logger

logger = get_logger(__name__)


class ImportMetaWorker(QObject):
    progreso = Signal(int, str)
    finalizado = Signal(int)
    error = Signal(str)

    def __init__(self, ruta: str):
        super().__init__()
        self.ruta = ruta

    def ejecutar(self) -> None:
        try:
            self.progreso.emit(10, "Leyendo archivo...")
            cantidad = MetaController.importar_metas(self.ruta)
            self.progreso.emit(100, "Importación completada.")
        except MetaImportError as exc:
            self.error.emit(str(exc))
        except Exception as exc:
            logger.exception("Error inesperado durante la importación de metas")
            self.error.emit(f"Error inesperado: {exc}")
        else:
            self.finalizado.emit(cantidad)


class ImportarMetaView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hilo: QThread | None = None
        self._worker: ImportMetaWorker | None = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Importar Metas Presupuestales")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Importa el archivo rptMetaPresupuestal (.xls) para actualizar "
            "el catálogo de metas. Todas las metas existentes serán "
            "reemplazadas por los datos del archivo."
        )
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: #605E5C;")
        layout.addWidget(subtitulo)

        fila_archivo = QHBoxLayout()
        self.input_archivo = QLineEdit()
        self.input_archivo.setReadOnly(True)
        btn_examinar = QPushButton("Examinar...")
        btn_examinar.setObjectName("SecondaryButton")
        btn_examinar.clicked.connect(self._seleccionar_archivo)
        fila_archivo.addWidget(self.input_archivo)
        fila_archivo.addWidget(btn_examinar)
        layout.addLayout(fila_archivo)

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
            self, "Seleccionar rptMetaPresupuestal", "", "Excel (*.xls *.xlsx)"
        )
        if ruta:
            self.input_archivo.setText(ruta)

    def _iniciar_importacion(self) -> None:
        ruta = self.input_archivo.text().strip()
        if not ruta:
            QMessageBox.warning(self, "Datos incompletos", "Seleccione un archivo.")
            return

        self.btn_importar.setEnabled(False)
        self.barra_progreso.setValue(0)
        self.log.clear()
        self._log("Iniciando importación...")

        self._hilo = QThread(self)
        self._worker = ImportMetaWorker(ruta=ruta)
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

    def _on_finalizado(self, cantidad: int) -> None:
        self._log(f"Importación completada: {cantidad} metas registradas.")
        QMessageBox.information(
            self, "Importación exitosa",
            f"Se importaron {cantidad} metas correctamente."
        )

    def _on_error(self, mensaje: str) -> None:
        self._log(f"ERROR: {mensaje}")
        QMessageBox.critical(self, "Error de importación", mensaje)

    def _on_hilo_finalizado(self) -> None:
        self.btn_importar.setEnabled(True)

    def _log(self, mensaje: str) -> None:
        self.log.append(mensaje)
