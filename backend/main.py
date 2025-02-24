import os
import uuid
import shutil
import networkx as nx
import asyncio
import time
from datetime import datetime
import glob

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import pandas as pd
import uvicorn
import community as community_louvain
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

from .functions import classify_and_save_edges, process_graph_with_rombach, process_graph_with_be, process_graph_with_holme, load_graph_file, process_graph
from .utils import  draw_interactive
from .Metrics import calculate_all_network_metrics

from contextlib import asynccontextmanager

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

output_dir = "../static"
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
async def upload_graph(file: UploadFile = File(...), algorithm: str = Form(...)):
    try:
        
        if algorithm not in ["rombach", "be", "holme"]:
            print(f"Invalid algorithm detected: {algorithm}")
            raise HTTPException(status_code=400, detail=f"Invalid algorithm: {algorithm}")
        
        try:
            print("Loading graph file...")
            graph = await load_graph_file(file)
            print(f"Graph loaded successfully: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")

        algorithm_params = {
            "rombach": {
                "num_runs": 10,
                "alpha": 0.3,
                "beta": 0.6
            },
            "be": {
                "num_runs": 10
            },
            "holme": {
                "num_iterations": 100,
                "threshold": 0.01
            }
        }.get(algorithm, {})
        
        print(f"Using algorithm parameters: {algorithm_params}")
        
        try:
            print(f"Processing graph with {algorithm} algorithm...")
            results = process_graph(graph, algorithm, **algorithm_params)
            print(f"Results algorithm type: {results.get('metrics', {}).keys()}") 
            print("Graph processed successfully")
        except Exception as e:
            print(f"Error processing graph: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error processing graph: {str(e)}")
        
        return JSONResponse(
            content={
                "message": f"Graph processed successfully using {algorithm.capitalize()} algorithm",
                **results
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("../static", filename)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    else:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")



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