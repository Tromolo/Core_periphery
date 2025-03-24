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

from .functions import load_graph_file, get_algorithm_function, get_node_classifications_and_coreness, generate_csv, generate_edges_csv, generate_gdf, get_core_stats
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
    threshold: float = Form(0.05),
    calculate_closeness: bool = Form(False),
    calculate_betweenness: bool = Form(False)
):
    start_time = time.time()
    try:
        try:
            graph = await load_graph_file(file)
        except Exception as e:
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
        
        algorithm_func = get_algorithm_function(algorithm)
        classifications, coreness = algorithm_func(graph, **params)
        
        degrees = dict(graph.degree())
        
        closeness = {}
        betweenness = {}
        centrality_summary = {}
        
        core_nodes = set(node for node, cls in classifications.items() if cls == 'C')
        periphery_nodes = set(graph.nodes()) - core_nodes

        edge_types = {}
        core_core_edges = 0
        core_periphery_edges = 0
        periphery_periphery_edges = 0
        
        for u, v in graph.edges():
            if u in core_nodes:
                if v in core_nodes:
                    edge_type = "C-C"
                    core_core_edges += 1
                else:
                    edge_type = "C-P"
                    core_periphery_edges += 1
            else:
                if v in core_nodes:
                    edge_type = "P-C"
                    core_periphery_edges += 1
                else:
                    edge_type = "P-P"
                    periphery_periphery_edges += 1
            edge_types[(u, v)] = edge_type
            edge_types[(v, u)] = edge_type
        
        total_nodes = len(graph.nodes())
        total_edges = graph.number_of_edges()
        core_percentage = (len(core_nodes) / total_nodes * 100) if total_nodes > 0 else 0
        
        max_core_edges = len(core_nodes) * (len(core_nodes) - 1) / 2
        core_density = core_core_edges / max_core_edges if max_core_edges > 0 else 0.0
        
        periphery_core_connectivity = (core_periphery_edges / len(periphery_nodes)) if len(periphery_nodes) > 0 else 0.0
        
        core_core_percentage = (core_core_edges / total_edges * 100) if total_edges > 0 else 0
        core_periphery_percentage = (core_periphery_edges / total_edges * 100) if total_edges > 0 else 0
        periphery_periphery_percentage = (periphery_periphery_edges / total_edges * 100) if total_edges > 0 else 0
        
        periphery_isolation = periphery_periphery_percentage
        core_periphery_ratio = (core_periphery_edges / total_edges) if total_edges > 0 else 0
        
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
        
        max_core_core = len(core_nodes) * (len(core_nodes) - 1) / 2
        max_core_periphery = len(core_nodes) * len(periphery_nodes)
        max_periphery_periphery = len(periphery_nodes) * (len(periphery_nodes) - 1) / 2
        
        core_core_match = core_core_edges
        core_periphery_match = core_periphery_edges
        periphery_periphery_match = max_periphery_periphery - periphery_periphery_edges
        
        total_pattern_score = core_core_match + core_periphery_match + periphery_periphery_match
        max_pattern_score = max_core_core + max_core_periphery + max_periphery_periphery
        
        ideal_pattern_match = (total_pattern_score / max_pattern_score * 100) if max_pattern_score > 0 else 0
        
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
        
        structure_quality = "uncertain"
        if core_density > 0.7 and periphery_periphery_percentage < 10:
            structure_quality = "strong"
        elif core_density > 0.4 and periphery_periphery_percentage < 20:
            structure_quality = "moderate"
        elif periphery_periphery_percentage > core_core_percentage or periphery_periphery_percentage > core_periphery_percentage:
            structure_quality = "weak"
        else:
            structure_quality = "mixed"

        core_stats = {
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
        
        if calculate_closeness:
            try:
                print("Computing closeness centrality...")
                closeness = nx.closeness_centrality(graph)
                centrality_values = list(closeness.values())
                if centrality_values:
                    centrality_summary["closeness"] = {
                        "avg": sum(centrality_values) / len(centrality_values),
                        "max": max(centrality_values),
                        "min": min(centrality_values)
                    }
                else:
                    centrality_summary["closeness"] = {"avg": 0, "max": 0, "min": 0}
            except Exception as e:
                print(f"Warning: Failed to compute closeness centrality: {str(e)}")
                centrality_summary["closeness"] = {"avg": 0, "max": 0, "min": 0}
                closeness = {node: 0.0 for node in graph.nodes()}

        if calculate_betweenness:
            try:
                print("Computing betweenness centrality...")
                betweenness = nx.betweenness_centrality(graph)
                centrality_values = list(betweenness.values())
                if centrality_values:
                    centrality_summary["betweenness"] = {
                        "avg": sum(centrality_values) / len(centrality_values),
                        "max": max(centrality_values),
                        "min": min(centrality_values)
                    }
                else:
                    centrality_summary["betweenness"] = {"avg": 0, "max": 0, "min": 0}
            except Exception as e:
                print(f"Warning: Failed to compute betweenness centrality: {str(e)}")
                centrality_summary["betweenness"] = {"avg": 0, "max": 0, "min": 0}
                betweenness = {node: 0.0 for node in graph.nodes()}

        node_csv_file = generate_csv(
            graph, 
            degrees,
            string_classifications=classifications,
            coreness_values=coreness,
            calculate_closeness=calculate_closeness,
            calculate_betweenness=calculate_betweenness,
            pre_calculated_closeness=closeness,
            pre_calculated_betweenness=betweenness
        )

        edge_csv_file = generate_edges_csv(
            graph,
            string_classifications=classifications,
            coreness_values=coreness,
            pre_calculated_edge_types=edge_types
        )
        
        gdf_file = generate_gdf(
            graph,
            degrees,
            pre_calculated_closeness=closeness if calculate_closeness else None,
            pre_calculated_betweenness=betweenness if calculate_betweenness else None,
            string_classifications=classifications,
            coreness_values=coreness,
            pre_calculated_edge_types=edge_types
        )

        network_metrics = calculate_all_network_metrics(
            graph, 
            classifications, 
            coreness, 
            algorithm, 
            params, 
            pre_calculated_core_stats=core_stats
        )

        graph_data = {"nodes": [], "edges": []}
        
        for node in graph.nodes():
            node_data = {
                "id": str(node),
                "type": classifications[node],
                "coreness": float(coreness[node]),
                "degree": degrees.get(node, 0),
            }
            
            if calculate_closeness:
                node_data["closeness"] = closeness.get(node, 0.0)
                
            if calculate_betweenness:
                node_data["betweenness"] = betweenness.get(node, 0.0)
            
            graph_data["nodes"].append(node_data)

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
        
        core_nodes_data = [node for node in graph_data["nodes"] if node["type"] == "C"]
        periphery_nodes_data = [node for node in graph_data["nodes"] if node["type"] == "P"]

        top_core_nodes = sorted(core_nodes_data, key=lambda node: node["coreness"], reverse=True)[:5]
        top_periphery_nodes = sorted(periphery_nodes_data, key=lambda node: node["coreness"])[:5]

        top_nodes_result = {
            "top_core_nodes": top_core_nodes,
            "top_periphery_nodes": top_periphery_nodes
        }

        if calculate_closeness or calculate_betweenness:
            top_nodes_result["centrality_summary"] = centrality_summary

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
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.2f} seconds")
        return JSONResponse(content={
            "message": f"Core-periphery analysis with {algorithm} algorithm completed successfully",
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