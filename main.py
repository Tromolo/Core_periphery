import os
import uuid
import shutil
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from networkx.algorithms.community import louvain_communities
from networkx.readwrite import json_graph
import plotly.graph_objects as go
from pyvis.network import Network
import dask
import dask.delayed
import uvicorn
import matplotlib as mpl
import numpy as np

app = FastAPI()

templates = Jinja2Templates(directory="templates")
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

global_graph_a = None
global_graph_b = None

LARGE_NODE_THRESHOLD = 2000
LARGE_EDGE_THRESHOLD = 5000

@dask.delayed
def _betweenness_subgraph(sub_nodes, G):
    return nx.betweenness_centrality(G.subgraph(sub_nodes))

def compute_betweenness_centrality_dask(G, chunks=4):
    nodes = list(G.nodes())
    chunk_size = max(1, len(nodes)//chunks)
    subgraphs = [nodes[i:i+chunk_size] for i in range(0, len(nodes), chunk_size)]
    tasks = []
    for sub_nodes in subgraphs:
        tasks.append(_betweenness_subgraph(sub_nodes, G))
    partials = dask.compute(*tasks)
    combined = {}
    for part_dict in partials:
        for node, val in part_dict.items():
            combined[node] = combined.get(node, 0) + val
    return combined

def load_graph_file(file: UploadFile) -> nx.Graph:
    if not file.filename:
        raise ValueError("No file provided.")
    filename = file.filename
    ext = filename.split(".")[-1].lower()

    os.makedirs("tmp", exist_ok=True)
    path = os.path.join("tmp", f"{uuid.uuid4()}.{ext}")
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
        elif ext in ["csv","txt"]:
            df = pd.read_csv(path, sep=None, header=None, engine='python')
            if df.shape[1]<2:
                raise ValueError("File must have at least two columns (source,target).")
            if df.shape[1]==2:
                G= nx.from_pandas_edgelist(df, source=0, target=1)
            else:
                G= nx.from_pandas_edgelist(df, source=0, target=1, edge_attr=2)
        else:
            raise ValueError("Unsupported file type: "+ext)
        return G
    finally:
        if os.path.exists(path):
            os.remove(path)

def filter_graph(
    G: nx.Graph,
    min_degree=0,
    largest_component=False,
    filter_community_id=-1,
    edge_weight_threshold=0.0
)->nx.Graph:
    H = G.copy()
    if edge_weight_threshold>0 and "weight" in nx.get_edge_attributes(H,"weight"):
        to_remove=[]
        for (u,v,data) in H.edges(data=True):
            w = data.get("weight",1.0)
            if w<edge_weight_threshold:
                to_remove.append((u,v))
        H.remove_edges_from(to_remove)
    if min_degree>0:
        degs= dict(H.degree())
        rm=[n for n,d in degs.items() if d<min_degree]
        H.remove_nodes_from(rm)
    if largest_component and not nx.is_empty(H):
        comps=list(nx.connected_components(H))
        if len(comps)>1:
            biggest = max(comps, key=len)
            H= H.subgraph(biggest).copy()
    if filter_community_id!=-1 and not nx.is_empty(H):
        c= list(louvain_communities(H))
        if 0<=filter_community_id< len(c):
            chosen=c[filter_community_id]
            H= H.subgraph(chosen).copy()
    return H

def detect_core_periphery_by_degree(G: nx.Graph, threshold:int):
    degs= dict(G.degree())
    core = [n for n,d in degs.items() if d>=threshold]
    periphery=[n for n,d in degs.items() if d<threshold]
    return core,periphery

def compute_centrality_measures(G: nx.Graph, skip_expensive=False):
    out={}
    out["degree_centrality"] = nx.degree_centrality(G)
    if not skip_expensive:
        if G.number_of_nodes()>LARGE_NODE_THRESHOLD or G.number_of_edges()>LARGE_EDGE_THRESHOLD:
            out["betweenness_centrality"] = compute_betweenness_centrality_dask(G)
        else:
            out["betweenness_centrality"] = nx.betweenness_centrality(G)
    else:
        out["betweenness_centrality"] = "Skipped for large graph"
    out["closeness_centrality"] = nx.closeness_centrality(G)
    if not skip_expensive:
        try:
            out["eigenvector_centrality"] = nx.eigenvector_centrality(G)
        except nx.PowerIterationFailedConvergence:
            out["eigenvector_centrality"] = "Failed to converge"
    else:
        out["eigenvector_centrality"]="Skipped for large graph"
    return out

def plot_clustering_coefficient_distribution(G: nx.Graph, suffix:str):
    if G.number_of_nodes()==0:
        return
    ccs = list(nx.clustering(G).values())
    if not ccs:
        return
    plt.figure(figsize=(10,6))
    plt.hist(ccs,bins=20,color="skyblue",edgecolor="black")
    plt.title(f"Clustering Distribution {suffix}")
    plt.xlabel("Clustering Coefficient")
    plt.ylabel("Frequency")
    plt.grid(True)
    outpath= f"static/clustering_distribution{suffix}.png"
    plt.savefig(outpath)
    plt.close()

def compute_connected_components(G: nx.Graph):
    if G.number_of_nodes()==0:
        return {"num_components":0,"component_sizes":[]}
    comps=list(nx.connected_components(G))
    sizes= [len(c) for c in comps]
    return {"num_components":len(comps),"component_sizes":sizes}

def detect_communities(G: nx.Graph, suffix:str):
    if G.number_of_nodes()==0:
        return {"num_communities":0,"community_sizes":[]}
    try:
        c= list(louvain_communities(G))
        c_sizes= [len(x) for x in c]
        community_map= {}
        for i, comm_set in enumerate(c):
            for nd in comm_set:
                community_map[nd]=i
        if G.number_of_nodes()>0:
            fig, ax = plt.subplots(figsize=(15,10))
            pos=nx.spring_layout(G)
            colors= [community_map[n] for n in G.nodes()]
            if G.number_of_edges()>1000:
                #print("Skipping edges for large graph.")
                nx.draw_networkx_nodes(G,pos,node_color=colors,cmap=plt.cm.tab20,
                                       node_size=20, alpha=0.8,ax=ax)
            else:
                nx.draw_networkx_nodes(G,pos,node_color=colors,cmap=plt.cm.tab20,
                                       node_size=20,alpha=0.8,ax=ax)
                nx.draw_networkx_edges(G,pos,alpha=0.2,ax=ax)
            ax.set_title(f"Community Detection {suffix}")
            ax.axis("off")

            sm = mpl.cm.ScalarMappable(cmap=mpl.cm.tab20,
                                       norm=mpl.colors.Normalize(vmin=0,vmax=len(c)-1))
            sm.set_array([])
            fig.colorbar(sm, ax=ax, label="Community ID")
            outpath= f"static/community_detection{suffix}.png"
            plt.savefig(outpath)
            plt.close()
        return {"num_communities":len(c),"community_sizes":c_sizes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in community detection {suffix}: {e}")

def visualize_graph(G: nx.Graph, suffix:str, layout="spring", node_size_scale=10.0, node_alpha=1.0):
    outimg=f"static/graph_improved{suffix}.png"
    try:
        if G.number_of_nodes()==0:
            plt.figure(figsize=(6,4))
            plt.text(0.5,0.5, f"No nodes {suffix}", ha='center',va='center',fontsize=14)
            plt.axis('off')
            plt.savefig(outimg)
            plt.close()
            return
        fig,ax= plt.subplots(figsize=(15,10))
        if layout=="kamada_kawai":
            pos= nx.kamada_kawai_layout(G)
        else:
            pos= nx.spring_layout(G)
        degs= dict(G.degree())
        node_sizes= [degs[n]*node_size_scale for n in G.nodes()]
        node_colors=[degs[n] for n in G.nodes()]

        nodes= nx.draw_networkx_nodes(G,pos,node_size=node_sizes,node_color=node_colors,
                                      cmap=plt.cm.viridis,alpha=node_alpha, ax=ax)
        if G.number_of_edges()>2000:
            print("Skipping edges (large).")
        else:
            nx.draw_networkx_edges(G,pos,edge_color="gray",alpha=0.7,ax=ax)
        top_nodes= sorted(degs, key=degs.get, reverse=True)[:5]
        nx.draw_networkx_labels(G,pos, labels={n: str(n) for n in top_nodes}, font_size=12,ax=ax)
        ax.set_title(f"{layout.capitalize()} Graph Visualization {suffix}")
        ax.axis("off")
        fig.colorbar(nodes,ax=ax,label="Node Degree")

        plt.savefig(outimg)
        print(f"Graph visualization saved to {outimg}")
    except Exception as e:
        print(f"Error in visualize graph {suffix}: {e}")
    finally:
        plt.close()

def analyze_graph(G: nx.Graph, degree_threshold=0, layout="spring", node_size_scale=10.0, node_alpha=1.0, suffix="_A"):
    num_nodes= G.number_of_nodes()
    num_edges= G.number_of_edges()
    density= nx.density(G) if num_nodes>1 else 0
    avg_clustering= nx.average_clustering(G) if num_nodes>1 else 0
    try:
        if num_nodes>1000 or not nx.is_connected(G):
            avg_shortest_path="Skipped (large or disconnected)"
        else:
            avg_shortest_path= nx.average_shortest_path_length(G)
    except nx.NetworkXError:
        avg_shortest_path= "Infinity (Disconnected)"
    skip_expensive = (num_edges>LARGE_EDGE_THRESHOLD or num_nodes> LARGE_NODE_THRESHOLD)
    centrals= compute_centrality_measures(G,skip_expensive=skip_expensive)

    plot_clustering_coefficient_distribution(G, suffix)
    comm_data= detect_communities(G, suffix)
    visualize_graph(G, suffix, layout, node_size_scale,node_alpha)
    comps= compute_connected_components(G)
    core, periphery= detect_core_periphery_by_degree(G, degree_threshold)

    return {
      "num_nodes": num_nodes,
      "num_edges": num_edges,
      "density": density,
      "avg_clustering": avg_clustering,
      "avg_shortest_path": avg_shortest_path,
      "connected_components": comps,
      "centrality_measures": centrals,
      "community_data": comm_data,
      "core_periphery_data": {
         "threshold": degree_threshold,
         "num_core_nodes": len(core),
         "num_periphery_nodes": len(periphery),
         "core_nodes_sample": core[:10],
         "periphery_nodes_sample": periphery[:10],
      },
      "graph_image": f"/static/graph_improved{suffix}.png",
      "clustering_image": f"/static/clustering_distribution{suffix}.png",
      "community_image": f"/static/community_detection{suffix}.png"
    }


def make_plotly_html_with_suffix(G: nx.Graph, suffix="_A"):
    if G.number_of_nodes()==0:
        return f"<h3>No nodes to display {suffix}</h3>"
    pos= nx.spring_layout(G)
    x_nodes, y_nodes=[],[]
    for n in G.nodes():
        x_nodes.append(pos[n][0])
        y_nodes.append(pos[n][1])
    edge_x, edge_y=[],[]
    if G.number_of_edges()<=3000:
        for (u,v) in G.edges():
            x0,y0 = pos[u]
            x1,y1 = pos[v]
            edge_x.extend([x0,x1,None])
            edge_y.extend([y0,y1,None])
    edge_trace= go.Scatter(
      x=edge_x,y=edge_y,
      line=dict(width=1,color="#888"),
      hoverinfo="none",
      mode="lines"
    )
    node_trace= go.Scatter(
      x=x_nodes,y=y_nodes,
      mode="markers",
      hoverinfo="text",
      marker=dict(
        showscale=True,
        colorscale="YlGnBu",
        color=[],
        size=10,
        colorbar=dict(
          thickness=15,
          title=f"Node Degree {suffix}",
          xanchor="left",
          titleside="right"
        ),
        line_width=2
      )
    )
    degs= [val for (_,val) in G.degree()]
    node_trace.marker.color= degs
    node_txt= [f"{suffix} Node: {n}, deg: {G.degree(n)}" for n in G.nodes()]
    node_trace.text= node_txt

    fig= go.Figure(
      data=[edge_trace,node_trace],
      layout= go.Layout(
         title=f"Plotly Graph {suffix}",
         title_x=0.5,
         showlegend=False,
         hovermode="closest",
         margin=dict(b=20,l=5,r=5,t=40),
         xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
         yaxis=dict(showgrid=False,zeroline=False,showticklabels=False)
      )
    )
    return fig.to_html(full_html=True)

def make_pyvis_html_with_suffix(G: nx.Graph, suffix="_A"):
    if G.number_of_nodes()==0:
        return f"<h3>No nodes {suffix}</h3>"
    net= Network(height="750px", width="100%", bgcolor="#222222",font_color="white")
    net.from_nx(G)
    net.force_atlas_2based()
    out_html= f"static/pyvis_graph{suffix}.html"
    net.show(out_html, notebook=False)
    with open(out_html,"r",encoding="utf-8") as f:
        content=f.read()
    return content

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(
    fileA: UploadFile= File(...),
    fileB: UploadFile= File(None),
    degree_threshold: int= Query(0),
    layout: str= Query("spring"),
    node_size_scale: float= Query(10.0),
    node_alpha: float= Query(1.0),
    min_degree: int= Query(0),
    largest_component: bool= Query(False),
    filter_community_id: int= Query(-1),
    edge_weight_threshold: float= Query(0.0)
):
    global global_graph_a, global_graph_b
    try:
        # A
        Ga= load_graph_file(fileA)
        global_graph_a= Ga
        Gaf= filter_graph(Ga, min_degree, largest_component, filter_community_id, edge_weight_threshold)
        resultA= analyze_graph(Gaf, degree_threshold, layout, node_size_scale,node_alpha, suffix="_A")

        # B
        if fileB and fileB.filename:
            Gb= load_graph_file(fileB)
            global_graph_b= Gb
            Gbf= filter_graph(Gb, min_degree, largest_component, filter_community_id, edge_weight_threshold)
            resultB= analyze_graph(Gbf, degree_threshold, layout, node_size_scale,node_alpha, suffix="_B")
            return {"graphA": resultA, "graphB": resultB}
        else:
            global_graph_b=None
            return {"graphA": resultA}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/heatmap", response_class=FileResponse)
async def heatmap_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="Graph A not available.")
    out_png= "static/adjacency_heatmap_A.png"
    A= nx.to_numpy_array(global_graph_a, nodelist= sorted(global_graph_a.nodes()))
    if A.size==0:
        raise HTTPException(status_code=400, detail="Graph A empty.")
    fig,ax= plt.subplots(figsize=(8,6))
    sns.heatmap(A,cmap="viridis",square=True,ax=ax)
    ax.set_title("Heatmap A")
    plt.savefig(out_png,dpi=150,bbox_inches="tight")
    plt.close(fig)
    return FileResponse(out_png,media_type="image/png",filename="adjacency_heatmap_A.png")


@app.get("/heatmap_b", response_class=FileResponse)
async def heatmap_b():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="Graph B not available.")
    out_png= "static/adjacency_heatmap_B.png"
    A= nx.to_numpy_array(global_graph_b, nodelist= sorted(global_graph_b.nodes()))
    if A.size==0:
        raise HTTPException(status_code=400, detail="Graph B empty.")
    fig,ax= plt.subplots(figsize=(8,6))
    sns.heatmap(A,cmap="viridis",square=True,ax=ax)
    ax.set_title("Heatmap B")
    plt.savefig(out_png,dpi=150,bbox_inches="tight")
    plt.close(fig)
    return FileResponse(out_png,media_type="image/png",filename="adjacency_heatmap_B.png")


