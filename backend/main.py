import os
import uuid
import shutil
import networkx as nx
import asyncio
import time
from datetime import datetime
import glob
from collections import Counter

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.responses import JSONResponse
import pandas as pd
import uvicorn
import community as community_louvain
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel

from .functions import classify_and_save_edges, process_graph_with_rombach, process_graph_with_be, process_graph_with_holme, load_graph_file, process_graph
from .utils import  draw_interactive
from .Metrics import calculate_all_network_metrics, calculate_network_metrics, calculate_connected_components, prepare_community_analysis_data

from contextlib import asynccontextmanager

class AlgorithmRequest(BaseModel):
    algorithm: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cleanup_task = asyncio.create_task(cleanup_static_directory())
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

# Define the static directory path using absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.abspath(os.path.join(current_dir, "..", "static"))
print(f"Static directory path: {output_dir}")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

app.mount("/static", StaticFiles(directory=output_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
global_graph = None

@app.post("/upload_graph")
async def upload_graph(file: UploadFile = File(...)):
    try:
        global global_graph
        
        try:
            print("Loading graph file...")
            global_graph = await load_graph_file(file)
            print(f"Graph loaded successfully: {global_graph.number_of_nodes()} nodes, {global_graph.number_of_edges()} edges")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")

        try:
            print("Calculating network metrics...")
            # Calculate only basic network metrics, community data, and connected components
            network_metrics = calculate_network_metrics(global_graph)
            community_data = prepare_community_analysis_data(global_graph)
            
            # Prepare basic graph data for visualization
            graph_data = {
                "nodes": [],
                "edges": []
            }
            
            # Calculate node metrics for visualization
            degrees = dict(global_graph.degree())
            # Add nodes
            for node in global_graph.nodes():
                node_degree = degrees.get(node, 0)
                
                graph_data["nodes"].append({
                    "id": str(node),
                    "degree": node_degree,
                })
                
            # Add edges
            for edge in global_graph.edges():
                source, target = edge
                # Get edge data if available
                edge_data = global_graph.get_edge_data(source, target) or {}
                weight = edge_data.get('weight', 1.0)
                
                graph_data["edges"].append({
                    "id": f"{source}-{target}",
                    "source": str(source),
                    "target": str(target),
                    "weight": float(weight)
                })
            
            # Get degree distribution directly from network_metrics
            # No need to recalculate it
            degree_distribution = network_metrics.get('degree_distribution', [])
            
            print("Network metrics calculated successfully")
        except Exception as e:
            print(f"Error calculating network metrics: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error calculating network metrics: {str(e)}")
        
        return JSONResponse(
            content={
                "message": "Graph uploaded and network metrics calculated successfully",
                "network_metrics": network_metrics,
                "community_data": community_data,
                "graph_data": graph_data,
                "degree_distribution": degree_distribution
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Add a new endpoint for direct file upload and analysis in one step
@app.post("/analyze")
async def analyze_uploaded_graph(
    file: UploadFile = File(...),
    algorithm: str = Form(...),
    alpha: float = Form(0.3),
    beta: float = Form(0.6),
    num_runs: int = Form(10),
    num_iterations: int = Form(100),
    threshold: float = Form(0.05)
):
    try:
        # Load the graph from the uploaded file
        try:
            print("Loading graph file...")
            graph = await load_graph_file(file)
            print(f"Graph loaded successfully: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")
        
        # Set algorithm parameters based on the selected algorithm
        params = {}
        if algorithm == 'rombach':
            params = {
                'alpha': alpha,
                'beta': beta,
                'num_runs': num_runs
            }
        elif algorithm == 'be':
            params = {
                'num_runs': num_runs
            }
        elif algorithm == 'holme':
            params = {
                'num_iterations': num_iterations,
                'threshold': threshold
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid algorithm: {algorithm}")
        
        # Process the graph with the selected algorithm
        print(f"Processing graph with {algorithm} algorithm...")
        
        # Get algorithm function
        from backend.functions import get_algorithm_function
        algorithm_func = get_algorithm_function(algorithm)
        
        # Run the core-periphery detection algorithm
        classifications, coreness = algorithm_func(graph, **params)
        
        # Convert numeric classifications (0/1) to string format ('P'/'C') for compatibility
        string_classifications = {}
        if isinstance(classifications, dict):
            for node, value in classifications.items():
                string_classifications[node] = 'C' if value == 1 else 'P'
        else:
            # Handle list format
            string_classifications = ['C' if val == 1 else 'P' for val in classifications]
        
        # Print debug information about classifications
        if isinstance(string_classifications, dict):
            core_count = sum(1 for v in string_classifications.values() if v == 'C')
            periphery_count = sum(1 for v in string_classifications.values() if v == 'P')
        else:
            core_count = string_classifications.count('C')
            periphery_count = string_classifications.count('P')
        
        print(f"Classification conversion: {core_count} core nodes, {periphery_count} periphery nodes")
        
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
        
        # Get core statistics - use string_classifications for better compatibility
        from backend.functions import get_core_stats
        core_stats = get_core_stats(graph, string_classifications)
        
        # For graph visualization, calculate centrality metrics
        degrees = dict(graph.degree())
        try:
            import networkx as nx
            betweenness = nx.betweenness_centrality(graph)
            closeness = nx.closeness_centrality(graph)
        except Exception as e:
            print(f"Error calculating centrality metrics: {str(e)}")
            betweenness = {node: 0.0 for node in graph.nodes()}
            closeness = {node: 0.0 for node in graph.nodes()}
        
        # Generate node CSV file with pre-calculated betweenness
        from backend.functions import generate_csv, generate_edges_csv
        node_csv_file = generate_csv(graph, classifications, coreness, pre_calculated_betweenness=betweenness)
        
        # Generate edges CSV file
        edge_csv_file = generate_edges_csv(graph, classifications, coreness)
        
        # Generate GDF file
        from backend.functions import generate_gdf
        gdf_file = generate_gdf(graph, classifications, coreness, pre_calculated_betweenness=betweenness)
        
        # Generate static image
        from backend.functions import draw_static
        image_file = draw_static(graph, classifications, coreness)
        
        # Get top nodes
        from backend.functions import get_top_nodes
        top_nodes_result = get_top_nodes(graph, coreness, string_classifications)
        
        # Calculate only the core-periphery specific metrics - avoid redundant calculations
        from backend.Metrics import calculate_all_network_metrics
        network_metrics = calculate_all_network_metrics(graph, classifications, coreness, algorithm, params, pre_calculated_core_stats=core_stats)
        
        # Build graph data with core-periphery information
        graph_data = {"nodes": [], "edges": []}
        
        # Add nodes with core-periphery classification
        for i, node in enumerate(graph.nodes()):
            node_type = classifications_list[i]
            if isinstance(node_type, int):
                node_type = "C" if node_type == 1 else "P"
                
            coreness_value = coreness_list[i]
            node_degree = degrees.get(node, 0)
            
            graph_data["nodes"].append({
                "id": str(node),
                "type": node_type,
                "coreness": float(coreness_value),
                "degree": node_degree,
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
        
        # Prepare the algorithm parameters for response
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
        
        print("Core-periphery analysis completed successfully")
        
        return JSONResponse(content={
            "message": f"Core-periphery analysis with {algorithm} algorithm completed successfully",
            "classifications": classifications_list,
            "network_metrics": network_metrics,
            "algorithm_params": algorithm_params,
            "top_nodes": top_nodes_result,
            "node_csv_file": node_csv_file,
            "edge_csv_file": edge_csv_file,
            "gdf_file": gdf_file,
            "image_file": image_file,
            "graph_data": graph_data
        })
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(output_dir, filename)
    if os.path.exists(file_path):
        # Set appropriate media type based on file extension
        ext = filename.split(".")[-1].lower()
        media_type = 'application/octet-stream'  # Default
        
        # Define media types for common extensions
        if ext == 'png':
            media_type = 'image/png'
        elif ext == 'jpg' or ext == 'jpeg':
            media_type = 'image/jpeg'
        elif ext == 'csv':
            media_type = 'text/csv'
        elif ext == 'gdf':
            media_type = 'text/plain'
        
        # Create response with appropriate headers
        response = FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
        # Force download by setting Content-Disposition header
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        
        return response
    else:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

@app.get("/check_file/{filename}")
async def check_file(filename: str):
    file_path = os.path.join("../static", filename)
    exists = os.path.exists(file_path)
    return {"filename": filename, "exists": exists, "path": file_path}

#Not used for now idk let it here for now
# modularity_core_periphery_detection modularita podla Rombach et al. (2017)
def modularity_core_periphery_detection(G: nx.Graph):

    if G.number_of_nodes() == 0:
        return [], []

    partition = community_louvain.best_partition(G)

    community_groups = {}
    for node, comm_id in partition.items():
        community_groups.setdefault(comm_id, []).append(node)

    max_density = -1
    core_comm = None
    for comm_id, nodes in community_groups.items():
        subgraph = G.subgraph(nodes)
        d = nx.density(subgraph)
        if d > max_density:
            max_density = d
            core_comm = comm_id

    core_nodes = community_groups[core_comm]
    periphery_nodes = [n for n in G.nodes() if n not in core_nodes]

    return core_nodes, periphery_nodes


# Koeficient jadra a periferii podla Holme (2005)
def compute_core_periphery_coefficient(G: nx.Graph, core_nodes: list, periphery_nodes: list):
    if G.number_of_nodes() == 0:
        return 0.0

    core_set = set(core_nodes)
    periphery_set = set(periphery_nodes)

    ideal_edges = 0
    actual_edges = 0

    for node in core_nodes:
        neighbors = set(G[node])
        core_neighbors = neighbors & core_set
        ideal_edges += len(core_nodes) - 1
        actual_edges += len(core_neighbors)

    for node in core_nodes:
        neighbors = set(G[node])
        periphery_neighbors = neighbors & periphery_set
        ideal_edges += len(periphery_nodes)
        actual_edges += len(periphery_neighbors)

    for node in periphery_nodes:
        neighbors = set(G[node])
        periphery_neighbors = neighbors & periphery_set
        actual_edges -= len(periphery_neighbors)

    coefficient = actual_edges / ideal_edges if ideal_edges > 0 else 0.0
    return coefficient


async def cleanup_static_directory():
    """
    Periodically cleans up files in the static directory that are older than 5 minutes
    """
    while True:
        try:
            current_time = time.time()
            static_dir = "../static"
            
            files = glob.glob(os.path.join(static_dir, "*"))
            
            for file_path in files:
                if os.path.isdir(file_path):
                    continue
                    
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > 300:  
                    try:
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {str(e)}")
            
        except Exception as e:
            print(f"Error in cleanup task: {str(e)}")
        
        await asyncio.sleep(300)

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) #workers=4