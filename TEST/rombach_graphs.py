import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Nastavenie štýlu
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12})

# Načítanie dát
rombach_results = pd.read_csv('TEST/results/stability_rombach/rombach_stability_results.csv')

# 1. Súhrnná heatmapa pre vplyv alpha na pattern match pre všetky siete
# Vyberieme len beta=0.5 a num_runs=10 pre jednoduchosť
filtered_data_alpha = rombach_results[(rombach_results['parameters.beta'] == 0.5) & 
                                    (rombach_results['parameters.num_runs'] == 10)]

# Vytvorenie pivot tabuľky pre heatmapu
alpha_heatmap = filtered_data_alpha.pivot_table(
    index='network', 
    columns='parameters.alpha', 
    values='metrics.ideal_pattern_match',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(alpha_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Vplyv parametra alpha na Pattern Match Rombach algoritmu (beta=0.5)', fontsize=14)
plt.xlabel('Alpha parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_alpha_pattern_match.png', dpi=300)
plt.close()

# 2. Súhrnná heatmapa pre vplyv beta na pattern match pre všetky siete
# Vyberieme len alpha=0.5 a num_runs=10 pre jednoduchosť
filtered_data_beta = rombach_results[(rombach_results['parameters.alpha'] == 0.5) & 
                                   (rombach_results['parameters.num_runs'] == 10)]

# Vytvorenie pivot tabuľky pre heatmapu
beta_heatmap = filtered_data_beta.pivot_table(
    index='network', 
    columns='parameters.beta', 
    values='metrics.ideal_pattern_match',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(beta_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Vplyv parametra beta na Pattern Match Rombach algoritmu (alpha=0.5)', fontsize=14)
plt.xlabel('Beta parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_beta_pattern_match.png', dpi=300)
plt.close()

# 3. Súhrnná heatmapa pre vplyv num_runs na stabilitu výsledkov
# Vyberieme len alpha=0.5 a beta=0.5 pre jednoduchosť
stability_data = rombach_results[(rombach_results['parameters.alpha'] == 0.5) & 
                               (rombach_results['parameters.beta'] == 0.5)]

# Vytvorenie pivot tabuľky pre heatmapu
stability_heatmap = stability_data.pivot_table(
    index='network', 
    columns='parameters.num_runs', 
    values='metrics.ideal_pattern_match',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(stability_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Vplyv num_runs na Pattern Match Rombach algoritmu (alpha=0.5, beta=0.5)', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_stability_pattern_match.png', dpi=300)
plt.close()