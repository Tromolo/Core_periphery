import networkx as nx
from community import community_louvain
from joblib import Parallel, delayed
import numpy as np
import uuid
import matplotlib.pyplot as plt
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from collections import Counter


def calculate_betweenness_distribution(G):
    betweenness = nx.betweenness_centrality(G)
    return [round(bc, 2) for bc in betweenness.values()]


def calculate_core_periphery_metrics(G, classifications):
    core_nodes = [node for node, cls in classifications.items() if cls == "C"]
    periphery_nodes = [node for node, cls in classifications.items() if cls == "P"]

    core_subgraph = G.subgraph(core_nodes)
    periphery_core_edges = G.subgraph(core_nodes + periphery_nodes).number_of_edges()

    core_density = round(nx.density(core_subgraph), 2) if core_nodes else 0.0
    periphery_core_connectivity = round(periphery_core_edges / max(1, len(periphery_nodes)), 2)

    return {
        "core_density": core_density,
        "periphery_core_connectivity": periphery_core_connectivity
    }


def calculate_community_core_overlap(G, classifications):
    partition = community_louvain.best_partition(G)
    community_core_overlap = {}

    for node, community in partition.items():
        if classifications[node] == "C":
            if community not in community_core_overlap:
                community_core_overlap[community] = 0
            community_core_overlap[community] += 1

    return community_core_overlap


def calculate_network_metrics(graph: nx.Graph) -> Dict[str, Any]:
    """Calculate basic network metrics using parallel processing."""
    try:
        with ThreadPoolExecutor() as executor:
            futures = {
                'nodes': executor.submit(lambda: graph.number_of_nodes()),
                'edges': executor.submit(lambda: graph.number_of_edges()),
                'density': executor.submit(nx.density, graph),
                'clustering': executor.submit(nx.average_clustering, graph),
                'degree_dist': executor.submit(lambda: [d for n, d in graph.degree()]),
            }
            
            try:
                futures['assortativity'] = executor.submit(nx.degree_assortativity_coefficient, graph)
            except:
                futures['assortativity'] = None
            
            metrics = {}
            for key, future in futures.items():
                if future is not None:
                    try:
                        metrics[key] = future.result()
                    except Exception:
                        metrics[key] = None
            
            if metrics['degree_dist']:
                degree_dist = metrics['degree_dist']
                metrics.update({
                    'avg_degree': float(np.mean(degree_dist)),
                    'max_degree': int(max(degree_dist)),
                    'min_degree': int(min(degree_dist)),
                    'degree_std': float(np.std(degree_dist))
                })
                
                from collections import Counter
                degree_counts = Counter(degree_dist)
                metrics['degree_distribution'] = [
                    {"degree": k, "count": v} for k, v in sorted(degree_counts.items())
                ]
                
            metrics.pop('degree_dist', None)
            
            if 'nodes' in metrics:
                metrics['node_count'] = metrics.pop('nodes')
            if 'edges' in metrics:
                metrics['edge_count'] = metrics.pop('edges')
            
            metrics['connected_components'] = calculate_connected_components(graph)
            
            return metrics
            
    except Exception as e:
        print(f"Error calculating network metrics: {str(e)}")
        return None


def calculate_connected_components(G):
    components = list(nx.connected_components(G))
    num_components = len(components)
    
    if num_components == 0:
        return {
            "num_components": 0,
            "largest_component_size": 0,
            "smallest_component_size": 0,
            "component_size_distribution": []
        }
    
    component_sizes = [len(comp) for comp in components]
    
    return {
        "num_components": num_components,
        "largest_component_size": max(component_sizes),
        "smallest_component_size": min(component_sizes),
        "component_size_distribution": sorted(component_sizes, reverse=True)
    }


