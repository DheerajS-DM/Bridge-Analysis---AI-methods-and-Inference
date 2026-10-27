import unittest
import polars as pl
from core.schema import Node3D, ElementFrame, HazardContext
from core.state_manager import StateManager
from core.semantic_network import OntologicalSemanticNet
from ai.hazard_utility_engine import BayesianHazardUtilityEngine

class TestBayesianUtility(unittest.TestCase):
    def test_hazard_posteriors_and_utility(self):
        engine = BayesianHazardUtilityEngine()
        weather = HazardContext(wind_speed=30.0, scour_depth=2.0, seismic_pga=0.5)
        posteriors = engine.compute_hazard_posteriors(weather)
        self.assertAlmostEqual(sum(posteriors.values()), 1.0, places=4)

        state_mgr = StateManager()
        net = OntologicalSemanticNet()
        nodes = [
            Node3D(id=1, x=0.0, y=0.0, z=0.0, boundary_conditions=[1, 1, 1, 1, 1, 1]),
            Node3D(id=2, x=0.0, y=0.0, z=3.0, boundary_conditions=[0, 0, 0, 0, 0, 0])
        ]
        elements = [
            ElementFrame(id=1, node_start=1, node_end=2, area_0=0.01, iy_0=1e-4, iz_0=1e-4, j_0=1e-4, e_0=2e11, yield_stress_fy=3.5e8, plastic_hinge_capacity=1e5)
        ]
        state_mgr.initialize_tables(nodes, elements)
        net.build_network(state_mgr.df_nodes, state_mgr.df_elements)

        attack_vec, logs, thought_data = engine.select_optimal_attack_target(state_mgr.df_nodes, state_mgr, net, weather)
        self.assertIn(attack_vec.target_node_id, [1, 2])
        self.assertGreater(len(logs), 0)
        self.assertIn("top_candidates", thought_data)

if __name__ == "__main__":
    unittest.main()
