import pandas as pd

data = pd.read_csv('TEST/results/stability_be/be_stability_results.csv')
df = pd.DataFrame(data)

small_networks = ['Karate Club', 'Dolphins', 'Les Miserables']
medium_networks = ['Football', 'YeastL']
large_networks = ['Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97']

small_df = df[(df['network'].isin(small_networks)) & (df['parameters.num_runs'] >= 10) & (df['parameters.num_runs'] <= 20)]
medium_df = df[(df['network'].isin(medium_networks)) & (df['parameters.num_runs'] >= 5) & (df['parameters.num_runs'] <= 10)]

small_network_means = small_df.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means = medium_df.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values = small_network_means.mean()
medium_average_values = medium_network_means.mean()

print("BE ALGORITHM RESULTS WITH RECOMMENDED PARAMETERS")
print("Small networks average values (num_runs = 10-20):")
print(small_average_values)
print("\nMedium networks average values (num_runs = 5-10):")
print(medium_average_values)
print("\n" + "-"*50 + "\n")

data_rombach = pd.read_csv('TEST/results/stability_rombach/rombach_stability_results.csv')
df_rombach = pd.DataFrame(data_rombach)

df_rombach_filtered = df_rombach[
    (df_rombach['parameters.beta'] == 0.9) & 
    (df_rombach['parameters.alpha'] >= 0.5) & 
    (df_rombach['parameters.alpha'] <= 0.9) & 
    (df_rombach['parameters.num_runs'] == 5)
]

small_df_rombach = df_rombach_filtered[df_rombach_filtered['network'].isin(small_networks)]
medium_df_rombach = df_rombach_filtered[df_rombach_filtered['network'].isin(medium_networks)]
large_df_rombach = df_rombach_filtered[df_rombach_filtered['network'].isin(large_networks)]

small_network_means_rombach = small_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means_rombach = medium_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
large_network_means_rombach = large_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values_rombach = small_network_means_rombach.mean()
medium_average_values_rombach = medium_network_means_rombach.mean()
large_average_values_rombach = large_network_means_rombach.mean()

print("ROMBACH ALGORITHM RESULTS WITH RECOMMENDED PARAMETERS")
print("Parameters: β = 0.9, α = 0.5-0.9, num_runs = 5")
print("Small networks average values:")
print(small_average_values_rombach)
print("\nMedium networks average values:")
print(medium_average_values_rombach)
print("\nLarge networks average values:")
print(large_average_values_rombach)
print("\n" + "-"*50 + "\n")

data_cucuringu = pd.read_csv('TEST/results/stability_cucuringu/cucuringu_stability_results.csv')
df_cucuringu = pd.DataFrame(data_cucuringu)

df_cucuringu_filtered = df_cucuringu[df_cucuringu['parameters.beta'] == 0.1]

small_df_cucuringu = df_cucuringu_filtered[df_cucuringu_filtered['network'].isin(small_networks)]
medium_df_cucuringu = df_cucuringu_filtered[df_cucuringu_filtered['network'].isin(medium_networks)]
large_df_cucuringu = df_cucuringu_filtered[df_cucuringu_filtered['network'].isin(large_networks)]

small_network_means_cucuringu = small_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means_cucuringu = medium_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
large_network_means_cucuringu = large_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values_cucuringu = small_network_means_cucuringu.mean()
medium_average_values_cucuringu = medium_network_means_cucuringu.mean()
large_average_values_cucuringu = large_network_means_cucuringu.mean()

print("CUCURINGU (LOWRANKCORE) ALGORITHM RESULTS WITH RECOMMENDED PARAMETERS")
print("Parameters: beta = 0.1 (maximizing pattern match)")
print("Small networks average values:")
print(small_average_values_cucuringu)
print("\nMedium networks average values:")
print(medium_average_values_cucuringu)
print("\nLarge networks average values:")
print(large_average_values_cucuringu)

