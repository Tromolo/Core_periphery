import networkx as nx
import numpy as np
from community import community_louvain
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Dict, Any
import uuid
from fastapi import UploadFile
import os
import shutil
import pandas as pd
from .BE import BE
from .Holme import Holme
from .rombach import Rombach
from .Metrics import calculate_all_network_metrics, prepare_community_analysis_data, calculate_network_metrics, calculate_connected_components
from .utils import draw, draw_interactive, save_visualization
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import csv

output_dir = "../static"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def classify_and_save_edges(graph: nx.Graph, classifications: Dict, output_file: str) -> None:
    """
    Classify edges based on node classifications and save to CSV.
    
    Args:
        graph: NetworkX graph object
        classifications: Dictionary of node classifications (C/P)
        output_file: Path to save the CSV file
    """

    edge_data = []
    for u, v in graph.edges():
        edge_type = 'core-core' if classifications[u] == 'C' and classifications[v] == 'C' else \
                   'periphery-periphery' if classifications[u] == 'P' and classifications[v] == 'P' else \
                   'core-periphery'
        
        edge_data.append({
            'source': u,
            'target': v,
            'source_type': classifications[u],
            'target_type': classifications[v],
            'edge_type': edge_type
        })
    
    # Convert to DataFrame and save
    df = pd.DataFrame(edge_data)
    df.to_csv(output_file, index=False)

def infer_edge_list_columns(df: pd.DataFrame):
    """Infer source, target, and optional weight columns from a DataFrame."""
    num_cols = df.shape[1]

    if num_cols == 2:
        df.columns = ["source", "target"]
    elif num_cols == 3:
        df.columns = ["source", "target", "weight"]
    elif num_cols > 3:
        df.columns = ["source", "target"] + [f"attr_{i}" for i in range(1, num_cols - 1)]
    else:
        raise ValueError(f"Unexpected column count: {num_cols}. Ensure the file is a valid edge list.")

    return df

async def load_graph_file(file: UploadFile) -> nx.Graph:
    if not file.filename:
        raise ValueError("No file provided.")

    filename = file.filename
    ext = filename.split(".")[-1].lower()

    os.makedirs("../tmp", exist_ok=True)
    path = os.path.join("../tmp", f"{uuid.uuid4()}.{ext}")

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        if ext == "gml":
            G = nx.read_gml(path)
        elif ext == "graphml":
            G = nx.read_graphml(path)
        elif ext == "gexf":
            G = nx.read_gexf(path)
        elif ext == "edgelist":
            G = nx.read_edgelist(path, create_using=nx.MultiGraph())
        elif ext in ["csv", "txt"]:
            # Detect delimiter automatically
            with open(path, "r") as f:
                sample = f.read(1024)  # Read a small portion of the file
                sep = ";" if ";" in sample else ","

            try:
                df = pd.read_csv(path, sep=sep)
            except Exception as e:
                raise ValueError(f"Failed to read CSV with detected separator '{sep}': {e}")

            if df.shape[1] < 2:
                raise ValueError(f"Invalid edge list format: {df.shape[1]} columns found.")

            if "source" not in df.columns or "target" not in df.columns:
                df = pd.read_csv(path, sep=sep, header=None)
                if df.shape[1] < 2:
                    raise ValueError(f"Invalid edge list format: {df.shape[1]} columns found.")

                df = infer_edge_list_columns(df)

            edge_attrs = list(df.columns.difference(["source", "target"]))
            G = nx.from_pandas_edgelist(df, source="source", target="target", edge_attr=edge_attrs if edge_attrs else None)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return G
    finally:
        if os.path.exists(path):
            os.remove(path)

