import numpy as np
import polars as pl
from typing import Dict, Tuple, List, Any
from core.schema import HazardContext, AttackVector
from core.state_manager import StateManager
from core.semantic_network import OntologicalSemanticNet
from physics.hazard_load_patterns import SourcedHazardLoadFactory

class BayesianHazardUtilityEngine:
    """Computes posterior hazard probabilities P(E_i | theta) and maximizes multi-factor destructive utility U(n).
    Returns intermediate candidate evaluation metrics for the thought-process visualization popup."""
    def __init__(self, omega_penalty: float = 2.5):
        self.omega = omega_penalty
        self.hazard_types = ["earthquake", "wind", "flood_scour"]
        self.prior_probabilities = {"earthquake": 0.4, "wind": 0.35, "flood_scour": 0.25}

    def compute_hazard_posteriors(self, weather: HazardContext) -> Dict[str, float]:
        """Calculates posterior hazard probabilities P(E_i | theta) given weather context."""
        likelihoods = {
            "earthquake": 1.0 + (weather.seismic_pga * 6.0),
            "wind": 1.0 + (weather.wind_speed / 8.0),
            "flood_scour": 1.0 + (weather.scour_depth * 2.5)
        }
        unnorm = {h: likelihoods[h] * self.prior_probabilities[h] for h in self.hazard_types}
        total = sum(unnorm.values())
        return {h: unnorm[h] / total for h in self.hazard_types}

    def select_optimal_attack_target(
        self,
        nodes_df: pl.DataFrame,
        state_mgr: StateManager,
        net: OntologicalSemanticNet,
        weather: HazardContext
    ) -> Tuple[AttackVector, List[str], Dict[str, Any]]:
        """Evaluates ArgMax_n U(n). Returns attack vector, professional logs, and candidate metrics."""
        logs = []
        posteriors = self.compute_hazard_posteriors(weather)
        logs.append("[HAZARD INFERENCE] Computed Bayesian posterior probabilities P(E_i | theta):")
        for h, p in posteriors.items():
            logs.append(f"   - {h.replace('_', ' ').title()}: P = {p:.3f}")

        best_node_id = -1
        max_utility = -float("inf")
        min_margin = 1.0
        best_hazard = max(posteriors, key=posteriors.get)

        candidate_scores: List[Dict[str, Any]] = []

        logs.append(f"[HEURISTIC EVALUATION] Engaged Vulnerability Heuristic (Tensile Margin Penalty omega={self.omega}):")
        logs.append(f"   Scanning {len(nodes_df)} candidate structural nodes for critical tensile margin S(n, t)...")

        for row in nodes_df.iter_rows(named=True):
            node_id = row["id"]
            adj_elements = net.get_adjacent_elements(node_id)
            S_n = state_mgr.get_tensile_margin(node_id, adj_elements)

            # Expected destructive utility U(n) = Base Force - omega * Tensile_Margin * Scale
            base_force = 450000.0 if best_hazard == "earthquake" else 250000.0
            utility = base_force * (1.0 + posteriors[best_hazard]) - (self.omega * S_n * 120000.0)

            candidate_scores.append({
                "node_id": node_id,
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row["z"]),
                "tensile_margin": round(S_n, 3),
                "utility": round(utility, 1)
            })

            if utility > max_utility:
                max_utility = utility
                best_node_id = node_id
                min_margin = S_n

        # Rank candidates descending by utility
        candidate_scores.sort(key=lambda c: c["utility"], reverse=True)
        top_candidates = candidate_scores[:5]

        logs.append(f"[TARGET SELECTION] ArgMax_n U(n) selected Node #{best_node_id} (Tensile Margin S(n,t)={min_margin:.3f}).")
        logs.append(f"[FAILURE HYPOTHESIS] Primary vulnerability identified at Node #{best_node_id} under dominant {best_hazard.title()} excitation. Risk Utility U(n)={max_utility/1e3:.2f} kN equivalent.")

        # Determine load scenario record
        scenario_id = weather.scenario_id or ("el_centro_1940" if best_hazard == "earthquake" else "irc6_wind_cyclone")
        scenario_meta = SourcedHazardLoadFactory.AVAILABLE_SCENARIOS.get(scenario_id, {})

        attack_vec = AttackVector(
            target_node_id=best_node_id,
            hazard_type=best_hazard,
            impulse_vector=(400000.0, 0.0, -200000.0, 0.0, 0.0, 0.0),
            utility_score=max_utility,
            is_transient=True,
            record_id=scenario_id,
            time_series_meta=scenario_meta
        )

        thought_data = {
            "posteriors": posteriors,
            "best_node_id": best_node_id,
            "min_margin": min_margin,
            "top_candidates": top_candidates,
            "best_hazard": best_hazard,
            "scenario_meta": scenario_meta,
            "summary_text": f"Node #{best_node_id} prioritized: Lowest tensile margin ({min_margin:.2f}) under dominant {best_hazard.title()} hazard."
        }

        return attack_vec, logs, thought_data
