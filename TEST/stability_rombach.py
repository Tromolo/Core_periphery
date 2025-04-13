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
    else:
        raise ValueError(f"Neznáma sieť: {network_name}")

    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
         print(f"Varovanie: Graf načítaný ako MultiGraph. Konvertujem na jednoduchý Graf.")
         G = nx.Graph(G)
         
    return G

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
            periphery = set(G.nodes())
    elif isinstance(communities, tuple) and len(communities) == 2:
        if isinstance(communities[0], set) and isinstance(communities[1], set):
            core, periphery = communities
        else:
             periphery = set(G.nodes())
    else:
        periphery = set(G.nodes())

    if G and not core.isdisjoint(periphery):
         periphery = set(G.nodes()) - core
    elif G and core.union(periphery) != set(G.nodes()):
        all_nodes = set(G.nodes())
        identified_nodes = core.union(periphery)
        missing_nodes = all_nodes - identified_nodes
        periphery.update(missing_nodes)

    core_size = len(core)
    periphery_size = len(periphery)
    total_nodes = G.number_of_nodes() if G else 0


    core_percentage = (core_size / total_nodes) * 100 if total_nodes > 0 else 0

    obs_core_core = 0
    obs_core_periphery = 0
    obs_periphery_periphery = 0
    if G:
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

    return {
        'core_size': core_size,
        'periphery_size': periphery_size,
        'core_percentage': core_percentage,
        'pattern_match': ideal_pattern_match
    }


def run_rombach_algorithm(G, network_name, alpha, beta, num_runs, repetitions=1):
    """Spustí Rombach algoritmus pre dané parametre a vypočíta metriky."""
    results = []
    try:
        rombach_algorithm = get_algorithm_function("Rombach")
    except ValueError as e:
        print(f"Chyba pri získavaní Rombach algoritmu: {e}")
        return results

    for rep in range(repetitions):
        start_time = time.time()

        seed = 42 + rep + int(alpha * 100) + int(beta * 1000) + num_runs
        random.seed(seed)
        np.random.seed(seed)

        try:
            classifications, coreness_scores, algo_stats = rombach_algorithm(G, alpha=alpha, beta=beta, num_runs=num_runs)

            end_time = time.time()
            runtime = end_time - start_time

            core_stats = calculate_core_stats(G, classifications)

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
                'metrics.core_percentage': core_stats['core_percentage']
            })

        except Exception as e:
            print(f"Chyba pri spustení Rombach algoritmu (a={alpha:.2f}, b={beta:.2f}, runs={num_runs}, rep={rep}): {e}")

    return results

def plot_heatmap(data, value_col, title, filename, cmap="viridis", fmt=".1f"):
    """Vykreslí heatmapu pre dané dáta."""
    if data.empty:
        print(f"Chýbajú dáta pre heatmapu: {filename}")
        return
    try:
        pivot_table = data.pivot_table(index='parameters.beta', columns='parameters.alpha', values=value_col)
        pivot_table = pivot_table.sort_index(ascending=False)

        plt.figure(figsize=(10, 8))
        sns.heatmap(pivot_table, annot=True, fmt=fmt, cmap=cmap, linewidths=.5)
        plt.title(title, fontsize=14)
        plt.xlabel('Parameter Alpha', fontsize=12)
        plt.ylabel('Parameter Beta', fontsize=12)
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"Heatmapa uložená do '{filename}'")
        plt.close()
    except Exception as e:
        print(f"Chyba pri vytváraní heatmapy '{filename}': {e}")
        traceback.print_exc()

