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

try:
    from backend.functions import get_algorithm_function, load_graph_from_path
except ImportError as e:
    print(f"Chyba pri importe funkcií z backend: {e}")
    print("Skontrolujte, či je cesta k projektu správne nastavená v sys.path.")
    sys.exit(1)

results_dir = os.path.join(project_path, 'TEST/results/stability_rombach')
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
    else:
        raise ValueError(f"Neznáma sieť: {network_name}")
    
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
         print(f"Varovanie: Graf načítaný ako MultiGraph. Konvertujem na jednoduchý Graf.")
         G = nx.Graph(G)
         
    return G

def calculate_core_stats(G, coreness_scores):
    """Vypočíta štatistiky jadra na základe výsledkov CP algoritmu."""
    # Sort nodes by coreness score (highest to lowest)
    sorted_nodes = sorted(coreness_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Find natural threshold as the largest gap in scores
    if len(sorted_nodes) <= 1:
        threshold = 0
    else:
        gaps = [sorted_nodes[i-1][1] - sorted_nodes[i][1] for i in range(1, len(sorted_nodes))]
        max_gap_index = gaps.index(max(gaps))
        threshold = (sorted_nodes[max_gap_index][1] + sorted_nodes[max_gap_index+1][1]) / 2
    
    # Identify core and periphery nodes
    core = set()
    periphery = set()
    
    for node, score in coreness_scores.items():
        if score > threshold:
            core.add(node)
        else:
            periphery.add(node)
    
    core_size = len(core)
    periphery_size = len(periphery)
    total_nodes = G.number_of_nodes()
    
    core_percentage = (core_size / total_nodes) * 100 if total_nodes > 0 else 0
    
    # Count edges between different node types
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
    
    # Calculate maximum possible edges for density calculations
    max_core_core = core_size * (core_size - 1) / 2 if core_size > 1 else 0
    max_core_periphery = core_size * periphery_size
    max_periphery_periphery = periphery_size * (periphery_size - 1) / 2 if periphery_size > 1 else 0
    
    # Calculate densities
    core_density = obs_core_core / max_core_core if max_core_core > 0 else 0
    periphery_density = obs_periphery_periphery / max_periphery_periphery if max_periphery_periphery > 0 else 0
    core_periphery_ratio = core_density / periphery_density if periphery_density > 0 else float('inf')
    
    # Calculate pattern match
    correct_core_core = obs_core_core
    correct_core_periphery = obs_core_periphery  # In ideal CP model, all possible core-periphery edges exist
    correct_periphery_periphery = max_periphery_periphery - obs_periphery_periphery  # In ideal model, no periphery-periphery edges
    
    total_correct = correct_core_core + correct_core_periphery + correct_periphery_periphery
    total_possible = max_core_core + max_core_periphery + max_periphery_periphery
    
    pattern_match = (total_correct / total_possible * 100) if total_possible > 0 else 0
    
    return {
        'core_size': core_size,
        'periphery_size': periphery_size,
        'core_percentage': core_percentage,
        'pattern_match': pattern_match,
        'core_density': core_density,
        'periphery_density': periphery_density,
        'core_periphery_ratio': core_periphery_ratio
    }

def run_rombach_algorithm(G, network_name, alpha, beta, num_runs, repetitions):
    """Spustí Rombach algoritmus."""
    results = []
    
    # Získame funkciu algoritmu zo slovníka algoritmov
    rombach_algorithm = get_algorithm_function('rombach')
    
    for rep in range(1, repetitions + 1):
        start_time = time.time()
        
        # Nastavenie seedu pre reprodukovateľnosť
        np.random.seed(42 + rep)
        random.seed(42 + rep)
        
        try:
            classifications, coreness_scores, algo_stats = rombach_algorithm(G, alpha=alpha, beta=beta, num_runs=num_runs)
            
            end_time = time.time()
            runtime = end_time - start_time
            
            # Výpočet core stats
            core_stats = calculate_core_stats(G, coreness_scores)
            
            results.append({
                'network': network_name,
                'algorithm': 'Rombach',
                'parameters.alpha': alpha,
                'parameters.beta': beta,
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
            
            print(f"Sieť: {network_name}, alpha: {alpha:.2f}, beta: {beta:.2f}, num_runs: {num_runs}, rep: {rep}, pattern_match: {core_stats['pattern_match']:.2f}%, core_size: {core_stats['core_size']}, core_percentage: {core_stats['core_percentage']:.2f}%")

        except Exception as e:
            print(f"Chyba pri spustení Rombach algoritmu (alpha={alpha}, beta={beta}, rep {rep}): {e}")
            traceback.print_exc()
    
    return results

def append_to_csv(results, csv_path):
    """Pridá výsledky do CSV súboru."""
    df = pd.DataFrame(results)
    
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
        print(f"Results appended to {csv_path}")
    else:
        df.to_csv(csv_path, index=False)
        print(f"New results file created at {csv_path}")

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
    
    # Parameter values for Rombach algorithm
    alpha_values = np.round(np.linspace(0.1, 0.9, 5), 2)  # 0.1, 0.3, 0.5, 0.7, 0.9
    beta_values = np.round(np.linspace(0.1, 0.9, 5), 2)   # 0.1, 0.3, 0.5, 0.7, 0.9
    
    # Rôzne počty behov pre malé a veľké siete
    small_num_runs_values = [5, 10, 20]  # Pre malé siete
    large_num_runs_values = [5, 10,20]      # Pre veľké siete
    
    # Use different repetition counts based on network size
    small_repetitions = 1  # Rombach už má repetitions v alpha a beta
    large_repetitions = 1
    
    csv_file = os.path.join(results_dir, 'rombach_stability_results.csv')
    
    # Najprv spracuj malé siete a prepíš pôvodný súbor
    print("=== SPRACOVANIE MALÝCH SIETÍ ===")
    small_results = []
    total_small_runs = len(small_networks) * len(alpha_values) * len(beta_values) * len(small_num_runs_values) * small_repetitions
    current_run = 0
    
    for network_name in small_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            print(f"Spúšťam Rombach pre {len(alpha_values)} alpha x {len(beta_values)} beta x {len(small_num_runs_values)} num_runs ...")
            
            for alpha in alpha_values:
                for beta in beta_values:
                    for num_runs in small_num_runs_values:
                        print(f"  alpha={alpha:.2f}, beta={beta:.2f}, num_runs={num_runs} ...")
                        results = run_rombach_algorithm(G, network_name, alpha, beta, num_runs, small_repetitions)
                        small_results.extend(results)
                        current_run += len(results)
                        print(f"Pokrok malých sietí: {current_run}/{total_small_runs} behov ({(current_run/total_small_runs)*100:.1f}%)")
            
            print(f"\nDokončené pre sieť {network_name}.")
                
        except Exception as e:
            print(f"\nChyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()
    
    # Zapíš malé siete (prepíše súbor)
    if small_results:
        results_df = pd.DataFrame(small_results)
        results_df.to_csv(csv_file, index=False)
        print(f"Výsledky malých sietí boli uložené do súboru '{csv_file}'")
    
    # Potom spracuj veľké siete a appenduj k existujúcemu súboru
    print("\n=== SPRACOVANIE VEĽKÝCH SIETÍ ===")
    large_results = []
    total_large_runs = len(large_networks) * len(alpha_values) * len(beta_values) * len(large_num_runs_values) * large_repetitions
    current_run = 0
    
    for network_name in large_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            print(f"Spúšťam Rombach pre {len(alpha_values)} alpha x {len(beta_values)} beta x {len(large_num_runs_values)} num_runs ...")
            
            for alpha in alpha_values:
                for beta in beta_values:
                    for num_runs in large_num_runs_values:
                        print(f"  alpha={alpha:.2f}, beta={beta:.2f}, num_runs={num_runs} ...")
                        results = run_rombach_algorithm(G, network_name, alpha, beta, num_runs, large_repetitions)
                        large_results.extend(results)
                        current_run += len(results)
                        print(f"Pokrok veľkých sietí: {current_run}/{total_large_runs} behov ({(current_run/total_large_runs)*100:.1f}%)")
                        
                        # Priebežne zapisuj výsledky veľkých sietí (pridaj ich k existujúcemu súboru)
                        if results:
                            results_df = pd.DataFrame(results)
                            results_df.to_csv(csv_file, mode='a', header=False, index=False)
                            print(f"Výsledky pre {network_name} s alpha={alpha:.2f}, beta={beta:.2f}, num_runs={num_runs} boli pridané do súboru '{csv_file}'")
        
            print(f"\nDokončené pre sieť {network_name}.")
                
        except Exception as e:
            print(f"\nChyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()
    
    # Načítaj kompletné výsledky pre generovanie heatmáp
    print("\n=== GENEROVANIE HEATMÁP ===")
    try:
        complete_results_df = pd.read_csv(csv_file)
        
        # Generate plots for each network and combination of alpha/beta
        all_networks = small_networks + large_networks
        for network in all_networks:
            network_df = complete_results_df[complete_results_df['network'] == network]
            
            if network_df.empty:
                print(f"Žiadne dáta pre sieť {network}")
                continue
            
            print(f"Vykresľujem grafy pre sieť {network}")
            
            # For each alpha value, create a heatmap of beta vs num_runs
            for alpha in alpha_values:
                alpha_df = network_df[network_df['parameters.alpha'] == alpha]
                
                if alpha_df.empty:
                    print(f"  Žiadne dáta pre alpha={alpha:.2f}")
                    continue
                
                # Pattern match stability by beta and num_runs
                plot_filename = os.path.join(results_dir, f'rombach_stability_{network.replace(" ", "_")}_alpha{alpha:.1f}_pattern_match.png')
                try:
                    plot_stability_heatmap(
                        alpha_df, 
                        x_col='parameters.beta', 
                        y_col='parameters.num_runs',
                        value_col='metrics.ideal_pattern_match',
                        title=f'{network}: Pattern Match (%) for α={alpha:.1f}',
                        filename=plot_filename,
                        cmap='viridis',
                        fmt='.1f'
                    )
                except Exception as e:
                    print(f"  Chyba pri vytváraní pattern match heatmapy pre α={alpha:.1f}: {e}")
                
                # Core percentage stability
                plot_filename = os.path.join(results_dir, f'rombach_stability_{network.replace(" ", "_")}_alpha{alpha:.1f}_core_percentage.png')
                try:
                    plot_stability_heatmap(
                        alpha_df, 
                        x_col='parameters.beta', 
                        y_col='parameters.num_runs',
                        value_col='metrics.core_percentage',
                        title=f'{network}: Core Percentage (%) for α={alpha:.1f}',
                        filename=plot_filename,
                        cmap='plasma',
                        fmt='.1f'
                    )
                except Exception as e:
                    print(f"  Chyba pri vytváraní core percentage heatmapy pre α={alpha:.1f}: {e}")
                
                # Core density heatmap
                plot_filename = os.path.join(results_dir, f'rombach_stability_{network.replace(" ", "_")}_alpha{alpha:.1f}_core_density.png')
                try:
                    plot_stability_heatmap(
                        alpha_df, 
                        x_col='parameters.beta', 
                        y_col='parameters.num_runs',
                        value_col='metrics.core_density',
                        title=f'{network}: Core Density for α={alpha:.1f}',
                        filename=plot_filename,
                        cmap='Reds',
                        fmt='.2f'
                    )
                except Exception as e:
                    print(f"  Chyba pri vytváraní core density heatmapy pre α={alpha:.1f}: {e}")
                
                # Periphery density heatmap
                plot_filename = os.path.join(results_dir, f'rombach_stability_{network.replace(" ", "_")}_alpha{alpha:.1f}_periphery_density.png')
                try:
                    plot_stability_heatmap(
                        alpha_df, 
                        x_col='parameters.beta', 
                        y_col='parameters.num_runs',
                        value_col='metrics.periphery_density',
                        title=f'{network}: Periphery Density for α={alpha:.1f}',
                        filename=plot_filename,
                        cmap='Blues',
                        fmt='.2f'
                    )
                except Exception as e:
                    print(f"  Chyba pri vytváraní periphery density heatmapy pre α={alpha:.1f}: {e}")
                
                # Core-Periphery ratio heatmap
                plot_filename = os.path.join(results_dir, f'rombach_stability_{network.replace(" ", "_")}_alpha{alpha:.1f}_cp_ratio.png')
                try:
                    plot_stability_heatmap(
                        alpha_df, 
                        x_col='parameters.beta', 
                        y_col='parameters.num_runs',
                        value_col='metrics.core_periphery_ratio',
                        title=f'{network}: Core-Periphery Ratio for α={alpha:.1f}',
                        filename=plot_filename,
                        cmap='RdBu_r',
                        fmt='.1f'
                    )
                except Exception as e:
                    print(f"  Chyba pri vytváraní Core-Periphery ratio heatmapy pre α={alpha:.1f}: {e}")
    
    except Exception as e:
        print(f"Chyba pri generovaní heatmáp: {e}")
        traceback.print_exc()
    
    print(f"Analýza Rombach dokončená. Výsledky sú v adresári '{results_dir}'")

if __name__ == "__main__":
    main()