@app.get("/statistics")
async def stats_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="Graph A not available.")
    G= global_graph_a
    out={}
    degs= [d for _,d in G.degree()]
    out["degree_distribution"]= degs
    if G.number_of_nodes()>1:
        out["average_clustering"]= nx.average_clustering(G)
    else:
        out["average_clustering"]=0
    if G.number_of_nodes()>0:

        L=nx.laplacian_matrix(G).todense()
        ev= sorted(np.linalg.eigvals(L).real)
        out["laplacian_eigenvalues"]= ev[:10]
    else:
        out["laplacian_eigenvalues"]=[]
    return out


@app.get("/statistics_b")
async def stats_b_():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="Graph B not available.")
    G= global_graph_b
    out={}
    degs= [d for _,d in G.degree()]
    out["degree_distribution"]= degs
    if G.number_of_nodes()>1:
        out["average_clustering"]= nx.average_clustering(G)
    else:
        out["average_clustering"]=0
    if G.number_of_nodes()>0:

        L= nx.laplacian_matrix(G).todense()
        ev= sorted(np.linalg.eigvals(L).real)
        out["laplacian_eigenvalues"]=ev[:10]
    else:
        out["laplacian_eigenvalues"]=[]
    return out


@app.get("/export_graph")
async def export_a(format: str= Query("gexf")):
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No graph A.")
    if format not in ["gexf","graphml","json"]:
        raise HTTPException(status_code=400, detail="Unsupported format.")
    out= f"static/graphA_export.{format}"
    try:
        if format=="gexf":
            nx.write_gexf(global_graph_a,out)
            return FileResponse(out,media_type="application/octet-stream", filename="graphA_export.gexf")
        elif format=="graphml":
            nx.write_graphml(global_graph_a,out)
            return FileResponse(out,media_type="application/xml", filename="graphA_export.graphml")
        else:
            data=json_graph.node_link_data(global_graph_a)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export A error: {e}")