def process_graph_with_rombach(graph: nx.Graph, num_runs: int = 10, alpha: float = 0.3, beta: float = 0.9) -> Tuple[Dict, Dict]:
    """Process graph with Rombach algorithm."""
    rombach = Rombach(num_runs=num_runs, alpha=alpha, beta=beta)
    rombach.detect(graph)
    x = {node: rombach.x_[i] for i, node in enumerate(graph.nodes())}
    mean_coreness = sum(x.values()) / len(x)
    c = {node: 1 if x[node] > mean_coreness else 0 for node in graph.nodes()}
    return c, x

def process_graph_with_be(graph: nx.Graph, num_runs: int = 10) -> Tuple[Dict, Dict]:
    """Process graph with BE algorithm."""
    be = BE(num_runs=num_runs)
    be.detect(graph)
    x = {node: be.x_[i] for i, node in enumerate(graph.nodes())}
    mean_coreness = sum(x.values()) / len(x)
    c = {node: 1 if x[node] > mean_coreness else 0 for node in graph.nodes()}
    return c, x

def process_graph_with_holme(graph: nx.Graph, num_iterations: int = 100, threshold: float = 0.05) -> Tuple[Dict, Dict]:
    """Process graph with Holme algorithm."""
    holme = Holme(num_iterations=num_iterations, threshold=threshold)
    holme.detect(graph)
    x = {node: holme.x_[i] for i, node in enumerate(graph.nodes())}
    mean_coreness = sum(x.values()) / len(x)
    c = {node: 1 if x[node] > mean_coreness else 0 for node in graph.nodes()}
    return c, x

def export_to_gdf(graph, classifications, output_path):
    """Export graph to GDF format for Gephi."""
    try:
        with open(output_path, 'w') as f:
            # Write node definitions
            f.write("nodedef>name VARCHAR,label VARCHAR,class VARCHAR\n")
            for node in graph.nodes():
                node_class = classifications.get(node, "Unknown")
                f.write(f"{node},{node},{node_class}\n")
            
            # Write edge definitions
            f.write("edgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE\n")
            for u, v, data in graph.edges(data=True):
                weight = data.get('weight', 1.0)
                f.write(f"{u},{v},{weight}\n")
                
        print(f"Successfully exported graph to GDF format: {output_path}")
        return True
    except Exception as e:
        print(f"Error exporting to GDF: {str(e)}")
        return False

def get_core_stats(graph, classifications):
    """Calculate core-periphery specific metrics."""
    core_nodes = [i for i, val in enumerate(classifications) if val == 1]
    periphery_nodes = [i for i, val in enumerate(classifications) if val == 0]
    
    return {
        "core_size": len(core_nodes),
        "periphery_size": len(periphery_nodes),
        "core_percentage": len(core_nodes) / len(classifications) * 100 if classifications else 0
    }

def draw_static(graph, c, x):
    """Generate a static image of the graph with core-periphery visualization."""
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.png"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        # Create a figure
        plt.figure(figsize=(10, 10))
        
        # Get node colors based on classifications
        node_colors = ['red' if (c[i] if isinstance(c, list) else c.get(node, 0)) > 0.5 else 'blue' 
                      for i, node in enumerate(graph.nodes())]
        
        # Draw the graph
        pos = nx.spring_layout(graph)
        nx.draw_networkx(
            graph,
            pos=pos,
            node_color=node_colors,
            node_size=100,
            with_labels=False,
            alpha=0.8
        )
        
        # Add a legend
        red_patch = mpatches.Patch(color='red', label='Core')
        blue_patch = mpatches.Patch(color='blue', label='Periphery')
        plt.legend(handles=[red_patch, blue_patch])
        
        # Save the figure
        plt.savefig(filepath)
        plt.close()
        
        return filename
    except Exception as e:
        print(f"Error generating static image: {str(e)}")
        return None

