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


def calculate_connected_components(G):
    """Calculate connected components statistics."""
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

        # Add connected components analysis
        metrics["connected_components"] = calculate_connected_components(graph)

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
    
def prepare_community_analysis_data(graph):
    """
    Prepare community analysis data for visualization in the frontend.
    Returns community statistics, visualization, and membership information.
    """
    try:
        # Detect communities using Louvain method
        communities = community_louvain.best_partition(graph)
        
        # Calculate modularity score
        modularity = community_louvain.modularity(communities, graph)
        
        # Count community sizes
        community_sizes = Counter(communities.values())
        
        # Prepare size distribution for visualization
        size_distribution = [
            {"community": str(community), "size": size} 
            for community, size in sorted(community_sizes.items())
        ]
        
        # Calculate basic statistics
        num_communities = len(community_sizes)
        community_size_values = list(community_sizes.values())
        mean_size = np.mean(community_size_values)
        max_size = max(community_size_values)
        min_size = min(community_size_values)
        
        # Create visualization
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(graph, seed=42)
        
        # Create color map for communities
        cmap = plt.cm.get_cmap("tab20", num_communities)
        community_colors = {}
        
        for node, community_id in communities.items():
            if community_id not in community_colors:
                community_colors[community_id] = cmap(community_id % num_communities)
                
        node_colors = [community_colors[communities[node]] for node in graph.nodes()]
        
        nx.draw_networkx(
            graph,
            pos=pos,
            node_color=node_colors,
            with_labels=False,
            node_size=80,
            edge_color="gray",
            alpha=0.7
        )
        
        plt.title("Community Structure Visualization")
        plt.axis("off")
        
        # Get the current working directory and construct absolute path
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root and then to static
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        print(f"Current directory: {current_dir}")
        print(f"Attempting to save visualization to directory: {output_dir}")
        
        try:
            # Ensure the directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate a unique filename
            community_viz_file = f"{uuid.uuid4()}_community.png"
            full_path = os.path.join(output_dir, community_viz_file)
            print(f"Saving visualization to: {full_path}")
            
            # Save the figure
            plt.savefig(full_path, dpi=300, bbox_inches="tight")
            print(f"Successfully saved visualization to: {full_path}")
            
            # Check if file was actually created
            if os.path.exists(full_path):
                print(f"Confirmed file exists at: {full_path}")
            else:
                print(f"WARNING: File was not created at: {full_path}")
                
            plt.close()
        except Exception as save_error:
            print(f"Error saving visualization: {str(save_error)}")
            community_viz_file = None
        
        # Return data in the format expected by the frontend
        return {
            "num_communities": num_communities,
            "mean_size": round(mean_size, 2),
            "max_size": max_size,
            "min_size": min_size,
            "modularity": round(modularity, 3),
            "size_distribution": size_distribution,
            "visualization_file": community_viz_file,
            "community_membership": {str(node): community for node, community in communities.items()}
        }
    except Exception as e:
        print(f"Error in community analysis: {str(e)}")
        return None