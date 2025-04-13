import pandas as pd
import numpy as np

# Načítanie dát
df = pd.read_csv('TEST/results/parameter_sensitivity_rerun/parameter_sensitivity_results_rerun.csv')

# Definícia kategórií sietí
small_networks = ['Karate Club', 'Dolphins', 'Les Miserables']
medium_networks = ['Football']
large_networks = ['Facebook Combined', 'Power Grid']
synthetic_networks = ['Bianconi-0.7', 'Bianconi-0.97']

# Nájdenie optimálnych výsledkov pre každú kombináciu sieť+algoritmus
optimal_results = []

for network in df['network'].unique():
    for algorithm in df[df['network'] == network]['algorithm'].unique():
        # Filtrovanie pre konkrétnu sieť a algoritmus
        subset = df[(df['network'] == network) & (df['algorithm'] == algorithm)]
        
        if not subset.empty:
            # Najprv zoradíme podľa pattern match a vyberieme prvý riadok
            best_row = subset.sort_values('metrics.ideal_pattern_match', ascending=False).iloc[0]
            
            # Pridanie najlepšieho výsledku
            optimal_results.append({
                'network': network,
                'algorithm': algorithm,
                'pattern_match': best_row['metrics.ideal_pattern_match'],
                'core_size': best_row['metrics.core_percentage'],
                'runtime': best_row['runtime'],
                'params': {
                    'num_runs': best_row.get('parameters.num_runs', None),
                    'alpha': best_row.get('parameters.alpha', None),
                    'beta': best_row.get('parameters.beta', None)
                }
            })

# Konverzia na DataFrame
optimal_df = pd.DataFrame(optimal_results)

# Výpočet priemerov pre kategórie sietí
print("\nPriemery pre kategórie sietí (optimálne parametre):")

for category_name, networks in [
    ("Malé siete (Karate, Dolphins, Les Miserables)", small_networks),
    ("Stredné siete (Football)", medium_networks),
    ("Veľké siete (Facebook, Power Grid)", large_networks)
]:
    print(f"\n{category_name}:")
    for algorithm in ['BE', 'Rombach', 'Cucuringu']:
        selection = optimal_df[(optimal_df['network'].isin(networks)) & 
                              (optimal_df['algorithm'] == algorithm)]
        
        if not selection.empty:
            pm_avg = selection['pattern_match'].mean()
            cs_avg = selection['core_size'].mean()
            rt_avg = selection['runtime'].mean()
            
            if algorithm == 'BE' and category_name.startswith("Veľké siete"):
                print(f"{algorithm}: Pattern Match = --, Core Size = --, Runtime = >3600s")
            else:
                print(f"{algorithm}: Pattern Match = {pm_avg:.1f}%, Core Size = {cs_avg:.1f}%, Runtime = {rt_avg:.3f}s")
        else:
            print(f"{algorithm}: Žiadne dáta")

# Výpis optimálnych parametrov a výsledkov pre jednotlivé siete
print("\nOptimálne parametre a výsledky pre každú sieť:")
for network in small_networks + medium_networks + large_networks:
    print(f"\n{network}:")
    network_results = optimal_df[optimal_df['network'] == network]
    for _, row in network_results.iterrows():
        params_str = ""
        if row['algorithm'] == 'Rombach':
            params_str = f" (alpha={row['params']['alpha']}, beta={row['params']['beta']}, num_runs={row['params']['num_runs']})"
        elif row['algorithm'] == 'BE':
            params_str = f" (num_runs={row['params']['num_runs']})"
        elif row['algorithm'] == 'Cucuringu':
            params_str = f" (beta={row['params']['beta']})"
            
        print(f"{row['algorithm']}{params_str}: Pattern Match = {row['pattern_match']:.1f}%, Core Size = {row['core_size']:.1f}%, Runtime = {row['runtime']:.3f}s") 