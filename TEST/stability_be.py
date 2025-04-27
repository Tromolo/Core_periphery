import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import time
import os
import sys
import random
import traceback
import seaborn as sns

project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)
from backend.functions import get_algorithm_function
from backend.functions import load_graph_from_path

results_dir = os.path.join(project_path, 'TEST/results/stability_be')
os.makedirs(results_dir, exist_ok=True)

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
            
    elif network_name == 'Facebook Combined':
        facebook_path = os.path.join(project_path, 'data/male_site/facebook_combined.csv')
        try:
            G = load_graph_from_path(facebook_path)
            print(f"Sieť Facebook Combined načítaná z {facebook_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Facebook Combined z {facebook_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Facebook Combined z {facebook_path}")
            
    elif network_name == 'Power Grid':
        power_grid_path = os.path.join(project_path, 'data/male_site/USpowergrid_n4941.csv')
        try:
            G = load_graph_from_path(power_grid_path)
            print(f"Sieť Power Grid načítaná z {power_grid_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Power Grid z {power_grid_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Power Grid z {power_grid_path}")
            
    elif network_name == 'Bianconi-0.7':
        bianconi07_path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.7 3.csv')
        try:
            G = load_graph_from_path(bianconi07_path)
            print(f"Sieť Bianconi-0.7 načítaná z {bianconi07_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Bianconi-0.7 z {bianconi07_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Bianconi-0.7 z {bianconi07_path}")
            
    elif network_name == 'Bianconi-0.97':
        bianconi97_path = os.path.join(project_path, 'data/site_pro_modely/Bianconi-Triadic-Closure 0.97 3.csv')
        try:
            G = load_graph_from_path(bianconi97_path)
            print(f"Sieť Bianconi-0.97 načítaná z {bianconi97_path}")
        except Exception as e:
            print(f"Chyba pri načítaní Bianconi-0.97 z {bianconi97_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť Bianconi-0.97 z {bianconi97_path}")
    
    elif network_name == 'YeastL':
        yeastl_path = os.path.join(project_path, 'data/male_site/YeastL.csv')
        try:
            G = load_graph_from_path(yeastl_path)
            print(f"Sieť YeastL načítaná z {yeastl_path}")
        except Exception as e:
            print(f"Chyba pri načítaní YeastL z {yeastl_path}: {e}")
            raise ValueError(f"Nepodarilo sa načítať sieť YeastL z {yeastl_path}")
    
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
    
    # Calculate densities
    core_density = obs_core_core / max_core_core if max_core_core > 0 else 0
    periphery_density = obs_periphery_periphery / max_periphery_periphery if max_periphery_periphery > 0 else 0
    core_periphery_ratio = core_density / periphery_density if periphery_density > 0 else float('inf')
    
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
        'pattern_match': pattern_match,
        'core_density': core_density,
        'periphery_density': periphery_density,
        'core_periphery_ratio': core_periphery_ratio
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
                'metrics.core_percentage': core_stats['core_percentage'],
                'metrics.core_density': core_stats['core_density'],
                'metrics.periphery_density': core_stats['periphery_density'],
                'metrics.core_periphery_ratio': core_stats['core_periphery_ratio']
            })
            
            print(f"Sieť: {network_name}, num_runs: {num_runs}, rep: {rep}, pattern_match: {core_stats['pattern_match']:.2f}%, core_size: {core_stats['core_size']}, core_percentage: {core_stats['core_percentage']:.2f}%")
        
        except Exception as e:
            import traceback
            print(f"Chyba pri spustení BE algoritmu (rep {rep}, num_runs {num_runs}): {e}")
            traceback.print_exc()
            
    
    return results

def plot_stability_heatmap(df, x_col, y_col, value_col, title, filename, cmap='viridis', fmt='.1f'):
    """Vykresľuje heatmapu stability."""
    plt.figure(figsize=(10, 8))
    
    # Pivot dáta pre heatmapu
    pivot_df = df.pivot_table(
        index=y_col, 
        columns=x_col,
        values=value_col,
        aggfunc='mean'
    )
    
    # Vytvor heatmapu
    ax = sns.heatmap(pivot_df, annot=True, cmap=cmap, fmt=fmt)
    
    plt.title(title, fontsize=14)
    plt.tight_layout()
    
    try:
        plt.savefig(filename, dpi=300)
        print(f"Heatmapa uložená do '{filename}'")
    except Exception as e:
        print(f"Chyba pri ukladaní heatmapy '{filename}': {e}")
    
    plt.close()

