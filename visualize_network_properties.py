import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# Set style for academic plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper")

# Create a directory for figures if it doesn't exist
import os
if not os.path.exists('Figures'):
    os.makedirs('Figures')

# Load the data
network_properties = pd.read_csv('network_properties_summary.csv')
structure_properties = pd.read_csv('results/final_structure_properties.csv')

# Combine the datasets
data = []

# Get all the unique networks
networks = network_properties['Network'].unique()

for network in networks:
    # Get network properties
    network_row = network_properties[network_properties['Network'] == network].iloc[0]
    
    # Get pattern match values for each algorithm
    be_row = structure_properties[(structure_properties['Network'] == network) & 
                                (structure_properties['Algorithm'] == 'BE')].iloc[0]
    
    rombach_row = structure_properties[(structure_properties['Network'] == network) & 
                                    (structure_properties['Algorithm'] == 'Rombach')].iloc[0]
    
    lowrank_row = structure_properties[(structure_properties['Network'] == network) & 
                                    (structure_properties['Algorithm'] == 'LowRankCore')].iloc[0]
    
    # Add to the dataset
    data.append({
        'Network': network,
        'Nodes (N)': network_row['Nodes (N)'],
        'Density': network_row['Density'],
        'Average Degree': network_row['Average Degree'],
        'Average Clustering Coefficient': network_row['Average Clustering Coefficient'],
        'Modularity': network_row['Modularity'],
        'BE Pattern Match': be_row['ideal_pattern_match'],
        'Rombach Pattern Match': rombach_row['ideal_pattern_match'],
        'LowRankCore Pattern Match': lowrank_row['ideal_pattern_match']
    })

# Convert to DataFrame
df = pd.DataFrame(data)

# Print the dataframe for verification
print(df)

# Figure 1: Average Degree vs Pattern Match
plt.figure(figsize=(10, 6))

# Sort by Average Degree for better visualization
df = df.sort_values('Average Degree')

# Plot each algorithm
plt.scatter(df['Average Degree'], df['BE Pattern Match'], s=80, marker='o', 
            label='BE', alpha=0.7, color='#1f77b4')
plt.scatter(df['Average Degree'], df['Rombach Pattern Match'], s=80, marker='s', 
            label='Rombach', alpha=0.7, color='#ff7f0e')
plt.scatter(df['Average Degree'], df['LowRankCore Pattern Match'], s=80, marker='^', 
            label='LowRankCore (Cucuringu)', alpha=0.7, color='#2ca02c')

# Add network labels next to points (only for BE to avoid clutter)
for i, row in df.iterrows():
    plt.annotate(row['Network'], 
                 xy=(row['Average Degree'], row['BE Pattern Match']),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=8, alpha=0.8)

# Adding horizontal line at y=80 for reference
plt.axhline(y=80, color='gray', linestyle='--', alpha=0.5)

# Log scale for x-axis due to the wide range of degrees
plt.xscale('log')
plt.xlim(df['Average Degree'].min() * 0.8, df['Average Degree'].max() * 1.2)
plt.ylim(30, 105)  # Ensure y-axis captures all values with some padding

