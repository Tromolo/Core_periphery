import networkx as nx
from community import community_louvain
from joblib import Parallel, delayed
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional


def calculate_average_path_length(G):
    try:
        largest_component = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_component)
        return round(nx.average_shortest_path_length(subgraph), 2)
    except Exception:
        return "N/A"


def calculate_diameter(G):
    try:
        largest_component = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_component)
        return nx.diameter(subgraph)
    except Exception:
        return "N/A"


def calculate_edge_density(G):
    return round(nx.density(G), 2)


def calculate_assortativity_coefficient(G):
    return round(nx.degree_assortativity_coefficient(G), 2)


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
            # Basic metrics
            futures = {
                'nodes': executor.submit(lambda: graph.number_of_nodes()),
                'edges': executor.submit(lambda: graph.number_of_edges()),
                'density': executor.submit(nx.density, graph),
                'clustering': executor.submit(nx.average_clustering, graph),
                'degree_dist': executor.submit(lambda: [d for n, d in graph.degree()]),
            }
            
            # Path-based metrics
            try:
                futures['avg_path_length'] = executor.submit(nx.average_shortest_path_length, graph)
                futures['diameter'] = executor.submit(nx.diameter, graph)
            except:
                futures['avg_path_length'] = None
                futures['diameter'] = None
            
            # Community detection
            try:
                communities = community_louvain.best_partition(graph)
                futures['modularity'] = executor.submit(
                    community_louvain.modularity, communities, graph
                )
            except:
                futures['modularity'] = None
            
            # Collect results
            metrics = {}
            for key, future in futures.items():
                if future is not None:
                    try:
                        metrics[key] = future.result()
                    except Exception:
                        metrics[key] = None
            
            # Calculate degree statistics
            if metrics['degree_dist']:
                degree_dist = metrics['degree_dist']
                metrics.update({
                    'avg_degree': float(np.mean(degree_dist)),
                    'max_degree': int(max(degree_dist)),
                    'min_degree': int(min(degree_dist)),
                    'degree_std': float(np.std(degree_dist))
                })
                
            # Remove degree_dist from final metrics
            metrics.pop('degree_dist', None)
            
            return metrics
            
    except Exception:
        return None


def calculate_all_network_metrics(graph: nx.Graph, classifications: Dict, coreness: Dict, 
                                algorithm: str = None, algorithm_params: Dict = None) -> Dict:
    """
    Calculate all network metrics including core-periphery specific metrics.
    """
    try:
        # Basic network metrics
        metrics = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": nx.density(graph),
            "clustering": nx.average_clustering(graph),
            "modularity": community_louvain.modularity(community_louvain.best_partition(graph), graph),
        }
        
        # Try to calculate metrics that might fail for disconnected graphs
        try:
            metrics["avg_path_length"] = nx.average_shortest_path_length(graph)
            metrics["diameter"] = nx.diameter(graph)
        except nx.NetworkXError:
            metrics["avg_path_length"] = None
            metrics["diameter"] = None
            
        try:
            metrics["assortativity"] = nx.degree_assortativity_coefficient(graph)
        except:
            metrics["assortativity"] = None

        # Core-periphery specific metrics
        core_nodes = [node for node, type in classifications.items() if type == 'C']
        periphery_nodes = [node for node, type in classifications.items() if type == 'P']
        
        metrics["core_stats"] = {
            "core_size": len(core_nodes),
            "periphery_size": len(periphery_nodes)
        }

        if algorithm == "rombach":
            metrics["rombach_params"] = {
                "Q": sum(coreness.values()) / len(coreness),
                "alpha": algorithm_params.get('alpha', 0.0),
                "beta": algorithm_params.get('beta', 0.0)
            }
        elif algorithm == "holme":
            metrics["holme_params"] = {
                "Q": sum(coreness.values()) / len(coreness),
                "num_iterations": algorithm_params.get('num_iterations', 100),
                "threshold": algorithm_params.get('threshold', 0.05)
            }
        elif algorithm == "be":
            metrics["be_params"] = {
                "Q": sum(coreness.values()) / len(coreness),
                "num_runs": algorithm_params.get('num_runs', 10)
            }


        top_nodes = []
        betweenness = nx.betweenness_centrality(graph)
        for node in graph.nodes():
            top_nodes.append({
                "id": node,
                "type": classifications[node],
                "coreness": coreness[node],
                "betweenness": betweenness[node],
                "degree": graph.degree(node)
            })
        

        top_nodes.sort(key=lambda x: x["coreness"], reverse=True)
        metrics["top_nodes"] = top_nodes[:5]

        return metrics

    except Exception as e:
        print(f"Error calculating metrics: {str(e)}")
        return {}


def calculate_centrality_metrics(graph):
    """
    Calculate various centrality metrics using parallel processing.
    """
    try:
        with ThreadPoolExecutor() as executor:
            betweenness_future = executor.submit(nx.betweenness_centrality, graph)
            degree_future = executor.submit(lambda g: dict(g.degree()), graph)
            closeness_future = executor.submit(nx.closeness_centrality, graph)
            eigenvector_future = executor.submit(nx.eigenvector_centrality_numpy, graph)
            
            centrality_metrics = {
                "betweenness": betweenness_future.result(),
                "degree": degree_future.result(),
                "closeness": closeness_future.result(),
                "eigenvector": eigenvector_future.result()
            }
            
            return centrality_metrics
    except Exception as e:
        print(f"Error calculating centrality metrics: {str(e)}")
        return None