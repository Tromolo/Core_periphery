import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import traceback

project_path = '/home/hruby/PycharmProjects/Core_periphery'
if project_path not in sys.path:
    sys.path.append(project_path)

results_dir = os.path.join(project_path, "results")
centrality_dir = os.path.join(results_dir, "node_centralities")
optimal_cores_dir = os.path.join(results_dir, "optimal_cores")
res_dirs = os.path.join(project_path, "TEST/results")
props_csv_path = "network_properties_summary.csv" 
img_dir = os.path.join(project_path, "img")
os.makedirs(img_dir, exist_ok=True) 

be_csv_path = os.path.join(res_dirs+"/stability_be", "be_stability_results.csv")
rombach_csv_path = os.path.join(res_dirs+"/stability_rombach", "rombach_stability_results.csv")
cucuringu_csv_path = os.path.join(res_dirs+"/stability_cucuringu", "cucuringu_stability_results.csv")

print("Spúšťam generovanie analytických grafov...")

try:
    props_df = pd.read_csv(props_csv_path)
    be_results = pd.read_csv(be_csv_path)
    rombach_results = pd.read_csv(rombach_csv_path)
    cucuringu_results = pd.read_csv(cucuringu_csv_path)
except FileNotFoundError as e:
    print(f"\nCHYBA: Nepodarilo sa nájsť jeden zo vstupných súborov: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nCHYBA pri načítavaní CSV súborov: {e}")
    sys.exit(1)

be_results.rename(columns={'network': 'Network'}, inplace=True) 
rombach_results.rename(columns={'network': 'Network'}, inplace=True) 
cucuringu_results.rename(columns={'network': 'Network'}, inplace=True) 

be_optimal_params = {
    "Karate Club": {"num_runs": 20}, "Dolphins": {"num_runs": 20},
    "Les Miserables": {"num_runs": 20}, "Football": {"num_runs": 20}
}
rombach_optimal_params = {
    "Karate Club": {"alpha": 0.5, "beta": 0.7, "num_runs": 10},
    "Dolphins": {"alpha": 0.5, "beta": 0.7, "num_runs": 10},
    "Les Miserables": {"alpha": 0.5, "beta": 0.7, "num_runs": 10},
    "Football": {"alpha": 0.5, "beta": 0.7, "num_runs": 10},
    "Facebook Combined": {"alpha": 0.5, "beta": 0.7, "num_runs": 5},
    "Power Grid": {"alpha": 0.7, "beta": 0.7, "num_runs": 10},
    "Bianconi-0.7": {"alpha": 0.5, "beta": 0.7, "num_runs": 10},
    "Bianconi-0.97": {"alpha": 0.5, "beta": 0.7, "num_runs": 10}
}
cucuringu_optimal_params = {network: {"beta": 0.1} for network in props_df['Network']}

def get_optimal_avg(df, network, params, value_col):
    mask = pd.Series(True, index=df.index)
    mask &= (df['Network'] == network)
    param_col_map = {'num_runs': 'parameters.num_runs', 'alpha': 'parameters.alpha', 'beta': 'parameters.beta'}
    for key, val in params.items():
         param_col = None
         if key in param_col_map and param_col_map[key] in df.columns: param_col = param_col_map[key]
         elif key in df.columns: param_col = key
         if param_col: mask &= (df[param_col] == val)
    filtered = df[mask]
    if not filtered.empty and value_col in filtered.columns: return filtered[value_col].mean()
    return np.nan

optimal_results = []
for network in props_df['Network']:
    res = {"Network": network}
    if network in be_optimal_params:
        res['BE_PatternMatch'] = get_optimal_avg(be_results, network, be_optimal_params[network], 'metrics.ideal_pattern_match')
    else: res['BE_PatternMatch'] = np.nan
    if network in rombach_optimal_params:
        res['Rombach_PatternMatch'] = get_optimal_avg(rombach_results, network, rombach_optimal_params[network], 'metrics.ideal_pattern_match')
    else: res['Rombach_PatternMatch'] = np.nan
    if network in cucuringu_optimal_params:
         res['Cucuringu_PatternMatch'] = get_optimal_avg(cucuringu_results, network, cucuringu_optimal_params[network], 'metrics.ideal_pattern_match')
    else: res['Cucuringu_PatternMatch'] = np.nan
    optimal_results.append(res)
optimal_df = pd.DataFrame(optimal_results)

merged_df = pd.merge(props_df, optimal_df, on="Network", how="left")

plot_data_long = merged_df.melt(
    id_vars=['Network', 'Nodes (N)', 'Edges (E)', 'Density', 'Modularity'], 
    value_vars=['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch'],
    var_name='Algorithm', 
    value_name='Pattern Match (%)'
)
plot_data_long['Algorithm'] = plot_data_long['Algorithm'].str.replace('_PatternMatch', '')
plot_data_long.dropna(subset=['Pattern Match (%)'], inplace=True) 

print("\nPripravené dáta pre grafy (ukážka):")
print(plot_data_long.head())

plt.figure(figsize=(10, 6))
sns.scatterplot(data=plot_data_long, x='Nodes (N)', y='Pattern Match (%)', hue='Algorithm', style='Algorithm', s=100)
plt.xscale('log') 
plt.title('Vplyv veľkosti siete (N) na Pattern Match (optimálne parametre)')
plt.xlabel('Počet uzlov (N) - log scale')
plt.ylabel('Pattern Match (%)')
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend(title='Algoritmus')
plt.tight_layout()
try:
    plt.savefig(os.path.join(img_dir, 'size_vs_pattern_match.png'), dpi=300)
    print(f"Graf 'size_vs_pattern_match.png' uložený do {img_dir}")
