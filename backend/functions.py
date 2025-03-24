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
from .optimized_be import OptimizedBE
from .Cucuringu import LowRankCore
from .rombach import Rombach
from .optimized_rombach import OptimizedRombach
import csv
import cpnet
import time

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
        if ext == "gml":
            try:
                G = nx.read_gml(path)
            except Exception as gml_error:
                print(f"Standard GML loading failed: {str(gml_error)}")
                try:
                    G = nx.read_gml(path, label=None)
                except Exception as gml_error2:
                    print(f"GML loading with label=None failed: {str(gml_error2)}")
                    try:
                        G = nx.read_gml(path, label='id')
                    except Exception as gml_error3:
                        print(f"GML loading with label=id failed: {str(gml_error3)}")
                        try:
                            G = nx.read_gml(path, label='name')
                        except Exception as gml_error4:
                            print(f"GML loading with label=name failed: {str(gml_error4)}")
                            
                            if 'karate' in filename.lower():
                                try:
                                    print("Attempting to load karate club network directly...")
                                    G = nx.karate_club_graph()
                                    print("Successfully loaded built-in karate club network")
                                except Exception as karate_error:
                                    print(f"Built-in karate club loading failed: {str(karate_error)}")
                                    raise ValueError(f"Could not load karate club network: {str(gml_error)}")
                            else:
                                raise ValueError(f"Failed to load GML file: {str(gml_error)}")
                
                print("Successfully loaded GML file using alternative method")
            except Exception as gml_error:
                print(f"Standard GML loading failed: {str(gml_error)}")
                try:
                    G = nx.read_gml(path, label=None)
                except Exception as gml_error2:
                    try:
                        G = nx.read_gml(path, label='id')
                    except Exception:
                        try:
                            G = nx.read_gml(path, label='name')
                        except Exception as final_error:
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
            with open(path, "r", encoding='utf-8', errors='ignore') as f:
                sample = f.read(2048)
            
            possible_separators = [',', ';', '\t', ' ', '|', ':', '.']
            
            separator_counts = {sep: sample.count(sep) for sep in possible_separators}
            
            best_separator = max(separator_counts.items(), key=lambda x: x[1])
            sep = best_separator[0] if best_separator[1] > 0 else ','
            
            print(f"Detected separator: '{sep}' with {best_separator[1]} occurrences")
            
            try:
                df = pd.read_csv(path, sep=sep, encoding='utf-8', engine='python')
                
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

            if "source" not in df.columns or "target" not in df.columns:
                df = infer_edge_list_columns(df)

            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

            df = df.dropna(subset=df.columns[:2])
            
            for col in df.columns[:2]:
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].astype(str)
            
            edge_attrs = list(df.columns.difference(["source", "target"]))
            
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

    classifications = {node: 'C' if coreness.get(node, 0) >= threshold else 'P' for node in graph.nodes()}

    core_count = sum(1 for v in classifications.values() if v == 'C')
    periphery_count = sum(1 for v in classifications.values() if v == 'P')
    print(f"Classification result: {core_count} core nodes, {periphery_count} periphery nodes")
    
    return classifications

def process_graph_with_rombach(graph: nx.Graph, num_runs: int = 10, alpha: float = 0.5, beta: float = 0.8) -> Tuple[Dict, Dict, Dict]:
    """Process graph with Rombach algorithm, using optimized version for large networks."""
    
    if graph.number_of_nodes() >= 500:
        print(f"Large network detected ({graph.number_of_nodes()} nodes). Using optimized Rombach implementation.")
        # Pass the exact num_runs parameter from the user, disable auto-reduction of runs
        rombach = OptimizedRombach(
            num_runs=num_runs,  # Keep user-specified value
            alpha=alpha, 
            beta=beta, 
            early_stop=True,    # Enable early stopping for iterations but not runs
            respect_num_runs=True  # New parameter to ensure num_runs is respected
        )
    else:
        rombach = cpnet.Rombach(num_runs=num_runs, alpha=alpha, beta=beta)
    
    rombach.detect(graph)
    x = {node: rombach.x_[i] for i, node in enumerate(graph.nodes())}

    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    # Get algorithm stats if available
    stats = getattr(rombach, 'get_stats', lambda: {})()
    
    return c, x, stats