@app.get("/export_graph_b")
async def export_b(format: str= Query("gexf")):
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No graph B.")
    if format not in ["gexf","graphml","json"]:
        raise HTTPException(status_code=400, detail="Unsupported format.")
    out= f"static/graphB_export.{format}"
    try:
        if format=="gexf":
            nx.write_gexf(global_graph_b,out)
            return FileResponse(out,media_type="application/octet-stream", filename="graphB_export.gexf")
        elif format=="graphml":
            nx.write_graphml(global_graph_b,out)
            return FileResponse(out,media_type="application/xml", filename="graphB_export.graphml")
        else:
            data= json_graph.node_link_data(global_graph_b)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export B error: {e}")


@app.get("/d3_graph", response_class=HTMLResponse)
async def d3_a(request: Request):
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="Graph A not available.")
    return templates.TemplateResponse("d3_graph.html", {"request": request})

@app.get("/d3_data")
async def d3_data_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No graph A.")
    data= json_graph.node_link_data(global_graph_a)
    return data


@app.get("/d3_graph_b", response_class=HTMLResponse)
async def d3_b(request: Request):
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="Graph B not available.")
    return templates.TemplateResponse("d3_graph_b.html", {"request": request})

@app.get("/d3_data_b")
async def d3_data_b():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No graph B.")
    data= json_graph.node_link_data(global_graph_b)
    return data


