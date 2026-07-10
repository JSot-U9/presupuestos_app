# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from config import APP_NAME
from models.usuario import Usuario
from ui.login_window import LoginWindow
from ui.views.configuracion_view import ConfiguracionView
from ui.views.dashboard_view import DashboardView
from ui.views.importar_meta_view import ImportarMetaView
from ui.views.importar_view import ImportarView
from ui.views.presupuesto_view import PresupuestoView
from ui.views.proyectos_view import ProyectosView
from ui.views.reportes_view import ReportesView
from ui.widgets.sidebar import Sidebar
from ui.widgets.topbar import TopBar


class MainWindow(QMainWindow):
    def __init__(self, usuario: Usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 720)
        self._construir_ui()

    def _construir_ui(self) -> None:
        contenedor = QWidget()
        self.setCentralWidget(contenedor)
        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.topbar = TopBar(self.usuario.nombre_completo, self.usuario.rol)
        self.topbar.btn_salir.clicked.connect(self._cerrar_sesion)
        layout_principal.addWidget(self.topbar)

        cuerpo = QWidget()
        layout_cuerpo = QHBoxLayout(cuerpo)
        layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        layout_cuerpo.setSpacing(0)
        layout_principal.addWidget(cuerpo, stretch=1)

        self.sidebar = Sidebar()
        self.sidebar.modulo_seleccionado.connect(self._cambiar_modulo)
        layout_cuerpo.addWidget(self.sidebar)

        # Restricción de rol simple para v1: solo ADMIN ve Configuración.
        if self.usuario.rol != "ADMIN":
            self.sidebar.ocultar_modulo("configuracion")

        self.stack = QStackedWidget()
        layout_cuerpo.addWidget(self.stack, stretch=1)

        self.vistas = {
            "dashboard": DashboardView(),
            "proyectos": ProyectosView(self.usuario.username),
            "presupuesto": PresupuestoView(),
            "importar": ImportarView(),
            "importar_meta": ImportarMetaView(),
            "reportes": ReportesView(),
            "configuracion": ConfiguracionView(),
        }
        for vista in self.vistas.values():
            self.stack.addWidget(vista)

        self._cambiar_modulo("dashboard")

    def _cambiar_modulo(self, clave: str) -> None:
        vista = self.vistas.get(clave)
        if vista is None:
            return
        # Refresca datos al entrar al módulo (evita mostrar información obsoleta)
        if hasattr(vista, "cargar_datos"):
            vista.cargar_datos()
        elif hasattr(vista, "actualizar_datos"):
            vista.actualizar_datos()
        elif hasattr(vista, "cargar_usuarios"):
            vista.cargar_usuarios()
        self.stack.setCurrentWidget(vista)

    def _cerrar_sesion(self) -> None:
        self.close()
        login = LoginWindow()
        if login.exec():
            nueva_ventana = MainWindow(login.usuario_autenticado)
            nueva_ventana.show()
            self._ventana_reemplazo = nueva_ventana  # evita garbage collection
