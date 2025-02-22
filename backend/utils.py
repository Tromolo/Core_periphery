from collections import Counter, defaultdict

import matplotlib as mpl
import networkx as nx
import numba
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from scipy import sparse
from typing import Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def to_adjacency_matrix(net):
    if sparse.issparse(net):
        if type(net) == "scipy.sparse.csr.csr_matrix":
            return net
        return sparse.csr_matrix(net, dtype=np.float64), np.arange(net.shape[0])
    elif "networkx" in "%s" % type(net):
        return (
            sparse.csr_matrix(nx.adjacency_matrix(net), dtype=np.float64),
            net.nodes(),
        )
    elif "numpy.ndarray" == type(net):
        return sparse.csr_matrix(net, dtype=np.float64), np.arange(net.shape[0])


def to_nxgraph(net):
    if sparse.issparse(net):
        return nx.from_scipy_sparse_matrix(net)
    elif "networkx" in "%s" % type(net):
        return net
    elif "numpy.ndarray" == type(net):
        return nx.from_numpy_array(net)


def set_node_colors(c, x, cmap, colored_nodes):

    node_colors = defaultdict(lambda x: "#8d8d8d")
    node_edge_colors = defaultdict(lambda x: "#4d4d4d")

    cnt = Counter([c[d] for d in colored_nodes])
    num_groups = len(cnt)

    # Set up the palette
    if cmap is None:
        if num_groups <= 10:
            cmap = sns.color_palette().as_hex()
        elif num_groups <= 20:
            cmap = sns.color_palette("tab20").as_hex()
        else:
            cmap = sns.color_palette("hls", num_groups).as_hex()

    # Calc size of groups
    cmap = dict(
        zip(
            [d[0] for d in cnt.most_common(num_groups)],
            [cmap[i] for i in range(num_groups)],
        )
    )
    bounds = np.linspace(0, 1, 11)
    norm = mpl.colors.BoundaryNorm(bounds, ncolors=12, extend="both")

    # Calculate the color for each node using the palette
    cmap_coreness = {
        k: sns.light_palette(v, n_colors=12).as_hex() for k, v in cmap.items()
    }
    cmap_coreness_dark = {
        k: sns.dark_palette(v, n_colors=12).as_hex() for k, v in cmap.items()
    }

    for d in colored_nodes:
        node_colors[d] = cmap_coreness[c[d]][norm(x[d]) - 1]
        node_edge_colors[d] = cmap_coreness_dark[c[d]][-norm(x[d])]
    return node_colors, node_edge_colors


def classify_nodes(G, c, x, max_num=None):
    non_residuals = [d for d in G.nodes() if (c[d] is not None) and (x[d] is not None)]
    residuals = [d for d in G.nodes() if (c[d] is None) or (x[d] is None)]

    # Count the number of groups
    cnt = Counter([c[d] for d in non_residuals])
    cvals = np.array([d[0] for d in cnt.most_common(len(cnt))])

    if max_num is not None:
        cvals = set(cvals[:max_num])
    else:
        cvals = set(cvals)

    #
    colored_nodes = [d for d in non_residuals if c[d] in cvals]
    muted = [d for d in non_residuals if not c[d] in cvals]

    # Bring core nodes to front
    order = np.argsort([x[d] for d in colored_nodes])
    colored_nodes = [colored_nodes[d] for d in order]

    return colored_nodes, muted, residuals


def calc_node_pos(G, layout_algorithm):
    if layout_algorithm is None:
        return nx.spring_layout(G)
    else:
        return layout_algorithm(G)

