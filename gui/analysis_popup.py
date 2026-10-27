from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, List

class AnalysisOverlayPopup(QDialog):
    """Professional dark-themed modal dialog illustrating the Bayesian
    heuristic thought process and vulnerability ranking with support for all structural nodes."""

    def __init__(self, thought_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bayesian Vulnerability Analysis - Forensic Thought Process")
        self.setMinimumSize(680, 480)
        self.thought_data = thought_data
        self.showing_all = False

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
                padding: 5px;
                border: 1px solid #313244;
                font-weight: bold;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Bayesian Hazard Utility & Heuristic Evaluation")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title)

        posteriors = thought_data.get("posteriors", {})
        post_str = "  |  ".join([f"{k.replace('_', ' ').title()}: P={v:.3f}" for k, v in posteriors.items()])
        post_lbl = QLabel(f"Bayesian Posterior Distribution P(Hazard | Theta):\n{post_str}")
        post_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(post_lbl)

        header_row = QHBoxLayout()
        self.tbl_label = QLabel("Ranked Candidate Structural Nodes [ArgMax U(n)]:")
        self.tbl_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_row.addWidget(self.tbl_label)
        header_row.addStretch()

        self.btn_toggle_all = QPushButton("View All Scanned Nodes")
        self.btn_toggle_all.clicked.connect(self._on_toggle_all)
        header_row.addWidget(self.btn_toggle_all)
        layout.addLayout(header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Node ID", "Structural Component Role", "Tensile Margin S(n,t)", "Risk Utility U(n)", "Target Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self._populate_table(self.thought_data.get("top_candidates", []))

        summary = thought_data.get("summary_text", "")
        sum_lbl = QLabel(f"Analytical Conclusion:\n{summary}")
        sum_lbl.setWordWrap(True)
        sum_lbl.setStyleSheet("color: #fab387; font-size: 11px; padding: 6px; background-color: #1e1e2e; border-radius: 4px;")
        layout.addWidget(sum_lbl)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_continue = QPushButton("Proceed with Hazard Injection")
        btn_continue.clicked.connect(self.accept)
        btn_box.addWidget(btn_continue)
        layout.addLayout(btn_box)

    def _populate_table(self, candidates: List[Dict[str, Any]]) -> None:
        target_id = self.thought_data.get("best_node_id", -1)
        self.table.setRowCount(len(candidates))

        for row, cand in enumerate(candidates):
            nid = cand["node_id"]
            is_target = (nid == target_id)
            status_text = "PRIORITIZED TARGET" if is_target else "Evaluated"

            it_nid = QTableWidgetItem(f"Node #{nid}")
            it_role = QTableWidgetItem(cand.get("component_role", "Frame Joint"))
            it_margin = QTableWidgetItem(f"{cand['tensile_margin']:.3f}")
            it_util = QTableWidgetItem(f"{cand['utility']/1e3:.1f} kN eq.")
            it_status = QTableWidgetItem(status_text)

            for it in [it_nid, it_role, it_margin, it_util, it_status]:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_target:
                    it.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, it_nid)
            self.table.setItem(row, 1, it_role)
            self.table.setItem(row, 2, it_margin)
            self.table.setItem(row, 3, it_util)
            self.table.setItem(row, 4, it_status)

    def _on_toggle_all(self) -> None:
        self.showing_all = not self.showing_all
        if self.showing_all:
            self.btn_toggle_all.setText("Show Top 10 Only")
            self.tbl_label.setText(f"All Scanned Structural Nodes ({len(self.thought_data.get('all_candidates', []))} Nodes):")
            self._populate_table(self.thought_data.get("all_candidates", []))
        else:
            self.btn_toggle_all.setText("View All Scanned Nodes")
            self.tbl_label.setText("Ranked Candidate Structural Nodes [ArgMax U(n)]:")
            self._populate_table(self.thought_data.get("top_candidates", []))
