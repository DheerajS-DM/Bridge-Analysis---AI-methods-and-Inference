import polars as pl
import numpy as np

def compute_chloride_corrosion_area(a_0: float, t_years: float, t_init: float = 2.0, kappa: float = 0.015, gamma: float = 0.5) -> float:
    """Formulates cross-sectional loss A_k(t) = A_k(0) - kappa * (t - t_init)^gamma."""
    if t_years <= t_init:
        return a_0
    loss = kappa * ((t_years - t_init) ** gamma)
    return max(a_0 * 0.1, a_0 - loss)

def compute_modulus_decay(e_0: float, t_years: float, lambda_env: float = 0.005) -> float:
    """Formulates elastic modulus decay E_k(t) = E_k(0) * exp(-lambda_env * t)."""
    return float(e_0 * np.exp(-lambda_env * t_years))

def apply_chronic_degradation(elements_df: pl.DataFrame, t_years: float, lambda_env: float = 0.005, kappa: float = 0.015) -> pl.DataFrame:
    """Executes vectorized chronic deterioration across all frame sections in a single Polars kernel step."""
    return elements_df.with_columns([
        (pl.col("e_0") * (-lambda_env * t_years).exp()).alias("e_0"),
        (pl.col("area_0") - kappa * (t_years ** 0.5)).clip_lower(pl.col("area_0") * 0.1).alias("area_0")
    ])
