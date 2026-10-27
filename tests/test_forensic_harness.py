import unittest
import numpy as np
import polars as pl
from core.schema import Node3D, ElementFrame, HazardContext
from physics.hazard_load_patterns import SourcedHazardLoadFactory
from physics.bridge_models import BridgeGenerator
from physics.model_importer import BridgeModelImporter
from ai.damage_assessor import DamageAssessor
from ai.retrofit_library import IRCRetrofitActionLibrary
from ai.partial_order_planner import PartialOrderPlanner

class TestForensicHarness(unittest.TestCase):
    def test_sourced_ground_motions_and_factory(self):
        t, acc, meta = SourcedHazardLoadFactory.load_ground_motion_record("el_centro_1940")
        self.assertGreater(len(t), 100)
        self.assertAlmostEqual(meta["pga_g"], 0.313, places=2)
        self.assertEqual(meta["hazard_type"], "earthquake")

    def test_indian_standards_scour_model(self):
        scour_res = SourcedHazardLoadFactory.calculate_lacey_scour_and_ssi(design_discharge_cumec=3500.0)
        self.assertGreater(scour_res["maximum_pier_scour_m"], 0.0)
        self.assertIn("IRC:78:2014", scour_res["governing_standard"])

    def test_expanded_bridge_models(self):
        nodes, elements = BridgeGenerator.generate_caltrans_box_girder_bridge()
        self.assertGreater(len(nodes), 20)
        self.assertGreater(len(elements), 20)

        nodes_arch, elements_arch = BridgeGenerator.generate_tied_arch_bridge()
        self.assertGreater(len(nodes_arch), 20)

    def test_damage_assessment_and_irc_planning(self):
        nodes, elements = BridgeGenerator.generate_industrial_truss_bridge()
        df_elements = pl.DataFrame([e.model_dump() for e in elements])
        stresses = {e.id: float(e.yield_stress_fy) * 1.15 for e in elements[:3]}

        reports = DamageAssessor.assess_structure(df_elements, stresses, scour_depth_m=2.5)
        self.assertGreater(len(reports), 0)
        top_rep = reports[0]
        self.assertGreater(top_rep.dcr, 0.8)

        planner = PartialOrderPlanner()
        planner.generate_actions_from_damage_reports(reports)
        plan = planner.solve(initial_state={"DamageDetected"}, goal_conditions={"FlexuralCapacityRestored"})
        self.assertGreater(len(plan.steps), 2)
        self.assertGreater(plan.total_cost_inr, 0.0)

if __name__ == "__main__":
    unittest.main()
