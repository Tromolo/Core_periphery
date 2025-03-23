import os
import networkx as nx
import asyncio
import time
import glob
from collections import Counter

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.responses import JSONResponse
import uvicorn
import community as community_louvain
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel

from .functions import load_graph_file, get_algorithm_function, get_node_classifications_and_coreness, generate_csv, generate_edges_csv, generate_gdf
from .Metrics import calculate_all_network_metrics, calculate_network_metrics, calculate_connected_components, prepare_community_analysis_data

from contextlib import asynccontextmanager

class AlgorithmRequest(BaseModel):
    algorithm: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(cleanup_static_directory())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

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
            global_graph = await load_graph_file(file)
            print(f"Graph loaded successfully: {global_graph.number_of_nodes()} nodes, {global_graph.number_of_edges()} edges")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")

        try:
            network_metrics = calculate_network_metrics(global_graph)
            community_data = prepare_community_analysis_data(global_graph)
            
            graph_data = {
                "nodes": [],
                "edges": []
            }
            
            degrees = dict(global_graph.degree())
            for node in global_graph.nodes():
                node_degree = degrees.get(node, 0)
                
                graph_data["nodes"].append({
                    "id": str(node),
                    "degree": node_degree,
                })
                
            for edge in global_graph.edges():
                source, target = edge
                edge_data = global_graph.get_edge_data(source, target) or {}
                weight = edge_data.get('weight', 1.0)
                
                graph_data["edges"].append({
                    "id": f"{source}-{target}",
                    "source": str(source),
                    "target": str(target),
                    "weight": float(weight)
                })
            
            degree_distribution = network_metrics.get('degree_distribution', [])
            
        except Exception as e:
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
        try:
            print("Loading graph file...")
            graph = await load_graph_file(file)
            print(f"Graph loaded successfully: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")
        
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
        
        print(f"Processing graph with {algorithm} algorithm...")

        algorithm_func = get_algorithm_function(algorithm)
        classifications, coreness = algorithm_func(graph, **params)

        string_classifications, coreness_values = get_node_classifications_and_coreness(graph, classifications, coreness)
        
        if isinstance(classifications, dict):
            classifications_list = [classifications.get(node, 0) for node in graph.nodes()]
        else:
            nodes = list(graph.nodes())
            node_to_idx = {node: idx for idx, node in enumerate(nodes)}
            classifications_list = [classifications[node_to_idx.get(node, -1)] if 0 <= node_to_idx.get(node, -1) < len(classifications) else 0 
                                  for node in graph.nodes()]
                
        core_count = sum(1 for c in classifications_list if c > 0.5)
        periphery_count = len(classifications_list) - core_count
        print(f"Classification conversion: {core_count} core nodes, {periphery_count} periphery nodes")

        from backend.functions import get_core_stats
        print("Computing core-periphery statistics...")
        core_stats = get_core_stats(graph, string_classifications)
        
        print("Computing node metrics...")
        degrees = dict(graph.degree())
        try:
            print("Computing closeness centrality...")
            closeness = nx.closeness_centrality(graph)
        except Exception as e:
            closeness = {node: 0.0 for node in graph.nodes()}

        print("Generating output files...")
        
        node_csv_file = generate_csv(
            graph, 
            classifications, 
            coreness, 
            string_classifications=string_classifications,
            coreness_values=coreness_values
        )

        edge_csv_file = generate_edges_csv(
            graph, 
            classifications, 
            coreness,
            string_classifications=string_classifications,
            coreness_values=coreness_values
        )
        
        gdf_file = generate_gdf(
            graph, 
            classifications, 
            coreness,
            degrees,
            closeness,
            string_classifications=string_classifications,
            coreness_values=coreness_values
        )
        
        print("Computing network metrics...")
        network_metrics = calculate_all_network_metrics(
            graph, 
            classifications, 
            coreness, 
            algorithm, 
            params, 
            pre_calculated_core_stats=core_stats
        )
                
        print("Preparing graph data response...")
        graph_data = {"nodes": [], "edges": []}
        
        for node in graph.nodes():
            node_type = string_classifications[node]
            coreness_value = coreness_values[node]
            node_degree = degrees.get(node, 0)
            
            graph_data["nodes"].append({
                "id": str(node),
                "type": node_type,
                "coreness": float(coreness_value),
                "degree": node_degree,
                "closeness": closeness.get(node, 0.0)
            })
            
        for edge in graph.edges():
            source, target = edge
            edge_data = graph.get_edge_data(source, target) or {}
            weight = edge_data.get('weight', 1.0)
            
            graph_data["edges"].append({
                "id": f"{source}-{target}",
                "source": str(source),
                "target": str(target),
                "weight": float(weight)
            })
        
        print("Finding top nodes...")
        top_core_nodes = sorted(
            [node for node in graph_data["nodes"] if node["type"] == "C"],
            key=lambda node: node["coreness"], 
            reverse=True
        )[:5]

        top_periphery_nodes = sorted(
            [node for node in graph_data["nodes"] if node["type"] == "P"],
            key=lambda node: node["coreness"]
        )[:5]

        top_nodes_result = {
            "top_core_nodes": top_core_nodes,
            "top_periphery_nodes": top_periphery_nodes
        }

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
            "graph_data": graph_data,
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
        ext = filename.split(".")[-1].lower()
        media_type = 'application/octet-stream'
        
        if ext == 'png':
            media_type = 'image/png'
        elif ext == 'jpg' or ext == 'jpeg':
            media_type = 'image/jpeg'
        elif ext == 'csv':
            media_type = 'text/csv'
        elif ext == 'gdf':
            media_type = 'text/plain'
        
        response = FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
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