def main():
    # All networks
    small_networks = [
        'Karate Club', 'Dolphins', 'Les Miserables', 'Football'
    ]
    
    large_networks = [
        'Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97', 'YeastL'
    ]
    
    # Rôzne počty behov pre malé a veľké siete
    small_num_runs_values = [5, 10,20, 50]  # Pre malé siete
    large_num_runs_values = [5, 10]      # Pre veľké siete
    
    # Use different repetition counts based on network size
    small_repetitions = 10
    large_repetitions = 1
    
    csv_file = os.path.join(results_dir, 'be_stability_results.csv')
    
    # Najprv spracuj malé siete a prepíš pôvodný súbor
    print("=== SPRACOVANIE MALÝCH SIETÍ ===")
    small_results = []
    total_small_runs = len(small_networks) * len(small_num_runs_values) * small_repetitions
    current_run = 0
    
    for network_name in small_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            
            for num_runs in small_num_runs_values:
                print(f"Spúšťam BE algoritmus s num_runs={num_runs}, repetitions={small_repetitions} ...")
                results = run_be_algorithm(G, network_name, num_runs, small_repetitions)
                small_results.extend(results)
                current_run += len(results)
                print(f"Pokrok malých sietí: {current_run}/{total_small_runs} behov ({(current_run/total_small_runs)*100:.1f}%)")
                
        except Exception as e:
            print(f"Chyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()
    
    # Zapíš malé siete (prepíše súbor)
    if small_results:
        results_df = pd.DataFrame(small_results)
        results_df.to_csv(csv_file, index=False)
        print(f"Výsledky malých sietí boli uložené do súboru '{csv_file}'")
    
    # Potom spracuj veľké siete a appenduj k existujúcemu súboru
    print("\n=== SPRACOVANIE VEĽKÝCH SIETÍ ===")
    large_results = []
    total_large_runs = len(large_networks) * len(large_num_runs_values) * large_repetitions
    current_run = 0
    
    for network_name in large_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            
            for num_runs in large_num_runs_values:
                print(f"Spúšťam BE algoritmus s num_runs={num_runs}, repetitions={large_repetitions} ...")
                results = run_be_algorithm(G, network_name, num_runs, large_repetitions)
                large_results.extend(results)
                current_run += len(results)
                print(f"Pokrok veľkých sietí: {current_run}/{total_large_runs} behov ({(current_run/total_large_runs)*100:.1f}%)")
                
                # Priebežne zapisuj výsledky veľkých sietí (pridaj ich k existujúcemu súboru)
                if results:
                    results_df = pd.DataFrame(results)
                    results_df.to_csv(csv_file, mode='a', header=False, index=False)
                    print(f"Výsledky pre {network_name} s num_runs={num_runs} boli pridané do súboru '{csv_file}'")
                
        except Exception as e:
            print(f"Chyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()
    
    # Načítaj kompletné výsledky pre generovanie heatmáp
    print("\n=== GENEROVANIE HEATMÁP ===")
    try:
        complete_results_df = pd.read_csv(csv_file)
        
        # Generate plots for each network
        all_networks = small_networks + large_networks
        for network in all_networks:
            network_df = complete_results_df[complete_results_df['network'] == network]
            
            if network_df.empty:
                print(f"Žiadne dáta pre sieť {network}")
                continue
            
            print(f"Vykresľujem grafy pre sieť {network}")
            
            # Pattern match stability by num_runs
            plot_filename = os.path.join(results_dir, f'be_stability_{network.replace(" ", "_")}_pattern_match.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.num_runs', 
                y_col='repetition',
                value_col='metrics.ideal_pattern_match',
                title=f'{network}: Ideal Pattern Match (%) by num_runs and repetitions',
                filename=plot_filename,
                cmap='viridis',
                fmt='.1f'
            )
            
            # Core size stability by num_runs
            plot_filename = os.path.join(results_dir, f'be_stability_{network.replace(" ", "_")}_core_percentage.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.num_runs', 
                y_col='repetition',
                value_col='metrics.core_percentage',
                title=f'{network}: Core Percentage (%) by num_runs and repetitions',
                filename=plot_filename,
                cmap='plasma',
                fmt='.1f'
            )
            
            # Core density heatmap
            plot_filename = os.path.join(results_dir, f'be_stability_{network.replace(" ", "_")}_core_density.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.num_runs', 
                y_col='repetition',
                value_col='metrics.core_density',
                title=f'{network}: Core Density by num_runs and repetitions',
                filename=plot_filename,
                cmap='Reds',
                fmt='.2f'
            )
            
            # Periphery density heatmap
            plot_filename = os.path.join(results_dir, f'be_stability_{network.replace(" ", "_")}_periphery_density.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.num_runs', 
                y_col='repetition',
                value_col='metrics.periphery_density',
                title=f'{network}: Periphery Density by num_runs and repetitions',
                filename=plot_filename,
                cmap='Blues',
                fmt='.2f'
            )
            
            # Core-Periphery ratio heatmap
            plot_filename = os.path.join(results_dir, f'be_stability_{network.replace(" ", "_")}_cp_ratio.png')
            try:
                plot_stability_heatmap(
                    network_df, 
                    x_col='parameters.num_runs', 
                    y_col='repetition',
                    value_col='metrics.core_periphery_ratio',
                    title=f'{network}: Core-Periphery Ratio by num_runs and repetitions',
                    filename=plot_filename,
                    cmap='RdBu_r',
                    fmt='.1f'
                )
            except Exception as e:
                print(f"Chyba pri vykresľovaní Core-Periphery ratio pre {network}: {e}")
    
    except Exception as e:
        print(f"Chyba pri generovaní heatmáp: {e}")
        traceback.print_exc()
    
    print(f"Analýza BE dokončená. Výsledky sú v adresári '{results_dir}'")

if __name__ == "__main__":
    main()