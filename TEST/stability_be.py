import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import time
import os
import sys
import random

project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)
from backend.functions import get_algorithm_function
from backend.functions import load_graph_from_path

os.makedirs('/home/hruby/PycharmProjects/Core_periphery/TEST/results/stability_be', exist_ok=True)

def load_network(network_name):
    """Načíta sieť podľa názvu."""
    if network_name == 'Karate Club':
        G = nx.karate_club_graph()
        G = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()})
        print(f"Sieť Karate Club načítaná z networkx (uzly premenované na string)")
    
    elif network_name == 'Dolphins':
        dolphins_path = os.path.join(project_path, 'data/male_site/dolphins.gml')
        try:
            G = load_graph_from_path(dolphins_path)
            print(f"Sieť Dolphins načítaná z {dolphins_path} pomocou load_graph_from_path")
        except Exception as e:
            print(f"Chyba pri načítaní Dolphins z {dolphins_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Dolphins z {dolphins_path}")
            
    elif network_name == 'Les Miserables':
        les_mis_path = os.path.join(project_path, 'data/male_site/lesmis.gml')
        try:
            G = load_graph_from_path(les_mis_path)
            print(f"Sieť Les Miserables načítaná z {les_mis_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Les Miserables z {les_mis_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Les Miserables z {les_mis_path}")
            
    elif network_name == 'Football':
        football_path = os.path.join(project_path, 'data/male_site/football.gml')
        try:
            G = load_graph_from_path(football_path)
            print(f"Sieť Football načítaná z {football_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Football z {football_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Football z {football_path}")
    
    return G

def calculate_core_stats(G, communities):
    core = set()
    periphery = set()

    if isinstance(communities, dict):
        sample_value = next(iter(communities.values())) if communities else None
        if isinstance(sample_value, str):    
            core = {node for node, membership in communities.items() if membership == 'C'}
            periphery = {node for node, membership in communities.items() if membership == 'P'}
        elif isinstance(sample_value, int):
            core = {node for node, membership in communities.items() if membership == 1}
            periphery = {node for node, membership in communities.items() if membership == 0}
        else:
            print(f"Warning: Unexpected value type in classification dictionary: {type(sample_value)}. Assuming all periphery.")
            periphery = set(G.nodes())

    elif isinstance(communities, tuple) and len(communities) == 2:
        if isinstance(communities[0], set) and isinstance(communities[1], set):
            core, periphery = communities
        else:
             print(f"Warning: Expected tuple of sets, but got types ({type(communities[0])}, {type(communities[1])}). Assuming all periphery.")
             periphery = set(G.nodes())
    else:
        print(f"Warning: Unrecognized classification format: {type(communities)}. Assuming all periphery.")
        periphery = set(G.nodes())

    if not core.isdisjoint(periphery):
         print("Warning: Core and periphery sets are not disjoint. Recalculating periphery.")
         periphery = set(G.nodes()) - core
    elif core.union(periphery) != set(G.nodes()):
        print("Warning: Core and periphery sets do not cover all nodes. Adjusting sets.")
        all_nodes = set(G.nodes())
        identified_nodes = core.union(periphery)
        missing_nodes = all_nodes - identified_nodes
        periphery.update(missing_nodes)
        print(f"Added {len(missing_nodes)} missing nodes to periphery.")

    core_size = len(core)
    periphery_size = len(periphery)
    total_nodes = G.number_of_nodes()
    
    print(f"Core stats calculation: {core_size} core nodes, {periphery_size} periphery nodes, {total_nodes} total nodes")
    
    core_percentage = (core_size / total_nodes) * 100 if total_nodes > 0 else 0
    
    obs_core_core = 0
    obs_core_periphery = 0
    obs_periphery_periphery = 0

    for u, v in G.edges():
        u_is_core = u in core
        v_is_core = v in core
        if u_is_core and v_is_core:
            obs_core_core += 1
        elif u_is_core or v_is_core: 
            obs_core_periphery += 1
        else:
            obs_periphery_periphery += 1
            
    max_core_core = core_size * (core_size - 1) / 2 if core_size > 1 else 0
    max_core_periphery = core_size * periphery_size
    max_periphery_periphery = periphery_size * (periphery_size - 1) / 2 if periphery_size > 1 else 0
    
    correct_core_core = obs_core_core
    correct_core_periphery = obs_core_periphery
    correct_periphery_periphery = max_periphery_periphery - obs_periphery_periphery 
    
    total_correct = correct_core_core + correct_core_periphery + correct_periphery_periphery
    total_possible = max_core_core + max_core_periphery + max_periphery_periphery
    
    ideal_pattern_match = (total_correct / total_possible * 100) if total_possible > 0 else 0


    pattern_match = ideal_pattern_match 
    
    return {
        'core_size': core_size,
        'periphery_size': periphery_size,
        'core_percentage': core_percentage,
        'pattern_match': pattern_match
    }

