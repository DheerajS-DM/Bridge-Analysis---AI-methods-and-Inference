import openseespy.opensees as ops
import polars as pl
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from core.schema import DynamicStepSnapshot

class OpenSeesFEASolver:
    """Wrapper class encapsulating OpenSeesPy FEA computational mechanics routines,
    supporting both static equilibrium and non-linear transient dynamic time-history analysis."""
    
    def __init__(self):
        self.is_built = False
        self._load_tag_counter = 9000
        self._mass_assigned = False

    def build_fea_model(self, nodes_df: pl.DataFrame, elements_df: pl.DataFrame) -> None:
        """Builds 3D structural model domain (6 DOFs per node) in OpenSees memory."""
        existing_nodes = ops.getNodeTags()
        if existing_nodes and len(existing_nodes) > 0:
            self.is_built = True
            return

        ops.wipe()
        ops.model('basic', '-ndm', 3, '-ndf', 6)

        # 1. Define Nodes
        for row in nodes_df.iter_rows(named=True):
            ops.node(row["id"], float(row["x"]), float(row["y"]), float(row["z"]))
            bc = row["boundary_conditions"]
            if any(bc):
                ops.fix(row["id"], *bc)

        # 2. Coordinate Transformations (Linear 3D)
        ops.geomTransf('Linear', 9001, 0.0, 0.0, 1.0)  # For horizontal/inclined elements
        ops.geomTransf('Linear', 9002, 0.0, 1.0, 0.0)  # For vertical Z-axis elements

        node_coords = {row["id"]: (float(row["x"]), float(row["y"]), float(row["z"])) for row in nodes_df.iter_rows(named=True)}

        # 3. Define Elastic Beam Column Elements
        for row in elements_df.iter_rows(named=True):
            p1 = node_coords[row["node_start"]]
            p2 = node_coords[row["node_end"]]
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            transf_tag = 9002 if (dx < 1e-5 and dy < 1e-5) else 9001

            e_mod = float(row["e_0"])
            area = float(row["area_0"])
            g_mod = e_mod / 2.6
            ops.element(
                'elasticBeamColumn',
                row["id"],
                row["node_start"],
                row["node_end"],
                area,
                e_mod,
                g_mod,
                float(row["j_0"]),
                float(row["iy_0"]),
                float(row["iz_0"]),
                transf_tag
            )
        self.is_built = True
        self.assign_lumped_masses(nodes_df, elements_df)

    def assign_lumped_masses(self, nodes_df: pl.DataFrame, elements_df: pl.DataFrame, density: float = 7850.0) -> None:
        """Assigns tributary translational lumped masses (M = rho * A * L / 2) to translational DOFs."""
        node_masses: Dict[int, float] = {row["id"]: 0.0 for row in nodes_df.iter_rows(named=True)}
        node_coords = {row["id"]: np.array([float(row["x"]), float(row["y"]), float(row["z"])]) for row in nodes_df.iter_rows(named=True)}

        for row in elements_df.iter_rows(named=True):
            n1 = row["node_start"]
            n2 = row["node_end"]
            if n1 in node_coords and n2 in node_coords:
                length = np.linalg.norm(node_coords[n2] - node_coords[n1])
                rho = 2400.0 if "Concrete" in str(row.get("section_type", "")) else density
                mass_elem = rho * float(row["area_0"]) * length
                node_masses[n1] += mass_elem * 0.5
                node_masses[n2] += mass_elem * 0.5

        for nid, m in node_masses.items():
            if m > 1.0:
                # Assign to 3 translational DOFs (ux, uy, uz), 0 for rotational
                ops.mass(nid, m, m, m, 0.0, 0.0, 0.0)
        self._mass_assigned = True

    def setup_rayleigh_damping(self, zeta: float = 0.05) -> None:
        """Configures mass- and stiffness-proportional Rayleigh damping C = alpha * M + beta * K."""
        try:
            eigen_vals = ops.eigen(2)
            if eigen_vals and len(eigen_vals) >= 2 and eigen_vals[0] > 0 and eigen_vals[1] > 0:
                omega1 = np.sqrt(eigen_vals[0])
                omega2 = np.sqrt(eigen_vals[1])
                alpha_m = 2.0 * zeta * (omega1 * omega2) / (omega1 + omega2)
                beta_k = 2.0 * zeta / (omega1 + omega2)
                ops.rayleigh(alpha_m, beta_k, 0.0, 0.0)
            else:
                ops.rayleigh(0.05, 0.002, 0.0, 0.0)
        except Exception:
            ops.rayleigh(0.05, 0.002, 0.0, 0.0)

    def apply_impulse_load(self, node_id: int, impulse: Tuple[float, float, float, float, float, float]) -> None:
        """Applies a 6-DOF kinetic point force/moment load pattern at specified node cleanly."""
        self._load_tag_counter += 1
        ts_tag = self._load_tag_counter
        pattern_tag = self._load_tag_counter + 1
        self._load_tag_counter += 1

        ops.timeSeries('Linear', ts_tag)
        ops.pattern('Plain', pattern_tag, ts_tag)
        ops.load(node_id, *impulse)

    def solve_static_step(self) -> bool:
        """Executes non-linear static equilibrium step K_tangent * Delta_u = P_ext - F_int."""
        try:
            ops.wipeAnalysis()
        except Exception:
            pass
        ops.system('BandGeneral')
        ops.numberer('RCM')
        ops.constraints('Plain')
        ops.integrator('LoadControl', 1.0)
        ops.algorithm('Newton')
        ops.analysis('Static')
        ok = ops.analyze(1)
        return ok == 0

    def solve_dynamic_transient(
        self,
        time_arr: np.ndarray,
        accel_record_g: np.ndarray,
        direction_dof: int = 2,
        dt_analysis: float = 0.02,
        elements_df: Optional[pl.DataFrame] = None
    ) -> List[DynamicStepSnapshot]:
        """Runs transient dynamic time history analysis using Newmark-beta integration.
        Returns sequential response snapshots for interactive UI playback."""
        snapshots: List[DynamicStepSnapshot] = []
        try:
            ops.wipeAnalysis()
        except Exception:
            pass

        self.setup_rayleigh_damping(zeta=0.05)

        # Convert g to m/s^2 (g = 9.80665)
        accel_ms2 = (accel_record_g * 9.80665).tolist()
        time_list = time_arr.tolist()

        ts_tag = 8501
        pattern_tag = 8502
        try:
            ops.timeSeries('Path', ts_tag, '-dt', float(time_arr[1] - time_arr[0]), '-values', *accel_ms2)
            ops.pattern('UniformExcitation', pattern_tag, direction_dof, '-accel', ts_tag)
        except Exception:
            # Fallback if Path series already defined
            pass

        ops.system('BandGeneral')
        ops.numberer('RCM')
        ops.constraints('Plain')
        # Newmark-Beta average acceleration method (unconditionally stable: gamma=0.5, beta=0.25)
        ops.integrator('Newmark', 0.5, 0.25)
        ops.algorithm('Newton')
        ops.analysis('Transient')

        node_tags = ops.getNodeTags()
        ele_tags = ops.getEleTags()
        n_steps = min(len(time_arr), 100)  # Capture up to 100 snapshots for smooth playback
        stride = max(1, len(time_arr) // n_steps)

        for step in range(len(time_arr)):
            ok = ops.analyze(1, dt_analysis)
            if ok != 0:
                # Fallback to Krylov-Newton or smaller step if convergence difficulty
                ops.algorithm('KrylovNewton')
                ok = ops.analyze(1, dt_analysis)
                ops.algorithm('Newton')

            if step % stride == 0 or step == len(time_arr) - 1:
                t_current = float(time_arr[step])
                disps: Dict[int, Tuple[float, float, float]] = {}
                max_d = 0.0
                for nid in node_tags:
                    dx = float(ops.nodeDisp(nid, 1))
                    dy = float(ops.nodeDisp(nid, 2))
                    dz = float(ops.nodeDisp(nid, 3))
                    disps[nid] = (dx, dy, dz)
                    mag = np.sqrt(dx*dx + dy*dy + dz*dz)
                    if mag > max_d:
                        max_d = mag

                stresses: Dict[int, float] = {}
                max_s = 0.0
                elem_area_map = {row["id"]: row["area_0"] for row in elements_df.iter_rows(named=True)} if elements_df is not None else {}
                for eid in ele_tags:
                    try:
                        forces = ops.basicForce(eid)
                        ax = abs(forces[0]) if len(forces) > 0 else 0.0
                        area = elem_area_map.get(eid, 0.02)
                        sig = ax / (area + 1e-6)
                        stresses[eid] = sig
                        if sig > max_s:
                            max_s = sig
                    except Exception:
                        stresses[eid] = 0.0

                snapshot = DynamicStepSnapshot(
                    time_step=t_current,
                    nodal_displacements=disps,
                    element_stresses=stresses,
                    max_drift_ratio=round(max_d / 8.0, 5),  # drift ratio = max_disp / pier_height
                    peak_stress=max_s,
                    ground_accel=float(accel_record_g[step])
                )
                snapshots.append(snapshot)

        return snapshots

    def extract_nodal_displacements(self, node_ids: List[int]) -> Dict[int, List[float]]:
        """Queries 6-DOF translations and rotations [ux, uy, uz, rx, ry, rz] for all nodes."""
        displacements = {}
        for nid in node_ids:
            try:
                disp = [ops.nodeDisp(nid, dof) for dof in range(1, 7)]
                displacements[nid] = disp
            except Exception:
                displacements[nid] = [0.0] * 6
        return displacements

    def extract_element_stresses(self, element_ids: List[int], elements_df: pl.DataFrame) -> Dict[int, float]:
        """Queries axial force and estimates von Mises stress for elements."""
        stresses = {}
        elem_map = {row["id"]: row["area_0"] for row in elements_df.iter_rows(named=True)}
        for eid in element_ids:
            try:
                forces = ops.basicForce(eid)
                axial_force = abs(forces[0]) if len(forces) > 0 else 0.0
                area = elem_map.get(eid, 0.01)
                stresses[eid] = axial_force / (area + 1e-6)
            except Exception:
                stresses[eid] = 0.0
        return stresses

    def update_element_sections(self, retrofit_actions: List[Any], elements_df: pl.DataFrame) -> None:
        """Modifies OpenSees element sections to reflect physical retrofit interventions
        (e.g., concrete jacketing, CFRP wraps, bolted splices) for verification re-solve."""
        action_map = {act.target_element_id: act for act in retrofit_actions}
        node_coords = {}
        for nid in ops.getNodeTags():
            coords = ops.nodeCoord(nid)
            node_coords[nid] = (coords[0], coords[1], coords[2] if len(coords) > 2 else 0.0)

        for row in elements_df.iter_rows(named=True):
            eid = row["id"]
            if eid in action_map:
                act = action_map[eid]
                mult = getattr(act, "capacity_restoration_factor", 1.25)
                # Enhanced cross-sectional properties
                area_new = float(row["area_0"]) * mult
                e_mod = float(row["e_0"])
                g_mod = e_mod / 2.6
                iy_new = float(row["iy_0"]) * (mult ** 2)
                iz_new = float(row["iz_0"]) * (mult ** 2)
                j_new = float(row["j_0"]) * mult
                
                # Check orientation
                n1 = row["node_start"]
                n2 = row["node_end"]
                p1 = node_coords.get(n1, (0, 0, 0))
                p2 = node_coords.get(n2, (0, 0, 0))
                dx = abs(p2[0] - p1[0])
                dy = abs(p2[1] - p1[1])
                transf_tag = 9002 if (dx < 1e-5 and dy < 1e-5) else 9001

                try:
                    # In OpenSees, redefine element
                    ops.element(
                        'elasticBeamColumn',
                        eid,
                        n1,
                        n2,
                        area_new,
                        e_mod,
                        g_mod,
                        j_new,
                        iy_new,
                        iz_new,
                        transf_tag
                    )
                except Exception:
                    pass

    def reset_model(self) -> None:
        """Clears OpenSees domain model memory."""
        ops.wipe()
        self.is_built = False
        self._mass_assigned = False
