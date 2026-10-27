import numpy as np

class DynamicBayesianInference:
    """Dynamic Bayesian Network / Hidden Markov Model for tracking latent degradation states under noisy observations."""
    def __init__(self, n_states: int = 3):
        self.n_states = n_states
        # Default Transition Matrix P(X_t | X_{t-1}): [Intact, Corroded/Cracked, Plastic Yield]
        self.T = np.array([
            [0.95, 0.04, 0.01],
            [0.00, 0.90, 0.10],
            [0.00, 0.00, 1.00]
        ])
        # Default Emission Matrix P(e_t | X_t) for noisy sensor observations
        self.E = np.array([
            [0.85, 0.12, 0.03],
            [0.10, 0.80, 0.10],
            [0.02, 0.18, 0.80]
        ])

    def predict(self, prior_belief: np.ndarray) -> np.ndarray:
        """Computes prediction step: P(X_t | e_{1:t-1}) = int P(X_t | X_{t-1}) P(X_{t-1} | e_{1:t-1}) dX_{t-1}."""
        return np.dot(prior_belief, self.T)

    def update(self, predicted_belief: np.ndarray, observation_idx: int) -> np.ndarray:
        """Computes posterior update: P(X_t | e_{1:t}) = alpha * P(e_t | X_t) * P(X_t | e_{1:t-1})."""
        likelihood = self.E[:, observation_idx]
        posterior = likelihood * predicted_belief
        return posterior / (np.sum(posterior) + 1e-12)

    def filter_step(self, prior_belief: np.ndarray, observation_idx: int) -> np.ndarray:
        """Executes forward Bayesian filter step."""
        pred = self.predict(prior_belief)
        return self.update(pred, observation_idx)