def generate_csv(graph, c, x):
    """Generate a CSV file with node and edge data."""
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        # Create node classifications
        classifications = {}
        for i, node in enumerate(graph.nodes()):
            coreness = c[i] if isinstance(c, list) else c.get(node, 0)
            classifications[node] = "C" if coreness > 0.5 else "P"
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['source', 'target', 'type'])
            
            for u, v in graph.edges():
                edge_type = f"{classifications[u]}-{classifications[v]}"
                writer.writerow([u, v, edge_type])
        
        return filename
    except Exception as e:
        print(f"Error generating CSV file: {str(e)}")
        return None

def generate_gdf(graph, c, x):
    """Generate a GDF file with node and edge data."""
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.gdf"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        # Create node classifications
        classifications = {}
        for i, node in enumerate(graph.nodes()):
            coreness = c[i] if isinstance(c, list) else c.get(node, 0)
            classifications[node] = "C" if coreness > 0.5 else "P"
        
        # Write to GDF
        with open(filepath, 'w') as f:
            # Write node definitions
            f.write("nodedef>name VARCHAR,label VARCHAR,type VARCHAR,coreness DOUBLE\n")
            for node in graph.nodes():
                coreness = c[node] if isinstance(c, dict) else c[list(graph.nodes()).index(node)]
                f.write(f"{node},{node},{classifications[node]},{coreness}\n")
            
            # Write edge definitions
            f.write("edgedef>node1 VARCHAR,node2 VARCHAR,type VARCHAR\n")
            for u, v in graph.edges():
                edge_type = f"{classifications[u]}-{classifications[v]}"
                f.write(f"{u},{v},{edge_type}\n")
        
        return filename
    except Exception as e:
        print(f"Error generating GDF file: {str(e)}")
        return None

