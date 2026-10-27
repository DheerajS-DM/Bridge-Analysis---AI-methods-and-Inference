import unittest
from physics.bridge_models import BridgeGenerator

class TestBridgeModels(unittest.TestCase):


    def test_generate_industrial_truss_bridge(self):
        nodes, elements = BridgeGenerator.generate_industrial_truss_bridge()
        self.assertGreater(len(nodes), 30)
        self.assertGreater(len(elements), 40)

if __name__ == "__main__":
    unittest.main()
