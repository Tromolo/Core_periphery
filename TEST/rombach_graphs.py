import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 12})

rombach_results = pd.read_csv('TEST/results/stability_rombach/rombach_stability_results.csv')


filtered_data_alpha = rombach_results[(rombach_results['parameters.beta'] == 0.9) & 
                                    (rombach_results['parameters.num_runs'] == 5)]

alpha_heatmap = filtered_data_alpha.pivot_table(
    index='network', 
    columns='parameters.alpha', 
    values='metrics.ideal_pattern_match',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(alpha_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Vplyv parametra alpha na Pattern Match Rombach algoritmu (beta=0.9)', fontsize=14)
plt.xlabel('Alpha parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_alpha_pattern_match.png', dpi=300)
plt.close()


filtered_data_beta = rombach_results[(rombach_results['parameters.alpha'] == 0.5) & 
                                   (rombach_results['parameters.num_runs'] == 10)]

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

stability_data = rombach_results[(rombach_results['parameters.alpha'] == 0.5) & 
                               (rombach_results['parameters.beta'] == 0.9)]

stability_heatmap = stability_data.pivot_table(
    index='network', 
    columns='parameters.num_runs', 
    values='metrics.ideal_pattern_match',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(stability_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Pattern Match (%)'})

plt.title('Vplyv num_runs na Pattern Match Rombach algoritmu (alpha=0.5, beta=0.9)', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_stability_pattern_match.png', dpi=300)
plt.close()


alpha_core_heatmap = filtered_data_alpha.pivot_table(
    index='network', 
    columns='parameters.alpha', 
    values='metrics.core_percentage',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(alpha_core_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Core Size (%)'})

plt.title('Vplyv parametra alpha na Core Size Rombach algoritmu (beta=0.9)', fontsize=14)
plt.xlabel('Alpha parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_alpha_core_size.png', dpi=300)
plt.close()


# Beta heatmap for core size
filtered_data_beta_core = rombach_results[(rombach_results['parameters.alpha'] == 0.1)]

beta_core_heatmap = filtered_data_beta_core.pivot_table(
    index='network', 
    columns='parameters.beta', 
    values='metrics.core_percentage',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(beta_core_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Core Size (%)'})

plt.title('Vplyv parametra beta na Core Size Rombach algoritmu (alpha=0.1)', fontsize=14)
plt.xlabel('Beta parameter', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_beta_core_size.png', dpi=300)
plt.close()


stability_core_heatmap = stability_data.pivot_table(
    index='network', 
    columns='parameters.num_runs', 
    values='metrics.core_percentage',
    aggfunc='mean'
)

plt.figure(figsize=(10, 8))
ax = sns.heatmap(stability_core_heatmap, annot=True, fmt='.1f', cmap='RdYlGn', 
                linewidths=.5, cbar_kws={'label': 'Core Size (%)'})

plt.title('Vplyv num_runs na Core Size Rombach algoritmu (alpha=0.5, beta=0.9)', fontsize=14)
plt.xlabel('Počet opakovaní (num_runs)', fontsize=12)
plt.ylabel('Sieť', fontsize=12)
plt.tight_layout()
plt.savefig('TEST/results/stability_rombach/rombach_stability_core_size.png', dpi=300)
plt.close()