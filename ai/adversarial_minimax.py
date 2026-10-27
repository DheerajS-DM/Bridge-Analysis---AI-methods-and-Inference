from typing import List, Tuple, Optional
import polars as pl
from physics.opensees_wrapper import OpenSeesFEASolver

class AdversarialMinimaxEngine:
    """Evaluates multi-step cascading failure sequences using Minimax search with Physics-Informed Alpha-Beta Pruning."""
    def __init__(self, max_depth: int = 4, prune_threshold: float = 0.35):
        self.max_depth = max_depth
        self.prune_threshold = prune_threshold

    def evaluate_state_score(self, solver: OpenSeesFEASolver, nodes_df: pl.DataFrame) -> float:
        """Calculates global strain energy / cumulative displacement evaluation metric."""
        node_ids = nodes_df["id"].to_list()
        disps = solver.extract_nodal_displacements(node_ids)
        total_disp = sum(sum(abs(val) for val in d[:3]) for d in disps.values())
        return float(total_disp)

    def minimax(
        self,
        solver: OpenSeesFEASolver,
        depth: int,
        alpha: float,
        beta: float,
        is_attacker: bool,
        candidate_nodes: List[int],
        nodes_df: pl.DataFrame
    ) -> Tuple[float, Optional[int]]:
        """Adversarial game-tree search with physics-informed alpha-beta pruning."""
        if depth == 0 or not candidate_nodes:
            return self.evaluate_state_score(solver, nodes_df), None

        best_target = None
        if is_attacker:
            max_eval = -float("inf")
            for node_id in candidate_nodes:
                solver.apply_impulse_load(node_id, (100000.0, 0.0, 0.0, 0.0, 0.0, 0.0))
                converged = solver.solve_static_step()
                if not converged:
                    return 1e9, node_id

                eval_score, _ = self.minimax(solver, depth - 1, alpha, beta, False, candidate_nodes, nodes_df)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_target = node_id

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-Beta Pruning
            return max_eval, best_target
        else:
            min_eval = float("inf")
            solver.solve_static_step()
            eval_score, _ = self.minimax(solver, depth - 1, alpha, beta, True, candidate_nodes, nodes_df)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                pass  # Alpha-Beta Pruning
            return min_eval, None
