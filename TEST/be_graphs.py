import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Nastavenie štýlu
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12})

# Načítanie dát
be_results = pd.read_csv('TEST/results/stability_be/be_stability_results.csv')

# Definovanie sietí pre jednotlivé sady
small_medium_set = ['Karate Club', 'Dolphins', 'Les Miserables', 'Football']
large_set = ['YeastL', 'Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97']

# Rozdelenie dataframov na dve sady
set1_data = be_results[be_results['network'].isin(small_medium_set)]
set2_data = be_results[be_results['network'].isin(large_set)]

# Vytvorenie súhrnných štatistík pre Set 1
set1_summary = set1_data.groupby(['network', 'parameters.num_runs']).agg({
    'metrics.ideal_pattern_match': ['mean'],
    'metrics.core_percentage': ['mean'],
    'metrics.core_size': ['mean'],
    'runtime': ['mean']
}).reset_index()

# Zjednodušenie názvov stĺpcov
set1_summary.columns = ['network', 'num_runs', 'pattern_match', 'core_percentage', 'core_size', 'runtime']

# Vytvorenie súhrnných štatistík pre Set 2
set2_summary = set2_data.groupby(['network', 'parameters.num_runs']).agg({
    'metrics.ideal_pattern_match': ['mean'],
    'metrics.core_percentage': ['mean'],
    'metrics.core_size': ['mean'],
    'runtime': ['mean']
}).reset_index()

# Zjednodušenie názvov stĺpcov
set2_summary.columns = ['network', 'num_runs', 'pattern_match', 'core_percentage', 'core_size', 'runtime']

# --- SET 1: Malé a stredné siete (plná analýza) ---

# Vytvorenie pivot tabuľky pre heatmapu (core percentage)
heatmap_data = set1_summary.pivot(index='network', columns='num_runs', values='core_percentage')

# Vytvorenie heatmapy
plt.figure(figsize=(10, 6))
ax = sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlGnBu', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (%)'})

plt.title('Veľkosť jadra (%) BE algoritmu - malé a stredné siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_core_percentage_small_medium.png', dpi=300)
plt.close()

# Podobná heatmapa pre pattern match (Set 1)
plt.figure(figsize=(10, 6))
heatmap_data_pm = set1_summary.pivot(index='network', columns='num_runs', values='pattern_match')

ax = sns.heatmap(heatmap_data_pm, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Pattern Match (%) BE algoritmu - malé a stredné siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_pattern_match_small_medium.png', dpi=300)
plt.close()

# Heatmapa pre výpočtový čas (Set 1)
plt.figure(figsize=(10, 6))
heatmap_data_rt = set1_summary.pivot(index='network', columns='num_runs', values='runtime')

ax = sns.heatmap(heatmap_data_rt, annot=True, fmt='.2f', cmap='Purples', 
                linewidths=.5, cbar_kws={'label': 'Výpočtový čas (s)'})

plt.title('Výpočtový čas (s) BE algoritmu - malé a stredné siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_runtime_small_medium.png', dpi=300)
plt.close()

# Core Size heatmapa (Set 1)
plt.figure(figsize=(10, 6))
heatmap_data_cs = set1_summary.pivot(index='network', columns='num_runs', values='core_size')

ax = sns.heatmap(heatmap_data_cs, annot=True, fmt='.1f', cmap='YlOrBr', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (počet uzlov)'})

plt.title('Veľkosť jadra (počet uzlov) BE algoritmu - malé a stredné siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_core_size_small_medium.png', dpi=300)
plt.close()

# --- SET 2: Veľké siete (čiastočná analýza) ---

# Vytvorenie pivot tabuľky pre heatmapu (core percentage)
heatmap_data2 = set2_summary.pivot(index='network', columns='num_runs', values='core_percentage')

# Vytvorenie heatmapy
plt.figure(figsize=(10, 8))
ax = sns.heatmap(heatmap_data2, annot=True, fmt='.1f', cmap='YlGnBu', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (%)'})

plt.title('Veľkosť jadra (%) BE algoritmu - veľké siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_core_percentage_large.png', dpi=300)
plt.close()

# Podobná heatmapa pre pattern match (Set 2)
plt.figure(figsize=(10, 8))
heatmap_data_pm2 = set2_summary.pivot(index='network', columns='num_runs', values='pattern_match')

ax = sns.heatmap(heatmap_data_pm2, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Pattern Match (%) BE algoritmu - veľké siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_pattern_match_large.png', dpi=300)
plt.close()

# Heatmapa pre výpočtový čas (Set 2)
plt.figure(figsize=(10, 8))
heatmap_data_rt2 = set2_summary.pivot(index='network', columns='num_runs', values='runtime')

ax = sns.heatmap(heatmap_data_rt2, annot=True, fmt='.2f', cmap='Purples', 
                linewidths=.5, cbar_kws={'label': 'Výpočtový čas (s)'})

plt.title('Výpočtový čas (s) BE algoritmu - veľké siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_runtime_large.png', dpi=300)
plt.close()

# Core Size heatmapa (Set 2)
plt.figure(figsize=(10, 8))
heatmap_data_cs2 = set2_summary.pivot(index='network', columns='num_runs', values='core_size')

ax = sns.heatmap(heatmap_data_cs2, annot=True, fmt='.1f', cmap='YlOrBr', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (počet uzlov)'})

plt.title('Veľkosť jadra (počet uzlov) BE algoritmu - veľké siete', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_core_size_large.png', dpi=300)
plt.close()