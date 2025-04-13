import networkx as nx
import pandas as pd
import os
import time


project_path = "." 

NETWORK_NAMES = [
    "Karate Club", 
    "Dolphins", 
    "Les Miserables",
    "Football",
    "Facebook Combined", 
    "Power Grid",      
    "Bianconi-0.7",    
    "Bianconi-0.97"    
]

OUTPUT_CSV = "network_properties_summary.csv"


def load_graph_from_path(path):
    _, ext = os.path.splitext(path)
    G = None 

    if ext == '.gml':
        try:
            print(f"  Načítavam GML {path} pomocou nx.read_gml")
            G = nx.read_gml(path, label='id') 
            G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
        except Exception as load_error:
            print(f"  CHYBA: Zlyhalo načítanie GML {path}: {load_error}")
            raise load_error

    elif ext == '.csv':

        try:
            print(f"  Načítavam CSV {path} pomocou pandas (delimiter=';')")
            df = pd.read_csv(path, delimiter=';', header=None, usecols=[0, 1], 
                             names=['source', 'target'], 
                             dtype=str, 
                             comment='#') 

            G = nx.from_pandas_edgelist(df, source='source', target='target', create_using=nx.Graph)
            print(f"  Graf vytvorený z pandas: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")

        except Exception as load_error:
             print(f"  CHYBA: Zlyhalo načítanie/spracovanie CSV {path} pomocou pandas: {load_error}")
             raise load_error

    else:
        raise ValueError(f"Nepodporovaný formát súboru: {ext} pre {path}")

    if G is None: 
        raise ValueError(f"Graf nebol úspešne načítaný pre {path}")
        
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
         print(f"  Varovanie: Graf načítaný ako MultiGraph. Konvertujem na jednoduchý Graf.")
         G = nx.Graph(G)
    else:
         G.remove_edges_from(nx.selfloop_edges(G))

    return G

def load_network(network_name):
    """Načíta sieť podľa názvu (podľa vášho kódu)."""
    G = None
    print(f"\nNačítavam sieť: {network_name}")
    
    if network_name == 'Karate Club':
        G = nx.karate_club_graph()
        G = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()}) 
        print(f"  Sieť Karate Club načítaná z networkx (uzly pretypované na string)")
    
    elif network_name == 'Dolphins':
        path = os.path.join(project_path, 'data/male_site/dolphins.gml')
        G = load_graph_from_path(path)
        print(f"  Sieť Dolphins načítaná z {path}")
            
    elif network_name == 'Les Miserables':
        path = os.path.join(project_path, 'data/male_site/lesmis.gml')
        G = load_graph_from_path(path)
        print(f"  Sieť Les Miserables načítaná z {path}")
            
    elif network_name == 'Football':
        path = os.path.join(project_path, 'data/male_site/football.gml')
        G = load_graph_from_path(path)
        print(f"  Sieť Football načítaná z {path}")
            
    elif network_name == 'Facebook Combined':
        path = os.path.join(project_path, 'data/male_site/facebook_combined.csv') 
        G = load_graph_from_path(path) 
        print(f"  Sieť Facebook Combined načítaná z {path}")
            
    elif network_name == 'Power Grid':
        path = os.path.join(project_path, 'data/male_site/USpowergrid_n4941.csv') 
        G = load_graph_from_path(path)
        print(f"  Sieť Power Grid načítaná z {path}")
            
    elif network_name == 'Bianconi-0.7':
        path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.7 3.csv')
        G = load_graph_from_path(path)
        print(f"  Sieť Bianconi-0.7 načítaná z {path}")
            
    elif network_name == 'Bianconi-0.97':
        path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.97 3.csv')
        G = load_graph_from_path(path)
        print(f"  Sieť Bianconi-0.97 načítaná z {path}")
    else:
        raise ValueError(f"Neznáma sieť: {network_name}")

    if G is None:
        raise ValueError(f"Nepodarilo sa načítať sieť: {network_name}")

    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
         print(f"  Varovanie: Konvertujem MultiGraph na Graph.")
         G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G)) 
    print(f"  Finálny graf: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
    
    if G.number_of_nodes() > 0:
        node_type = type(list(G.nodes())[0])
        if node_type != str:
             print(f"  Varovanie: Uzly nie sú string (typ: {node_type}), pretypujem pre konzistenciu.")
             G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})

    return G

