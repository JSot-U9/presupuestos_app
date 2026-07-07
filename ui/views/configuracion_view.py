# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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

from config import ROLES
from controllers.auth_controller import AuthController
from utils.logger import get_logger
from utils.validators import ValidationError

logger = get_logger(__name__)


class NuevoUsuarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo usuario")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_username = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_nombre = QLineEdit()
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(ROLES)

        form.addRow("Usuario *", self.input_username)
        form.addRow("Contraseña *", self.input_password)
        form.addRow("Nombre completo", self.input_nombre)
        form.addRow("Rol", self.combo_rol)
        layout.addLayout(form)

        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("SecondaryButton")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Crear")
        btn_guardar.clicked.connect(self.accept)
        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addLayout(botones)


class ConfiguracionView(QWidget):
    """Gestión de usuarios. Los parámetros generales y copias de seguridad
    quedan como TODO explícito para v2 (fuera del alcance mínimo de v1)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()
        self.cargar_usuarios()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titulo = QLabel("Configuración · Usuarios")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        header.addWidget(titulo)
        header.addStretch()

        btn_nuevo = QPushButton("+ Nuevo usuario")
        btn_nuevo.clicked.connect(self._crear_usuario)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Usuario", "Nombre completo", "Rol", "Activo"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        nota = QLabel(
            "Nota v1: parámetros generales y copias de seguridad automáticas "
            "quedan pendientes para la versión 2."
        )
        nota.setStyleSheet("color: #A19F9D; font-size: 11px;")
        layout.addWidget(nota)

    def cargar_usuarios(self) -> None:
        try:
            usuarios = AuthController.listar_usuarios()
        except Exception:  # noqa: BLE001
            logger.exception("Error listando usuarios")
            return

        self.tabla.setRowCount(len(usuarios))
        for fila, u in enumerate(usuarios):
            valores = [u.username, u.nombre_completo, u.rol, "Sí" if u.activo else "No"]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(valor))

    def _crear_usuario(self) -> None:
        dialogo = NuevoUsuarioDialog(parent=self)
        if dialogo.exec() == QDialog.Accepted:
            try:
                AuthController.crear_usuario(
                    username=dialogo.input_username.text(),
                    password=dialogo.input_password.text(),
                    nombre_completo=dialogo.input_nombre.text(),
                    rol=dialogo.combo_rol.currentText(),
                )
            except ValidationError as exc:
                QMessageBox.warning(self, "Datos inválidos", str(exc))
                return
            except Exception:  # noqa: BLE001
                logger.exception("Error creando usuario")
                QMessageBox.critical(self, "Error", "No se pudo crear el usuario.")
                return
            self.cargar_usuarios()
