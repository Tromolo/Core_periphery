import pandas as pd
import numpy as np
import networkx as nx
import time
import os
import sys
import random
import traceback

project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)

try:
    from backend.functions import get_algorithm_function, load_graph_from_path 
except ImportError as e:
    print(f"Chyba pri importe funkcií z backend: {e}")
    print("Skontrolujte, či je cesta k projektu správne nastavená v sys.path.")
    sys.exit(1)

output_dir = os.path.join(project_path, 'results', 'optimal_cores')
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, 'cucuringu_optimal_cores.csv')

network_list_for_cucu = [
    "Karate Club", "Dolphins", "Les Miserables", "Football",
    "Facebook Combined", "Power Grid", "Bianconi-0.7", "Bianconi-0.97",
    "YeastL"
]
cucuringu_optimal_params = {network: {"beta": 0.1} for network in network_list_for_cucu}

FIXED_SEED = 42 

def load_graph_from_path(path):
    """Načíta graf z cesty (GML alebo CSV pomocou pandas)."""
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
                             names=['source', 'target'], dtype=str, comment='#') 
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
        elif network_name == 'YeastL':
            path = os.path.join(project_path, 'data/male_site/YeastL.csv')
            G = load_graph_from_path(path)
            print(f"  Sieť YeastL načítaná z {path}")
        else:
            raise ValueError(f"Neznáma sieť: {network_name}")
    except Exception as e:
        print(f"FATÁLNA CHYBA pri načítavaní siete {network_name}: {e}")
        return None 
    if G is None: return None

    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)): G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G)) 
    print(f"  Finálny graf: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
    if G.number_of_nodes() > 0:
        node_type = type(list(G.nodes())[0])
        if node_type != str:
             print(f"  Varovanie: Uzly nie sú string (typ: {node_type}), pretypujem.")
             try: G = nx.relabel_nodes(G, {n: str(n) for n in G.nodes()})
             except Exception as relabel_error: print(f"  CHYBA pretypovania: {relabel_error}")
    return G

all_core_data = []
print(f"\nSpúšťam extrakciu core uzlov pre Cucuringu algoritmus (optimálne parametre)...")

try:
    cucuringu_algorithm = get_algorithm_function("Cucuringu")
except ValueError as e:
    print(f"Chyba: Nepodarilo sa získať Cucuringu algoritmus: {e}")
    sys.exit(1)

for network_name, params in cucuringu_optimal_params.items():
    
    G = load_network(network_name)
    if G is None:
        print(f"Preskakujem sieť {network_name}, nepodarilo sa načítať.")
        continue
        
    beta = params['beta']
    print(f"  Spracúvam {network_name} s beta={beta}...")
    
    start_time = time.time()
    
    random.seed(FIXED_SEED)
    np.random.seed(FIXED_SEED)
    
    core_nodes_list = []
    try:
        classifications, coreness_scores, algo_stats = cucuringu_algorithm(G, beta=beta)
        
        core_nodes = set()
        if isinstance(classifications, dict):
            sample_value = next(iter(classifications.values())) if classifications else None
            if isinstance(sample_value, str) and sample_value in ['C', 'P']:
                core_nodes = {node for node, membership in classifications.items() if membership == 'C'}
            elif isinstance(sample_value, int) and sample_value in [0, 1]:
                 core_nodes = {node for node, membership in classifications.items() if membership == 1}
            else:
                 print(f"  Varovanie: Neočakávaný formát klasifikácie (dict value type: {type(sample_value)}) pre {network_name}. Core set bude prázdny.")
        elif isinstance(classifications, tuple) and len(classifications) == 2:
             if isinstance(classifications[0], set):
                 core_nodes = classifications[0]
             else:
                  print(f"  Varovanie: Neočakávaný formát klasifikácie (tuple element type: {type(classifications[0])}) pre {network_name}. Core set bude prázdny.")
        else:
            print(f"  Varovanie: Nerozpoznaný formát klasifikácie ({type(classifications)}) pre {network_name}. Core set bude prázdny.")
            
        core_nodes_list = sorted(list(core_nodes)) 
        
        end_time = time.time()
        print(f"  Dokončené za {end_time - start_time:.2f}s. Nájdených {len(core_nodes_list)} core uzlov.")
        
    except Exception as e:
        print(f"  CHYBA pri spustení Cucuringu algoritmu pre {network_name} (beta={beta}): {e}")
        traceback.print_exc()
        core_nodes_list = ["ERROR"] 

    all_core_data.append({
        "Network": network_name,
        "beta": beta,
        "Core_Nodes": ",".join(map(str, core_nodes_list)) 
    })

if all_core_data:
    df_cores = pd.DataFrame(all_core_data)
    try:
        df_cores.to_csv(output_csv, index=False)
        print(f"\nZoznamy core uzlov pre Cucuringu uložené do: {output_csv}")
    except Exception as e:
        print(f"\nCHYBA pri ukladaní výsledkov do {output_csv}: {e}")
else:
    print("\nNeboli vygenerované žiadne dáta o core uzloch.")

print("\nSkript extract_optimal_cucuringu_cores.py dokončený.")
