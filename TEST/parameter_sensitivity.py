import pandas as pd
import os

# Vytvoríme priečinok pre výsledky, ak neexistuje
os.makedirs('TEST/results/optimal_params', exist_ok=True)

# List of networks
small_networks = ['Karate Club', 'Dolphins', 'Les Miserables']
medium_networks = ['Football', 'YeastL']
large_networks = ['Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97']

all_networks = small_networks + medium_networks + large_networks

# Zoznam všetkých metrík, ktoré chceme zbierať
metrics_columns = [
    'metrics.ideal_pattern_match',
    'metrics.core_size',
    'metrics.periphery_size',
    'metrics.core_percentage',
    'metrics.core_density',
    'metrics.periphery_density',
    'metrics.core_periphery_ratio',
    'runtime'
]

# BE ALGORITHM
data_be = pd.read_csv('TEST/results/stability_be/be_stability_results.csv')
df_be = pd.DataFrame(data_be)

# Pripravíme výsledný DataFrame pre BE algoritmus
be_results = []

# Pre každú sieť spracujeme dáta s optimálnymi parametrami
for network in small_networks:
    # Pre malé siete: num_runs = 10-20
    filtered_df = df_be[(df_be['network'] == network) & 
                       (df_be['parameters.num_runs'] >= 10) & 
                       (df_be['parameters.num_runs'] <= 20)]
    
    if not filtered_df.empty:
        avg_values = filtered_df[metrics_columns].mean()
        result_dict = {
            'network': network,
            'network_type': 'small',
            'recommended_params': 'num_runs = 10-20'
        }
        
        # Pridáme všetky metriky
        for col in metrics_columns:
            result_dict[col.replace('metrics.', '')] = avg_values[col]
            
        be_results.append(result_dict)

for network in medium_networks:
    # Pre stredné siete: num_runs = 5-10
    filtered_df = df_be[(df_be['network'] == network) & 
                       (df_be['parameters.num_runs'] >= 5) & 
                       (df_be['parameters.num_runs'] <= 10)]
    
    if not filtered_df.empty:
        avg_values = filtered_df[metrics_columns].mean()
        result_dict = {
            'network': network,
            'network_type': 'medium',
            'recommended_params': 'num_runs = 5-10'
        }
        
        # Pridáme všetky metriky
        for col in metrics_columns:
            result_dict[col.replace('metrics.', '')] = avg_values[col]
            
        be_results.append(result_dict)

for network in large_networks:
    filtered_df = df_be[(df_be['network'] == network) & 
                       (df_be['parameters.num_runs'] >= 5)]
    
    if not filtered_df.empty:
        avg_values = filtered_df[metrics_columns].mean()
        result_dict = {
            'network': network,
            'network_type': 'large',
            'recommended_params': 'num_runs >= 5'    
        }
        
        for col in metrics_columns:
            result_dict[col.replace('metrics.', '')] = avg_values[col]
            
        be_results.append(result_dict)
    

# Vytvoríme a uložíme výsledný DataFrame pre BE
if be_results:
    be_results_df = pd.DataFrame(be_results)
    be_results_df.to_csv('TEST/results/optimal_params/be_optimal_results.csv', index=False)

# ROMBACH ALGORITHM
data_rombach = pd.read_csv('TEST/results/stability_rombach/rombach_stability_results.csv')
df_rombach = pd.DataFrame(data_rombach)

# Pripravíme výsledný DataFrame pre Rombach algoritmus
rombach_results = []

for network in all_networks:
    # Pre všetky siete: β = 0.9, α = 0.5-0.9, num_runs ≥ 5
    filtered_df = df_rombach[(df_rombach['network'] == network) & 
                            (df_rombach['parameters.beta'] == 0.9) & 
                            (df_rombach['parameters.alpha'] >= 0.5) & 
                            (df_rombach['parameters.alpha'] <= 0.9) & 
                            (df_rombach['parameters.num_runs'] == 5)]
    
    if not filtered_df.empty:
        avg_values = filtered_df[metrics_columns].mean()
        
        # Určíme typ siete pre výstup
        if network in small_networks:
            network_type = "small"
        elif network in medium_networks:
            network_type = "medium"
        else:
            network_type = "large"
            
        result_dict = {
            'network': network,
            'network_type': network_type,
            'recommended_params': 'β = 0.9, α = 0.5-0.9, num_runs = 5'
        }
        
        # Pridáme všetky metriky
        for col in metrics_columns:
            result_dict[col.replace('metrics.', '')] = avg_values[col]
            
        rombach_results.append(result_dict)

# Vytvoríme a uložíme výsledný DataFrame pre Rombach
if rombach_results:
    rombach_results_df = pd.DataFrame(rombach_results)
    rombach_results_df.to_csv('TEST/results/optimal_params/rombach_optimal_results.csv', index=False)

# CUCURINGU (LOWRANKCORE) ALGORITHM
data_cucuringu = pd.read_csv('TEST/results/stability_cucuringu/cucuringu_stability_results.csv')
df_cucuringu = pd.DataFrame(data_cucuringu)

# Pripravíme výsledný DataFrame pre Cucuringu algoritmus
cucuringu_results = []

for network in all_networks:
    # Pre všetky siete: beta = 0.1
    filtered_df = df_cucuringu[(df_cucuringu['network'] == network) & 
                             (df_cucuringu['parameters.beta'] == 0.1)]
    
    if not filtered_df.empty:
        avg_values = filtered_df[metrics_columns].mean()
        
        # Určíme typ siete pre výstup
        if network in small_networks:
            network_type = "small"
        elif network in medium_networks:
            network_type = "medium"
        else:
            network_type = "large"
            
        result_dict = {
            'network': network,
            'network_type': network_type,
            'recommended_params': 'beta = 0.1 (maximizing pattern match)'
        }
        
        # Pridáme všetky metriky
        for col in metrics_columns:
            result_dict[col.replace('metrics.', '')] = avg_values[col]
            
        cucuringu_results.append(result_dict)

# Vytvoríme a uložíme výsledný DataFrame pre Cucuringu
if cucuringu_results:
    cucuringu_results_df = pd.DataFrame(cucuringu_results)
    cucuringu_results_df.to_csv('TEST/results/optimal_params/cucuringu_optimal_results.csv', index=False)

# Vytvoríme kombinovaný súbor so všetkými algoritmami
all_results = []

# Pridáme BE výsledky
if be_results:
    for result in be_results:
        result_copy = result.copy()
        result_copy['algorithm'] = 'BE'
        all_results.append(result_copy)

# Pridáme Rombach výsledky
if rombach_results:
    for result in rombach_results:
        result_copy = result.copy()
        result_copy['algorithm'] = 'Rombach'
        all_results.append(result_copy)

# Pridáme Cucuringu výsledky
if cucuringu_results:
    for result in cucuringu_results:
        result_copy = result.copy()
        result_copy['algorithm'] = 'LowRankCore'
        all_results.append(result_copy)

# Vytvoríme a uložíme kombinovaný DataFrame
if all_results:
    all_results_df = pd.DataFrame(all_results)
    all_results_df.to_csv('TEST/results/optimal_params/all_optimal_results.csv', index=False)

print("Výsledky boli úspešne uložené do priečinka TEST/results/optimal_params/")