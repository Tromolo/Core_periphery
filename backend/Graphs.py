import networkx as nx
from networkx.generators.community import stochastic_block_model


def generate_synthetic_graphs():
    graphs = {
        "Star Graph": nx.star_graph(n=20),
        "Core-Periphery SBM": stochastic_block_model(
            sizes=[10, 20], p=[[0.8, 0.1], [0.1, 0.05]]
        ),
        "Barabási-Albert Graph": nx.barabasi_albert_graph(n=50, m=2),
        "Erdős-Rényi Graph": nx.erdos_renyi_graph(n=30, p=0.1),
    }
    return graphs
"""graphs = generate_synthetic_graphs()

for name, graph in graphs.items():
    print(f"Processing {name}...")

    # Rombach
    rombach_core, _ = process_graph_with_rombach(graph)
    visualize_core_periphery(
        graph, rombach_core, f"Rombach Core-Periphery: {name}", f"rombach_{name}.png"
    )

    # Holme
    holme_core, _ = process_graph_with_holme(graph)
    visualize_core_periphery(
        graph, holme_core, f"Holme Core-Periphery: {name}", f"holme_{name}.png"
    )

    # Borgatti-Everett
    be_core, _ = process_graph_with_be(graph)
    visualize_core_periphery(
        graph, be_core, f"Borgatti Everett Core-Periphery: {name}", f"be_{name}.png"
    )

    print(f"Visualizations for {name} saved.")"""