def run_be_algorithm(G, network_name, num_runs, repetitions=10):
    results = []
    
    be_algorithm = get_algorithm_function("BE")
    
    for rep in range(repetitions):
        start_time = time.time()
        
        random.seed(42 + rep)
        np.random.seed(42 + rep)
        
        try:
            classifications, coreness_scores, algo_stats = be_algorithm(G, num_runs=num_runs)
            
            end_time = time.time()
            runtime = end_time - start_time
            
            core_stats = calculate_core_stats(G, classifications) 
            
            results.append({
                'network': network_name,
                'algorithm': 'BE',
                'parameters.num_runs': num_runs,
                'repetition': rep,
                'runtime': runtime, 
                'metrics.ideal_pattern_match': core_stats['pattern_match'], 
                'metrics.core_size': core_stats['core_size'],
                'metrics.periphery_size': core_stats['periphery_size'],
                'metrics.core_percentage': core_stats['core_percentage']
            })
            
            print(f"Sieť: {network_name}, num_runs: {num_runs}, rep: {rep}, pattern_match: {core_stats['pattern_match']:.2f}%, core_size: {core_stats['core_size']}, core_percentage: {core_stats['core_percentage']:.2f}%")
        
        except Exception as e:
            import traceback
            print(f"Chyba pri spustení BE algoritmu (rep {rep}, num_runs {num_runs}): {e}")
            traceback.print_exc()
            
    
    return results

def main():
    networks = [
        'Karate Club', 'Dolphins',
        'Les Miserables', 'Football'
    ]
    
    num_runs_values = [5, 10, 20, 50]
    
    repetitions = 10
    
    all_results = []
    
    for network_name in networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            
            for num_runs in num_runs_values:
                results = run_be_algorithm(G, network_name, num_runs, repetitions)
                all_results.extend(results)
        except Exception as e:
            print(f"Chyba pri spracovaní siete {network_name}: {e}")
    
    results_df = pd.DataFrame(all_results)
    
    if len(results_df) == 0:
        print("Žiadne výsledky neboli získané!")
        return
    
    csv_file = '/home/hruby/PycharmProjects/Core_periphery/TEST/results/stability_be/be_stability_results.csv'
    results_df.to_csv(csv_file, index=False)
    print(f"Výsledky boli uložené do súboru '{csv_file}'")
    
    summary = results_df.groupby(['network', 'parameters.num_runs']).agg({
        'metrics.ideal_pattern_match': ['mean', 'std'],
        'metrics.core_percentage': ['mean', 'std'],
        'runtime': ['mean', 'std']
    }).reset_index()
    
    print("\nSúhrn výsledkov:")
    print(summary)
    
    plt.figure(figsize=(10, 6))
    
    colors = {'Karate Club': '#1f77b4', 'Dolphins': '#ff7f0e'}
    
    for network in networks:
        network_data = summary[summary['network'] == network]
        
        if len(network_data) > 0:
            plt.errorbar(
                network_data['parameters.num_runs'], 
                network_data[('metrics.ideal_pattern_match', 'mean')], 
                yerr=network_data[('metrics.ideal_pattern_match', 'std')],
                fmt='o-', linewidth=2, markersize=8, capsize=5, 
                color=colors[network], label=f'{network}'
            )
            
            for i, row in network_data.iterrows():
                plt.text(
                    row['parameters.num_runs'], 
                    row[('metrics.ideal_pattern_match', 'mean')] + 2, 
                    f"{row[('metrics.ideal_pattern_match', 'mean')]:.1f}% ±{row[('metrics.ideal_pattern_match', 'std')]:.1f}",
                    ha='center', fontsize=9, color=colors[network]
                )
    
    plt.title('Vplyv parametra num_runs na kvalitu detekcie BE algoritmu', fontsize=14)
    plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
    plt.ylabel('Pattern Match (%)', fontsize=12)
    
    plt.legend(loc='best', fontsize=10)
    
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.ylim(0, 100)  
    
    plt.tight_layout()
    plt.savefig('/home/hruby/PycharmProjects/Core_periphery/TEST/results/stability_be/be_pattern_match.png', dpi=300)
    plt.close()
    
    plt.figure(figsize=(10, 6))
    
    for network in networks:
        network_data = summary[summary['network'] == network]
        
        if len(network_data) > 0:
            plt.errorbar(
                network_data['parameters.num_runs'], 
                network_data[('metrics.core_percentage', 'mean')], 
                yerr=network_data[('metrics.core_percentage', 'std')],
                fmt='s-', linewidth=2, markersize=8, capsize=5, 
                color=colors[network], label=f'{network}'
            )
            
            for i, row in network_data.iterrows():
                plt.text(
                    row['parameters.num_runs'], 
                    row[('metrics.core_percentage', 'mean')] + 2, 
                    f"{row[('metrics.core_percentage', 'mean')]:.1f}% ±{row[('metrics.core_percentage', 'std')]:.1f}",
                    ha='center', fontsize=9, color=colors[network]
                )
    
    plt.title('Vplyv parametra num_runs na veľkosť jadra BE algoritmu', fontsize=14)
    plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
    plt.ylabel('Veľkosť jadra (%)', fontsize=12)
    
    plt.legend(loc='best', fontsize=10)
    
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('/home/hruby/PycharmProjects/Core_periphery/TEST/results/stability_be/be_core_size.png', dpi=300)
    plt.close()
    
    print("Grafy boli uložené do adresára '/home/hruby/PycharmProjects/Core_periphery/TEST/results/stability_be/'")

if __name__ == "__main__":
    main()