def calculate_all_network_metrics(graph: nx.Graph, classifications: Dict, coreness: Dict, 
                                algorithm: str = None, algorithm_params: Dict = None, 
                                pre_calculated_core_stats: Dict = None) -> Dict:
    """
    Calculate all network metrics including core-periphery specific metrics.
    """
    try:
        metrics = {}
        
        if pre_calculated_core_stats is not None:
            core_stats = pre_calculated_core_stats
            
        metrics["core_stats"] = {
            "core_size": core_stats["core_size"],
            "periphery_size": core_stats["periphery_size"],
            "core_percentage": core_stats["core_percentage"]
        }
        
        metrics["core_periphery_metrics"] = {
            "core_density": core_stats["core_density"],
            "periphery_core_connectivity": core_stats["periphery_core_connectivity"],
            "periphery_isolation": core_stats["periphery_isolation"],
            "core_periphery_ratio": core_stats["core_periphery_ratio"]
        }
        
        metrics["core_periphery_analysis"] = {
            "structure_quality": core_stats["structure_quality"],
            "connection_patterns": core_stats["connection_patterns"],
            "ideal_pattern_match": core_stats["ideal_pattern_match"],
            "interpretations": {
                "core_density": core_stats["core_density_interpretation"],
                "cp_ratio": core_stats["cp_ratio_interpretation"],
                "pattern_match": core_stats["pattern_match_interpretation"]
            }
        }
        
        # Calculate coreness Q value only once and reuse it
        if any(algorithm == alg for alg in ["rombach", "holme", "be"]):
            coreness_values = [v for v in coreness.values() if isinstance(v, (int, float))]
            Q = sum(coreness_values) / max(1, len(coreness_values)) if coreness_values else 0
            
            if algorithm == "rombach":
                metrics["rombach_params"] = {
                    "Q": Q,
                    "alpha": algorithm_params.get('alpha', 0.0),
                    "beta": algorithm_params.get('beta', 0.0)
                }
            elif algorithm == "holme":
                metrics["holme_params"] = {
                    "Q": Q,
                    "num_iterations": algorithm_params.get('num_iterations', 100),
                    "threshold": algorithm_params.get('threshold', 0.05)
                }
            elif algorithm == "be":
                metrics["be_params"] = {
                    "Q": Q,
                    "num_runs": algorithm_params.get('num_runs', 10)
                }
            
        return metrics
    except Exception as e:
        print(f"Error calculating core-periphery metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to calculate metrics: {str(e)}",
        }

    
def prepare_community_analysis_data(graph):
    """
    Prepare community analysis data for visualization in the frontend.
    Returns community statistics and membership information for client-side visualization.
    """
    try:
        communities = community_louvain.best_partition(graph)
        
        modularity = community_louvain.modularity(communities, graph)
        
        community_sizes = Counter(communities.values())
        
        size_distribution = [
            {"community": str(community), "size": size} 
            for community, size in sorted(community_sizes.items())
        ]
        
        num_communities = len(community_sizes)
        community_size_values = list(community_sizes.values())
        mean_size = np.mean(community_size_values)
        max_size = max(community_size_values)
        min_size = min(community_size_values)
        
        graph_data = {
            "nodes": [],
            "edges": [],
            "communities": {}
        }
        
        degrees = dict(graph.degree())
        
        for node in graph.nodes():
            node_id = str(node)
            community_id = communities[node]
            node_degree = degrees.get(node, 0)
            
            graph_data["nodes"].append({
                "id": node_id,
                "label": node_id,
                "size": node_degree + 3, 
                "degree": node_degree, 
                "community": community_id
            })
            graph_data["communities"][node_id] = community_id
        
        for source, target in graph.edges():
            graph_data["edges"].append({
                "source": str(source),
                "target": str(target),
                "weight": 1  # Default weight
            })
        
        return {
            "num_communities": num_communities,
            "mean_size": round(mean_size, 2),
            "max_size": max_size,
            "min_size": min_size,
            "modularity": round(modularity, 3),
            "size_distribution": size_distribution,
            "community_membership": {str(node): community for node, community in communities.items()},
            "graph_data": graph_data
        }
    except Exception as e:
        print(f"Error in community analysis: {str(e)}")
        return None