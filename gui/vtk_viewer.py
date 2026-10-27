import pyvista as pv
from pyvistaqt import QtInteractor
import vtk
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import polars as pl
from typing import Dict, List, Tuple, Optional, Any
from core.schema import DamageReport, PlanAction

# Suppress VTK popup warnings
vtk.vtkObject.GlobalWarningDisplayOff()

class VTKStructureViewer(QWidget):
    """PyVista / VTK 3D OpenGL rendering canvas with a muted industrial dark theme.
    Renders 3D structural frames, dynamic transient waves, heuristic candidate analysis spheres,
    damage badges (plastic hinges, buckling, scour), and physical retrofit geometry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)
        # Deep Charcoal Dark Slate Theme
        self.plotter.set_background("#11111b")
        self.current_cad_mesh: Optional[pv.DataSet] = None
        self._analysis_actor = None
        self._reticle_actor = None

    def render_structural_mesh(
        self,
        nodes_df: pl.DataFrame,
        elements_df: pl.DataFrame,
        displacements: Optional[Dict[int, List[float]]] = None,
        stresses: Optional[Dict[int, float]] = None,
        damage_reports: Optional[List[DamageReport]] = None,
        retrofit_actions: Optional[List[PlanAction]] = None,
        disp_scale: float = 300.0
    ) -> None:
        """Renders 3D structural frame using a muted, subdued industrial palette."""
        self.plotter.clear()
        if len(nodes_df) == 0 or len(elements_df) == 0:
            return

        # Build node coordinate lookup
        node_coords = {}
        for row in nodes_df.iter_rows(named=True):
            nid = row["id"]
            x, y, z = float(row["x"]), float(row["y"]), float(row["z"])
            if displacements and nid in displacements:
                disp = displacements[nid]
                x += float(disp[0]) * disp_scale
                y += float(disp[1]) * disp_scale
                z += float(disp[2]) * disp_scale
            node_coords[nid] = (x, y, z)

        damaged_map = {r.element_id: r for r in damage_reports} if damage_reports else {}
        retrofit_map = {a.target_element_id: a for a in retrofit_actions} if retrofit_actions else {}

        # Muted Colormap / Color mapping
        # Slate Grey baseline for intact elements: #45475a
        # Concrete piers: #3b3d4a
        # Yielded / high stress: muted amber #b85d3b to crimson #a63d40
        # Retrofitted: reinforced steel blue #6c7086 / #89b4fa
        for row in elements_df.iter_rows(named=True):
            eid = row["id"]
            p1 = node_coords.get(row["node_start"])
            p2 = node_coords.get(row["node_end"])
            if not p1 or not p2:
                continue

            sec_type = str(row.get("section_type", ""))
            is_pier = ("Pier" in sec_type or "Column" in sec_type or "Bent" in sec_type)
            radius = 0.40 if is_pier else 0.22

            # Check if retrofitted
            if eid in retrofit_map:
                radius *= 1.35 # Visual section enlargement (IRC:SP:40 Cl 5.3)
                elem_color = "#5b708b" # Subdued retrofit steel blue
            elif eid in damaged_map:
                rep = damaged_map[eid]
                if rep.dcr > 1.0:
                    elem_color = "#a63d40" # Subdued crimson
                elif rep.dcr > 0.8:
                    elem_color = "#b85d3b" # Burnished copper
                else:
                    elem_color = "#8f764a" # Ochre
            elif stresses and eid in stresses and stresses[eid] > 0:
                fy = float(row.get("yield_stress_fy", 3.5e8))
                ratio = min(1.2, stresses[eid] / (fy + 1e-6))
                if ratio > 1.0:
                    elem_color = "#a63d40"
                elif ratio > 0.75:
                    elem_color = "#b85d3b"
                elif ratio > 0.45:
                    elem_color = "#4e6a57" # Subdued olive
                else:
                    elem_color = "#364353" # Muted slate gunmetal
            else:
                elem_color = "#313244" if is_pier else "#45475a" # Muted slate grey

            line = pv.Line(p1, p2)
            try:
                tube = line.tube(radius=radius, n_sides=10)
                self.plotter.add_mesh(tube, color=elem_color, smooth_shading=True, specular=0.3, ambient=0.25)
            except Exception:
                self.plotter.add_mesh(line, color=elem_color, line_width=3)

        # Render 3D Damage Badges / Glyphs
        if damage_reports:
            self._render_damage_badges(damage_reports, elements_df, node_coords)

        # Add nodes with subtle matte graphite spheres
        points = list(node_coords.values())
        if points:
            poly = pv.PolyData(points)
            self.plotter.add_mesh(poly, color="#585b70", point_size=5, render_points_as_spheres=True)

        self.plotter.show_grid(color="#2a2b3d")
        self.plotter.reset_camera()
        self.plotter.update()

    def _render_damage_badges(self, reports: List[DamageReport], elements_df: pl.DataFrame, node_coords: Dict[int, Tuple[float, float, float]]) -> None:
        """Renders 3D physical indicators for plastic hinges, buckling, and scour."""
        elem_lookup = {row["id"]: (row["node_start"], row["node_end"]) for row in elements_df.iter_rows(named=True)}

        for rep in reports:
            if rep.element_id not in elem_lookup:
                continue
            n1, n2 = elem_lookup[rep.element_id]
            p1 = np.array(node_coords.get(n1, (0, 0, 0)))
            p2 = np.array(node_coords.get(n2, (0, 0, 0)))
            midpoint = (p1 + p2) * 0.5

            if rep.damage_category == "plastic_hinge":
                # Red torus/sphere at column base
                hinge_pos = p2 if p2[2] < p1[2] else p1
                sphere = pv.Sphere(radius=0.75, center=hinge_pos)
                self.plotter.add_mesh(sphere, color="#a63d40", opacity=0.85, smooth_shading=True)
            elif rep.damage_category == "diagonal_buckling":
                # Amber marker on compression member
                box = pv.Cube(center=midpoint, x_length=0.8, y_length=0.8, z_length=0.8)
                self.plotter.add_mesh(box, color="#b85d3b", opacity=0.85)
            elif rep.damage_category == "foundation_scour":
                # Scour inverted cone at pier base
                base_pos = p2 if p2[2] < p1[2] else p1
                cone = pv.Cone(center=base_pos, direction=(0, 0, 1), height=1.5, radius=1.8)
                self.plotter.add_mesh(cone, color="#3e5f76", opacity=0.6)

    def highlight_candidate_nodes(self, top_candidates: List[Dict[str, Any]], target_node_id: int) -> None:
        """Visualizes candidate nodes during the Bayesian heuristic search."""
        for cand in top_candidates:
            nid = cand["node_id"]
            pos = (cand["x"], cand["y"], cand["z"])
            margin = cand.get("tensile_margin", 0.5)

            # Gradient from green to red based on margin
            if nid == target_node_id:
                color = "#a63d40"  # Critical target
                rad = 0.8
            elif margin < 0.3:
                color = "#b85d3b"
                rad = 0.6
            else:
                color = "#89b4fa"
                rad = 0.45

            sph = pv.Sphere(radius=rad, center=pos)
            self.plotter.add_mesh(sph, color=color, opacity=0.9, smooth_shading=True)

        self.plotter.update()

    def update_dynamic_transient_frame(
        self,
        nodes_df: pl.DataFrame,
        elements_df: pl.DataFrame,
        displacements: Dict[int, Tuple[float, float, float]],
        stresses: Dict[int, float],
        disp_scale: float = 250.0
    ) -> None:
        """Frame-by-frame lightweight update for transient dynamic time-history playback."""
        # Convert displacements tuple to list
        disp_list = {nid: [v[0], v[1], v[2], 0, 0, 0] for nid, v in displacements.items()}
        self.render_structural_mesh(
            nodes_df=nodes_df,
            elements_df=elements_df,
            displacements=disp_list,
            stresses=stresses,
            disp_scale=disp_scale
        )
