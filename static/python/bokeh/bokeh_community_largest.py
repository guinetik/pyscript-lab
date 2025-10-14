"""
Bokeh Largest Community Example

Shows a detailed view of the largest detected community with nodes colored
by degree (connectivity). Reveals the internal structure of the biggest
technology cluster. Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory
from bokeh.palettes import Category20_20
from bokeh.models import Circle as CircleGlyph
from bokeh.transform import linear_cmap

print("🐍 Starting Largest Community example...")

# Load data using shared DataLoader (should be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Detect communities
communities, modularity, node_to_community = factory.detect_communities(G)

# Get largest community subgraph
largest_subgraph = factory.get_largest_community(G, communities)
largest_size = len(largest_subgraph.nodes())

# Sample some member names
sample_nodes = list(largest_subgraph.nodes())[:10]
print(f"🐍 Sample members: {', '.join(sample_nodes)}")

# Get degree range for color mapping
degrees = dict(nx.degree(largest_subgraph))
min_degree = min(degrees.values())
max_degree = max(degrees.values())

# Create network plot
plot = factory.create_network_plot(
    largest_subgraph,
    title=f"Largest Community ({largest_size} nodes)",
    layout='kamada_kawai',
    height=600
)

# Override node coloring to use degree instead of group
from bokeh.plotting import from_networkx
pos = nx.kamada_kawai_layout(largest_subgraph)
network_graph = from_networkx(largest_subgraph, pos)

factory.compute_node_radii(largest_subgraph)
network_graph.node_renderer.glyph = CircleGlyph(
    radius='radius',
    fill_color=linear_cmap('degree', Category20_20, min_degree, max_degree)
)

# Replace the renderer
plot.renderers[0] = network_graph

factory.embed(plot, "community-largest-output")

print("✅ Largest community rendered successfully!")