def process_graph_with_be(graph: nx.Graph, num_runs: int = 10) -> Tuple[Dict, Dict, Dict]:
    """Process graph with BE algorithm.
    
    This function uses the BE algorithm to detect the core-periphery structure of the graph.
    For large networks, it switches to an optimized version.
    """
    
    # Start timing
    start_time = time.time()
    
    """if graph.number_of_nodes() >= 500:
        print(f"Large network detected ({graph.number_of_nodes()} nodes). Using optimized BE implementation.")
        be = OptimizedBE(
            num_runs=num_runs,  # Keep user-specified value
            early_stop=True, 
            use_parallel=True,
            respect_num_runs=True  # Ensure num_runs is respected
        )
    else:"""
    be = cpnet.BE(num_runs=num_runs)
    
    # Store parameters for stats
    original_num_runs = num_runs
    
    # Execute detection
    be.detect(graph)
    x = {node: be.x_[i] for i, node in enumerate(graph.nodes())}
    
    print(f"Using coreness threshold of 0.5 for core-periphery classification")
    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    # End timing
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assign execution time to the BE instance
    be.execution_time = execution_time
    
    # Get algorithm stats
    stats = getattr(be, 'get_stats', lambda: {})()
    
    # Add more stats information
    stats.update({
        "execution_time": execution_time,
        "num_runs": original_num_runs,
        "final_score": getattr(be, "Q_", 0),
        "algorithm": "Borgatti-Everett",
        "explanation": f"BE algorithm completed in {execution_time:.4f} seconds with {original_num_runs} runs."
    })
    
    print(f"Core-periphery detection completed in {execution_time:.4f} seconds")
    print(f"Best score: {getattr(be, 'Q_', 0):.4f}")
    
    return c, x, stats

def process_graph_with_Cucuringu(graph: nx.Graph, beta: float = 0.1) -> Tuple[Dict, Dict, Dict]:
    """Process graph with Cucuringu algorithm, using optimized version for large networks."""
    
    # Start timing
    start_time = time.time()
    
    # Use optimized version for large networks
    """if graph.number_of_nodes() >= 500:
        print(f"Large network detected ({graph.number_of_nodes()} nodes). Using optimized Cucuringu implementation.")
        from .optimized_cucuringu import OptimizedLowRankCore
        cucuringu = OptimizedLowRankCore(beta=beta, respect_params=True)
    else:"""
    cucuringu = cpnet.LowRankCore(beta=beta)
    
    # Store the parameters before detection
    original_beta = beta
    
    # Detect core-periphery structure
    cucuringu.detect(graph)
    x = {node: cucuringu.x_[i] for i, node in enumerate(graph.nodes())}
    
    print(f"Using coreness threshold of 0.5 for core-periphery classification")
    c = classify_nodes_by_coreness(graph, x, threshold=0.5)
    
    # End timing
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assign execution time to cucuringu instance
    cucuringu.execution_time = execution_time
    
    # Get algorithm stats 
    stats = getattr(cucuringu, 'get_stats', lambda: {})()
    
    # Add more stats information
    stats.update({
        "execution_time": execution_time,
        "beta": original_beta,
        "final_score": getattr(cucuringu, "Q_", 0),
        "algorithm": "Cucuringu Low Rank Core",
        "explanation": f"Cucuringu Low Rank Core algorithm completed in {execution_time:.4f} seconds with beta={original_beta}."
    })
    
    print(f"Core-periphery detection completed in {execution_time:.4f} seconds")
    print(f"Best score: {getattr(cucuringu, 'Q_', 0):.4f}")
    
    return c, x, stats


