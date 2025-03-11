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
from .Metrics import calculate_all_network_metrics, prepare_community_analysis_data
from .utils import draw, draw_interactive, save_visualization

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

def process_graph(graph: nx.Graph, algorithm: str = "rombach", **kwargs) -> Dict[str, Any]:
    """Process graph with specified algorithm and calculate metrics."""
    try:
        if algorithm == "rombach":
            c, x = process_graph_with_rombach(
                graph, 
                num_runs=kwargs.get('num_runs', 10),
                alpha=kwargs.get('alpha', 0.3),
                beta=kwargs.get('beta', 0.6)
            )

            algorithm_params = {
                "alpha": kwargs.get('alpha', 0.3),
                "beta": kwargs.get('beta', 0.6),
                "num_runs": kwargs.get('num_runs', 10)
            }
        elif algorithm == "be":
            c, x = process_graph_with_be(
                graph,
                num_runs=kwargs.get('num_runs', 10)
            )
            algorithm_params = {
                "num_runs": kwargs.get('num_runs', 10)
            }
        elif algorithm == "holme":
            c, x = process_graph_with_holme(
                graph,
                num_iterations=kwargs.get('num_iterations', 100),
                threshold=kwargs.get('threshold', 0.05)
            )
            algorithm_params = {
                "num_iterations": kwargs.get('num_iterations', 100),
                "threshold": kwargs.get('threshold', 0.05)
            }
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
            
        classifications = {node: "C" if c[node] == 1 else "P" for node in graph.nodes()}
        
        metrics = calculate_all_network_metrics(
            graph, 
            classifications, 
            x,
            algorithm=algorithm,
            algorithm_params=algorithm_params
        )
        
        # Use absolute path for output files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        
        output_csv = f"{uuid.uuid4()}.csv"
        output_img = f"{uuid.uuid4()}.png"
        output_gdf = f"{uuid.uuid4()}.gdf"

        # Use absolute paths for saving files
        csv_path = os.path.join(output_dir, output_csv)
        img_path = os.path.join(output_dir, output_img)
        gdf_path = os.path.join(output_dir, output_gdf)
        
        print(f"Saving CSV to: {csv_path}")
        classify_and_save_edges(graph, classifications, csv_path)
        
        print(f"Saving GDF to: {gdf_path}")
        export_to_gdf(graph, classifications, gdf_path)
        
        print(f"Saving visualization to: {img_path}")
        save_visualization(graph, classifications, img_path, 
                         title=f"Core-Periphery ({algorithm.capitalize()})")
        
        try:
            interactive_plot = draw_interactive(graph, c, x)
        except Exception:
            interactive_plot = None
        
        community_data = prepare_community_analysis_data(graph)

        return {
            "classifications": classifications,
            "csv_file": output_csv,
            "gdf_file": output_gdf,
            "image_file": output_img,
            "interactive_plot": interactive_plot,
            "metrics": metrics,
            "community_data": community_data
        }
        
    except Exception as e:
        raise Exception(f"Error processing graph: {str(e)}")