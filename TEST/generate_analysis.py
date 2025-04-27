import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.ticker import MaxNLocator

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.3)

# Load the data
network_properties = pd.read_csv('network_properties_summary.csv')
structure_properties = pd.read_csv('results/final_structure_properties.csv')

# Create a merged dataframe for analysis
data = []

# For each network in the network_properties
for network in network_properties['Network'].unique():
    # Get network properties
    avg_degree = network_properties.loc[network_properties['Network'] == network, 'Average Degree'].values[0]
    avg_clustering = network_properties.loc[network_properties['Network'] == network, 'Average Clustering Coefficient'].values[0]
    
    # Get pattern match values for each algorithm
    for algorithm in ['BE', 'Rombach', 'LowRankCore']:
        pattern_match = structure_properties.loc[
            (structure_properties['Network'] == network) & 
            (structure_properties['Algorithm'] == algorithm), 
            'ideal_pattern_match'
        ].values
        
        # Some networks might not have results for all algorithms
        if len(pattern_match) > 0:
            data.append({
                'Network': network,
                'Algorithm': algorithm,
                'Average Degree': avg_degree,
                'Average Clustering Coefficient': avg_clustering,
                'Pattern Match (%)': pattern_match[0]
            })

# Convert to DataFrame
df = pd.DataFrame(data)

# Create a color palette for consistent colors across plots
algorithm_colors = {"BE": "#3498db", "Rombach": "#e74c3c", "LowRankCore": "#2ecc71"}
algorithm_markers = {"BE": "o", "Rombach": "s", "LowRankCore": "^"}

# Plot 1: Average Degree vs Pattern Match
plt.figure(figsize=(9, 6))
ax = sns.scatterplot(data=df, x='Average Degree', y='Pattern Match (%)', 
                     hue='Algorithm', style='Algorithm', s=120,
                     palette=algorithm_colors, markers=algorithm_markers)

# Add network labels to points
for i, point in df.iterrows():
    plt.text(point['Average Degree']+0.5, point['Pattern Match (%)'], 
             point['Network'], fontsize=8)

plt.title('Impact of Average Degree on Pattern Match', fontsize=16)
plt.xlabel('Average Degree', fontsize=14)
plt.ylabel('Pattern Match (%)', fontsize=14)
plt.legend(title='Algorithm', fontsize=12, title_fontsize=13)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('avg_degree_vs_pattern_match.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Average Clustering Coefficient vs Pattern Match
plt.figure(figsize=(9, 6))
ax = sns.scatterplot(data=df, x='Average Clustering Coefficient', y='Pattern Match (%)', 
                     hue='Algorithm', style='Algorithm', s=120,
                     palette=algorithm_colors, markers=algorithm_markers)

# Add network labels to points
for i, point in df.iterrows():
    plt.text(point['Average Clustering Coefficient']+0.02, point['Pattern Match (%)'], 
             point['Network'], fontsize=8)

plt.title('Impact of Clustering Coefficient on Pattern Match', fontsize=16)
plt.xlabel('Average Clustering Coefficient', fontsize=14)
plt.ylabel('Pattern Match (%)', fontsize=14)
plt.legend(title='Algorithm', fontsize=12, title_fontsize=13)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('avg_clustering_vs_pattern_match.png', dpi=300, bbox_inches='tight')
plt.close()

# Combined visualization (both plots side by side)
plt.figure(figsize=(16, 7))

# Plot 1: Average Degree vs Pattern Match
plt.subplot(1, 2, 1)
sns.scatterplot(data=df, x='Average Degree', y='Pattern Match (%)', 
                hue='Algorithm', style='Algorithm', s=100,
                palette=algorithm_colors, markers=algorithm_markers)
plt.title('Impact of Average Degree on Pattern Match', fontsize=15)
plt.xlabel('Average Degree', fontsize=13)
plt.ylabel('Pattern Match (%)', fontsize=13)

# Plot 2: Average Clustering Coefficient vs Pattern Match
plt.subplot(1, 2, 2)
sns.scatterplot(data=df, x='Average Clustering Coefficient', y='Pattern Match (%)', 
                hue='Algorithm', style='Algorithm', s=100,
                palette=algorithm_colors, markers=algorithm_markers)
plt.title('Impact of Clustering Coefficient on Pattern Match', fontsize=15)
plt.xlabel('Average Clustering Coefficient', fontsize=13)
plt.ylabel('Pattern Match (%)', fontsize=13)

plt.tight_layout()
plt.savefig('core_periphery_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Detailed correlation analysis
correlations = []
for algorithm in df['Algorithm'].unique():
    algo_data = df[df['Algorithm'] == algorithm]
    
    # Pearson correlation
    degree_corr = np.corrcoef(algo_data['Average Degree'], algo_data['Pattern Match (%)'])[0,1]
    cluster_corr = np.corrcoef(algo_data['Average Clustering Coefficient'], algo_data['Pattern Match (%)'])[0,1]
    
    correlations.append({
        'Algorithm': algorithm,
        'Degree_Correlation': degree_corr,
        'Clustering_Correlation': cluster_corr
    })

correlation_df = pd.DataFrame(correlations)

# Print the correlation results
print("Correlation with Pattern Match:")
print(correlation_df)

# Save correlation results to CSV
correlation_df.to_csv('pattern_match_correlations.csv', index=False)

# Create bar plot for correlations
plt.figure(figsize=(10, 6))
x = np.arange(len(correlation_df))
width = 0.35

plt.bar(x - width/2, correlation_df['Degree_Correlation'], width, label='Average Degree', color='#3498db')
plt.bar(x + width/2, correlation_df['Clustering_Correlation'], width, label='Clustering Coefficient', color='#e74c3c')

plt.xlabel('Algorithm', fontsize=14)
plt.ylabel('Correlation Coefficient (r)', fontsize=14)
plt.title('Correlation between Network Properties and Pattern Match', fontsize=16)
plt.xticks(x, correlation_df['Algorithm'], fontsize=12)
plt.legend(fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('correlation_analysis.png', dpi=300, bbox_inches='tight')
plt.show()