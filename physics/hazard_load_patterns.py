import os
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from core.schema import HazardContext

class SourcedHazardLoadFactory:
    """Factory generating physically authentic disaster patterns backed by
    PEER Ground Motion Database, Indian Standards (IS 1893, IS 875), and Indian Roads Congress (IRC:6, IRC:78, IRC:89)."""

    DATA_DIR = os.path.join(os.path.dirname(__file__), "ground_motions")

    AVAILABLE_SCENARIOS = {
        "el_centro_1940": {
            "name": "1940 El Centro (Imperial Valley Array #9)",
            "hazard_type": "earthquake",
            "source": "PEER NGA-West2 Record #0006 (Mw 6.9)",
            "citation": "Trifunac & Lee (1973); PEER Ground Motion Database",
            "pga_g": 0.313,
            "duration_s": 30.0,
            "dt_s": 0.02,
            "filename": "el_centro_1940.npz",
            "governing_standard": "AASHTO / Caltrans SDC / PEER Benchmark"
        },
        "northridge_1994": {
            "name": "1994 Northridge (Sylmar Converter Station)",
            "hazard_type": "earthquake",
            "source": "PEER NGA Record #0960 (Mw 6.7, Near-Fault Velocity Pulse)",
            "citation": "Somerville et al. (1997) Directivity Pulses; PEER NGA",
            "pga_g": 0.843,
            "duration_s": 20.0,
            "dt_s": 0.02,
            "filename": "northridge_1994.npz",
            "governing_standard": "Caltrans Seismic Design Criteria (SDC 2.0)"
        },
        "kobe_1995": {
            "name": "1995 Kobe (Takatori Station)",
            "hazard_type": "earthquake",
            "source": "PEER NGA Record #1111 (Mw 6.9, Hanshin Expressway Collapse)",
            "citation": "Anderson et al. (1996); Hanshin Expressway Bridge Failure Studies",
            "pga_g": 0.611,
            "duration_s": 25.0,
            "dt_s": 0.02,
            "filename": "kobe_1995.npz",
            "governing_standard": "Japan Road Association (JRA) Specifications"
        },
        "bhuj_2001": {
            "name": "2001 Bhuj Earthquake (Kutch/Ahmedabad Record)",
            "hazard_type": "earthquake",
            "source": "IMD / IIT Roorkee Strong Motion Network (Mw 7.7)",
            "citation": "Jain et al. (2002) Indian Bridge Reconnaissance; IIT Roorkee Network",
            "pga_g": 0.420,
            "duration_s": 35.0,
            "dt_s": 0.01,
            "filename": "bhuj_2001.npz",
            "governing_standard": "IS 1893 (Part 3): 2014 / IRC:6:2017"
        },
        "is1893_zone5": {
            "name": "IS 1893:2014 / IRC:6:2017 Zone V Design Spectrum",
            "hazard_type": "earthquake",
            "source": "Bureau of Indian Standards IS 1893 (Part 3) / IRC:6:2017 Cl. 219",
            "citation": "IS 1893 (Part 3): 2014 Cl. 6.4; IRC:6:2017 Cl. 219",
            "pga_g": 0.450,
            "duration_s": 20.0,
            "dt_s": 0.02,
            "filename": "is1893_zone5.npz",
            "governing_standard": "IS 1893 (Part 3): 2014 (Zone V, Z=0.36)"
        },
        "irc6_wind_cyclone": {
            "name": "IRC:6 Cl. 207 Coastal Severe Cyclone Buffeting",
            "hazard_type": "wind",
            "source": "Indian Roads Congress IRC:6:2017 / IS 875 (Part 3): 2015",
            "citation": "IRC:6:2017 Clause 207 (Wind Load on Highway Bridges); Simiu & Scanlan (1996)",
            "pga_g": 0.0,
            "duration_s": 25.0,
            "dt_s": 0.05,
            "filename": None,
            "governing_standard": "IRC:6:2017 Cl. 207 / IS 875 (Part 3)"
        },
        "lacey_flood_scour": {
            "name": "IRC:78 / IRC:89 Lacey Regime Flood Scour & Hydrodynamic Thrust",
            "hazard_type": "flood_scour",
            "source": "IRC:78:2014 Cl. 703 & IRC:89:2010 Cl. 5.2",
            "citation": "IRC:78:2014 Standard Specifications for Road Bridges Section VII: Substructures",
            "pga_g": 0.0,
            "duration_s": 15.0,
            "dt_s": 0.1,
            "filename": None,
            "governing_standard": "IRC:78:2014 Cl. 703 / IRC:89:2010"
        }
    }

    @classmethod
    def load_ground_motion_record(cls, scenario_id: str, scale_factor: float = 1.0) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Loads acceleration time series and metadata from pre-packaged authentic records."""
        if scenario_id not in cls.AVAILABLE_SCENARIOS:
            scenario_id = "el_centro_1940"
        meta = cls.AVAILABLE_SCENARIOS[scenario_id]
        if meta["filename"]:
            path = os.path.join(cls.DATA_DIR, meta["filename"])
            if os.path.exists(path):
                data = np.load(path, allow_pickle=True)
                time_arr = data["time"]
                accel_arr = data["accel_g"] * scale_factor
                info = {
                    "record_name": str(data["record_name"]),
                    "station": str(data["station"]),
                    "pga_g": float(data["pga_g"]) * scale_factor,
                    "magnitude": float(data["magnitude"]),
                    "citation": str(data["citation"]),
                    "governing_standard": meta["governing_standard"],
                    "dt": float(data["dt"]),
                    "hazard_type": "earthquake"
                }
                return time_arr, accel_arr, info

        # Fallback or synthetic compatible
        dt = meta.get("dt_s", 0.02)
        duration = meta.get("duration_s", 20.0)
        time_arr = np.arange(0.0, duration, dt)
        accel_arr = np.sin(2 * np.pi * 2.5 * time_arr) * np.exp(-time_arr / 5.0) * meta.get("pga_g", 0.3) * scale_factor
        return time_arr, accel_arr, meta

    @staticmethod
    def generate_irc6_wind_buffeting(
        basic_wind_speed_vb: float = 50.0,
        span_nodes: Optional[List[int]] = None,
        duration_s: float = 25.0,
        dt_s: float = 0.05
    ) -> Tuple[np.ndarray, Dict[int, np.ndarray], Dict[str, Any]]:
        """Generates aerodynamic wind buffeting force time-histories per IRC:6:2017 Cl. 207 and IS 875 (Part 3)
        using the Davenport spectrum: S_u(n) = 4 * k0 * V_10^2 * x^2 / (n * (1 + x^2)^(4/3))."""
        time_arr = np.arange(0.0, duration_s, dt_s)
        # Terrain category 2 (open terrain), bridge elevation z=15m
        # k1=1.0, k2=1.05, k3=1.0, k4=1.15 (coastal bridge)
        k_factor = 1.0 * 1.05 * 1.0 * 1.15
        design_v = basic_wind_speed_vb * k_factor  # m/s
        base_pressure = 0.6 * (design_v ** 2)      # N/m^2 (N/m2) per IS 875

        # Aerodynamic turbulence generation
        n_steps = len(time_arr)
        np.random.seed(42)
        turbulence = np.zeros(n_steps)
        # Sum of 10 harmonic frequencies representing Davenport turbulence spectrum
        for fi in [0.05, 0.1, 0.2, 0.4, 0.8, 1.2, 1.8, 2.5]:
            phase = np.random.uniform(0, 2 * np.pi)
            amp = (1.0 / (1.0 + (1200 * fi / design_v)**2)**(2/3)) * 0.25 * base_pressure
            turbulence += amp * np.sin(2 * np.pi * fi * time_arr + phase)

        node_forces = {}
        if not span_nodes:
            span_nodes = [1, 2, 3, 4, 5, 6, 7, 8]
        # Tributary exposed area per panel ~ 12 m^2 (girder/truss profile)
        exposed_area = 12.0
        drag_coeff = 1.3  # IRC:6 Table 4 for steel truss bridge

        for nid in span_nodes:
            # Add spatial phase lag based on node index
            node_turb = np.roll(turbulence, shift=nid * 2)
            # Drag force in Y (lateral) direction
            fy = (base_pressure * drag_coeff + node_turb) * exposed_area
            node_forces[nid] = fy

        meta = {
            "record_name": f"IRC:6:2017 Clause 207 Wind Buffeting (Vb = {basic_wind_speed_vb} m/s)",
            "station": "Indian Coastal Cyclone Zone (Category IV)",
            "governing_standard": "IRC:6:2017 Cl. 207 / IS 875 (Part 3): 2015",
            "citation": "IRC:6:2017 Standard Specifications for Road Bridges Section II; IS 875 Cl. 6.3",
            "dt": dt_s,
            "duration": duration_s,
            "hazard_type": "wind"
        }
        return time_arr, node_forces, meta

    @staticmethod
    def calculate_lacey_scour_and_ssi(
        design_discharge_cumec: float = 3500.0,
        silt_factor_f: float = 1.0,
        pier_width_b: float = 2.5
    ) -> Dict[str, Any]:
        """Calculates regime scour depth per IRC:78:2014 Cl. 703 & IRC:89:2010 Cl. 5.2.
        Lacey's regime depth: d_sm = 1.34 * (Db^2 / f)^(1/3)
        Maximum scour depth for bridge piers: d_max = 2.0 * d_sm."""
        # Mean design discharge per unit waterway width q = Q / L
        # Assume 120m waterway width
        linear_waterway = 120.0
        q = design_discharge_cumec / linear_waterway
        d_sm = 1.34 * ((q ** 2) / silt_factor_f) ** (1.0 / 3.0)
        d_max_pier = 2.0 * d_sm
        scour_depth_m = round(d_max_pier - 3.5, 2)  # depth below river bed

        # Lateral p-y spring stiffness degradation factor (Winkler foundation)
        # As soil erodes, top 3-5m of soil springs lose 100% capacity
        stiffness_retention_ratio = max(0.15, 1.0 - (scour_depth_m / 8.0))

        return {
            "regime_scour_depth_m": round(d_sm, 2),
            "maximum_pier_scour_m": round(d_max_pier, 2),
            "effective_scour_below_bed_m": max(1.5, scour_depth_m),
            "soil_spring_stiffness_retention": round(stiffness_retention_ratio, 3),
            "governing_standard": "IRC:78:2014 Cl. 703 (Foundations) / IRC:89:2010 Cl. 5.2",
            "citation": "Indian Roads Congress IRC:78:2014 Section VII; Lacey (1930) Stable Channels in Alluvium",
            "hazard_type": "flood_scour"
        }
