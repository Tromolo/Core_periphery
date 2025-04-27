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


results_dir = os.path.join(project_path, 'TEST/results/stability_cucuringu')
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

def plot_stability_heatmap(df, x_col, y_col, value_col, title, filename, cmap='viridis', fmt='.1f'):
    """Vytvorí heat map z údajov dataframe. Hodnota x_col je na x-osi, y_col na y-osi a value_col je hodnota."""
    try:
        # Vytvor pivot table pre heatmap
        pivot_df = df.pivot_table(index=y_col, columns=x_col, values=value_col, aggfunc='mean')
        
        plt.figure(figsize=(10, 6))
        ax = sns.heatmap(pivot_df, annot=True, fmt=fmt, cmap=cmap, linewidths=.5, cbar_kws={'label': value_col})
        
        plt.title(title, fontsize=14)
        plt.tight_layout()
        
        # Uloženie obrázka
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Heatmap uložená do {filename}")
        plt.close()
        
    except Exception as e:
        print(f"Chyba pri vytváraní heatmap: {e}")
        traceback.print_exc()

def calculate_core_stats(G, communities):
    """Vypočíta základné štatistiky a Ideal Pattern Match pre danú klasifikáciu."""
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
            print(f"Varovanie: Neočakávaný typ hodnôt v slovníku klasifikácie: {type(sample_value)}. Predpokladám všetky uzly ako perifériu.")
            periphery = set(G.nodes())

    elif isinstance(communities, tuple) and len(communities) == 2:
        if isinstance(communities[0], set) and isinstance(communities[1], set):
            core, periphery = communities
        else:
             print(f"Varovanie: Očakával sa tuple setov, ale prišlo ({type(communities[0])}, {type(communities[1])}). Predpokladám všetky uzly ako perifériu.")
             periphery = set(G.nodes())
    else:
        print(f"Varovanie: Nerozpoznaný formát klasifikácie: {type(communities)}. Predpokladám všetky uzly ako perifériu.")
        periphery = set(G.nodes())

    if not core.isdisjoint(periphery):
         print("Varovanie: Množiny core a periphery nie sú disjunktné. Prepočítavam perifériu.")
         periphery = set(G.nodes()) - core
    elif core.union(periphery) != set(G.nodes()):
        print("Varovanie: Množiny core a periphery nepokrývajú všetky uzly. Upravujem množiny.")
        all_nodes = set(G.nodes())
        identified_nodes = core.union(periphery)
        missing_nodes = all_nodes - identified_nodes
        periphery.update(missing_nodes)
        print(f"Pridaných {len(missing_nodes)} chýbajúcich uzlov do periférie.")

    core_size = len(core)
    periphery_size = len(periphery)
    total_nodes = G.number_of_nodes()

    print(f"Výpočet metrík: {core_size} core uzlov, {periphery_size} periphery uzlov, {total_nodes} celkovo uzlov")

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

    # Výpočet Ideal Pattern Match
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

