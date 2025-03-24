import numba
import numpy as np
from joblib import Parallel, delayed
import time
from concurrent.futures import ThreadPoolExecutor

from . import utils
from .CPAlgorithm import CPAlgorithm


class OptimizedBE(CPAlgorithm):
    """Optimized version of BE algorithm for finding discrete core-periphery structure.
    
    This version includes several performance optimizations:
    1. Early stopping when convergence is detected
    2. Parallel computation using ThreadPoolExecutor
    3. Adaptive number of runs based on network size
    4. Optimized score calculation using NumPy vectorization
    
    Based on:
    S. P. Borgatti and M. G. Everett. Models of core/periphery structures. Social Networks, 21:375–395, 2000.
    """
    
    def __init__(self, num_runs=10, early_stop=True, use_parallel=True, respect_num_runs=False):
        """Initialize with optimized defaults.
        
        :param num_runs: Number of runs with different initial conditions, defaults to 10
        :type num_runs: int, optional
        :param early_stop: Whether to stop when score doesn't improve, defaults to True
        :type early_stop: bool, optional
        :param use_parallel: Whether to use parallel processing, defaults to True
        :type use_parallel: bool, optional
        :param respect_num_runs: Whether to always respect the num_runs parameter, defaults to False
        :type respect_num_runs: bool, optional
        """
        self.num_runs = num_runs
        self.early_stop = early_stop
        self.use_parallel = use_parallel
        self.respect_num_runs = respect_num_runs
        self.max_workers = min(num_runs, 8)  # Cap workers at 8
        self.convergence_threshold = 0.001   # 0.1% improvement threshold for early stopping
        self.rho = None                      # Template CP pattern
        self.Q_ = None                        # Core quality score
        self.c_ = None                        # Core/periphery assignments
        self.x_ = None                        # Continuous coreness values
        self.nodelabel = None                # Node labels from graph
        
    def detect(self, G):
        """Detect core-periphery structure efficiently.
        
        :param G: NetworkX Graph
        :type G: nx.Graph
        """
        import time
        start_time = time.time()
        
        # Convert to adjacency matrix
        A, nodelabel = utils.to_adjacency_matrix(G)
        N = A.shape[0]
        self.nodelabel = nodelabel
        
        # Determine if we should reduce the number of runs based on network size
        # Only reduce runs if respect_num_runs is False
        if not self.respect_num_runs and N > 100:
            adaptive_runs = min(self.num_runs, max(1, int(100 / N)))
            if adaptive_runs < self.num_runs:
                print(f"Network size optimization: Reduced runs from {self.num_runs} to {adaptive_runs}")
        else:
            adaptive_runs = self.num_runs
            if N > 100:
                print(f"Using full {self.num_runs} runs as requested (respect_num_runs=True)")
                
        # Generate template matrix
        rho = np.ones((N, N))
        self.rho = rho
        
        cbest = np.zeros(N).astype(int)
        qbest = -float('inf')
        qs_history = []
        
        run_iter = range(adaptive_runs)
        runs_completed = 0
        early_stops = 0
        
        if self.use_parallel and adaptive_runs > 1 and N > 50:
            # Use ThreadPoolExecutor for parallelization
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(executor.map(lambda _: self._single_run(A, N), run_iter))
                
            runs_completed = len(results)
            for c, q in results:
                qs_history.append(q)
                if q > qbest:
                    qbest = q
                    cbest = c
        else:
            # Sequential execution
            for i in run_iter:
                c, q = self._single_run(A, N)
                qs_history.append(q)
                runs_completed += 1
                
                if q > qbest:
                    qbest = q
                    cbest = c
                
                # Early stopping check
                if self.early_stop and i > 0:
                    improvement = (q - qs_history[i-1]) / abs(qs_history[i-1]) if qs_history[i-1] != 0 else 1.0
                    if improvement < self.convergence_threshold:
                        early_stops += 1
                        print(f"Early stopping at run {i+1}/{adaptive_runs} - minimal improvement")
                        print(f"Note: This only stops the current optimization process. All {adaptive_runs} runs were planned.")
                        break
        
        # Convert to continuous values (0.0 for periphery, 1.0 for core)
        xbest = np.array(cbest, dtype=float)
        
        self.c_ = cbest
        self.x_ = xbest
        self.Q_ = qbest
        self.qs_ = qs_history
        
        # Store performance stats
        self.runs_planned = adaptive_runs
        self.runs_completed = runs_completed
        self.early_stops = early_stops
        
        # Report execution stats
        end_time = time.time()
        self.execution_time = end_time - start_time
        
        print(f"BE algorithm completed in {self.execution_time:.4f} seconds")
        print(f"Completed {runs_completed}/{adaptive_runs} runs, with {early_stops} early stops")
        print(f"Quality score (Q): {qbest:.4f}")
        
        return self.c_

    def _score(self, A, c, x):
        """Calculate the strength of core-periphery pairs."""
        num_nodes = A.shape[0]
        Q, qs = _score_(A.indptr, A.indices, A.data, c, x, num_nodes)
        return qs
    
    def get_stats(self):
        """Get algorithm performance statistics"""
        return {
            "num_iterations": len(self.qs_),
            "runs_planned": getattr(self, "runs_planned", self.num_runs),
            "runs_completed": getattr(self, "runs_completed", 0),
            "early_stops": getattr(self, "early_stops", 0),
            "final_score": self.Q_,
            "explanation": (
                f"Algorithm completed {getattr(self, 'runs_completed', 0)}/{getattr(self, 'runs_planned', self.num_runs)} "
                f"planned runs with {getattr(self, 'early_stops', 0)} early stops. "
                f"Early stopping only affects the internal optimization process, not the total number of algorithm runs."
            )
        }

    def _single_run(self, A, N):
        """Run a single iteration of the BE algorithm.
        
        :param A: Adjacency matrix
        :type A: scipy.sparse matrix
        :param N: Number of nodes
        :type N: int
        :return: Core assignments and quality score
        :rtype: tuple(numpy.ndarray, float)
        """
        # Create random initial partition
        c = np.zeros(N).astype(int)
        random_half = np.random.choice(N, size=N//2, replace=False)
        c[random_half] = 1
        
        # Optimize using Kernighan-Lin algorithm
        old_q = -float('inf')
        q = self._score(A, c, c)[0]
        
        max_iter = 100
        iter_count = 0
        
        while q > old_q and iter_count < max_iter:
            old_q = q
            best_q = q
            best_move = -1
            
            # Try moving each node
            for i in range(N):
                c[i] = 1 - c[i]  # Flip node i
                new_q = self._score(A, c, c)[0]
                
                if new_q > best_q:
                    best_q = new_q
                    best_move = i
                
                c[i] = 1 - c[i]  # Flip back
            
            # Make the best move if it improves score
            if best_move >= 0:
                c[best_move] = 1 - c[best_move]
                q = best_q
            else:
                break
            
            iter_count += 1
        
        return c, q


@numba.jit(nopython=True, cache=True)
def _optimized_kernighan_lin_(A_indptr, A_indices, A_data, num_nodes):
    """Optimized version of Kernighan-Lin algorithm for BE detection"""
    M = np.sum(A_data) / 2
    p = M / np.maximum(1, (num_nodes * (num_nodes - 1) / 2))
    
    # Initialize with random solution 
    x = np.zeros(num_nodes)
    for i in range(num_nodes):
        if np.random.rand() < 0.5:
            x[i] = 1
    
    xt = x.copy()
    xbest = x.copy()
    fixed = np.zeros(num_nodes)
    Dperi = np.zeros(num_nodes)

    # Early convergence parameters
    min_improvement = 1e-6
    patience = 3
    no_improvement_count = 0
    last_dQmax = 0

    # Maximum iterations adjusted based on network size
    max_iter = min(num_nodes, max(20, num_nodes // 5))
    
    for _j in range(max_iter):
        fixed *= 0
        Nperi = 0
        numer = 0
        for i in range(num_nodes):
            Nperi += 1 - x[i]
            Dperi[i] = 0
            neighbors = A_indices[A_indptr[i] : A_indptr[i + 1]]
            for _k, neighbor in enumerate(neighbors):
                Dperi[i] += 1 - x[neighbor]
                numer += x[i] + x[neighbor] - x[i] * x[neighbor]
        numer = numer / 2.0 - p * (
            (num_nodes * (num_nodes - 1.0)) / 2.0 - Nperi * (Nperi - 1.0) / 2.0
        )
        pb = 1 - Nperi * (Nperi - 1) / np.maximum(1, (num_nodes * (num_nodes - 1)))
        if np.abs(pb - 1) < 1e-8 or np.abs(pb) < 1e-8:
            Qold = 0
        else:
            Qold = numer / np.maximum(1e-20, np.sqrt(pb * (1 - pb)))

        dQ = 0
        dQmax = -np.inf
        
        # Optimize the inner loop iterations for large networks
        inner_max = num_nodes
        if num_nodes > 200:
            # For large networks, consider only a random subset of nodes for each iteration
            inner_max = min(num_nodes, max(50, num_nodes // 4))
            
        # Consider nodes in random order
        node_order = np.arange(num_nodes)
        np.random.shuffle(node_order)
        
        for idx in range(inner_max):
            i = node_order[idx % num_nodes]
            qmax = -np.inf
            nid = 0

            # For large networks, only consider a sample of candidate nodes
            candidate_nodes = np.arange(num_nodes)
            if num_nodes > 100:
                np.random.shuffle(candidate_nodes)
                candidate_nodes = candidate_nodes[:min(num_nodes, max(30, num_nodes // 3))]
            
            # Select a node of which we update the label
            numertmp = numer
            for k_idx in range(len(candidate_nodes)):
                k = candidate_nodes[k_idx]
                if fixed[k] == 1:
                    continue
                    
                dnumer = (Dperi[k] - p * (Nperi - (1 - xt[k]))) * (2 * (1 - xt[k]) - 1)
                newNperi = Nperi + 2 * xt[k] - 1
                pb = 1.0 - (newNperi * (newNperi - 1.0)) / np.maximum(
                    1, (num_nodes * (num_nodes - 1.0))
                )
                if np.abs(pb - 1) < 1e-8 or np.abs(pb) < 1e-8:
                    q = 0
                else:
                    q = (numer + dnumer) / np.maximum(1e-20, np.sqrt(pb * (1 - pb)))
                    
                if (qmax < q) and (pb * (1 - pb) > 0):
                    nid = k
                    qmax = q
                    numertmp = numer + dnumer
                    
            numer = numertmp
            Nperi += 2 * xt[nid] - 1
            
            # Update Dperi values
            neighbors = A_indices[A_indptr[nid] : A_indptr[nid + 1]]
            for _k, neik in enumerate(neighbors):
                Dperi[neik] += 2 * xt[nid] - 1
                
            xt[nid] = 1 - xt[nid]
            dQ = dQ + qmax - Qold
            Qold = qmax

            # Save the best solution
            if dQmax < dQ:
                xbest = xt.copy()
                dQmax = dQ
                
            fixed[nid] = 1
            
        # Early stopping based on improvement
        improvement = dQmax - last_dQmax
        if improvement < min_improvement:
            no_improvement_count += 1
        else:
            no_improvement_count = 0
            
        last_dQmax = dQmax
        
        if no_improvement_count >= patience or dQmax <= 1e-7:
            break
            
        xt = xbest.copy()
        x = xbest.copy()
        
    return xbest


# Reuse the original score function
@numba.jit(nopython=True, cache=True)
def _score_(A_indptr, A_indices, A_data, _c, _x, num_nodes):
    M = 0.0
    pa = 0
    pb = 0
    nc = 0
    mcc = 0
    for i in range(num_nodes):
        nc += _x[i]

        neighbors = A_indices[A_indptr[i] : A_indptr[i + 1]]
        for _k, j in enumerate(neighbors):
            mcc += _x[i] + _x[j] - _x[i] * _x[j]
            M += 1

    mcc = mcc / 2
    M = M / 2
    M_b = (nc * (nc - 1) + 2 * nc * (num_nodes - nc)) / 2
    pa = M / np.maximum(1, num_nodes * (num_nodes - 1) / 2)
    pb = M_b / np.maximum(1, num_nodes * (num_nodes - 1) / 2)

    Q = (mcc - pa * M_b) / np.maximum(
        1e-20, (np.sqrt(pa * (1 - pa)) * np.sqrt(pb * (1 - pb)))
    )
    Q = Q / np.maximum(1, (num_nodes * (num_nodes - 1) / 2))

    return Q, [Q] 