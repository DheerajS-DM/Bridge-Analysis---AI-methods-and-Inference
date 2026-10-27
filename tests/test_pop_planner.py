import unittest
from core.schema import PlanAction
from ai.partial_order_planner import PartialOrderPlanner

class TestPartialOrderPlanner(unittest.TestCase):
    def test_partial_order_planning(self):
        planner = PartialOrderPlanner()
        op1 = PlanAction(id="Act1", name="Install Shoring", target_element_id=1, preconditions=["Damage"], effects=["ShoringInstalled"], duration_days=2, cost=1000)
        op2 = PlanAction(id="Act2", name="Replace Section", target_element_id=1, preconditions=["ShoringInstalled"], effects=["Repaired"], duration_days=5, cost=5000)
        
        planner.add_available_action(op1)
        planner.add_available_action(op2)

        plan = planner.solve(initial_state={"Damage"}, goal_conditions={"Repaired"})
        self.assertGreaterEqual(len(plan.steps), 3)  # Start + Finish + matching operators
        step_ids = [s.id for s in plan.steps]
        self.assertIn("Act2", step_ids)

if __name__ == "__main__":
    unittest.main()
