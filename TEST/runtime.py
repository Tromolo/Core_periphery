import pandas as pd
import numpy as np
import os

props_df = pd.read_csv("network_properties_summary.csv")

project_path = "." 
results_dir = os.path.join(project_path, "TEST", "results")

props_csv_path = "network_properties_summary.csv" # Predpokladáme v aktuálnom adresári
be_csv_path = os.path.join(results_dir, "stability_be", "be_stability_results.csv")
rombach_csv_path = os.path.join(results_dir, "stability_rombach", "rombach_stability_results.csv")
cucuringu_csv_path = os.path.join(results_dir, "stability_cucuringu", "cucuringu_stability_results.csv")

print(f"Načítavam vlastnosti siete z: {props_csv_path}")
print(f"Načítavam BE výsledky z: {be_csv_path}")
print(f"Načítavam Rombach výsledky z: {rombach_csv_path}")
print(f"Načítavam Cucuringu výsledky z: {cucuringu_csv_path}")

try:
    props_df = pd.read_csv(props_csv_path)
    be_results = pd.read_csv(be_csv_path)
    rombach_results = pd.read_csv(rombach_csv_path)
    cucuringu_results = pd.read_csv(cucuringu_csv_path)
except FileNotFoundError as e:
    print(f"\nCHYBA: Nepodarilo sa nájsť jeden zo súborov: {e}")
    print("Skontrolujte cesty a umiestnenie súborov.")
    exit()
except Exception as e:
    print(f"\nCHYBA pri načítavaní CSV súborov: {e}")
    exit()
    
# Premenovanie stĺpca pre zlúčenie
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
    query_parts = [f"Network == '{network}'"]
    for key, val in params.items():
        if key == 'num_runs':
            param_col = 'parameters.num_runs'
        elif key == 'beta' and 'parameters.beta' in df.columns:
             param_col = 'parameters.beta'
        elif key == 'alpha' and 'parameters.alpha' in df.columns:
             param_col = 'parameters.alpha'
        else:
             if key == 'beta' and 'parameters.beta' not in df.columns and 'parameters.beta' in df.columns:
                 param_col = 'parameters.beta'
             else:
                 print(f"Warning: Parameter key '{key}' not found directly in columns of dataframe for {network}")
                 continue 
        
        if isinstance(val, (int, float, np.number)):
             query_parts.append(f"`{param_col}` == {val}")
        else:
             query_parts.append(f"`{param_col}` == '{val}'")
             
    query = " & ".join(query_parts)
    
    try:
        filtered = df.query(query)
        if not filtered.empty:
            return filtered[value_col].mean()
        else:
            return np.nan
    except Exception as e:
        return np.nan


optimal_results = []
for network in props_df['Network']:
    res = {"Network": network}
    if network in be_optimal_params:
        res['BE_PatternMatch'] = get_optimal_avg(be_results, network, be_optimal_params[network], 'metrics.ideal_pattern_match')
        res['BE_CorePerc'] = get_optimal_avg(be_results, network, be_optimal_params[network], 'metrics.core_percentage')
    else:
         res['BE_PatternMatch'] = np.nan
         res['BE_CorePerc'] = np.nan
         
    if network in rombach_optimal_params:
        res['Rombach_PatternMatch'] = get_optimal_avg(rombach_results, network, rombach_optimal_params[network], 'metrics.ideal_pattern_match')
        res['Rombach_CorePerc'] = get_optimal_avg(rombach_results, network, rombach_optimal_params[network], 'metrics.core_percentage')
    else:
         res['Rombach_PatternMatch'] = np.nan
         res['Rombach_CorePerc'] = np.nan
         
    if network in cucuringu_optimal_params:
         beta_col_name = 'parameters.beta' 
         res['Cucuringu_PatternMatch'] = get_optimal_avg(cucuringu_results, network, cucuringu_optimal_params[network], 'metrics.ideal_pattern_match')
         res['Cucuringu_CorePerc'] = get_optimal_avg(cucuringu_results, network, cucuringu_optimal_params[network], 'metrics.core_percentage')
    else:
         res['Cucuringu_PatternMatch'] = np.nan
         res['Cucuringu_CorePerc'] = np.nan
         
    optimal_results.append(res)

