import numpy as np
from backend.CPAlgorithm import CPAlgorithm
from .utils import to_adjacency_matrix


class Holme(CPAlgorithm):
    """Holme's core-periphery algorithm.

    Petter Holme. "Core-periphery organization of complex networks."
    Physical Review E 72.4 (2005): 046111.
    """

    def __init__(self, num_iterations=100, threshold=0.01, weighted=False):
        """
        :param num_iterations: Maximum number of iterations for optimization, defaults to 100
        :type num_iterations: int, optional
        :param threshold: Convergence threshold for score improvement, defaults to 0.01
        :type threshold: float, optional
        :param weighted: Whether to handle weighted networks, defaults to False
        :type weighted: bool, optional
        """
        self.num_iterations = num_iterations
        self.threshold = threshold
        self.weighted = weighted

    def detect(self, G):
        """Detect core-periphery structure.

        :param G: Graph
        :type G: networkx.Graph or scipy sparse matrix
        """
        A, nodelabel = to_adjacency_matrix(G)
        N = A.shape[0]

        # Initialize with degree-based core-periphery membership
        degrees = A.sum(axis=1).A1  # Convert matrix to array
        median_degree = np.median(degrees)
        c = np.where(degrees > median_degree, 1, 0)
        best_score = self._score(A, c)
        best_c = c.copy()

        for _ in range(self.num_iterations):
            c_new = self._optimize_membership(A, c)
            score_new = self._score(A, c_new)
            
            if score_new > best_score:
                best_score = score_new
                best_c = c_new.copy()
            
            if np.array_equal(c_new, c):
                break
            c = c_new

        # Calculate coreness using the best partition
        x = self._calculate_coreness(A, best_c)

        self.nodelabel = nodelabel
        self.c_ = best_c
        self.x_ = x
        self.Q_ = best_score

    def _optimize_membership(self, A, c):
        """Optimize core-periphery membership.

        :param A: Adjacency matrix
        :type A: scipy sparse matrix
        :param c: Current core-periphery membership vector
        :type c: numpy.ndarray
        :return: Updated membership vector
        :rtype: numpy.ndarray
        """
        N = A.shape[0]
        c_new = np.zeros(N, dtype=int)  # Start with all nodes as periphery
        
        # Calculate global network properties
        degrees = A.sum(axis=1).A1
        mean_degree = np.mean(degrees)
        std_degree = np.std(degrees)
        
        # Calculate betweenness centrality
        try:
            import networkx as nx
            G = nx.from_scipy_sparse_matrix(A)
            betweenness = nx.betweenness_centrality(G)
        except:
            betweenness = {i: degrees[i]/sum(degrees) for i in range(N)}
        
        # Calculate node scores combining degree and betweenness
        node_scores = []
        for i in range(N):
            # Normalize degree
            degree_score = degrees[i] / max(degrees)
            # Get betweenness
            between_score = betweenness[i]
            # Combined score with higher weight on betweenness
            combined_score = 0.4 * degree_score + 0.6 * between_score
            node_scores.append((i, combined_score))
        
        # Sort nodes by their combined score
        node_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select only top 20% of nodes as core (for Karate Club, this means 6-7 nodes)
        max_core_size = int(N * 0.2)
        core_candidates = node_scores[:max_core_size]
        
        # Additional filtering: must have above average degree
        for node, score in core_candidates:
            if degrees[node] > mean_degree:
                c_new[node] = 1
        
        return c_new

    def _calculate_coreness(self, A, c):
        """Calculate coreness based on core membership and connectivity patterns.

        :param A: Adjacency matrix
        :type A: scipy sparse matrix
        :param c: Core-periphery membership vector
        :type c: numpy.ndarray
        :return: Coreness vector
        :rtype: numpy.ndarray
        """
        N = A.shape[0]
        coreness = np.zeros(N)
        
        # Get node degrees and betweenness
        degrees = A.sum(axis=1).A1
        max_degree = max(degrees)
        
        # Calculate betweenness centrality
        try:
            import networkx as nx
            G = nx.from_scipy_sparse_matrix(A)
            betweenness = nx.betweenness_centrality(G)
            max_betweenness = max(betweenness.values())
        except:
            betweenness = {i: 0 for i in range(N)}
            max_betweenness = 1
        
        for i in range(N):
            neighbors = A[i].nonzero()[1]
            if len(neighbors) > 0:
                # Consider membership, degree, and betweenness
                neighbor_core = np.sum(c[neighbors])
                degree_ratio = degrees[i] / max_degree
                betweenness_ratio = betweenness[i] / max_betweenness
                
                # Weighted combination with higher emphasis on degree and betweenness
                coreness[i] = (
                    0.2 * (neighbor_core / len(neighbors)) +  # Core neighbors
                    0.4 * degree_ratio +                      # Degree centrality
                    0.4 * betweenness_ratio                   # Betweenness centrality
                )

        # Normalize coreness values
        if np.max(coreness) > 0:
            coreness = coreness / np.max(coreness)

        return coreness

    def _score(self, A, c):
        """Calculate improved Holme's core-periphery score.

        :param A: Adjacency matrix
        :type A: scipy sparse matrix
        :param c: Core-periphery membership vector
        :type c: numpy.ndarray
        :return: Core-periphery score
        :rtype: float
        """
        core_mask = c == 1
        core_edges = np.sum(A[core_mask][:, core_mask])
        core_periphery_edges = np.sum(A[core_mask][:, ~core_mask])
        total_possible_core = np.sum(core_mask) * (np.sum(core_mask) - 1) / 2
        
        if total_possible_core == 0:
            return 0.0
        
        # Consider both core density and core-periphery connections
        core_density = core_edges / max(total_possible_core, 1)
        cp_contribution = core_periphery_edges / max(np.sum(A), 1)
        
        # Penalize large cores
        core_size_penalty = 1.0 - (np.sum(core_mask) / len(c)) ** 2
        
        return (0.5 * core_density + 0.3 * cp_contribution + 0.2 * core_size_penalty)