def get_top_nodes(graph, c):
    """Get the top nodes based on coreness values."""
    top_nodes = []
    betweenness = nx.betweenness_centrality(graph)
    
    # Calculate the threshold for core classification
    # Use the median coreness value as a threshold
    if isinstance(c, list):
        coreness_values = c
    else:
        coreness_values = list(c.values())
    
    # Use 0.5 as default threshold, but if all values are below 0.5,
    # use the median value to ensure we have some core nodes
    threshold = 0.5
    if max(coreness_values) < threshold:
        threshold = sorted(coreness_values)[len(coreness_values) // 2]
    
    print(f"Using coreness threshold of {threshold} for core-periphery classification")
    
    for i, node in enumerate(graph.nodes()):
        coreness = c[i] if isinstance(c, list) else c.get(node, 0)
        top_nodes.append({
            "id": node,
            "type": "C" if coreness > threshold else "P",
            "coreness": float(coreness),
            "betweenness": betweenness[node],
            "degree": graph.degree(node)
        })
    
    top_nodes.sort(key=lambda x: x["coreness"], reverse=True)
    return top_nodes[:5]

def get_algorithm_function(algorithm):
    """Return the appropriate algorithm function based on the algorithm name."""
    if algorithm == "rombach":
        return lambda graph, **params: process_graph_with_rombach(
            graph, 
            num_runs=params.get('num_runs', 10),
            alpha=params.get('alpha', 0.3),
            beta=params.get('beta', 0.6)
        )
    elif algorithm == "be":
        return lambda graph, **params: process_graph_with_be(
            graph,
            num_runs=params.get('num_runs', 10)
        )
    elif algorithm == "holme":
        return lambda graph, **params: process_graph_with_holme(
            graph,
            num_iterations=params.get('num_iterations', 100),
            threshold=params.get('threshold', 0.05)
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

def process_graph(graph, algorithm=None, params=None):
    """Process a graph with the specified algorithm and parameters."""
    try:
        # Get the algorithm function
        if algorithm:
            algorithm_func = get_algorithm_function(algorithm)
            
            # Process the graph with the algorithm
            if params:
                classifications, coreness = algorithm_func(graph, **params)
            else:
                classifications, coreness = algorithm_func(graph)
                
            # Convert classifications to a list for JSON serialization
            if isinstance(classifications, dict):
                classifications_list = [classifications.get(node, 0) for node in graph.nodes()]
            else:
                classifications_list = classifications
                
            # Convert coreness to a list for JSON serialization
            if isinstance(coreness, dict):
                coreness_list = [coreness.get(node, 0) for node in graph.nodes()]
            else:
                coreness_list = coreness
                
            # Get core statistics
            core_stats = get_core_stats(graph, classifications)
            
            # Generate CSV file
            csv_file = generate_csv(graph, classifications, coreness)
            
            # Generate GDF file
            gdf_file = generate_gdf(graph, classifications, coreness)
            
            # Generate static image
            image_file = draw_static(graph, classifications, coreness)
            
            # Calculate network metrics
            network_metrics = calculate_all_network_metrics(graph, classifications, coreness, algorithm, params)
            
            # Get top nodes
            top_nodes = get_top_nodes(graph, coreness)
            
            # Prepare algorithm parameters
            algorithm_params = {}
            if algorithm == "rombach":
                algorithm_params = {
                    "alpha": params.get('alpha', 0.3),
                    "beta": params.get('beta', 0.6),
                    "num_runs": params.get('num_runs', 10)
                }
            elif algorithm == "holme":
                algorithm_params = {
                    "num_iterations": params.get('num_iterations', 100),
                    "threshold": params.get('threshold', 0.05)
                }
            elif algorithm == "be":
                algorithm_params = {
                    "num_runs": params.get('num_runs', 10)
                }
                
            # Count core and periphery nodes
            core_count = sum(1 for node_type in classifications_list if node_type == 'C' or node_type == 1)
            periphery_count = len(classifications_list) - core_count
            print(f"Classification distribution: {core_count} core nodes, {periphery_count} periphery nodes")
            
            # Prepare graph data for visualization
            graph_data = {
                "nodes": [],
                "edges": []
            }
            
            # Calculate additional node metrics for visualization
            try:
                import networkx as nx
                degrees = dict(graph.degree())
                betweenness = nx.betweenness_centrality(graph)
                closeness = nx.closeness_centrality(graph)
            except Exception as e:
                print(f"Error calculating additional metrics: {str(e)}")
                degrees = {node: len(list(graph.neighbors(node))) for node in graph.nodes()}
                betweenness = {node: 0.0 for node in graph.nodes()}
                closeness = {node: 0.0 for node in graph.nodes()}
            
            # Add nodes
            for i, node in enumerate(graph.nodes()):
                node_type = classifications_list[i]
                if isinstance(node_type, int):
                    node_type = "C" if node_type == 1 else "P"
                    
                coreness_value = coreness_list[i]
                
                graph_data["nodes"].append({
                    "id": str(node),
                    "type": node_type,
                    "coreness": float(coreness_value),
                    "degree": degrees.get(node, 0),
                    "betweenness": betweenness.get(node, 0.0),
                    "closeness": closeness.get(node, 0.0)
                })
                
            # Add edges
            for edge in graph.edges():
                source, target = edge
                # Get edge data if available
                edge_data = graph.get_edge_data(source, target) or {}
                weight = edge_data.get('weight', 1.0)
                
                graph_data["edges"].append({
                    "id": f"{source}-{target}",
                    "source": str(source),
                    "target": str(target),
                    "weight": float(weight)
                })
                
            return {
                "classifications": classifications_list,
                "network_metrics": network_metrics,
                "core_stats": core_stats,
                "algorithm_params": algorithm_params,
                "top_nodes": top_nodes,
                "csv_file": csv_file,
                "gdf_file": gdf_file,
                "image_file": image_file,
                "graph_data": graph_data
            }
        else:
            # Only calculate network metrics and community data
            network_metrics = calculate_network_metrics(graph)
            community_data = prepare_community_analysis_data(graph)
            
            return {
                "network_metrics": network_metrics,
                "community_data": community_data
            }
            
    except Exception as e:
        print(f"Error processing graph: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e