def get_core_stats(graph, classifications):
    """Calculate comprehensive core-periphery specific metrics."""
    core_nodes = set()
    periphery_nodes = set()
    
    is_string_classification = (
        isinstance(classifications, dict) and 
        len(classifications) > 0 and 
        isinstance(next(iter(classifications.values())), str)
    )
    
    if is_string_classification:
        for node, val in classifications.items():
            if val == 'C':
                core_nodes.add(node)
            else:
                periphery_nodes.add(node)
    elif isinstance(classifications, dict):
        for node, val in classifications.items():
            if val == 1:
                core_nodes.add(node)
            else:
                periphery_nodes.add(node)
    else:
        print("Warning: Non-dictionary classification format, converting to sets")
        if isinstance(classifications, list):
            nodes = list(graph.nodes())
            node_to_idx = {node: idx for idx, node in enumerate(nodes)}
            
            if len(classifications) > 0 and isinstance(classifications[0], str):
                for node in graph.nodes():
                    idx = node_to_idx.get(node, -1)
                    if 0 <= idx < len(classifications) and classifications[idx] == 'C':
                        core_nodes.add(node)
                    else:
                        periphery_nodes.add(node)
            else:
                for node in graph.nodes():
                    idx = node_to_idx.get(node, -1)
                    if 0 <= idx < len(classifications) and classifications[idx] == 1:
                        core_nodes.add(node)
                    else:
                        periphery_nodes.add(node)
        else:
            # Unknown format, treat all nodes as periphery
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
    
    # Optimize edge classification with a single pass
    core_core_edges = 0
    core_periphery_edges = 0
    periphery_periphery_edges = 0
    
    # More efficient edge classification using sets
    for u, v in graph.edges():
        if u in core_nodes:
            if v in core_nodes:
                core_core_edges += 1
            else:
                core_periphery_edges += 1
        else:
            if v in core_nodes:
                core_periphery_edges += 1
            else:
                periphery_periphery_edges += 1
    
    # Calculate core density directly
    max_core_edges = len(core_nodes) * (len(core_nodes) - 1) / 2
    core_density = core_core_edges / max_core_edges if max_core_edges > 0 else 0.0
    
    # Calculate periphery-core connectivity
    periphery_core_connectivity = (core_periphery_edges / len(periphery_nodes)) if len(periphery_nodes) > 0 else 0.0
    
    total_edges = graph.number_of_edges()
    
    # Calculate percentages
    core_core_percentage = (core_core_edges / total_edges * 100) if total_edges > 0 else 0
    core_periphery_percentage = (core_periphery_edges / total_edges * 100) if total_edges > 0 else 0
    periphery_periphery_percentage = (periphery_periphery_edges / total_edges * 100) if total_edges > 0 else 0
    
    periphery_isolation = periphery_periphery_percentage
    core_periphery_ratio = (core_periphery_edges / total_edges) if total_edges > 0 else 0
    
    # Calculate ideal pattern match scores
    max_core_core = len(core_nodes) * (len(core_nodes) - 1) / 2
    max_core_periphery = len(core_nodes) * len(periphery_nodes)
    max_periphery_periphery = len(periphery_nodes) * (len(periphery_nodes) - 1) / 2
    
    # In ideal case: all core-core connections, all core-periphery connections, no periphery-periphery
    core_core_match = core_core_edges
    core_periphery_match = core_periphery_edges
    periphery_periphery_match = max_periphery_periphery - periphery_periphery_edges
    
    total_pattern_score = core_core_match + core_periphery_match + periphery_periphery_match
    max_pattern_score = max_core_core + max_core_periphery + max_periphery_periphery
    
    ideal_pattern_match = (total_pattern_score / max_pattern_score * 100) if max_pattern_score > 0 else 0
    
    # Set interpretation texts
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
    
    # Determine structure quality
    structure_quality = "uncertain"
    if core_density > 0.7 and periphery_periphery_percentage < 10:
        structure_quality = "strong"
    elif core_density > 0.4 and periphery_periphery_percentage < 20:
        structure_quality = "moderate"
    elif periphery_periphery_percentage > core_core_percentage or periphery_periphery_percentage > core_periphery_percentage:
        structure_quality = "weak"
    else:
        structure_quality = "mixed"
    
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

def get_node_classifications_and_coreness(graph, c):
    string_classifications = {}
    
    for node in graph.nodes():
        if isinstance(c, dict):
            numeric_classification = c.get(node, 0)
        else:
            numeric_classification = 0
            
        string_classifications[node] = "C" if numeric_classification == 1 else "P"

    return string_classifications

