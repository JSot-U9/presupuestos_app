# -*- coding: utf-8 -*-
"""Punto de entrada del Sistema de Gestión de Ejecución Presupuestal.

Uso:
    python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from config import APP_NAME, ORGANIZATION
from database.connection import get_session, init_db
from services.auth_service import AuthService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> int:
    init_db()
    with get_session() as session:
        AuthService.asegurar_admin_inicial(session)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)

    qss_path = Path(__file__).resolve().parent / "ui" / "resources" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    login = LoginWindow()
    if login.exec() != LoginWindow.Accepted or login.usuario_autenticado is None:
        logger.info("Inicio de sesión cancelado por el usuario.")
        return 0

    ventana_principal = MainWindow(login.usuario_autenticado)
    ventana_principal.show()

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        logger.exception("Error fatal no controlado")
        raise
