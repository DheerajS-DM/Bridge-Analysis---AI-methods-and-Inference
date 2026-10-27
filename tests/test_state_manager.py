import os
import tempfile
import unittest
from core.schema import Node3D, ElementFrame
from core.state_manager import StateManager

class TestStateManager(unittest.TestCase):
    def test_state_manager_initialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = StateManager(storage_dir=tmp_dir)
            nodes = [Node3D(id=1, x=0.0, y=0.0, z=0.0)]
            elements = [ElementFrame(id=1, node_start=1, node_end=2, area_0=0.01, iy_0=1e-4, iz_0=1e-4, j_0=1e-4, e_0=2e11, yield_stress_fy=3.5e8, plastic_hinge_capacity=1e5)]
            mgr.initialize_tables(nodes, elements)
            self.assertEqual(len(mgr.df_nodes), 1)
            self.assertEqual(len(mgr.df_elements), 1)

    def test_parquet_checkpointing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = StateManager(storage_dir=tmp_dir)
            nodes = [Node3D(id=1, x=0.0, y=0.0, z=0.0)]
            elements = [ElementFrame(id=1, node_start=1, node_end=2, area_0=0.01, iy_0=1e-4, iz_0=1e-4, j_0=1e-4, e_0=2e11, yield_stress_fy=3.5e8, plastic_hinge_capacity=1e5)]
            mgr.initialize_tables(nodes, elements)
            filepath = mgr.checkpoint_to_parquet(step=1)
            self.assertTrue(os.path.exists(filepath))

if __name__ == "__main__":
    unittest.main()