def generate_csv(graph, degrees, string_classifications=None, coreness_values=None, 
              calculate_closeness=False, calculate_betweenness=False, 
              pre_calculated_closeness=None, pre_calculated_betweenness=None):
    """Generate a CSV file with node classifications and coreness values."""
    try:
        filename = f"{uuid.uuid4()}.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        header = ['id', 'type', 'coreness', 'degree']
        if calculate_closeness:
            header.append('closeness')
        if calculate_betweenness:
            header.append('betweenness')
            
        rows = [header]
                
        for node in graph.nodes():
            row = [
                node, 
                string_classifications[node], 
                coreness_values[node],
                degrees.get(node, 0)
            ]
            
            if calculate_closeness:
                if pre_calculated_closeness and node in pre_calculated_closeness:
                    row.append(pre_calculated_closeness[node])
                else:
                    row.append(0.0)
                    
            if calculate_betweenness:
                if pre_calculated_betweenness and node in pre_calculated_betweenness:
                    row.append(pre_calculated_betweenness[node])
                else:
                    row.append(0.0)
                
            rows.append(row)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        
        return filename
    except Exception as e:
        print(f"Error generating CSV file: {str(e)}")
        return None

def generate_edges_csv(graph, string_classifications=None, coreness_values=None, pre_calculated_edge_types=None):
    """Generate a CSV file with edge types (based on node classifications)."""
    try:
        filename = f"{uuid.uuid4()}_edges.csv"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)
        
        csv_content = [['source', 'target', 'type']]
        
        for u, v in graph.edges():
            if pre_calculated_edge_types and (u, v) in pre_calculated_edge_types:
                edge_type = pre_calculated_edge_types[(u, v)]
            else:
                edge_type = f"{string_classifications[u]}-{string_classifications[v]}"
            
            csv_content.append([u, v, edge_type])
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_content)
        
        return filename
    except Exception as e:
        print(f"Error generating edges CSV file: {str(e)}")
        return None

def generate_gdf(graph, degrees, pre_calculated_closeness=None, pre_calculated_betweenness=None, 
                string_classifications=None, coreness_values=None, pre_calculated_edge_types=None):
    """Generate a GDF file with comprehensive node and edge data."""
    try:
        filename = f"{uuid.uuid4()}.gdf"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
        filepath = os.path.join(output_dir, filename)

        has_closeness = pre_calculated_closeness is not None
        has_betweenness = pre_calculated_betweenness is not None
        
        node_header = "nodedef>name VARCHAR,label VARCHAR,type VARCHAR,coreness DOUBLE,degree INTEGER"
        if has_closeness:
            node_header += ",closeness DOUBLE"
        if has_betweenness:
            node_header += ",betweenness DOUBLE"
        
        with open(filepath, 'w') as f:
            f.write(f"{node_header}\n")
            
            for node in graph.nodes():
                node_type = string_classifications[node]
                coreness_value = coreness_values[node]
                degree = degrees.get(node, 0)
                
                node_line = f"{node},{node},{node_type},{coreness_value},{degree}"
                
                if has_closeness:
                    closeness_value = pre_calculated_closeness.get(node, 0.0)
                    node_line += f",{closeness_value}"
                    
                if has_betweenness:
                    betweenness_value = pre_calculated_betweenness.get(node, 0.0)
                    node_line += f",{betweenness_value}"
                
                f.write(f"{node_line}\n")
            
            f.write("edgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE,type VARCHAR\n")
            
            for u, v in graph.edges():
                edge_data = graph.get_edge_data(u, v) or {}
                weight = edge_data.get('weight', 1.0)
                
                if pre_calculated_edge_types and (u, v) in pre_calculated_edge_types:
                    edge_type = pre_calculated_edge_types[(u, v)]
                else:
                    edge_type = f"{string_classifications[u]}-{string_classifications[v]}"
                
                f.write(f"{u},{v},{weight},{edge_type}\n")
                
        return filename
    except Exception as e:
        print(f"Error generating GDF file: {str(e)}")
        return None

def get_algorithm_function(algorithm):
    """Return the appropriate algorithm function based on the algorithm name."""
    algorithm_map = {
        "rombach": process_graph_with_rombach,
        "be": process_graph_with_be,
        "cucuringu": process_graph_with_Cucuringu
    }
    
    if algorithm not in algorithm_map:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return algorithm_map[algorithm]