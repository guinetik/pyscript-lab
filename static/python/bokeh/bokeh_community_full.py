"""
Bokeh Full Network with Communities Example

Shows the complete StackOverflow network colored by detected communities.
Uses greedy modularity optimization to identify technology clusters.
Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory
from bokeh.palettes import Turbo256

print("🐍 Starting Full Network with Communities example...")

# Load data using shared DataLoader (will be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Compute basic node attributes
factory.compute_node_degrees(G)

# Detect communities
communities, modularity, node_to_community = factory.detect_communities(G)
num_communities = len(communities)

# Create and embed visualization with community coloring
plot = factory.create_network_plot(
    G,
    title=f"StackOverflow Communities (Modularity: {modularity:.3f}, {num_communities} communities)",
    layout='kamada_kawai',
    height=600
)

# Override default tooltips to include community
plot.hover.tooltips = [
    ("Name", "@name"),
    ("Community", "@community"),
    ("Degree", "@degree")
]

factory.embed(plot, "community-full-output")

print("✅ Full network with communities rendered successfully!")