results = []

print("Starting network property calculation...")

for network_name in NETWORK_NAMES:
    
    start_time = time.time()

    try:
        G = load_network(network_name)
        
        N = G.number_of_nodes()
        E = G.number_of_edges()
        
        density = 0
        if N > 1: 
            density = nx.density(G)

        modularity_score = None
        num_communities = None
        if E > 0: 
            print("  Calculating communities (Louvain)...")
            try:
                communities = nx.community.louvain_communities(G, seed=42) 
                partition = {node: i for i, comm in enumerate(communities) for node in comm}
                modularity_score = nx.community.modularity(G, communities)
                num_communities = len(communities)
                print(f"  Modularity: {modularity_score:.4f}, Num Communities: {num_communities}")
            except Exception as e:
                print(f"  WARNING: Could not calculate communities/modularity for {network_name}: {e}")
        else:
             print("  Skipping community detection (no edges).")


        avg_degree_centrality = None
        avg_betweenness_centrality = None
        avg_closeness_centrality = None

        if N > 0:
            try:
                print("  Calculating Degree Centrality...")
                deg_cen = nx.degree_centrality(G)
                avg_degree_centrality = sum(deg_cen.values()) / N if N > 0 else 0
                print(f"  Avg Degree Centrality: {avg_degree_centrality:.4f}")
            except Exception as e:
                 print(f"  WARNING: Could not calculate Degree Centrality for {network_name}: {e}")
            
            if N <= 2000: 
                try:
                    print("  Calculating Betweenness Centrality (can be slow)...")
                    bet_cen = nx.betweenness_centrality(G, normalized=True) 
                    avg_betweenness_centrality = sum(bet_cen.values()) / N if N > 0 else 0
                    print(f"  Avg Betweenness Centrality: {avg_betweenness_centrality:.4f}")
                except Exception as e:
                     print(f"  WARNING: Could not calculate Betweenness Centrality for {network_name}: {e}")
                     
                try:
                    print("  Calculating Closeness Centrality (can be slow)...")
                    largest_cc_nodes = max(nx.connected_components(G), key=len)
                    if len(largest_cc_nodes) < N:
                        print(f"  INFO: Calculating Closeness only for the largest connected component ({len(largest_cc_nodes)} nodes).")
                        G_lcc = G.subgraph(largest_cc_nodes).copy()
                        clo_cen = nx.closeness_centrality(G_lcc)
                        avg_closeness_centrality = sum(clo_cen.values()) / len(largest_cc_nodes) if len(largest_cc_nodes) > 0 else 0
                            
                    else:
                         clo_cen = nx.closeness_centrality(G)
                         avg_closeness_centrality = sum(clo_cen.values()) / N if N > 0 else 0
                         
                    print(f"  Avg Closeness Centrality (LCC or All): {avg_closeness_centrality:.4f}")
                except Exception as e:
                     print(f"  WARNING: Could not calculate Closeness Centrality for {network_name}: {e}")
            else:
                print(f"  Skipping Betweenness/Closeness for large network (N={N}).")


        results.append({
            "Network": network_name,
            "Nodes (N)": N,
            "Edges (E)": E,
            "Density": density,
            "Modularity": modularity_score,
            "Num Communities": num_communities,
            "Avg Degree Centrality": avg_degree_centrality,
            "Avg Betweenness Centrality": avg_betweenness_centrality,
            "Avg Closeness Centrality": avg_closeness_centrality,
        })
        
        end_time = time.time()
        print(f"  Processing time for {network_name}: {end_time - start_time:.2f} seconds")

    except Exception as e:
        print(f"  ERROR processing {network_name}: {e}")
        results.append({"Network": network_name, "Nodes (N)": "Error", "Edges (E)": str(e)})


if results:
    df_results = pd.DataFrame(results)
    column_order = [
        "Network", "Nodes (N)", "Edges (E)", "Density", 
        "Modularity", "Num Communities", 
        "Avg Degree Centrality", "Avg Betweenness Centrality", "Avg Closeness Centrality"
    ]
    df_results = df_results.reindex(columns=column_order) 
    
    df_results.to_csv(OUTPUT_CSV, index=False, float_format='%.6f')
    print(f"\nResults saved to {OUTPUT_CSV}")
else:
    print("\nNo results generated.")

print("\nScript finished.")