optimal_df = pd.DataFrame(optimal_results)

merged_df = pd.merge(props_df, optimal_df, on="Network", how="left")

def get_size_category(n):
    if n < 100: return 'Malé'
    if n < 1000: return 'Stredné' 
    return 'Veľké'
merged_df['Size Category'] = merged_df['Nodes (N)'].apply(get_size_category)

density_bins = [0, 0.05, 0.15, 1.0] 
density_labels = ['<0.05 (Riedke)', '0.05-0.15 (Stredné)', '>0.15 (Husté)']
merged_df['Density Category'] = pd.cut(merged_df['Density'], bins=density_bins, labels=density_labels, right=False) # right=False includes lower bound

size_avg_pm = merged_df.groupby('Size Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].mean()
print("\nPriemerný Pattern Match podľa veľkosti siete (optimálne parametre):")
print(size_avg_pm)

density_avg_pm = merged_df.groupby('Density Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].mean()
density_avg_pm_overall = merged_df.groupby('Density Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].mean(numeric_only=True).mean(axis=1)
print("\nPriemerný Pattern Match podľa hustoty siete (optimálne parametre):")
print(density_avg_pm)
print("\nCelkový priemerný Pattern Match podľa hustoty:")
print(density_avg_pm_overall)
density_std_pm = merged_df.groupby('Density Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].std()
print("\nŠtandardná odchýlka Pattern Match podľa hustoty (ako miera citlivosti):")
print(density_std_pm) 

size_density_table = merged_df.groupby('Size Category')[['Nodes (N)', 'Density']].mean()
print("\nPriemerný počet uzlov a hustota podľa veľkosti siete:")
print(size_density_table)

correlations = {}
for algo in ['BE', 'Rombach', 'Cucuringu']:
    pm_col = f'{algo}_PatternMatch'
    valid_data = merged_df[['Modularity', pm_col]].dropna()
    if not valid_data.empty and len(valid_data) > 1:
        correlations[algo] = valid_data['Modularity'].corr(valid_data[pm_col], method='pearson')
    else:
        correlations[algo] = np.nan

print("\nKorelácia (Pearson) medzi Modularitou a Pattern Match:")
print(correlations)

modularity_bins = [0, 0.3, 0.7, 1.0] 
modularity_labels = ['Nízka (<0.3)', 'Stredná (0.3-0.7)', 'Vysoká (>0.7)']
merged_df['Modularity Category'] = pd.cut(merged_df['Modularity'], bins=modularity_bins, labels=modularity_labels, right=False)
modularity_avg_pm = merged_df.groupby('Modularity Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].mean()
modularity_avg_pm_overall = merged_df.groupby('Modularity Category')[['BE_PatternMatch', 'Rombach_PatternMatch', 'Cucuringu_PatternMatch']].mean(numeric_only=True).mean(axis=1)

print("\nPriemerný Pattern Match podľa kategórie modularity:")
print(modularity_avg_pm)
print("\nCelkový priemerný Pattern Match podľa modularity:")
print(modularity_avg_pm_overall)

try:
    low_mod_pm = modularity_avg_pm_overall.loc['Nízka (<0.3)']
    high_mod_pm = modularity_avg_pm_overall.loc['Vysoká (>0.7)']
    mod_diff_perc = ((low_mod_pm - high_mod_pm) / low_mod_pm) * 100 if low_mod_pm else 0
    print(f"\nPriemerný pokles PM pre siete s vysokou modularitou (>0.7) vs. nízkou (<0.3): {mod_diff_perc:.1f}%")
except KeyError:
    print("\nNepodarilo sa vypočítať rozdiel PM medzi vysokou a nízkou modularitou (chýbajú kategórie).")


size_avg_pm_dict = size_avg_pm.round(1).to_dict()

density_avg_pm_overall_dict = density_avg_pm_overall.round(1).to_dict()

size_density_dict = size_density_table.round({'Nodes (N)': 0, 'Density': 3}).to_dict()

modularity_corr_dict = {k: round(v, 2) for k, v in correlations.items()}

try:
    modularity_diff = round(mod_diff_perc, 1)
except NameError:
     modularity_diff = "N/A"

print("\n--- Dáta pripravené pre LaTeX ---")