@app.get("/plotly_graph", response_class=HTMLResponse)
async def plotly_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No graph A.")
    html= make_plotly_html_with_suffix(global_graph_a,"_A")
    return HTMLResponse(content=html)


@app.get("/plotly_graph_b", response_class=HTMLResponse)
async def plotly_b():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No graph B.")
    html= make_plotly_html_with_suffix(global_graph_b,"_B")
    return HTMLResponse(content=html)


@app.get("/pyvis_graph", response_class=HTMLResponse)
async def pyvis_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No graph A.")
    html= make_pyvis_html_with_suffix(global_graph_a,"_A")
    return HTMLResponse(content=html)


@app.get("/pyvis_graph_b", response_class=HTMLResponse)
async def pyvis_b():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No graph B.")
    html= make_pyvis_html_with_suffix(global_graph_b,"_B")
    return HTMLResponse(content=html)


@app.get("/shortest_path")
async def sp_a(source:str, target:str):
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No Graph A.")
    if source not in global_graph_a or target not in global_graph_a:
        raise HTTPException(status_code=400, detail="Invalid nodes in A.")
    try:
        path= nx.shortest_path(global_graph_a, source=source, target=target)
        return {"shortest_path": path, "length": len(path)-1}
    except nx.NetworkXNoPath:
        return {"shortest_path":None,"length":"No path"}