# Add titles and labels
plt.title('Relationship Between Average Degree and Pattern Match Quality', fontsize=14)
plt.xlabel('Average Degree (log scale)', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Figures/avg_degree_vs_pattern_match.png', dpi=300)

# Figure 2: Average Clustering Coefficient vs Pattern Match
plt.figure(figsize=(10, 6))

# Sort by clustering coefficient for better visualization
df = df.sort_values('Average Clustering Coefficient')

# Plot each algorithm
plt.scatter(df['Average Clustering Coefficient'], df['BE Pattern Match'], s=80, 
            marker='o', label='BE', alpha=0.7, color='#1f77b4')
plt.scatter(df['Average Clustering Coefficient'], df['Rombach Pattern Match'], s=80, 
            marker='s', label='Rombach', alpha=0.7, color='#ff7f0e')
plt.scatter(df['Average Clustering Coefficient'], df['LowRankCore Pattern Match'], s=80, 
            marker='^', label='LowRankCore (Cucuringu)', alpha=0.7, color='#2ca02c')

# Add network labels
for i, row in df.iterrows():
    plt.annotate(row['Network'], 
                 xy=(row['Average Clustering Coefficient'], row['BE Pattern Match']),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=8, alpha=0.8)

# Adding horizontal line at y=80 for reference
plt.axhline(y=80, color='gray', linestyle='--', alpha=0.5)

plt.xlim(df['Average Clustering Coefficient'].min() * 0.8, 
         df['Average Clustering Coefficient'].max() * 1.1)
plt.ylim(30, 105)  # Ensure y-axis captures all values with some padding

# Add titles and labels
plt.title('Relationship Between Average Clustering Coefficient and Pattern Match Quality', 
          fontsize=14)
plt.xlabel('Average Clustering Coefficient', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Figures/avg_clustering_vs_pattern_match.png', dpi=300)

# Figure 3: Modularity vs Pattern Match
plt.figure(figsize=(10, 6))

# Sort by modularity for better visualization
df = df.sort_values('Modularity')

# Create color scheme similar to the example
be_color = '#1f77b4'    # Blue
rombach_color = '#ff7f0e'  # Orange/Yellow
cucuringu_color = '#2ca02c'  # Green

# Plot each algorithm
plt.scatter(df['Modularity'], df['BE Pattern Match'], s=80, 
            marker='o', label='BE', alpha=0.7, color=be_color)
plt.scatter(df['Modularity'], df['Rombach Pattern Match'], s=80, 
            marker='s', label='Rombach', alpha=0.7, color=rombach_color)
plt.scatter(df['Modularity'], df['LowRankCore Pattern Match'], s=80, 
            marker='^', label='Cucuringu', alpha=0.7, color=cucuringu_color)

# Add network labels next to points (only for BE to avoid clutter)
for i, row in df.iterrows():
    plt.annotate(row['Network'], 
                 xy=(row['Modularity'], row['BE Pattern Match']),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=8, alpha=0.8)

# Adding horizontal line at y=80 for reference
plt.axhline(y=80, color='gray', linestyle='--', alpha=0.5)

# Add trend lines
# For BE
slope_be, intercept_be, r_value_be, p_value_be, std_err_be = stats.linregress(
    df['Modularity'], df['BE Pattern Match'])
x_be = np.array([df['Modularity'].min(), df['Modularity'].max()])
y_be = intercept_be + slope_be * x_be
plt.plot(x_be, y_be, '--', color=be_color, alpha=0.7)

# For Rombach
slope_rombach, intercept_rombach, r_value_rombach, p_value_rombach, std_err_rombach = stats.linregress(
    df['Modularity'], df['Rombach Pattern Match'])
x_rombach = np.array([df['Modularity'].min(), df['Modularity'].max()])
y_rombach = intercept_rombach + slope_rombach * x_rombach
plt.plot(x_rombach, y_rombach, '--', color=rombach_color, alpha=0.7)

# For Cucuringu
slope_cucuringu, intercept_cucuringu, r_value_cucuringu, p_value_cucuringu, std_err_cucuringu = stats.linregress(
    df['Modularity'], df['LowRankCore Pattern Match'])
x_cucuringu = np.array([df['Modularity'].min(), df['Modularity'].max()])
y_cucuringu = intercept_cucuringu + slope_cucuringu * x_cucuringu
plt.plot(x_cucuringu, y_cucuringu, '--', color=cucuringu_color, alpha=0.7)

plt.xlim(df['Modularity'].min() * 0.95, df['Modularity'].max() * 1.05)
plt.ylim(30, 105)  # Ensure y-axis captures all values with some padding

# Add titles and labels
plt.title('Vzťah modularity a Pattern Match (optimálne parametre)', fontsize=14)
plt.xlabel('Modularita (Louvain)', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10, title="Algoritmus")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Figures/modularity_vs_pattern_match.png', dpi=300)

# Figure 4: Density vs Pattern Match
plt.figure(figsize=(10, 6))

# Sort by density for better visualization
df = df.sort_values('Density')

# Create color scheme
be_color = '#1f77b4'    # Blue
rombach_color = '#ff7f0e'  # Orange/Yellow
cucuringu_color = '#2ca02c'  # Green

# Plot each algorithm
plt.scatter(df['Density'], df['BE Pattern Match'], s=80, 
            marker='o', label='BE', alpha=0.7, color=be_color)
plt.scatter(df['Density'], df['Rombach Pattern Match'], s=80, 
            marker='s', label='Rombach', alpha=0.7, color=rombach_color)
plt.scatter(df['Density'], df['LowRankCore Pattern Match'], s=80, 
            marker='^', label='Cucuringu', alpha=0.7, color=cucuringu_color)

# Add network labels next to points (only for BE to avoid clutter)
for i, row in df.iterrows():
    plt.annotate(row['Network'], 
                 xy=(row['Density'], row['BE Pattern Match']),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=8, alpha=0.8)

# Adding horizontal line at y=80 for reference
plt.axhline(y=80, color='gray', linestyle='--', alpha=0.5)

# Add trend lines
# For BE
slope_be, intercept_be, r_value_be, p_value_be, std_err_be = stats.linregress(
    df['Density'], df['BE Pattern Match'])
x_be = np.array([df['Density'].min(), df['Density'].max()])
y_be = intercept_be + slope_be * x_be
plt.plot(x_be, y_be, '--', color=be_color, alpha=0.7)

# For Rombach
slope_rombach, intercept_rombach, r_value_rombach, p_value_rombach, std_err_rombach = stats.linregress(
    df['Density'], df['Rombach Pattern Match'])
x_rombach = np.array([df['Density'].min(), df['Density'].max()])
y_rombach = intercept_rombach + slope_rombach * x_rombach
plt.plot(x_rombach, y_rombach, '--', color=rombach_color, alpha=0.7)

# For Cucuringu
slope_cucuringu, intercept_cucuringu, r_value_cucuringu, p_value_cucuringu, std_err_cucuringu = stats.linregress(
    df['Density'], df['LowRankCore Pattern Match'])
x_cucuringu = np.array([df['Density'].min(), df['Density'].max()])
y_cucuringu = intercept_cucuringu + slope_cucuringu * x_cucuringu
plt.plot(x_cucuringu, y_cucuringu, '--', color=cucuringu_color, alpha=0.7)

# Log scale for x-axis due to the wide range of density values
plt.xscale('log')
plt.xlim(df['Density'].min() * 0.5, df['Density'].max() * 2)
plt.ylim(30, 105)  # Ensure y-axis captures all values with some padding

# Add titles and labels
plt.title('Vzťah hustoty siete a Pattern Match (optimálne parametre)', fontsize=14)
plt.xlabel('Hustota siete (log scale)', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10, title="Algoritmus")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Figures/density_vs_pattern_match.png', dpi=300)

# Figure 5: Network Size (N) vs Pattern Match
plt.figure(figsize=(10, 6))

# Sort by network size for better visualization
df = df.sort_values('Nodes (N)')

# Create color scheme
be_color = '#1f77b4'    # Blue
rombach_color = '#ff7f0e'  # Orange/Yellow
cucuringu_color = '#2ca02c'  # Green

# Plot each algorithm
plt.scatter(df['Nodes (N)'], df['BE Pattern Match'], s=80, 
            marker='o', label='BE', alpha=0.7, color=be_color)
plt.scatter(df['Nodes (N)'], df['Rombach Pattern Match'], s=80, 
            marker='s', label='Rombach', alpha=0.7, color=rombach_color)
plt.scatter(df['Nodes (N)'], df['LowRankCore Pattern Match'], s=80, 
            marker='^', label='Cucuringu', alpha=0.7, color=cucuringu_color)

# Add network labels next to points (only for BE to avoid clutter)
for i, row in df.iterrows():
    plt.annotate(row['Network'], 
                 xy=(row['Nodes (N)'], row['BE Pattern Match']),
                 xytext=(5, 0), textcoords='offset points',
                 fontsize=8, alpha=0.8)

# Adding horizontal line at y=80 for reference
plt.axhline(y=80, color='gray', linestyle='--', alpha=0.5)

# Add trend lines
# For BE
slope_be, intercept_be, r_value_be, p_value_be, std_err_be = stats.linregress(
    np.log10(df['Nodes (N)']), df['BE Pattern Match'])  # Using log scale for fit
x_be_log = np.array([np.log10(df['Nodes (N)'].min()), np.log10(df['Nodes (N)'].max())])
y_be = intercept_be + slope_be * x_be_log
x_be = 10 ** x_be_log  # Convert back to original scale for plotting
plt.plot(x_be, y_be, '--', color=be_color, alpha=0.7)

# For Rombach
slope_rombach, intercept_rombach, r_value_rombach, p_value_rombach, std_err_rombach = stats.linregress(
    np.log10(df['Nodes (N)']), df['Rombach Pattern Match'])  # Using log scale for fit
x_rombach_log = np.array([np.log10(df['Nodes (N)'].min()), np.log10(df['Nodes (N)'].max())])
y_rombach = intercept_rombach + slope_rombach * x_rombach_log
x_rombach = 10 ** x_rombach_log  # Convert back to original scale for plotting
plt.plot(x_rombach, y_rombach, '--', color=rombach_color, alpha=0.7)

# For Cucuringu
slope_cucuringu, intercept_cucuringu, r_value_cucuringu, p_value_cucuringu, std_err_cucuringu = stats.linregress(
    np.log10(df['Nodes (N)']), df['LowRankCore Pattern Match'])  # Using log scale for fit
x_cucuringu_log = np.array([np.log10(df['Nodes (N)'].min()), np.log10(df['Nodes (N)'].max())])
y_cucuringu = intercept_cucuringu + slope_cucuringu * x_cucuringu_log
x_cucuringu = 10 ** x_cucuringu_log  # Convert back to original scale for plotting
plt.plot(x_cucuringu, y_cucuringu, '--', color=cucuringu_color, alpha=0.7)

# Log scale for x-axis due to the wide range of network sizes
plt.xscale('log')
plt.xlim(df['Nodes (N)'].min() * 0.8, df['Nodes (N)'].max() * 1.2)
plt.ylim(30, 105)  # Ensure y-axis captures all values with some padding

# Add titles and labels
plt.title('Vzťah veľkosti siete a Pattern Match (optimálne parametre)', fontsize=14)
plt.xlabel('Počet uzlov N (log scale)', fontsize=12)
plt.ylabel('Pattern Match (%)', fontsize=12)
plt.legend(fontsize=10, title="Algoritmus")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Figures/network_size_vs_pattern_match.png', dpi=300)

print("Visualizations have been saved to the 'Figures' directory.") 