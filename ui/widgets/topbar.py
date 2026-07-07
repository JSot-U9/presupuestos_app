# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from config import APP_NAME


class TopBar(QWidget):
    def __init__(self, nombre_usuario: str, rol: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        titulo = QLabel(APP_NAME)
        titulo.setObjectName("TopBarTitle")
        layout.addWidget(titulo)
        layout.addStretch()

        usuario_label = QLabel(f"{nombre_usuario}  ·  {rol}")
        usuario_label.setStyleSheet("color: white;")
        layout.addWidget(usuario_label)

        self.btn_salir = QPushButton("Cerrar sesión")
        self.btn_salir.setObjectName("SecondaryButton")
        self.btn_salir.setStyleSheet(
            "background-color: transparent; color: white; border: 1px solid white;"
        )
        layout.addWidget(self.btn_salir)