except Exception as e: print(f"Chyba pri ukladaní grafu 1: {e}")
plt.close()

plt.figure(figsize=(10, 6))
plot_data_density = plot_data_long[plot_data_long['Density'] > 0]
sns.scatterplot(data=plot_data_density, x='Density', y='Pattern Match (%)', hue='Algorithm', style='Algorithm', s=100)
plt.xscale('log') 
plt.title('Vplyv hustoty siete na Pattern Match (optimálne parametre)')
plt.xlabel('Hustota siete - log scale')
plt.ylabel('Pattern Match (%)')
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend(title='Algoritmus')
plt.tight_layout()
try:
    plt.savefig(os.path.join(img_dir, 'density_vs_pattern_match.png'), dpi=300)
    print(f"Graf 'density_vs_pattern_match.png' uložený do {img_dir}")
except Exception as e: print(f"Chyba pri ukladaní grafu 2: {e}")
plt.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=plot_data_long, x='Modularity', y='Pattern Match (%)', hue='Algorithm', style='Algorithm', s=100)
sns.regplot(data=plot_data_long[plot_data_long['Algorithm'] == 'BE'], x='Modularity', y='Pattern Match (%)', scatter=False, color='blue', ci=None, line_kws={'ls':'--'})
sns.regplot(data=plot_data_long[plot_data_long['Algorithm'] == 'Rombach'], x='Modularity', y='Pattern Match (%)', scatter=False, color='orange', ci=None, line_kws={'ls':'--'})
sns.regplot(data=plot_data_long[plot_data_long['Algorithm'] == 'Cucuringu'], x='Modularity', y='Pattern Match (%)', scatter=False, color='green', ci=None, line_kws={'ls':'--'})

plt.title('Vzťah modularity a Pattern Match (optimálne parametre)')
plt.xlabel('Modularita (Louvain)')
plt.ylabel('Pattern Match (%)')
plt.grid(True, which="both", ls="--", alpha=0.6)
plt.legend(title='Algoritmus')
plt.tight_layout()
try:
    plt.savefig(os.path.join(img_dir, 'modularity_vs_pattern_match.png'), dpi=300)
    print(f"Graf 'modularity_vs_pattern_match.png' uložený do {img_dir}")
except Exception as e: print(f"Chyba pri ukladaní grafu 3: {e}")
plt.close()

target_network = 'Karate Club'
target_algorithm = 'Rombach' 
print(f"\nGenerujem graf distribúcie centralít pre {target_network} / {target_algorithm}...")

safe_network_name = target_network.replace(" ", "_").replace("-","_").lower()
centrality_file = os.path.join(centrality_dir, f"{safe_network_name}_centralities.csv")
core_file = os.path.join(optimal_cores_dir, f"{target_algorithm.lower()}_optimal_cores.csv")

try:
    centrality_df = pd.read_csv(centrality_file)
    centrality_df['node_id'] = centrality_df['node_id'].astype(str)
    
    core_df = pd.read_csv(core_file)
    network_core_data = core_df[core_df['Network'] == target_network]
    
    if network_core_data.empty:
        print(f"Chyba: Nenašli sa core dáta pre {target_network}/{target_algorithm}")
    else:
        core_nodes_str = network_core_data.iloc[0]['Core_Nodes']
        core_nodes = set()
        if pd.notna(core_nodes_str) and core_nodes_str != "ERROR" and core_nodes_str:
            core_nodes = set(core_nodes_str.split(','))
        
        if not core_nodes:
             print(f"Chyba: Prázdny zoznam core uzlov pre {target_network}/{target_algorithm}")
        else:
            centrality_df['Group'] = centrality_df['node_id'].apply(lambda x: 'Core' if x in core_nodes else 'Periphery')
            
            fig, axes = plt.subplots(1, 3, figsize=(18, 5))
            fig.suptitle(f'Distribúcia Centralít ({target_network} / {target_algorithm})', fontsize=16)
            
            centrality_metrics = {
                'degree_centrality': 'Degree Centrality',
                'betweenness_centrality': 'Betweenness Centrality',
                'closeness_centrality': 'Closeness Centrality'
            }
            
            plot_generated = False
            for i, (col, title) in enumerate(centrality_metrics.items()):
                if col in centrality_df.columns and centrality_df[col].notna().any():
                    sns.boxplot(data=centrality_df, x='Group', y=col, ax=axes[i], order=['Core', 'Periphery'], palette='Set2')
                    axes[i].set_title(title)
                    axes[i].set_xlabel('Skupina uzlov')
                    axes[i].set_ylabel('Hodnota centrality')
                    plot_generated = True
                else:
                    axes[i].set_title(f'{title}\n(Dáta chýbajú)')
                    axes[i].axis('off')

            if plot_generated:
                plt.tight_layout(rect=[0, 0, 1, 0.95])
                try:
                    plt.savefig(os.path.join(img_dir, 'centrality_distribution.png'), dpi=300)
                    print(f"Graf 'centrality_distribution.png' uložený do {img_dir}")
                except Exception as e: print(f"Chyba pri ukladaní grafu 4: {e}")
            else:
                print("Graf distribúcie centralít nebol vygenerovaný (chýbajú dáta).")
            plt.close(fig)

except FileNotFoundError:
    print(f"Chyba: Nepodarilo sa nájsť vstupné súbory pre graf 4 ({centrality_file} alebo {core_file}).")
except Exception as e:
    print(f"Chyba pri generovaní grafu 4: {e}")
    traceback.print_exc()


print("\nGenerovanie grafov dokončené.")
