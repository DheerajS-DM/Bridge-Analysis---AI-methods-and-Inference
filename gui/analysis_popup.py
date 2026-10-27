from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, List

class AnalysisOverlayPopup(QDialog):
    """Professional dark-themed modal dialog illustrating the Bayesian
    heuristic thought process and vulnerability ranking without decorative emojis."""

    def __init__(self, thought_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bayesian Vulnerability Analysis - Forensic Thought Process")
        self.setMinimumSize(560, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #cdd6f4;
            }
            QTableWidget {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #313244;
                gridline-color: #313244;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 4px;
                border: 1px solid #313244;
                font-weight: bold;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header Title
        title = QLabel("Bayesian Hazard Utility & Heuristic Evaluation")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title)

        # Posteriors Section
        posteriors = thought_data.get("posteriors", {})
        post_str = "  |  ".join([f"{k.replace('_', ' ').title()}: P={v:.3f}" for k, v in posteriors.items()])
        post_lbl = QLabel(f"Bayesian Posterior Distribution P(Hazard | Theta):\n{post_str}")
        post_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(post_lbl)

        # Candidates Table
        tbl_label = QLabel("Ranked Candidate Vulnerability Assessment [ArgMax U(n)]:")
        tbl_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(tbl_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Node ID", "Tensile Margin S(n,t)", "Risk Utility U(n)", "Target Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        candidates: List[Dict[str, Any]] = thought_data.get("top_candidates", [])
        target_id = thought_data.get("best_node_id", -1)

        self.table.setRowCount(len(candidates))
        for row, cand in enumerate(candidates):
            nid = cand["node_id"]
            is_target = (nid == target_id)
            status_text = "PRIORITIZED TARGET" if is_target else "Evaluated"

            item_nid = QTableWidgetItem(f"Node #{nid}")
            item_margin = QTableWidgetItem(f"{cand['tensile_margin']:.3f}")
            item_util = QTableWidgetItem(f"{cand['utility']/1e3:.1f} kN eq.")
            item_status = QTableWidgetItem(status_text)

            for it in [item_nid, item_margin, item_util, item_status]:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_target:
                    it.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, item_nid)
            self.table.setItem(row, 1, item_margin)
            self.table.setItem(row, 2, item_util)
            self.table.setItem(row, 3, item_status)

        layout.addWidget(self.table)

        # Engineering Summary
        summary = thought_data.get("summary_text", "")
        sum_lbl = QLabel(f"Analytical Conclusion:\n{summary}")
        sum_lbl.setWordWrap(True)
        sum_lbl.setStyleSheet("color: #fab387; font-size: 11px; padding: 6px; background-color: #1e1e2e; border-radius: 4px;")
        layout.addWidget(sum_lbl)

        # Button row
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_continue = QPushButton("Proceed with Hazard Injection")
        btn_continue.clicked.connect(self.accept)
        btn_box.addWidget(btn_continue)
        layout.addLayout(btn_box)