def plot_combined_heatmaps(results_df, value_col, title_suffix, filename_suffix, cmap="viridis", fmt=".1f"):
    """Vykreslí kombinovanú heatmapu pre obe siete vedľa seba."""
    networks = results_df['network'].unique()
    if len(networks) != 2:
        print(f"Očakávali sa dáta pre 2 siete, nájdené: {len(networks)}. Heatmapa sa negeneruje.")
        return

    network1, network2 = networks[0], networks[1]
    df1 = results_df[results_df['network'] == network1]
    df2 = results_df[results_df['network'] == network2]

    agg1 = df1.groupby(['parameters.alpha', 'parameters.beta']).agg(
        avg_val=(value_col, 'mean')
    ).reset_index()
    agg2 = df2.groupby(['parameters.alpha', 'parameters.beta']).agg(
        avg_val=(value_col, 'mean')
    ).reset_index()

    try:
        pivot1 = agg1.pivot_table(index='parameters.beta', columns='parameters.alpha', values='avg_val').sort_index(ascending=False)
        pivot2 = agg2.pivot_table(index='parameters.beta', columns='parameters.alpha', values='avg_val').sort_index(ascending=False)
    except Exception as e:
        print(f"Chyba pri vytváraní pivot tables pre {filename_suffix}: {e}")
        return

    vmin = min(pivot1.min().min(), pivot2.min().min()) if not pivot1.empty and not pivot2.empty else 0
    vmax = max(pivot1.max().max(), pivot2.max().max()) if not pivot1.empty and not pivot2.empty else 100

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    fig.suptitle(f'Priemerný {title_suffix} vs Alpha, Beta (Rombach)', fontsize=16)

    sns.heatmap(pivot1, annot=True, fmt=fmt, cmap=cmap, linewidths=.5, ax=axes[0], vmin=vmin, vmax=vmax, cbar=False)
    axes[0].set_title(f'{network1}', fontsize=14)
    axes[0].set_xlabel('Parameter Alpha', fontsize=12)
    axes[0].set_ylabel('Parameter Beta', fontsize=12)

    sns.heatmap(pivot2, annot=True, fmt=fmt, cmap=cmap, linewidths=.5, ax=axes[1], vmin=vmin, vmax=vmax, cbar=True)
    axes[1].set_title(f'{network2}', fontsize=14)
    axes[1].set_xlabel('Parameter Alpha', fontsize=12)
    axes[1].set_ylabel('')

    plt.tight_layout(rect=[0, 0, 1, 0.96]) 
    plot_filename = os.path.join(results_dir, f'rombach_heatmap_{filename_suffix}_combined.png')
    try:
        plt.savefig(plot_filename, dpi=300)
        print(f"Kombinovaná heatmapa uložená do '{plot_filename}'")
    except Exception as e:
        print(f"Chyba pri ukladaní kombinovanej heatmapy '{plot_filename}': {e}")
    plt.close(fig)

def main():
    networks = [
        # Malé siete
        'Karate Club', 'Dolphins',
        # Stredné siete
        'Les Miserables', 'Football',
        # Veľké siete
        'Facebook Combined', 'Power Grid',
        # Syntetické siete
        'Bianconi-0.7', 'Bianconi-0.97'
    ]

    alpha_values = np.round(np.linspace(0.1, 0.9, 5), 2)
    beta_values = np.round(np.linspace(0.1, 0.9, 5), 2)
    num_runs_values = [5, 10, 20]

    repetitions = 1

    all_results = []

    total_runs = len(networks) * len(alpha_values) * len(beta_values) * len(num_runs_values) * repetitions
    current_run = 0
    print(f"Celkový počet behov algoritmu: {total_runs}")

    for network_name in networks:
        try:
            G = load_network(network_name)
            print(f"Sieť {network_name}: {G.number_of_nodes()} uzlov, {G.number_of_edges()} hrán")
            print(f"Spúšťam Rombach pre {len(alpha_values)} alpha x {len(beta_values)} beta x {len(num_runs_values)} num_runs ...")

            for alpha in alpha_values:
                for beta in beta_values:
                    for num_runs in num_runs_values:
                        current_run += repetitions 
                        print(f"  Beh {current_run}/{total_runs}: alpha={alpha:.2f}, beta={beta:.2f}, num_runs={num_runs} ...", end='\r')
                        results = run_rombach_algorithm(G, network_name, alpha, beta, num_runs, repetitions)
                        all_results.extend(results)
            print(f"\nDokončené pre sieť {network_name}.")

        except Exception as e:
            print(f"\nChyba pri spracovaní siete {network_name}: {e}")
            traceback.print_exc()

    if not all_results:
        print("Žiadne výsledky neboli získané!")
        return

    results_df = pd.DataFrame(all_results)

    csv_file = os.path.join(results_dir, 'rombach_stability_results.csv')
    try:
        results_df.to_csv(csv_file, index=False)
        print(f"Výsledky boli uložené do súboru '{csv_file}'")
    except Exception as e:
        print(f"Chyba pri ukladaní CSV súboru '{csv_file}': {e}")

    print("\n--- Vykresľovanie kombinovaných heatmap ---")

    plot_combined_heatmaps(results_df,
                           value_col='metrics.ideal_pattern_match',
                           title_suffix='Pattern Match (%)',
                           filename_suffix='pattern_match',
                           cmap='viridis',
                           fmt='.1f')

    plot_combined_heatmaps(results_df,
                           value_col='metrics.core_percentage',
                           title_suffix='Veľkosť Jadra (%)',
                           filename_suffix='core_size',
                           cmap='plasma',
                           fmt='.1f')

    print(f"\nAnalýza Rombach dokončená. Výsledky sú v adresári '{results_dir}'")

if __name__ == "__main__":
    main()
