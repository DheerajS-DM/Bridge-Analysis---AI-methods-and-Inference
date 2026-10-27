import os
import polars as pl
from typing import List, Dict, Any, Optional
from core.schema import Node3D, ElementFrame

class StateManager:
    """Manages active simulation state in memory using Polars DataFrames and logs periodic checkpoints to Apache Parquet."""
    def __init__(self, storage_dir: str = "./data_logs"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.df_nodes: pl.DataFrame = pl.DataFrame()
        self.df_elements: pl.DataFrame = pl.DataFrame()
        self.df_telemetry: pl.DataFrame = pl.DataFrame()

    def initialize_tables(self, nodes: List[Node3D], elements: List[ElementFrame]) -> None:
        """Constructs Apache Arrow-backed Polars schemas for nodes and elements."""
        self.df_nodes = pl.DataFrame([n.model_dump() for n in nodes])
        self.df_elements = pl.DataFrame([e.model_dump() for e in elements])
        self.df_telemetry = pl.DataFrame(schema={
            "step": pl.Int64,
            "node_id": pl.Int64,
            "ux": pl.Float64, "uy": pl.Float64, "uz": pl.Float64,
            "rx": pl.Float64, "ry": pl.Float64, "rz": pl.Float64,
            "von_mises_stress": pl.Float64
        })

    def update_element_degradation(self, element_id: int, area_eff: float, e_eff: float, damage: float) -> None:
        """Performs in-place vectorized updates of element section capacity slots."""
        self.df_elements = self.df_elements.with_columns([
            pl.when(pl.col("id") == element_id)
            .then(pl.lit(area_eff))
            .otherwise(pl.col("area_0"))
            .alias("area_0"),
            pl.when(pl.col("id") == element_id)
            .then(pl.lit(e_eff))
            .otherwise(pl.col("e_0"))
            .alias("e_0"),
            pl.when(pl.col("id") == element_id)
            .then(pl.lit(damage))
            .otherwise(pl.col("damage_d"))
            .alias("damage_d")
        ])

    def update_element_stress(self, element_id: int, stress: float) -> None:
        """Updates element current von Mises stress."""
        self.df_elements = self.df_elements.with_columns([
            pl.when(pl.col("id") == element_id)
            .then(pl.lit(stress))
            .otherwise(pl.col("current_stress"))
            .alias("current_stress")
        ])

    def log_step_telemetry(self, step: int, displacements: Dict[int, List[float]], stresses: Dict[int, float]) -> None:
        """Appends 6-DOF displacements and von Mises stresses to active telemetry dataframe."""
        new_rows = []
        for node_id, disp in displacements.items():
            stress = stresses.get(node_id, 0.0)
            new_rows.append({
                "step": step,
                "node_id": node_id,
                "ux": disp[0], "uy": disp[1], "uz": disp[2],
                "rx": disp[3], "ry": disp[4], "rz": disp[5],
                "von_mises_stress": stress
            })
        if new_rows:
            new_df = pl.DataFrame(new_rows)
            self.df_telemetry = pl.concat([self.df_telemetry, new_df])

    def get_tensile_margin(self, node_id: int, adjacent_element_ids: List[int]) -> float:
        """Calculates S(n, t) = min_{e in Adj(n)} ((sigma_allowable - sigma_vonMises) / sigma_allowable)."""
        adj_df = self.df_elements.filter(pl.col("id").is_in(adjacent_element_ids))
        if len(adj_df) == 0:
            return 1.0
        margins = []
        for row in adj_df.iter_rows(named=True):
            fy = row["yield_stress_fy"]
            damage = row["damage_d"]
            allowable = fy * (1.0 - damage)
            current_stress = row.get("current_stress", 0.0)
            margin = (allowable - current_stress) / (allowable + 1e-6)
            margins.append(margin)
        return float(min(margins))

    def checkpoint_to_parquet(self, step: int) -> str:
        """Flushes active state frame snapshot into compressed Snappy Apache Parquet log."""
        filepath = os.path.join(self.storage_dir, f"state_checkpoint_step_{step:06d}.parquet")
        self.df_elements.write_parquet(filepath, compression="snappy")
        return filepath

    def query_history_slice(self, start_step: int, end_step: int) -> pl.DataFrame:
        """Queries historical telemetry slice lazily."""
        return self.df_telemetry.filter(
            (pl.col("step") >= start_step) & (pl.col("step") <= end_step)
        )
