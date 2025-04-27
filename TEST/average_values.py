import pandas as pd

data = pd.read_csv('TEST/results/stability_be/be_stability_results.csv')

df = pd.DataFrame(data)

small_networks = ['Karate Club', 'Dolphins', 'Les Miserables']
medium_networks = ['Football', 'YeastL']
large_networks = ['Facebook Combined', 'Power Grid', 'Bianconi-0.7', 'Bianconi-0.97']

small_df = df[df['network'].isin(small_networks)]
medium_df = df[df['network'].isin(medium_networks)]
large_df = df[df['network'].isin(large_networks)]

small_network_means = small_df.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means = medium_df.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
large_network_means = large_df.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values = small_network_means.mean()
medium_average_values = medium_network_means.mean()
large_average_values = large_network_means.mean()

print("Small networks average values:")
print(small_average_values)
print("\nMedium networks average values:")
print(medium_average_values)
print("\nLarge networks average values:")
print(large_average_values)

data_rombach = pd.read_csv('TEST/results/stability_rombach/rombach_stability_results.csv')

df_rombach = pd.DataFrame(data_rombach)

small_df_rombach = df_rombach[df_rombach['network'].isin(small_networks)]
medium_df_rombach = df_rombach[df_rombach['network'].isin(medium_networks)]
large_df_rombach = df_rombach[df_rombach['network'].isin(large_networks)]

small_network_means_rombach = small_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means_rombach = medium_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
large_network_means_rombach = large_df_rombach.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values_rombach = small_network_means_rombach.mean()
medium_average_values_rombach = medium_network_means_rombach.mean()
large_average_values_rombach = large_network_means_rombach.mean()

print("Small networks average values:")
print(small_average_values_rombach)
print("\nMedium networks average values:")
print(medium_average_values_rombach)
print("\nLarge networks average values:")
print(large_average_values_rombach)


data_cucuringu = pd.read_csv('TEST/results/stability_cucuringu/cucuringu_stability_results.csv')

df_cucuringu = pd.DataFrame(data_cucuringu)

small_df_cucuringu = df_cucuringu[df_cucuringu['network'].isin(small_networks)]
medium_df_cucuringu = df_cucuringu[df_cucuringu['network'].isin(medium_networks)]
large_df_cucuringu = df_cucuringu[df_cucuringu['network'].isin(large_networks)]

small_network_means_cucuringu = small_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
medium_network_means_cucuringu = medium_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()
large_network_means_cucuringu = large_df_cucuringu.groupby('network')[['metrics.ideal_pattern_match', 'metrics.core_percentage', 'runtime']].mean()

small_average_values_cucuringu = small_network_means_cucuringu.mean()
medium_average_values_cucuringu = medium_network_means_cucuringu.mean()
large_average_values_cucuringu = large_network_means_cucuringu.mean()

print("Small networks average values:")
print(small_average_values_cucuringu)
print("\nMedium networks average values:")
print(medium_average_values_cucuringu)
print("\nLarge networks average values:")
print(large_average_values_cucuringu)
