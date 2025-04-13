import networkx as nx
import pandas as pd
import os
import time
import sys 


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

OUTPUT_SUMMARY_CSV = "network_properties_summary.csv"

OUTPUT_CENTRALITY_DIR = os.path.join(project_path, "results", "node_centralities")


CENTRALITY_NODE_LIMIT = 10000

def load_graph_from_path(path):
    """
    Načíta graf z cesty pomocou networkx.
    Rozpoznáva .gml a .csv (pomocou pandas pre robustnosť).
    """
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
    G = None
    print(f"\nNačítavam sieť: {network_name}")
    
    try:
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

    except Exception as e:
        print(f"FATÁLNA CHYBA pri načítavaní siete {network_name}: {e}")
        return None 

    if G is None:
        print(f"Varovanie: Nepodarilo sa načítať sieť {network_name}")
        return None

    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
         print(f"  Varovanie: Konvertujem MultiGraph na Graph.")
         G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G)) 
    print(f"  Finálny graf: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
    
    if G.number_of_nodes() > 0:
        node_type = type(list(G.nodes())[0])
        if node_type != str:
             print(f"  Varovanie: Uzly nie sú string (typ: {node_type}), pretypujem pre konzistenciu.")
             try:
                 G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
             except Exception as relabel_error:
                 print(f"  CHYBA pri pretypovaní uzlov na string: {relabel_error}")
    return G


os.makedirs(OUTPUT_CENTRALITY_DIR, exist_ok=True)
print(f"\nVýstupné súbory centralít budú uložené do: {OUTPUT_CENTRALITY_DIR}")


summary_results = []
print("\nStarting network property calculation...")

for network_name in NETWORK_NAMES:
    
    start_time = time.time()
    centrality_data_list = [] 

    try:
        G = load_network(network_name)
        
        if G is None:
            print(f"Preskakujem výpočty pre {network_name}, keďže sa ju nepodarilo načítať.")
            summary_results.append({"Network": network_name, "Nodes (N)": "Load Error", "Edges (E)": "N/A"})
            continue

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
                modularity_score = nx.community.modularity(G, communities)
                num_communities = len(communities)
                print(f"  Modularity: {modularity_score:.4f}, Num Communities: {num_communities}")
            except Exception as e:
                print(f"  WARNING: Could not calculate communities/modularity for {network_name}: {e}")
        else:
             print("  Skipping community detection (no edges).")


        deg_cen = {}
        bet_cen = {}
        clo_cen = {}

        if N > 0:
            try:
                print("  Calculating Degree Centrality...")
                deg_cen = nx.degree_centrality(G)
                print(f"  Degree Centrality calculated for {len(deg_cen)} nodes.")
            except Exception as e:
                 print(f"  WARNING: Could not calculate Degree Centrality for {network_name}: {e}")
            
            if N <= CENTRALITY_NODE_LIMIT: 
                try:
                    print(f"  Calculating Betweenness Centrality (N={N} <= limit={CENTRALITY_NODE_LIMIT})...")
                    bet_cen = nx.betweenness_centrality(G, normalized=True, k=None) # k=None pre presný výpočet
                    print(f"  Betweenness Centrality calculated for {len(bet_cen)} nodes.")
                except Exception as e:
                     print(f"  WARNING: Could not calculate Betweenness Centrality for {network_name}: {e}")
                     
                try:
                    print(f"  Calculating Closeness Centrality (N={N} <= limit={CENTRALITY_NODE_LIMIT})...")
                    if not nx.is_connected(G):
                         print(f"  INFO: Graph is not connected. Calculating Closeness only for the largest connected component.")
                         largest_cc_nodes = max(nx.connected_components(G), key=len)
                         G_lcc = G.subgraph(largest_cc_nodes).copy()
                         clo_cen = nx.closeness_centrality(G_lcc)
                         print(f"  Closeness Centrality calculated for {len(clo_cen)} nodes (LCC).")
                    else:
                         clo_cen = nx.closeness_centrality(G)
                         print(f"  Closeness Centrality calculated for {len(clo_cen)} nodes (all).")
                         
                except Exception as e:
                     print(f"  WARNING: Could not calculate Closeness Centrality for {network_name}: {e}")
            else:
                print(f"  Skipping Betweenness/Closeness calculation for large network (N={N} > limit={CENTRALITY_NODE_LIMIT}).")

            print("  Preparing detailed centrality data...")
            node_list = list(G.nodes())
            for node in node_list:
                 centrality_data_list.append({
                     'node_id': node,
                     'degree_centrality': deg_cen.get(node, None), 
                     'betweenness_centrality': bet_cen.get(node, None),
                     'closeness_centrality': clo_cen.get(node, None) 
                 })
        else:
             print("  Skipping centrality calculation (no nodes).")

        if centrality_data_list:
            centrality_df = pd.DataFrame(centrality_data_list)
            safe_network_name = network_name.replace(" ", "_").replace("-","_").lower()
            centrality_output_path = os.path.join(OUTPUT_CENTRALITY_DIR, f"{safe_network_name}_centralities.csv")
            try:
                centrality_df.to_csv(centrality_output_path, index=False, float_format='%.8g') 
                print(f"  Detailed centralities saved to: {centrality_output_path}")
            except Exception as e:
                print(f"  ERROR saving detailed centralities for {network_name} to {centrality_output_path}: {e}")
        else:
            print(f"  No centrality data generated for {network_name}.")

        summary_results.append({
            "Network": network_name,
            "Nodes (N)": N,
            "Edges (E)": E,
            "Density": density,
            "Modularity": modularity_score,
            "Num Communities": num_communities,
        })
        
        end_time = time.time()
        print(f"  Processing time for {network_name}: {end_time - start_time:.2f} seconds")

    except Exception as e:
        print(f"  GENERAL ERROR processing {network_name}: {e}")
        summary_results.append({"Network": network_name, "Nodes (N)": "Processing Error", "Edges (E)": str(e)})


if summary_results:
    df_summary = pd.DataFrame(summary_results)
    summary_column_order = [
        "Network", "Nodes (N)", "Edges (E)", "Density", 
        "Modularity", "Num Communities", 
    ]
    df_summary = df_summary.reindex(columns=summary_column_order) 
    
    try:
        df_summary.to_csv(OUTPUT_SUMMARY_CSV, index=False, float_format='%.6f')
        print(f"\nSummary results saved to {OUTPUT_SUMMARY_CSV}")
    except Exception as e:
        print(f"\nERROR saving summary results to {OUTPUT_SUMMARY_CSV}: {e}")
else:
    print("\nNo summary results generated.")

print("\nScript finished.")
