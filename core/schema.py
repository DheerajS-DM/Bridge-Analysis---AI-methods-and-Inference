from typing import List, Tuple, Dict, Optional, Any
from pydantic import BaseModel, Field

class Node3D(BaseModel):
    """Represents a 3D structural node with 6 Degrees of Freedom (DOFs)."""
    id: int
    x: float
    y: float
    z: float
    boundary_conditions: List[int] = Field(
        default_factory=lambda: [0, 0, 0, 0, 0, 0],
        description="6 DOFs: [ux, uy, uz, rx, ry, rz]. 1=fixed, 0=free"
    )

class ElementFrame(BaseModel):
    """Represents a 3D elastic/non-linear frame section element."""
    id: int
    node_start: int
    node_end: int
    section_type: str = "Steel_WSection"
    area_0: float = Field(..., description="Initial cross-sectional area (m^2)")
    iy_0: float = Field(..., description="Initial moment of inertia Y-axis (m^4)")
    iz_0: float = Field(..., description="Initial moment of inertia Z-axis (m^4)")
    j_0: float = Field(..., description="Initial torsional constant (m^4)")
    e_0: float = Field(..., description="Initial Elastic Modulus (Pa)")
    yield_stress_fy: float = Field(..., description="Yield stress capacity (Pa)")
    plastic_hinge_capacity: float = Field(..., description="Plastic moment capacity M_p (N.m)")
    damage_d: float = Field(default=0.0, description="Cumulative plastic damage metric [0, 1]")
    current_stress: float = Field(default=0.0, description="Current von Mises stress (Pa)")

class HazardContext(BaseModel):
    """Hyperparameter vector representing environmental and disaster conditions theta."""
    scenario_id: str = Field(default="el_centro_1940", description="Selected hazard record identifier")
    hazard_type: str = Field(default="earthquake", description="Hazard type (earthquake, wind, flood_scour, wave_surge)")
    wind_speed: float = Field(default=0.0, description="Wind speed magnitude (m/s)")
    scour_depth: float = Field(default=0.0, description="Foundation scour depth (m)")
    thermal_gradient: float = Field(default=0.0, description="Thermal gradient delta T (deg C)")
    seismic_pga: float = Field(default=0.0, description="Peak Ground Acceleration (g)")
    scale_factor: float = Field(default=1.0, description="Intensity scaling factor")

class AttackVector(BaseModel):
    """Represents a failure injection payload targeting a specific structural node or global domain."""
    target_node_id: int
    hazard_type: str
    impulse_vector: Optional[Tuple[float, float, float, float, float, float]] = None  # [Fx, Fy, Fz, Mx, My, Mz]
    utility_score: float = 0.0
    is_transient: bool = False
    record_id: Optional[str] = None
    time_series_meta: Dict[str, Any] = Field(default_factory=dict)

class DamageReport(BaseModel):
    """Represents forensic assessment findings for a distressed element governed by Indian Standards."""
    element_id: int
    component_type: str
    damage_category: str  # "plastic_hinge", "flange_yielding", "diagonal_buckling", "foundation_scour", etc.
    dcr: float            # Demand-to-Capacity Ratio (sigma / f_y)
    plastic_rotation: float = 0.0
    severity_score: float = 0.5
    governing_code: str = "IRC:SP:40:2019"
    criticality_rank: int = 1
    description: str = ""

class PlanAction(BaseModel):
    """Represents a standardized structural retrofit intervention operator for Partial Order Planning."""
    id: str
    name: str
    target_element_id: int
    standard_code: str = "IRC:SP:40:2019"
    clause_reference: str = "General Rehabilitation"
    academic_citation: str = ""
    preconditions: List[str] = Field(default_factory=list)
    effects: List[str] = Field(default_factory=list)
    duration_days: float = 3.0
    cost_inr: float = 0.0
    cost: float = 0.0
    phase: str = "primary"           # "emergency", "foundation", "primary", "verification"
    capacity_restoration_factor: float = 1.0
    curing_period_days: float = 0.0

    def model_post_init(self, __context: Any) -> None:
        if self.cost_inr == 0.0 and self.cost > 0.0:
            self.cost_inr = self.cost
        elif self.cost == 0.0 and self.cost_inr > 0.0:
            self.cost = self.cost_inr

class DynamicStepSnapshot(BaseModel):
    """Represents dynamic structural response at a discrete time step t."""
    time_step: float
    nodal_displacements: Dict[int, Tuple[float, float, float]]
    element_stresses: Dict[int, float]
    max_drift_ratio: float = 0.0
    peak_stress: float = 0.0
    ground_accel: float = 0.0

class PartialOrderPlan(BaseModel):
    """Represents a completed Partial Order Plan DAG with causal links and ordering constraints."""
    steps: List[PlanAction]
    orderings: List[Tuple[str, str]]
    causal_links: List[Tuple[str, str, str]]
    total_cost_inr: float = 0.0
    critical_path_days: float = 0.0
