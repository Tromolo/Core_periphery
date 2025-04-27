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
output_csv = os.path.join(output_dir, 'be_optimal_cores.csv')

be_optimal_params = {
    "Karate Club": {"num_runs": 20}, 
    "Dolphins": {"num_runs": 20},
    "Les Miserables": {"num_runs": 20}, 
    "Football": {"num_runs": 10},
    "Facebook Combined": {"num_runs": 1},
    "Power Grid": {"num_runs": 1},
    "Bianconi-0.7": {"num_runs": 1},
    "Bianconi-0.97": {"num_runs": 1},
    "YeastL": {"num_runs": 10}
}

FIXED_SEED = 42 

def load_network(network_name):
    """Načíta sieť podľa názvu."""
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
            print(f"  Sieť {network_name} nie je relevantná pre túto BE analýzu.")
            return None

    except Exception as e:
        print(f"FATÁLNA CHYBA pri načítavaní siete {network_name}: {e}")
        return None 

    if G is None:
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

all_core_data = []
print(f"\nSpúšťam extrakciu core uzlov pre BE algoritmus (optimálne parametre)...")

try:
    be_algorithm = get_algorithm_function("BE")
except ValueError as e:
    print(f"Chyba: Nepodarilo sa získať BE algoritmus: {e}")
    sys.exit(1)

for network_name, params in be_optimal_params.items():
    
    G = load_network(network_name)
    if G is None:
        print(f"Preskakujem sieť {network_name}, nepodarilo sa načítať.")
        continue
        
    num_runs = params['num_runs']
    print(f"  Spracúvam {network_name} s num_runs={num_runs}...")
    
    start_time = time.time()
    
    random.seed(FIXED_SEED)
    np.random.seed(FIXED_SEED)
    
    core_nodes_list = []
    try:
        classifications, coreness_scores, algo_stats = be_algorithm(G, num_runs=num_runs)
        

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
        print(f"  CHYBA pri spustení BE algoritmu pre {network_name} (num_runs={num_runs}): {e}")
        traceback.print_exc()
        core_nodes_list = ["ERROR"] 

    all_core_data.append({
        "Network": network_name,
        "num_runs": num_runs,
        "Core_Nodes": ",".join(map(str, core_nodes_list)) 
    })

if all_core_data:
    df_cores = pd.DataFrame(all_core_data)
    try:
        df_cores.to_csv(output_csv, index=False)
        print(f"\nZoznamy core uzlov pre BE uložené do: {output_csv}")
    except Exception as e:
        print(f"\nCHYBA pri ukladaní výsledkov do {output_csv}: {e}")
else:
    print("\nNeboli vygenerované žiadne dáta o core uzloch.")

print("\nSkript extract_optimal_be_cores.py dokončený.")
