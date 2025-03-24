import networkx as nx
import time
import numpy as np
from backend.BE import BE
from backend.optimized_be import OptimizedBE
import cpnet
def test_performance(graph, title="Test Network"):
    """Compare performance between original and optimized BE versions"""
    print(f"\n--- Performance Test on {title} ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges) ---")
    
    # Test original implementation
    print("\nTesting Original BE Implementation:")
    start_time = time.time()
    be = cpnet.BE(num_runs=10)
    be.detect(graph)
    end_time = time.time()
    orig_time = end_time - start_time
    print(f"Original implementation time: {orig_time:.4f} seconds")
    print(f"Q score: {be.Q_}")
    
    # Count core/periphery nodes (using 0.5 threshold even though BE returns binary 0/1)
    core_count = np.sum(be.x_ >= 0.5)
    periphery_count = np.sum(be.x_ < 0.5)
    print(f"Cores: {core_count}, Peripheries: {periphery_count}")
    
    # Count edge types
    core_nodes_orig = set([node for i, node in enumerate(graph.nodes()) if be.x_[i] >= 0.5])
    periphery_nodes_orig = set(graph.nodes()) - core_nodes_orig
    
    cc_edges_orig = 0
    cp_edges_orig = 0
    pp_edges_orig = 0
    
    for u, v in graph.edges():
        u_idx = list(graph.nodes()).index(u)
        v_idx = list(graph.nodes()).index(v)
        if be.x_[u_idx] >= 0.5:
            if be.x_[v_idx] >= 0.5:
                cc_edges_orig += 1
            else:
                cp_edges_orig += 1
        else:
            if be.x_[v_idx] >= 0.5:
                cp_edges_orig += 1
            else:
                pp_edges_orig += 1
    
    print(f"Edge types - C-C: {cc_edges_orig}, C-P/P-C: {cp_edges_orig}, P-P: {pp_edges_orig}")
    
    # Test optimized implementation
    print("\nTesting Optimized BE Implementation:")
    start_time = time.time()
    opt_be = OptimizedBE(num_runs=10, early_stop=True)
    opt_be.detect(graph)
    end_time = time.time()
    opt_time = end_time - start_time
    print(f"Optimized implementation time: {opt_time:.4f} seconds")
    print(f"Q score: {opt_be.Q_}")
    
    # Count core/periphery nodes
    core_count_opt = np.sum(opt_be.x_ >= 0.5)
    periphery_count_opt = np.sum(opt_be.x_ < 0.5)
    print(f"Cores: {core_count_opt}, Peripheries: {periphery_count_opt}")
    
    # Count edge types
    core_nodes_opt = set([node for i, node in enumerate(graph.nodes()) if opt_be.x_[i] >= 0.5])
    periphery_nodes_opt = set(graph.nodes()) - core_nodes_opt
    
    cc_edges_opt = 0
    cp_edges_opt = 0
    pp_edges_opt = 0
    
    for u, v in graph.edges():
        u_idx = list(graph.nodes()).index(u)
        v_idx = list(graph.nodes()).index(v)
        if opt_be.x_[u_idx] >= 0.5:
            if opt_be.x_[v_idx] >= 0.5:
                cc_edges_opt += 1
            else:
                cp_edges_opt += 1
        else:
            if opt_be.x_[v_idx] >= 0.5:
                cp_edges_opt += 1
            else:
                pp_edges_opt += 1
    
    print(f"Edge types - C-C: {cc_edges_opt}, C-P/P-C: {cp_edges_opt}, P-P: {pp_edges_opt}")
    
    # Calculate speedup
    speedup = orig_time / max(0.001, opt_time)
    print(f"\nSpeedup: {speedup:.2f}x faster")
    
    # Check quality difference
    quality_diff = abs(be.Q_ - opt_be.Q_) / max(0.001, abs(be.Q_))
    print(f"Quality difference: {quality_diff:.4f} ({quality_diff*100:.2f}%)")

    # Compare node assignments
    node_list = list(graph.nodes())
    agreement = np.sum((be.x_ >= 0.5) == (opt_be.x_ >= 0.5)) / len(be.x_)
    print(f"Core-periphery assignment agreement: {agreement:.4f} ({agreement*100:.2f}%)")
    
    # Compare edge classification differences
    edge_agreement = 0
    if cc_edges_orig + cp_edges_orig + pp_edges_orig > 0:
        # Calculate Jaccard similarity of edge classifications
        edge_class_diff = abs(cc_edges_orig - cc_edges_opt) + abs(cp_edges_orig - cp_edges_opt) + abs(pp_edges_orig - pp_edges_opt)
        edge_class_total = cc_edges_orig + cp_edges_orig + pp_edges_orig
        edge_agreement = 1 - (edge_class_diff / (2 * edge_class_total))
    print(f"Edge classification agreement: {edge_agreement:.4f} ({edge_agreement*100:.2f}%)")
    
    return {
        "original_time": orig_time,
        "optimized_time": opt_time,
        "speedup": speedup,
        "quality_diff": quality_diff,
        "node_agreement": agreement,
        "edge_agreement": edge_agreement,
        "original_score": be.Q_,
        "optimized_score": opt_be.Q_,
        "original_edges": (cc_edges_orig, cp_edges_orig, pp_edges_orig),
        "optimized_edges": (cc_edges_opt, cp_edges_opt, pp_edges_opt),
    }

# Tests on different network sizes
if __name__ == "__main__":
    print("=== BE Algorithm Performance Testing ===")
    
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
    
    print("\n=== Core-Periphery Classification Agreement ===")
    print(f"Small network node agreement: {small_results.get('node_agreement', 0)*100:.2f}%")
    print(f"Medium network node agreement: {medium_results.get('node_agreement', 0)*100:.2f}%")
    if large_results:
        print(f"Large network node agreement: {large_results.get('node_agreement', 0)*100:.2f}%")
    
    print("\n=== Edge Classification Agreement ===")
    print(f"Small network edge agreement: {small_results.get('edge_agreement', 0)*100:.2f}%")
    print(f"Medium network edge agreement: {medium_results.get('edge_agreement', 0)*100:.2f}%")
    if large_results:
        print(f"Large network edge agreement: {large_results.get('edge_agreement', 0)*100:.2f}%")
    
    print("\nOptimization strategies applied:")
    print("1. Early stopping when score improvement is minimal")
    print("2. Adaptive iteration count based on network size")
    print("3. Node sampling for large networks to reduce computation")
    print("4. Parallelized computation for multiple runs")
    print("5. Optimized inner loop with improved convergence detection")