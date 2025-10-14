"""
Bokeh Full Network Graph Example

Shows the complete StackOverflow network of programming languages and technologies
using Kamada-Kawai layout. Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory

print("🐍 Starting Full Network Graph example...")

# Load data using shared DataLoader (will be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Compute node attributes
factory.compute_node_degrees(G)
factory.compute_adjusted_node_sizes(G, adjustment=10)

# Create and embed visualization with Kamada-Kawai layout
plot = factory.create_network_plot(
    G,
    title="StackOverflow Networks - Full Graph (Kamada-Kawai Layout)",
    layout='kamada_kawai',
    height=400
)

factory.embed(plot, "network-full-output")

print("✅ Full network graph rendered successfully!")
