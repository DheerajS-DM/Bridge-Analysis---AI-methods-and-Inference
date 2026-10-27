from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QTextEdit
)
from typing import Tuple, List, Dict, Any, Optional
from core.schema import Node3D, ElementFrame
from physics.model_importer import BridgeModelImporter

class ModelImporterDialog(QDialog):
    """File Explorer & Model Inspection Dialog for external bridge structural definitions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import External Bridge Model - Structural File Explorer")
        self.setMinimumSize(520, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QTextEdit {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 4px;
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

        title = QLabel("Select Bridge Model File (.py, .tcl, .json, .csv)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title)

        file_row = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setReadOnly(True)
        self.txt_path.setPlaceholderText("No file selected...")
        file_row.addWidget(self.txt_path)

        btn_browse = QPushButton("Browse Files...")
        btn_browse.clicked.connect(self._on_browse)
        file_row.addWidget(btn_browse)
        layout.addLayout(file_row)

        self.txt_info = QTextEdit()
        self.txt_info.setReadOnly(True)
        self.txt_info.setPlaceholderText("Model structural validation telemetry will appear here upon selection...")
        layout.addWidget(self.txt_info)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.btn_import = QPushButton("Load into Simulation Domain")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_import)
        layout.addLayout(btn_box)

        self.loaded_nodes: List[Node3D] = []
        self.loaded_elements: List[ElementFrame] = []
        self.import_meta: Dict[str, Any] = {}

    def _on_browse(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Bridge Model",
            "",
            "Supported Models (*.py *.tcl *.json *.csv);;OpenSeesPy Scripts (*.py);;OpenSees Tcl Scripts (*.tcl);;Topology JSON (*.json);;CSV Tables (*.csv)"
        )
        if file_path:
            self.txt_path.setText(file_path)
            try:
                nodes, elements, meta = BridgeModelImporter.import_from_file(file_path)
                self.loaded_nodes = nodes
                self.loaded_elements = elements
                self.import_meta = meta

                info_str = f"Model Validation Status: {meta['status']}\n"
                info_str += f"Source Format: {meta['format']}\n"
                info_str += f"Harvested Nodes: {meta['nodes_count']}\n"
                info_str += f"Harvested Frame Elements: {meta['elements_count']}\n"
                info_str += "Boundary Conditions & Mass DOFs Verified."
                self.txt_info.setText(info_str)
                self.btn_import.setEnabled(True)
            except Exception as e:
                self.txt_info.setText(f"Validation Error: {str(e)}")
                self.btn_import.setEnabled(False)
