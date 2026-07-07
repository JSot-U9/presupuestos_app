# -*- coding: utf-8 -*-
from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.dashboard_controller import DashboardController
from utils.logger import get_logger

logger = get_logger(__name__)


class KpiCard(QWidget):
    def __init__(self, titulo: str, valor: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "KpiCard")
        self.setStyleSheet(
            "background-color: white; border-radius: 8px; border: 1px solid #E1DFDD;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet("font-size: 22px; font-weight: 700; color: #1F4E79;")
        layout.addWidget(self.lbl_valor)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #605E5C; font-size: 12px;")
        layout.addWidget(lbl_titulo)

    def actualizar(self, valor: str) -> None:
        self.lbl_valor.setText(valor)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._construir_ui()
        self.actualizar_datos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700;")
        header.addWidget(titulo)
        header.addStretch()
        btn_refrescar = QPushButton("Actualizar")
        btn_refrescar.clicked.connect(self.actualizar_datos)
        header.addWidget(btn_refrescar)
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.card_proyectos = KpiCard("Nº de Proyectos", "0")
        self.card_pim = KpiCard("PIM Total (S/)", "0.00")
        self.card_devengado = KpiCard("Devengado (S/)", "0.00")
        self.card_saldo = KpiCard("Saldo (S/)", "0.00")
        self.card_avance = KpiCard("% Ejecución", "0.00%")

        for i, card in enumerate(
            (self.card_proyectos, self.card_pim, self.card_devengado, self.card_saldo, self.card_avance)
        ):
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)

        self.figure = Figure(figsize=(6, 3.2), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas, stretch=1)

    def actualizar_datos(self) -> None:
        try:
            kpis = DashboardController.obtener_kpis()
            detalle = DashboardController.ejecucion_por_proyecto()
        except Exception:  # noqa: BLE001
            logger.exception("Error cargando KPIs del dashboard")
            return

        self.card_proyectos.actualizar(str(kpis.num_proyectos))
        self.card_pim.actualizar(f"{kpis.pim_total:,.2f}")
        self.card_devengado.actualizar(f"{kpis.devengado_total:,.2f}")
        self.card_saldo.actualizar(f"{kpis.saldo_total:,.2f}")
        self.card_avance.actualizar(f"{kpis.porcentaje_ejecucion:.2f}%")

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if detalle:
            codigos = [d[0] for d in detalle]
            pim_vals = [d[1] for d in detalle]
            dev_vals = [d[2] for d in detalle]
            x = range(len(codigos))
            ancho = 0.35
            ax.bar([i - ancho / 2 for i in x], pim_vals, width=ancho, label="PIM", color="#1F4E79")
            ax.bar([i + ancho / 2 for i in x], dev_vals, width=ancho, label="Devengado", color="#70AD47")
            ax.set_xticks(list(x))
            ax.set_xticklabels(codigos, rotation=30, ha="right", fontsize=8)
            ax.legend()
            ax.set_title("PIM vs Devengado por Proyecto")
        else:
            ax.text(0.5, 0.5, "Sin datos aún. Importe un Excel de presupuesto.",
                     ha="center", va="center", fontsize=10, color="#605E5C")
            ax.set_xticks([])
            ax.set_yticks([])
        self.canvas.draw_idle()
