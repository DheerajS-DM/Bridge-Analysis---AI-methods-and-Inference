from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List
from core.schema import DamageReport

class DamageDiagnosticsPanel(QWidget):
    """Forensic structural damage diagnostics dock panel displaying element failure modes,
    DCR metrics, and governing Indian Standard codes with 3D camera focus triggers."""

    elementSelected = pyqtSignal(int)  # emits element_id for 3D camera centering

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-weight: bold;
                color: #89b4fa;
            }
            QTableWidget {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #313244;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 4px;
                border: 1px solid #313244;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        title = QLabel("Forensic Damage Diagnostics & Indian Standard Failure Limits")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Element ID", "Component Type", "Damage Category", "DCR (Demand/Cap)", "Governing Standard"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

    def populate_reports(self, reports: List[DamageReport]) -> None:
        """Populates forensic distress reports into the ledger table."""
        self.table.setRowCount(len(reports))
        for row, rep in enumerate(reports):
            it_id = QTableWidgetItem(f"#{rep.element_id}")
            it_type = QTableWidgetItem(rep.component_type)
            it_cat = QTableWidgetItem(rep.damage_category.replace("_", " ").title())
            it_dcr = QTableWidgetItem(f"{rep.dcr:.2f}")
            it_code = QTableWidgetItem(rep.governing_code)

            for it in [it_id, it_type, it_cat, it_dcr, it_code]:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight severity
            if rep.dcr > 1.0:
                it_dcr.setForeground(Qt.GlobalColor.red)
            elif rep.dcr > 0.8:
                it_dcr.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, it_id)
            self.table.setItem(row, 1, it_type)
            self.table.setItem(row, 2, it_cat)
            self.table.setItem(row, 3, it_dcr)
            self.table.setItem(row, 4, it_code)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        item = self.table.item(row, 0)
        if item:
            eid_str = item.text().replace("#", "")
            try:
                self.elementSelected.emit(int(eid_str))
            except ValueError:
                pass
