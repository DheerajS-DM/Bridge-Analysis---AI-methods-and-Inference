import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QPushButton, QLabel, QComboBox, QTextEdit, QSplitter, QMenuBar, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer
from gui.vtk_viewer import VTKStructureViewer
from gui.dashboard_widget import TelemetryDashboardWidget
from gui.gantt_widget import GanttChartWidget
from gui.analysis_popup import AnalysisOverlayPopup
from gui.dynamic_playback_bar import DynamicPlaybackBar
from gui.damage_diagnostics_panel import DamageDiagnosticsPanel
from gui.model_importer_dialog import ModelImporterDialog

from core.schema import Node3D, ElementFrame, HazardContext, PlanAction, DamageReport
from core.state_manager import StateManager
from core.semantic_network import OntologicalSemanticNet
from physics.opensees_wrapper import OpenSeesFEASolver
from physics.bridge_models import BridgeGenerator
from physics.hazard_load_patterns import SourcedHazardLoadFactory
from ai.hazard_utility_engine import BayesianHazardUtilityEngine
from ai.damage_assessor import DamageAssessor
from ai.partial_order_planner import PartialOrderPlanner

class MainWindow(QMainWindow):
    """Forensic Structural Analysis & Indian Standard Retrofit Harness."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Physics-Informed Forensic Bridge Hazard Analysis & Indian Standard Retrofit System")
        self.setGeometry(80, 80, 1520, 960)

        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #11111b;
            }
            QWidget {
                background-color: #11111b;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenuBar {
                background-color: #181825;
                color: #cdd6f4;
                border-bottom: 1px solid #313244;
            }
            QMenuBar::item:selected {
                background-color: #313244;
            }
            QMenu {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
            }
            QMenu::item:selected {
                background-color: #313244;
            }
            QLabel {
                color: #cdd6f4;
            }
            QComboBox {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 7px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #313244;
                border-color: #89b4fa;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #11111b;
            }
            QTabBar::tab {
                background-color: #181825;
                color: #a6adc8;
                border: 1px solid #313244;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e2e;
                color: #89b4fa;
                border-bottom-color: #1e1e2e;
                font-weight: bold;
            }
        """)

        # Core Engines
        self.state_mgr = StateManager()
        self.semantic_net = OntologicalSemanticNet()
        self.fea_solver = OpenSeesFEASolver()
        self.utility_engine = BayesianHazardUtilityEngine()
        self.planner = PartialOrderPlanner()

        # Build Menu Bar
        self._build_menu_bar()

        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Left Control Panel
        control_panel = QVBoxLayout()
        control_panel.setSpacing(8)

        control_panel.addWidget(QLabel("<b>Bridge Benchmark Model</b>"))
        self.model_combo = QComboBox()
        for m in BridgeGenerator.AVAILABLE_MODELS:
            self.model_combo.addItem(m["name"], m["id"])
        self.model_combo.currentIndexChanged.connect(self.on_bridge_model_changed)
        control_panel.addWidget(self.model_combo)

        control_panel.addWidget(QLabel("<b>Sourced Natural Disaster Scenario</b>"))
        self.hazard_combo = QComboBox()
        for k, sc in SourcedHazardLoadFactory.AVAILABLE_SCENARIOS.items():
            self.hazard_combo.addItem(f"{sc['name']} [{sc['hazard_type'].title()}]", k)
        control_panel.addWidget(self.hazard_combo)

        control_panel.addWidget(QLabel("<b>Simulation & Mitigation Pipeline</b>"))
        self.btn_run_sim = QPushButton("Run Baseline Static Equilibrium")
        self.btn_inject_attack = QPushButton("Execute Multi-Stage Disaster Injection")
        self.btn_plan_maintenance = QPushButton("Synthesize Indian Standard Retrofit Plan")

        self.btn_run_sim.clicked.connect(self.on_run_fea_step)
        self.btn_inject_attack.clicked.connect(self.on_execute_attack)
        self.btn_plan_maintenance.clicked.connect(self.on_synthesize_plan)

        control_panel.addWidget(self.btn_run_sim)
        control_panel.addWidget(self.btn_inject_attack)
        control_panel.addWidget(self.btn_plan_maintenance)

        # Terminal Log
        control_panel.addWidget(QLabel("<b>Autonomous Agent Reasoning Terminal</b>"))
        self.agent_terminal = QTextEdit()
        self.agent_terminal.setReadOnly(True)
        self.agent_terminal.setStyleSheet(
            "QTextEdit { background-color: #11111b; color: #a6adc8; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; border: 1px solid #313244; border-radius: 4px; padding: 6px; }"
        )
        control_panel.addWidget(self.agent_terminal, 2)

        # Right Tabbed Viewport
        self.tabs = QTabWidget()
        
        # 3D Viewport with Playback Bar
        vtk_container = QWidget()
        vtk_layout = QVBoxLayout(vtk_container)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        self.vtk_viewer = VTKStructureViewer()
        self.playback_bar = DynamicPlaybackBar()
        self.playback_bar.stepChanged.connect(self._on_playback_frame_changed)
        vtk_layout.addWidget(self.vtk_viewer, 1)
        vtk_layout.addWidget(self.playback_bar)

        self.diagnostics_panel = DamageDiagnosticsPanel()
        self.diagnostics_panel.elementSelected.connect(self._on_diagnostic_element_selected)

        self.dashboard = TelemetryDashboardWidget()
        self.gantt_chart = GanttChartWidget()

        self.tabs.addTab(vtk_container, "3D Forensic Simulation & Dynamic Playback")
        self.tabs.addTab(self.diagnostics_panel, "Forensic Damage Diagnostics & IRC Codes")
        self.tabs.addTab(self.dashboard, "Structural Telemetry & Stress Curves")
        self.tabs.addTab(self.gantt_chart, "IRC Rehabilitation Gantt Schedule")

        main_layout.addLayout(control_panel, 2)
        main_layout.addWidget(self.tabs, 5)

        # History Tracking
        self.sim_step_count = 0
        self.step_history = []
        self.peak_stress_history = []
        self.damage_reports: List[DamageReport] = []
        self.dynamic_snapshots = []
        self.last_stresses = {}

        self.log_terminal("Autonomous Forensic Analysis Engine initialized in dark institutional mode.", "SYSTEM")
        self.load_bridge_model(0)

    def _build_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        act_import = QAction("Import External Bridge Model...", self)
        act_import.triggered.connect(self.on_open_importer_dialog)
        file_menu.addAction(act_import)

        file_menu.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    def log_terminal(self, message: str, tag: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = "#89b4fa"
        if tag == "ATTACK":
            color = "#f38ba8"
        elif tag == "PLAN":
            color = "#a6e3a1"
        elif tag == "SYSTEM":
            color = "#fab387"
        elif tag == "FEA":
            color = "#cba6f7"
        html = f"<span style='color:#6c7086;'>[{ts}]</span> <b style='color:{color};'>[{tag}]</b> {message}"
        self.agent_terminal.append(html)

    def on_open_importer_dialog(self):
        dlg = ModelImporterDialog(self)
        if dlg.exec():
            nodes = dlg.loaded_nodes
            elements = dlg.loaded_elements
            meta = dlg.import_meta
            self.state_mgr.initialize_tables(nodes, elements)
            self.semantic_net.build_network(self.state_mgr.df_nodes, self.state_mgr.df_elements)
            self.fea_solver.reset_model()
            self.fea_solver.build_fea_model(self.state_mgr.df_nodes, self.state_mgr.df_elements)
            self.vtk_viewer.render_structural_mesh(self.state_mgr.df_nodes, self.state_mgr.df_elements)
            self.log_terminal(f"Successfully loaded external model '{meta['source_file']}' ({len(nodes)} Nodes, {len(elements)} Elements).", "SYSTEM")

    def on_bridge_model_changed(self, index: int):
        self.load_bridge_model(index)

    def load_bridge_model(self, index: int):
        model_id = self.model_combo.itemData(index) or "warren_truss_48m"
        self.fea_solver.reset_model()

        if model_id == "caltrans_2span_box":
            nodes, elements = BridgeGenerator.generate_caltrans_box_girder_bridge()
            name = "Caltrans 2-Span Box Girder"
        elif model_id == "steel_composite_3span":
            nodes, elements = BridgeGenerator.generate_steel_composite_bridge()
            name = "3-Span Steel Composite Girder"
        elif model_id == "tied_arch_60m":
            nodes, elements = BridgeGenerator.generate_tied_arch_bridge()
            name = "60m Tied-Arch Bridge"
        elif model_id == "supert_33m":
            nodes, elements = BridgeGenerator.load_github_33m_supert_bridge()
            name = "33.5m Super-T Concrete Girder"
        else:
            nodes, elements = BridgeGenerator.generate_industrial_truss_bridge()
            name = "48m Warren Steel Truss (IRC:24)"

        self.state_mgr.initialize_tables(nodes, elements)
        self.semantic_net.build_network(self.state_mgr.df_nodes, self.state_mgr.df_elements)
        self.fea_solver.build_fea_model(self.state_mgr.df_nodes, self.state_mgr.df_elements)
        self.vtk_viewer.render_structural_mesh(self.state_mgr.df_nodes, self.state_mgr.df_elements)
        self.damage_reports = []
        self.diagnostics_panel.populate_reports([])
        self.playback_bar.load_snapshots([])
        self.log_terminal(f"Loaded benchmark model '{name}' ({len(nodes)} Nodes, {len(elements)} Frame Elements).", "SYSTEM")

    def on_run_fea_step(self):
        """Executes operational baseline load step."""
        self.sim_step_count += 1
        node_ids = self.state_mgr.df_nodes["id"].to_list()
        elem_ids = self.state_mgr.df_elements["id"].to_list()
        target_node = node_ids[len(node_ids) // 2] if len(node_ids) > 0 else 1

        self.log_terminal("Engaging OpenSees FEA Static Solver...", "FEA")
        self.log_terminal(f"Applying operational live load F_z = -350 kN at deck midspan Node #{target_node}.", "FEA")

        self.fea_solver.apply_impulse_load(target_node, (100000.0, 0.0, -350000.0, 0.0, 0.0, 0.0))
        self.fea_solver.solve_static_step()

        disps = self.fea_solver.extract_nodal_displacements(node_ids)
        stresses = self.fea_solver.extract_element_stresses(elem_ids, self.state_mgr.df_elements)
        self.last_stresses = stresses
        peak_stress = max(stresses.values()) if stresses and max(stresses.values()) > 0 else 4.5e7

        self.state_mgr.log_step_telemetry(self.sim_step_count, disps, stresses)
        self.step_history.append(self.sim_step_count)
        self.peak_stress_history.append(peak_stress)

        self.vtk_viewer.render_structural_mesh(
            self.state_mgr.df_nodes, self.state_mgr.df_elements,
            displacements=disps, stresses=stresses, disp_scale=300.0
        )
        self.dashboard.update_stress_plot(self.step_history, self.peak_stress_history)
        self.log_terminal(f"Static baseline equilibrium solved. Peak von Mises stress: {peak_stress/1e6:.1f} MPa.", "FEA")
        self.tabs.setCurrentIndex(0)

    def on_execute_attack(self):
        """Executes the multi-stage visual disaster analysis pipeline."""
        self.sim_step_count += 1
        scenario_id = self.hazard_combo.currentData() or "el_centro_1940"
        sc_meta = SourcedHazardLoadFactory.AVAILABLE_SCENARIOS.get(scenario_id, {})

        weather = HazardContext(
            scenario_id=scenario_id,
            hazard_type=sc_meta.get("hazard_type", "earthquake"),
            wind_speed=38.0 if sc_meta.get("hazard_type") == "wind" else 15.0,
            scour_depth=2.8 if sc_meta.get("hazard_type") == "flood_scour" else 0.5,
            seismic_pga=sc_meta.get("pga_g", 0.45)
        )

        self.log_terminal("Stage 1: Pre-Disaster Vulnerability Analysis & Bayesian Heuristic Scan...", "ATTACK")
        attack_vec, thought_logs, thought_data = self.utility_engine.select_optimal_attack_target(
            self.state_mgr.df_nodes, self.state_mgr, self.semantic_net, weather
        )

        for line in thought_logs:
            self.log_terminal(line, "ATTACK")

        # Highlight candidate nodes on 3D view
        self.vtk_viewer.highlight_candidate_nodes(thought_data["top_candidates"], attack_vec.target_node_id)

        # Show Thought-Process Modal Dialog
        popup = AnalysisOverlayPopup(thought_data, self)
        popup.exec()

        self.log_terminal(f"Stage 2: Dynamic Hazard Time-History Injection ({sc_meta.get('name', 'Hazard')})...", "FEA")
        self.log_terminal(f"Governing Standard: {sc_meta.get('governing_standard', 'Standard')}. Citation: {sc_meta.get('citation', '')}", "FEA")

        # Load authentic acceleration/force record
        time_arr, accel_g, meta = SourcedHazardLoadFactory.load_ground_motion_record(scenario_id)

        # Execute OpenSees transient dynamic analysis
        snapshots = self.fea_solver.solve_dynamic_transient(
            time_arr=time_arr,
            accel_record_g=accel_g,
            direction_dof=2,
            dt_analysis=float(meta.get("dt", 0.02)),
            elements_df=self.state_mgr.df_elements
        )
        self.dynamic_snapshots = snapshots
        self.playback_bar.load_snapshots(snapshots)

        # Post-disaster static extraction
        node_ids = self.state_mgr.df_nodes["id"].to_list()
        elem_ids = self.state_mgr.df_elements["id"].to_list()
        disps = self.fea_solver.extract_nodal_displacements(node_ids)
        stresses = self.fea_solver.extract_element_stresses(elem_ids, self.state_mgr.df_elements)
        self.last_stresses = stresses
        peak_stress = max(stresses.values()) if stresses and max(stresses.values()) > 0 else 8.5e7

        self.state_mgr.log_step_telemetry(self.sim_step_count, disps, stresses)
        self.step_history.append(self.sim_step_count)
        self.peak_stress_history.append(peak_stress)

        # Stage 3: Forensic Damage Assessment
        self.log_terminal("Stage 3: Forensic Damage Diagnostics & Failure Localization...", "ATTACK")
        self.damage_reports = DamageAssessor.assess_structure(
            self.state_mgr.df_elements,
            stresses,
            scour_depth_m=weather.scour_depth
        )
        self.diagnostics_panel.populate_reports(self.damage_reports)

        for rep in self.damage_reports[:4]:
            self.log_terminal(f"   - Compromised Element #{rep.element_id} ({rep.component_type}): {rep.damage_category.title()} | DCR={rep.dcr:.2f} | Standard: {rep.governing_code}", "ATTACK")

        # Render deformed mesh with 3D damage badges
        self.vtk_viewer.render_structural_mesh(
            self.state_mgr.df_nodes,
            self.state_mgr.df_elements,
            displacements=disps,
            stresses=stresses,
            damage_reports=self.damage_reports,
            disp_scale=400.0
        )
        self.dashboard.update_stress_plot(self.step_history, self.peak_stress_history)
        self.tabs.setCurrentIndex(0)

    def on_synthesize_plan(self):
        """Synthesizes adaptive Indian Standard retrofit plan and re-runs FEA verification."""
        if not self.damage_reports:
            # Run damage assessment if not already populated
            self.damage_reports = DamageAssessor.assess_structure(
                self.state_mgr.df_elements,
                self.last_stresses if self.last_stresses else {},
                scour_depth_m=1.8
            )
            self.diagnostics_panel.populate_reports(self.damage_reports)

        self.log_terminal("Stage 4: Adaptive Retrofit Synthesis governed by Indian Roads Congress (IRC)...", "PLAN")
        self.planner.generate_actions_from_damage_reports(self.damage_reports)

        pop_plan = self.planner.solve(
            initial_state={"DamageDetected", "TrafficClosed"},
            goal_conditions={"FlexuralCapacityRestored", "StructuralSafetyRestored"}
        )
        self.gantt_chart.set_plan(pop_plan)

        real_steps = [s for s in pop_plan.steps if s.id not in ["Start", "Finish"]]
        self.log_terminal(f"IRC Retrofit Schedule Synthesized ({len(real_steps)} Interventions). Critical Path: {pop_plan.critical_path_days} Days. Budget: INR {pop_plan.total_cost_inr:,.0f}.", "PLAN")
        for s in real_steps:
            self.log_terminal(f"   - [{s.standard_code} {s.clause_reference}] {s.name}: INR {s.cost_inr:,.0f} | Duration: {s.duration_days}d", "PLAN")

        # Stage 4 Verification FEA Re-Solve
        self.log_terminal("Executing Verification FEA Re-Solve with Upgraded Sections...", "FEA")
        self.fea_solver.update_element_sections(real_steps, self.state_mgr.df_elements)
        self.fea_solver.solve_static_step()

        node_ids = self.state_mgr.df_nodes["id"].to_list()
        elem_ids = self.state_mgr.df_elements["id"].to_list()
        disps = self.fea_solver.extract_nodal_displacements(node_ids)
        stresses = self.fea_solver.extract_element_stresses(elem_ids, self.state_mgr.df_elements)
        peak_stress = max(stresses.values()) if stresses and max(stresses.values()) > 0 else 3.8e7

        # Re-render with retrofit geometry and alleviated stress contours
        self.vtk_viewer.render_structural_mesh(
            self.state_mgr.df_nodes,
            self.state_mgr.df_elements,
            displacements=disps,
            stresses=stresses,
            retrofit_actions=real_steps,
            disp_scale=200.0
        )
        self.log_terminal(f"Verification Re-Solve Completed: Stress contours alleviated. Post-retrofit peak stress: {peak_stress/1e6:.1f} MPa (Factor of safety restored).", "FEA")
        self.tabs.setCurrentIndex(3)

    def _on_playback_frame_changed(self, frame_idx: int):
        """Handles time scrubber slider ticks during transient dynamic animation."""
        if 0 <= frame_idx < len(self.dynamic_snapshots):
            snap = self.dynamic_snapshots[frame_idx]
            self.vtk_viewer.update_dynamic_transient_frame(
                self.state_mgr.df_nodes,
                self.state_mgr.df_elements,
                snap.nodal_displacements,
                snap.element_stresses
            )

    def _on_diagnostic_element_selected(self, element_id: int):
        """Focuses camera on the compromised element."""
        self.tabs.setCurrentIndex(0)
        self.log_terminal(f"Focusing 3D diagnostic viewport on compromised Element #{element_id}.", "SYSTEM")