def run_cucuringu_algorithm(G, network_name, beta, repetitions=1):
    """Spustí Cucuringu algoritmus a vypočíta metriky."""

    results = []
    cucuringu_algorithm = get_algorithm_function("Cucuringu")

    for rep in range(repetitions):
        start_time = time.time()

        random.seed(42 + rep)
        np.random.seed(42 + rep)

        try:
            classifications, coreness_scores, algo_stats = cucuringu_algorithm(G, beta=beta)

            end_time = time.time()
            runtime = end_time - start_time

            core_stats = calculate_core_stats(G, classifications)

            results.append({
                'network': network_name,
                'algorithm': 'Cucuringu',
                'parameters.beta': beta,
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

            print(f"Sieť: {network_name}, beta: {beta:.2f}, rep: {rep}, "
                  f"pattern_match: {core_stats['pattern_match']:.2f}%, "
                  f"core_size: {core_stats['core_size']}, "
                  f"core_percentage: {core_stats['core_percentage']:.2f}%")

        except Exception as e:
            print(f"Chyba pri spustení Cucuringu algoritmu (beta {beta:.2f}, rep {rep}): {e}")
            traceback.print_exc()

    return results

def main():
    # All networks
    small_networks = [
        'Karate Club', 'Dolphins', 'Les Miserables', 'Football'
    ]
    
    large_networks = [
        'Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97', 'YeastL'
    ]
    
    # Rôzne hodnoty beta pre malé a veľké siete
    small_beta_values = np.round(np.linspace(0.1, 0.9, 9), 2) 
    large_beta_values = np.round(np.linspace(0.1, 0.9, 9), 2)
    
    # Počet opakovaní
    small_repetitions = 1
    large_repetitions = 1
    
    csv_file = os.path.join(results_dir, 'cucuringu_stability_results.csv')
    
    # Najprv spracuj malé siete a prepíš pôvodný súbor
    print("=== SPRACOVANIE MALÝCH SIETÍ ===")
    small_results = []
    total_small_runs = len(small_networks) * len(small_beta_values) * small_repetitions
    current_run = 0
    
    for network_name in small_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            
            for beta in small_beta_values:
                print(f"Spúšťam Cucuringu algoritmus s beta={beta:.2f}, repetitions={small_repetitions} ...")
                results = run_cucuringu_algorithm(G, network_name, beta, small_repetitions)
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
    total_large_runs = len(large_networks) * len(large_beta_values) * large_repetitions
    current_run = 0
    
    for network_name in large_networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name} načítaná: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            
            for beta in large_beta_values:
                print(f"Spúšťam Cucuringu algoritmus s beta={beta:.2f}, repetitions={large_repetitions} ...")
                results = run_cucuringu_algorithm(G, network_name, beta, large_repetitions)
                large_results.extend(results)
                current_run += len(results)
                print(f"Pokrok veľkých sietí: {current_run}/{total_large_runs} behov ({(current_run/total_large_runs)*100:.1f}%)")
                
                # Priebežne zapisuj výsledky veľkých sietí (pridaj ich k existujúcemu súboru)
                if results:
                    results_df = pd.DataFrame(results)
                    results_df.to_csv(csv_file, mode='a', header=False, index=False)
                    print(f"Výsledky pre {network_name} s beta={beta:.2f} boli pridané do súboru '{csv_file}'")
                
        except Exception as e:
            print(f"Chyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()
    
    # Načítaj kompletné výsledky pre generovanie heatmáp
    print("\n=== GENEROVANIE HEATMÁP A GRAFOV ===")
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
            
            # Pattern match stability by beta
            plot_filename = os.path.join(results_dir, f'cucuringu_stability_{network.replace(" ", "_")}_pattern_match.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.beta', 
                y_col='repetition',
                value_col='metrics.ideal_pattern_match',
                title=f'{network}: Ideal Pattern Match (%) by beta',
                filename=plot_filename,
                cmap='viridis',
                fmt='.1f'
            )
            
            # Core size stability by beta
            plot_filename = os.path.join(results_dir, f'cucuringu_stability_{network.replace(" ", "_")}_core_percentage.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.beta', 
                y_col='repetition',
                value_col='metrics.core_percentage',
                title=f'{network}: Core Percentage (%) by beta',
                filename=plot_filename,
                cmap='plasma',
                fmt='.1f'
            )
            
            # Core density heatmap
            plot_filename = os.path.join(results_dir, f'cucuringu_stability_{network.replace(" ", "_")}_core_density.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.beta', 
                y_col='repetition',
                value_col='metrics.core_density',
                title=f'{network}: Core Density by beta',
                filename=plot_filename,
                cmap='Reds',
                fmt='.2f'
            )
            
            # Periphery density heatmap
            plot_filename = os.path.join(results_dir, f'cucuringu_stability_{network.replace(" ", "_")}_periphery_density.png')
            plot_stability_heatmap(
                network_df, 
                x_col='parameters.beta', 
                y_col='repetition',
                value_col='metrics.periphery_density',
                title=f'{network}: Periphery Density by beta',
                filename=plot_filename,
                cmap='Blues',
                fmt='.2f'
            )
            
            # Core-Periphery ratio heatmap
            plot_filename = os.path.join(results_dir, f'cucuringu_stability_{network.replace(" ", "_")}_cp_ratio.png')
            try:
                plot_stability_heatmap(
                    network_df, 
                    x_col='parameters.beta', 
                    y_col='repetition',
                    value_col='metrics.core_periphery_ratio',
                    title=f'{network}: Core-Periphery Ratio by beta',
                    filename=plot_filename,
                    cmap='RdBu_r',
                    fmt='.1f'
                )
            except Exception as e:
                print(f"Chyba pri vykresľovaní Core-Periphery ratio pre {network}: {e}")
        
        # Vytvor aj agregované grafy pre všetky siete
        summary = complete_results_df.groupby(['network', 'parameters.beta']).agg(
            mean_pattern_match=('metrics.ideal_pattern_match', 'mean'),
            std_pattern_match=('metrics.ideal_pattern_match', 'std'),
            mean_core_percentage=('metrics.core_percentage', 'mean'),
            std_core_percentage=('metrics.core_percentage', 'std'),
            mean_runtime=('runtime', 'mean'),
            mean_core_density=('metrics.core_density', 'mean'),
            mean_periphery_density=('metrics.periphery_density', 'mean'),
            mean_core_periphery_ratio=('metrics.core_periphery_ratio', 'mean')
        ).reset_index()

        summary.fillna({
            'std_pattern_match': 0, 
            'std_core_percentage': 0,
            'mean_core_periphery_ratio': 0
        }, inplace=True)

        # Farby pre jednotlivé siete
        colors = {
            'Karate Club': '#1f77b4',
            'Dolphins': '#ff7f0e',
            'Les Miserables': '#2ca02c',
            'Football': '#d62728',
            'Facebook Combined': '#9467bd',
            'Power Grid': '#8c564b',
            'Bianconi-0.7': '#e377c2',
            'Bianconi-0.97': '#7f7f7f',
            'YeastL': '#bcbd22'
        }

        # Graf pre Pattern Match
        plt.figure(figsize=(10, 6))
        for network in all_networks:
            network_data = summary[summary['network'] == network]
            if not network_data.empty:
                plt.errorbar(
                    network_data['parameters.beta'],
                    network_data['mean_pattern_match'],
                    yerr=network_data['std_pattern_match'],
                    fmt='o-', linewidth=2, markersize=8, capsize=5,
                    color=colors.get(network, '#000000'), label=network
                )

        plt.title('Vplyv parametra beta na kvalitu detekcie Cucuringu algoritmu', fontsize=14)
        plt.xlabel('Parameter Beta', fontsize=12)
        plt.ylabel('Pattern Match (%)', fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.ylim(0, 105)
        plt.tight_layout()
        plot_file_pm = os.path.join(results_dir, 'cucuringu_pattern_match.png')
        plt.savefig(plot_file_pm, dpi=300)
        print(f"Graf pattern match uložený do '{plot_file_pm}'")
        plt.close()

        # Graf pre Core Percentage
        plt.figure(figsize=(10, 6))
        for network in all_networks:
            network_data = summary[summary['network'] == network]
            if not network_data.empty:
                plt.errorbar(
                    network_data['parameters.beta'],
                    network_data['mean_core_percentage'],
                    yerr=network_data['std_core_percentage'],
                    fmt='s-', linewidth=2, markersize=8, capsize=5,
                    color=colors.get(network, '#000000'), label=network
                )

        plt.title('Vplyv parametra beta na veľkosť jadra Cucuringu algoritmu', fontsize=14)
        plt.xlabel('Parameter Beta', fontsize=12)
        plt.ylabel('Veľkosť jadra (%)', fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.ylim(0, 105)
        plt.tight_layout()
        plot_file_cs = os.path.join(results_dir, 'cucuringu_core_size.png')
        plt.savefig(plot_file_cs, dpi=300)
        print(f"Graf veľkosti jadra uložený do '{plot_file_cs}'")
        plt.close()
        
        # Graf pre Core Density
        plt.figure(figsize=(10, 6))
        for network in all_networks:
            network_data = summary[summary['network'] == network]
            if not network_data.empty:
                plt.plot(
                    network_data['parameters.beta'],
                    network_data['mean_core_density'],
                    'o-', linewidth=2, markersize=8,
                    color=colors.get(network, '#000000'), label=network
                )

        plt.title('Vplyv parametra beta na hustotu jadra Cucuringu algoritmu', fontsize=14)
        plt.xlabel('Parameter Beta', fontsize=12)
        plt.ylabel('Hustota jadra', fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.ylim(0, 1.05)
        plt.tight_layout()
        plot_file_cd = os.path.join(results_dir, 'cucuringu_core_density.png')
        plt.savefig(plot_file_cd, dpi=300)
        print(f"Graf hustoty jadra uložený do '{plot_file_cd}'")
        plt.close()
        
        # Graf pre Periphery Density
        plt.figure(figsize=(10, 6))
        for network in all_networks:
            network_data = summary[summary['network'] == network]
            if not network_data.empty:
                plt.plot(
                    network_data['parameters.beta'],
                    network_data['mean_periphery_density'],
                    's-', linewidth=2, markersize=8,
                    color=colors.get(network, '#000000'), label=network
                )

        plt.title('Vplyv parametra beta na hustotu periférie Cucuringu algoritmu', fontsize=14)
        plt.xlabel('Parameter Beta', fontsize=12)
        plt.ylabel('Hustota periférie', fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.ylim(0, 1.05)
        plt.tight_layout()
        plot_file_pd = os.path.join(results_dir, 'cucuringu_periphery_density.png')
        plt.savefig(plot_file_pd, dpi=300)
        print(f"Graf hustoty periférie uložený do '{plot_file_pd}'")
        plt.close()
    
    except Exception as e:
        print(f"Chyba pri generovaní heatmáp a grafov: {e}")
        traceback.print_exc()
    
    print(f"Analýza Cucuringu dokončená. Výsledky sú v adresári '{results_dir}'")

if __name__ == "__main__":
    main()
