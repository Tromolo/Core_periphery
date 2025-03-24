import networkx as nx
import time
import numpy as np
import cpnet
from backend.rombach import Rombach
from backend.optimized_rombach import OptimizedRombach

def test_performance(graph, title="Test Network"):
    """Compare performance between original and optimized versions"""
    print(f"\n--- Performance Test on {title} ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges) ---")
    
    # Test original implementation
    print("\nTesting Original Rombach Implementation:")
    start_time = time.time()
    rombach = cpnet.Rombach(num_runs=10, alpha=0.3, beta=0.6, algorithm="ls")
    rombach.detect(graph)
    end_time = time.time()
    orig_time = end_time - start_time
    print(f"Original implementation time: {orig_time:.4f} seconds")
    print(f"Q score: {rombach.Q_}")
    
    core_count = np.sum(rombach.x_ >= 0.5)
    periphery_count = np.sum(rombach.x_ < 0.5)
    print(f"Cores: {core_count}, Peripheries: {periphery_count}")
    
    # Test optimized implementation
    print("\nTesting Optimized Rombach Implementation:")
    start_time = time.time()
    opt_rombach = OptimizedRombach(num_runs=10, alpha=0.3, beta=0.6, algorithm="ls", early_stop=True)
    opt_rombach.detect(graph)
    end_time = time.time()
    opt_time = end_time - start_time
    print(f"Optimized implementation time: {opt_time:.4f} seconds")
    print(f"Q score: {opt_rombach.Q_}")
    
    core_count = np.sum(opt_rombach.x_ >= 0.5)
    periphery_count = np.sum(opt_rombach.x_ < 0.5)
    print(f"Cores: {core_count}, Peripheries: {periphery_count}")
    
    # Calculate speedup
    speedup = orig_time / max(0.001, opt_time)
    print(f"\nSpeedup: {speedup:.2f}x faster")
    
    # Check quality difference
    quality_diff = abs(rombach.Q_ - opt_rombach.Q_) / max(0.001, abs(rombach.Q_))
    print(f"Quality difference: {quality_diff:.4f} ({quality_diff*100:.2f}%)")

    # Compare core-periphery assignments
    core_agreement = np.sum((rombach.x_ >= 0.5) == (opt_rombach.x_ >= 0.5)) / len(rombach.x_)
    print(f"Core-periphery assignment agreement: {core_agreement:.4f} ({core_agreement*100:.2f}%)")
    
    return {
        "original_time": orig_time,
        "optimized_time": opt_time,
        "speedup": speedup,
        "quality_diff": quality_diff,
        "core_agreement": core_agreement,
        "original_score": rombach.Q_,
        "optimized_score": opt_rombach.Q_
    }

# Tests on different network sizes
if __name__ == "__main__":
    print("=== Rombach Algorithm Performance Testing ===")
    
    # Test 1: Small network (Karate Club)
    G_small = nx.karate_club_graph()
    small_results = test_performance(G_small, "Zachary's Karate Club")
    
    # Test 2: Medium network (random)
    G_medium = nx.random_graphs.powerlaw_cluster_graph(200, 5, 0.5)
    medium_results = test_performance(G_medium, "Medium Network (200 nodes)")
    
    try:
        # Test 3: Larger network (if time permits)
        G_large = nx.random_graphs.powerlaw_cluster_graph(500, 8, 0.3)
        large_results = test_performance(G_large, "Large Network (500 nodes)")
    except Exception as e:
        print(f"Skipped large network test: {str(e)}")
        large_results = {}
    
    # Summary
    print("\n=== Performance Summary ===")
    print(f"Small network speedup: {small_results.get('speedup', 0):.2f}x")
    print(f"Medium network speedup: {medium_results.get('speedup', 0):.2f}x")
    if large_results:
        print(f"Large network speedup: {large_results.get('speedup', 0):.2f}x")
    
    print("\nOptimization strategies applied:")
    print("1. Reduced number of runs with early stopping")
    print("2. Adaptive iteration count based on network size")
    print("3. Numba JIT compilation for all critical functions")
    print("4. Parallel processing for large networks")
    print("5. Node sampling in large networks")
    print("6. Faster simulated annealing with adaptive steps") 