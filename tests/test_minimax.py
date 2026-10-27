import unittest
import polars as pl
from core.schema import Node3D, ElementFrame
from physics.opensees_wrapper import OpenSeesFEASolver
from ai.adversarial_minimax import AdversarialMinimaxEngine

class TestAdversarialMinimax(unittest.TestCase):
    def test_minimax_search(self):
        solver = OpenSeesFEASolver()
        nodes = [
            Node3D(id=1, x=0.0, y=0.0, z=0.0, boundary_conditions=[1, 1, 1, 1, 1, 1]),
            Node3D(id=2, x=0.0, y=0.0, z=3.0, boundary_conditions=[0, 0, 0, 0, 0, 0])
        ]
        elements = [
            ElementFrame(id=1, node_start=1, node_end=2, area_0=0.01, iy_0=1e-4, iz_0=1e-4, j_0=1e-4, e_0=2e11, yield_stress_fy=3.5e8, plastic_hinge_capacity=1e5)
        ]
        nodes_df = pl.DataFrame([n.model_dump() for n in nodes])
        elements_df = pl.DataFrame([e.model_dump() for e in elements])
        solver.build_fea_model(nodes_df, elements_df)

        minimax_engine = AdversarialMinimaxEngine(max_depth=2)
        score, target = minimax_engine.minimax(
            solver=solver,
            depth=2,
            alpha=-float("inf"),
            beta=float("inf"),
            is_attacker=True,
            candidate_nodes=[2],
            nodes_df=nodes_df
        )
        self.assertEqual(target, 2)
        solver.reset_model()

if __name__ == "__main__":
    unittest.main()