def draw(
    G,
    c,
    x,
    ax,
    draw_edge=True,
    font_size=0,
    pos=None,
    cmap=None,
    max_group_num=None,
    draw_nodes_kwd={},
    draw_edges_kwd={"edge_color": "#adadad"},
    draw_labels_kwd={},
    layout_algorithm=None,
):
    """Plot the core-periphery structure in the networks.

    :param G: Graph
    :type G:  networkx.Graph
    :param c: dict
    :type c: group membership c[i] of i
    :param x: core (x[i])=1 or periphery (x[i]=0)
    :type x: dict
    :param ax: axis
    :type ax: matplotlib.pyplot.ax
    :param draw_edge: whether to draw edges, defaults to True
    :type draw_edge: bool, optional
    :param font_size: font size for node labels, defaults to 0
    :type font_size: int, optional
    :param pos: pos[i] is the xy coordinate of node i, defaults to None
    :type pos: dict, optional
    :param cmap: colomap defaults to None
    :type cmap: matplotlib.cmap, optional
    :param max_group_num: Number of groups to color, defaults to None
    :type max_group_num: int, optional
    :param draw_nodes_kwd: Parameter for networkx.draw_networkx_nodes, defaults to {}
    :type draw_nodes_kwd: dict, optional
    :param draw_edges_kwd: Parameter for networkx.draw_networkx_edges, defaults to {"edge_color": "#adadad"}
    :type draw_edges_kwd: dict, optional
    :param draw_labels_kwd: Parameter for networkx.draw_networkx_labels, defaults to {}
    :type draw_labels_kwd: dict, optional
    :param layout_kwd: layout keywords, defaults to {}
    :type layout_kwd: dict, optional
    :return: (ax, pos)
    :rtype: matplotlib.pyplot.ax, dict
    """

    """default_c = max(c.values()) + 1 if c else 0
    default_x = 0  # Default to periphery (0)

    c = {node: c.get(node, default_c) for node in G.nodes()}
    x = {node: x.get(node, default_x) for node in G.nodes()}"""
    # Split node into residual and non-residual
    colored_nodes, muted_nodes, residuals = classify_nodes(G, c, x, max_group_num)

    node_colors, node_edge_colors = set_node_colors(c, x, cmap, colored_nodes)

    # Set the position of nodes
    if pos is None:
        pos = calc_node_pos(G, layout_algorithm)

    # Draw
    nodes = nx.draw_networkx_nodes(
        G,
        pos,
        node_color=[node_colors[d] for d in colored_nodes],
        nodelist=colored_nodes,
        ax=ax,
        # zorder=3,
        **draw_nodes_kwd
    )
    if nodes is not None:
        nodes.set_zorder(3)
        nodes.set_edgecolor([node_edge_colors[r] for r in colored_nodes])

    draw_nodes_kwd_residual = draw_nodes_kwd.copy()
    draw_nodes_kwd_residual["node_size"] = 0.1 * draw_nodes_kwd.get("node_size", 100)
    nodes = nx.draw_networkx_nodes(
        G,
        pos,
        node_color="#efefef",
        nodelist=residuals,
        node_shape="s",
        ax=ax,
        **draw_nodes_kwd_residual
    )
    if nodes is not None:
        nodes.set_zorder(1)
        nodes.set_edgecolor("#4d4d4d")

    if draw_edge:
        nx.draw_networkx_edges(
            G.subgraph(colored_nodes + residuals), pos, ax=ax, **draw_edges_kwd
        )

    if font_size > 0:
        if "font_size" not in draw_labels_kwd:
            draw_labels_kwd["font_size"] = font_size
        nx.draw_networkx_labels(G, pos, ax=ax, **draw_labels_kwd)

    ax.axis("off")

    return ax, pos


def draw_interactive(G, c, x, hover_text=None, node_size=10.0, pos=None, cmap=None):
    try:        
        if pos is None:
            pos = nx.spring_layout(G)

        node_trace = {
            'x': [],
            'y': [],
            'text': [],
            'mode': 'markers',
            'hoverinfo': 'text',
            'marker': {
                'size': [],
                'color': [],
                'line': {'color': [], 'width': 1}
            }
        }

        for node in G.nodes():
            x_pos, y_pos = pos[node]
            node_trace['x'].append(x_pos)
            node_trace['y'].append(y_pos)
            
            size = (x[node] + 1) * node_size
            node_trace['marker']['size'].append(size)
            
            color = 'red' if c[node] == 1 else 'blue'
            node_trace['marker']['color'].append(color)
            
            node_trace['text'].append(f'Node: {node}<br>Core: {c[node]}<br>Coreness: {x[node]}')

        figure = {
            'data': [node_trace],
            'layout': {
                'showlegend': False,
                'hovermode': 'closest',
                'margin': {'b': 20, 'l': 20, 'r': 20, 't': 20},
                'xaxis': {'showgrid': False, 'zeroline': False, 'showticklabels': False},
                'yaxis': {'showgrid': False, 'zeroline': False, 'showticklabels': False},
                'width': 800,
                'height': 800
            }
        }
        
        print("Debug - Successfully created figure")
        return figure

    except Exception as e:
        print(f"Error in draw_interactive: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def save_visualization(graph: nx.Graph, classifications: Dict, output_file: str, title: Optional[str] = None) -> None:
    """
    Save graph visualization to a file using the draw function.
    
    Args:
        graph: NetworkX graph object
        classifications: Dictionary of node classifications (C/P)
        output_file: Path to save the image file
        title: Optional title for the plot
    """

    c = {node: 1 if type == 'C' else 0 for node, type in classifications.items()}
    x = {node: 1.0 if type == 'C' else 0.0 for node, type in classifications.items()}
    
    # Create figure and axis
    plt.figure(figsize=(12, 8))
    ax = plt.gca()
    
    colored_nodes, _, _ = classify_nodes(graph, c, x)
    node_colors, node_edge_colors = set_node_colors(c, x, None, colored_nodes)
    
    core_node = next((node for node in colored_nodes if c[node] == 1), None)
    periphery_node = next((node for node in colored_nodes if c[node] == 0), None)
    
    draw(G=graph, 
         c=c, 
         x=x, 
         ax=ax,
         font_size=8,
         draw_nodes_kwd={'node_size': 500},
         draw_labels_kwd={'font_weight': 'bold'})
    
    if title:
        plt.title(title)
    
    legend_elements = [
        Patch(facecolor=node_colors[core_node] if core_node else '#ff7f7f',
              edgecolor=node_edge_colors[core_node] if core_node else '#8b0000',
              label='Core'),
        Patch(facecolor=node_colors[periphery_node] if periphery_node else '#7f7fff',
              edgecolor=node_edge_colors[periphery_node] if periphery_node else '#00008b',
              label='Periphery')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close()