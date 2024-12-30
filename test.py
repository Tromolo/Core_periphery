import networkx as nx
import pandas as pd
import time
import main


df = pd.read_csv('large_random_graph_edges.csv', names=['source', 'target'])
G_large = nx.from_pandas_edgelist(df, source='source', target='target')
G_large = nx.convert_node_labels_to_integers(G_large)


start_time = time.time()
core, periphery = main.detect_core_periphery_by_degree(G_large, threshold=5)
end_time = time.time()
print(f"Core-periphery detection time for 100,000 node graph: {end_time - start_time} seconds")

start_time = time.time()
core2, periphery2 = main.modularity_core_periphery_detection(G_large)
end_time = time.time()
print(f"Modularity core-periphery detection time for 100,000 node graph: {end_time - start_time} seconds")



print("HVIEZDA")
G_star = nx.star_graph(n=4)

core_deg, periph_deg = main.detect_core_periphery_by_degree(G_star, threshold=2)
core_mod, periph_mod = main.modularity_core_periphery_detection(G_star)
coeff_deg = main.compute_core_periphery_coefficient(G_star, core_deg, periph_deg)
coeff_mod = main.compute_core_periphery_coefficient(G_star, core_mod, periph_mod)

print("Počet uzlov:", G_star.number_of_nodes())
print("Stupne uzlov:", dict(G_star.degree()))
print("Jadro (degree-based):", core_deg)
print("Periféria (degree-based):", periph_deg)
print("Koeficient (degree-based):", coeff_deg)
print("Jadro (modularity-based):", core_mod)
print("Periféria (modularity-based):", periph_mod)
print("Koeficient (modularity-based):", coeff_mod)
print()


print("JEDEN UZOL")
G_single = nx.Graph()
G_single.add_node("A")

core_deg_s, periph_deg_s = main.detect_core_periphery_by_degree(G_single, threshold=1)
core_mod_s, periph_mod_s = main.modularity_core_periphery_detection(G_single)
coeff_deg_s = main.compute_core_periphery_coefficient(G_single, core_deg_s, periph_deg_s)
coeff_mod_s = main.compute_core_periphery_coefficient(G_single, core_mod_s, periph_mod_s)

print("Počet uzlov:", G_single.number_of_nodes())
print("Stupne uzlov:", dict(G_single.degree()))
print("Jadro (degree-based):", core_deg_s)
print("Periféria (degree-based):", periph_deg_s)
print("Koeficient (degree-based):", coeff_deg_s)
print("Jadro (modularity-based):", core_mod_s)
print("Periféria (modularity-based):", periph_mod_s)
print("Koeficient (modularity-based):", coeff_mod_s)
print()


print("PRAZDNY GRAF")
G_empty = nx.Graph()

core_deg_e, periph_deg_e = main.detect_core_periphery_by_degree(G_empty, threshold=1)
core_mod_e, periph_mod_e = main.modularity_core_periphery_detection(G_empty)
coeff_deg_e = main.compute_core_periphery_coefficient(G_empty, core_deg_e, periph_deg_e)
coeff_mod_e = main.compute_core_periphery_coefficient(G_empty, core_mod_e, periph_mod_e)

print("Počet uzlov:", G_empty.number_of_nodes())
print("Jadro (degree-based):", core_deg_e)
print("Periféria (degree-based):", periph_deg_e)
print("Koeficient (degree-based):", coeff_deg_e)
print("Jadro (modularity-based):", core_mod_e)
print("Periféria (modularity-based):", periph_mod_e)
print("Koeficient (modularity-based):", coeff_mod_e)


G_small = nx.erdos_renyi_graph(n=1000, p=0.01)
G_medium = nx.erdos_renyi_graph(n=5000, p=0.01)
G_large = nx.erdos_renyi_graph(n=10000, p=0.01)

# DEGREE-BASED
start_time = time.time()
core_small, periphery_small = main.detect_core_periphery_by_degree(G_small, threshold=10)
end_time = time.time()
print(f"Core-periphery detection for small graph (1000 nodes): Core size={len(core_small)}, Periphery size={len(periphery_small)}")
print(f"Degree-based detection time for small graph: {end_time - start_time} seconds")

start_time = time.time()
core_medium, periphery_medium = main.detect_core_periphery_by_degree(G_medium, threshold=10)
end_time = time.time()
print(f"Core-periphery detection for medium graph (5000 nodes): Core size={len(core_medium)}, Periphery size={len(periphery_medium)}")
print(f"Degree-based detection time for medium graph: {end_time - start_time} seconds")

start_time = time.time()
core_large, periphery_large = main.detect_core_periphery_by_degree(G_large, threshold=10)
end_time = time.time()
print(f"Core-periphery detection for large graph (10000 nodes): Core size={len(core_large)}, Periphery size={len(periphery_large)}")
print(f"Degree-based detection time for large graph: {end_time - start_time} seconds")

# MODULATIRY-BASED
start_time = time.time()
core_small_mod, periphery_small_mod = main.modularity_core_periphery_detection(G_small)
end_time = time.time()
print(f"Modularity core-periphery detection for small graph (1000 nodes): Core size={len(core_small_mod)}, Periphery size={len(periphery_small_mod)}")
print(f"Modularity detection time for small graph: {end_time - start_time} seconds")

start_time = time.time()
core_medium_mod, periphery_medium_mod = main.modularity_core_periphery_detection(G_medium)
end_time = time.time()
print(f"Modularity core-periphery detection for medium graph (5000 nodes): Core size={len(core_medium_mod)}, Periphery size={len(periphery_medium_mod)}")
print(f"Modularity detection time for medium graph: {end_time - start_time} seconds")

start_time = time.time()
core_large_mod, periphery_large_mod = main.modularity_core_periphery_detection(G_large)
end_time = time.time()
print(f"Modularity core-periphery detection for large graph (10000 nodes): Core size={len(core_large_mod)}, Periphery size={len(periphery_large_mod)}")
print(f"Modularity detection time for large graph: {end_time - start_time} seconds")