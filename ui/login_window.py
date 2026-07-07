# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config import APP_NAME
from controllers.auth_controller import AuthController, AuthError
from models.usuario import Usuario
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginWindow(QDialog):
    """Diálogo de inicio de sesión. Al aceptar, `self.usuario_autenticado`
    contiene el Usuario logueado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.usuario_autenticado: Usuario | None = None
        self.setWindowTitle(f"Iniciar sesión - {APP_NAME}")
        self.setFixedSize(380, 320)
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 30, 30, 30)

        titulo = QLabel(APP_NAME)
        titulo.setStyleSheet("font-size: 17px; font-weight: 700; color: #1F4E79;")
        titulo.setWordWrap(True)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Ingrese sus credenciales")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("color: #605E5C;")
        layout.addWidget(subtitulo)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Usuario")
        layout.addWidget(self.input_usuario)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_password)

        self.btn_login = QPushButton("Ingresar")
        self.btn_login.clicked.connect(self._intentar_login)
        layout.addWidget(self.btn_login)

        ayuda = QLabel("Usuario inicial por defecto: admin / admin123")
        ayuda.setStyleSheet("color: #A19F9D; font-size: 11px;")
        ayuda.setAlignment(Qt.AlignCenter)
        layout.addWidget(ayuda)

        layout.addStretch()

    def _intentar_login(self) -> None:
        username = self.input_usuario.text().strip()
        password = self.input_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingrese usuario y contraseña.")
            return

        try:
            usuario = AuthController.login(username, password)
        except AuthError as exc:
            QMessageBox.critical(self, "Error de acceso", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado en login")
            QMessageBox.critical(self, "Error inesperado", f"Ocurrió un error: {exc}")
            return

        self.usuario_autenticado = usuario
        self.accept()
