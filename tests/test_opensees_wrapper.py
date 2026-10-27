import unittest
import polars as pl
from core.schema import Node3D, ElementFrame
from physics.opensees_wrapper import OpenSeesFEASolver

class TestOpenSeesWrapper(unittest.TestCase):
    def test_opensees_build_and_solve(self):
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
        self.assertTrue(solver.is_built)
        
        solver.apply_impulse_load(2, (1000.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        converged = solver.solve_static_step()
        self.assertTrue(converged)
        
        disps = solver.extract_nodal_displacements([1, 2])
        self.assertIn(2, disps)
    def test_apply_load_after_ospgrillage_model(self):
        from physics.bridge_models import BridgeGenerator
        nodes, elements = BridgeGenerator.generate_industrial_truss_bridge()
        nodes_df = pl.DataFrame([n.model_dump() for n in nodes])
        elements_df = pl.DataFrame([e.model_dump() for e in elements])
        solver = OpenSeesFEASolver()
        solver.build_fea_model(nodes_df, elements_df)
        self.assertTrue(solver.is_built)
        
        # Test multiple load applications with dynamic tag allocation
        target_node = nodes[10].id
        solver.apply_impulse_load(target_node, (10000.0, 0.0, -50000.0, 0.0, 0.0, 0.0))
        converged = solver.solve_static_step()
        self.assertTrue(converged)
        
        solver.apply_impulse_load(target_node, (20000.0, 0.0, -100000.0, 0.0, 0.0, 0.0))
        converged2 = solver.solve_static_step()
        self.assertTrue(converged2)
        solver.reset_model()

if __name__ == "__main__":
    unittest.main()
