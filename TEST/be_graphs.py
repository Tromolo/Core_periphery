import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Nastavenie štýlu
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12})

# Načítanie dát
be_results = pd.read_csv('TEST/results/stability_be/be_stability_results.csv')

# Vytvorenie súhrnných štatistík
be_summary = be_results.groupby(['network', 'parameters.num_runs']).agg({
    'metrics.ideal_pattern_match': ['mean'],
    'metrics.core_percentage': ['mean'],
    'runtime': ['mean']
}).reset_index()

# Zjednodušenie názvov stĺpcov
be_summary.columns = ['network', 'num_runs', 'pattern_match', 'core_percentage', 'runtime']

# Vytvorenie pivot tabuľky pre heatmapu
heatmap_data = be_summary.pivot(index='network', columns='num_runs', values='core_percentage')

# Vytvorenie heatmapy
plt.figure(figsize=(10, 6))
ax = sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlGnBu', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (%)'})

plt.title('Veľkosť jadra (%) BE algoritmu v závislosti od num_runs', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_core_size_heatmap.png', dpi=300)
plt.close()

# Podobná heatmapa pre pattern match
plt.figure(figsize=(10, 6))
heatmap_data_pm = be_summary.pivot(index='network', columns='num_runs', values='pattern_match')

ax = sns.heatmap(heatmap_data_pm, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Pattern Match (%) BE algoritmu v závislosti od num_runs', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_pattern_match_heatmap.png', dpi=300)
plt.close()

# Heatmapa pre výpočtový čas
plt.figure(figsize=(10, 6))
heatmap_data_rt = be_summary.pivot(index='network', columns='num_runs', values='runtime')

ax = sns.heatmap(heatmap_data_rt, annot=True, fmt='.2f', cmap='Purples', 
                linewidths=.5, cbar_kws={'label': 'Výpočtový čas (s)'})

plt.title('Výpočtový čas (s) BE algoritmu v závislosti od num_runs', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_be/be_runtime_heatmap.png', dpi=300)
plt.close()