@app.get("/spectral_analysis")
async def spectral_a():
    if global_graph_a is None:
        raise HTTPException(status_code=400, detail="No Graph A.")

    L= nx.laplacian_matrix(global_graph_a).todense()
    ev= sorted(np.linalg.eigvals(L).real)
    return {
      "smallest_5_eigenvalues": ev[:5],
      "largest_5_eigenvalues": ev[-5:]
    }


@app.get("/shortest_path_b")
async def sp_b(source:str, target:str):
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No Graph B.")
    if source not in global_graph_b or target not in global_graph_b:
        raise HTTPException(status_code=400, detail="Invalid nodes in B.")
    try:
        path= nx.shortest_path(global_graph_b, source=source, target=target)
        return {"shortest_path": path, "length": len(path)-1}
    except nx.NetworkXNoPath:
        return {"shortest_path":None,"length":"No path"}



@app.get("/spectral_analysis_b")
async def spectral_b():
    if global_graph_b is None:
        raise HTTPException(status_code=400, detail="No Graph B.")

    L= nx.laplacian_matrix(global_graph_b).todense()
    ev= sorted(np.linalg.eigvals(L).real)
    return {
      "smallest_5_eigenvalues": ev[:5],
      "largest_5_eigenvalues": ev[-5:]
    }

if __name__=="__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080) #workers=4
