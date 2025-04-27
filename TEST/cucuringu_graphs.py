import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Nastavenie štýlu
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12})

# Načítanie dát
cucuringu_results = pd.read_csv('TEST/results/stability_cucuringu/cucuringu_stability_results.csv')

# Vytvorenie súhrnných štatistík
cucuringu_summary = cucuringu_results.groupby(['network', 'parameters.beta']).agg({
    'metrics.ideal_pattern_match': ['mean'],
    'metrics.core_percentage': ['mean'],
    'runtime': ['mean']
}).reset_index()

# Zjednodušenie názvov stĺpcov
cucuringu_summary.columns = ['network', 'beta', 'pattern_match', 'core_percentage', 'runtime']

# Vytvorenie pivot tabuľky pre heatmapu
heatmap_data = cucuringu_summary.pivot(index='network', columns='beta', values='core_percentage')

# Vytvorenie heatmapy
plt.figure(figsize=(10, 8))
ax = sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlGnBu', 
                linewidths=.5, cbar_kws={'label': 'Veľkosť jadra (%)'})

plt.title('Veľkosť jadra (%) LowRankCore algoritmu v závislosti od beta', fontsize=14)
plt.xlabel('Beta parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_cucuringu/cucuringu_core_size_heatmap.png', dpi=300)
plt.close()

# Podobná heatmapa pre pattern match
plt.figure(figsize=(10, 8))
heatmap_data_pm = cucuringu_summary.pivot(index='network', columns='beta', values='pattern_match')

ax = sns.heatmap(heatmap_data_pm, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Pattern Match (%) LowRankCore algoritmu v závislosti od beta', fontsize=14)
plt.xlabel('Beta parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_cucuringu/cucuringu_pattern_match_heatmap.png', dpi=300)
plt.close()

# Heatmapa pre výpočtový čas
plt.figure(figsize=(10, 8))
heatmap_data_rt = cucuringu_summary.pivot(index='network', columns='beta', values='runtime')

ax = sns.heatmap(heatmap_data_rt, annot=True, fmt='.2f', cmap='Purples', 
                linewidths=.5, cbar_kws={'label': 'Výpočtový čas (s)'})

plt.title('Výpočtový čas (s) LowRankCore algoritmu v závislosti od beta', fontsize=14)
plt.xlabel('Beta parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_cucuringu/cucuringu_runtime_heatmap.png', dpi=300)
plt.close() 