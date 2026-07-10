# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

MODULOS = [
    ("Dashboard", "dashboard"),
    ("Proyectos", "proyectos"),
    ("Presupuesto", "presupuesto"),
    ("Importar Excel", "importar"),
    ("Importar Metas", "importar_meta"),
    ("Reportes", "reportes"),
    ("Configuración", "configuracion"),
]


class Sidebar(QWidget):
    modulo_seleccionado = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lista = QListWidget()
        for texto, clave in MODULOS:
            item = QListWidgetItem(texto)
            item.setData(1000, clave)
            self.lista.addItem(item)

        self.lista.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.lista)

        self.lista.setCurrentRow(0)

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        clave = self.lista.item(row).data(1000)
        self.modulo_seleccionado.emit(clave)

    def ocultar_modulo(self, clave: str) -> None:
        """Oculta un módulo según permisos de rol (p.ej. Configuración solo ADMIN)."""
        for i in range(self.lista.count()):
            if self.lista.item(i).data(1000) == clave:
                self.lista.item(i).setHidden(True)
                break
