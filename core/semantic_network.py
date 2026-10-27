import networkx as nx
import polars as pl
from typing import List, Dict, Any, Tuple

class OntologicalSemanticNet:
    """Maps FEA physical topology into a Frame-and-Slot Ontological Semantic Multigraph."""
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def build_network(self, nodes_df: pl.DataFrame, elements_df: pl.DataFrame) -> None:
        """Constructs topological graph with node slots and element frames."""
        self.graph.clear()
        for row in nodes_df.iter_rows(named=True):
            self.graph.add_node(
                row["id"],
                coords=(row["x"], row["y"], row["z"]),
                dof_bc=row["boundary_conditions"]
            )
        for row in elements_df.iter_rows(named=True):
            self.graph.add_edge(
                row["node_start"],
                row["node_end"],
                key=row["id"],
                element_id=row["id"],
                section=row["section_type"],
                area=row["area_0"],
                e_modulus=row["e_0"],
                yield_stress=row["yield_stress_fy"],
                plastic_capacity=row["plastic_hinge_capacity"]
            )

    def get_adjacent_elements(self, node_id: int) -> List[int]:
        """Retrieves list of connected frame element IDs for a structural node."""
        element_ids = []
        for u, v, k, data in self.graph.edges(node_id, keys=True, data=True):
            element_ids.append(data["element_id"])
        for u, v, k, data in self.graph.in_edges(node_id, keys=True, data=True):
            element_ids.append(data["element_id"])
        return list(set(element_ids))

    def update_frame_slot(self, element_id: int, slot: str, value: Any) -> None:
        """Updates slot values dynamically within the topological multigraph."""
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            if data.get("element_id") == element_id:
                self.graph[u][v][k][slot] = value
                break

    def find_redundant_load_paths(self, source_node: int, boundary_nodes: List[int]) -> List[List[int]]:
        """Computes redundant kinematic load paths using graph traversal algorithms."""
        paths = []
        for target in boundary_nodes:
            if target != source_node and self.graph.has_node(target):
                try:
                    for path in nx.all_simple_paths(self.graph.to_undirected(), source=source_node, target=target, cutoff=5):
                        paths.append(path)
                except nx.NetworkXNoPath:
                    continue
        return paths
