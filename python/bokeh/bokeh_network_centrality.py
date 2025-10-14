"""
Bokeh Eigenvector Centrality Network Graph Example

Visualizes node influence using eigenvector centrality. Node size represents
how influential/central each technology is in the network. More central nodes
are connected to other important nodes. Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory

print("🐍 Starting Eigenvector Centrality Graph example...")

# Load data using shared DataLoader (should be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Compute eigenvector centrality
print("🐍 Computing eigenvector centrality...")
try:
    centrality = nx.eigenvector_centrality(G, max_iter=1000)
except:
    # Fallback to numpy version if regular version fails
    centrality = nx.eigenvector_centrality_numpy(G)

nx.set_node_attributes(G, name='centrality', values=centrality)

# Get centrality range
centrality_values = list(centrality.values())
min_cent = min(centrality_values)
max_cent = max(centrality_values)
print(f"🐍 Centrality range: {min_cent:.4f} to {max_cent:.4f}")

# Override nodesize with centrality-based sizes
centrality_as_nodesize = {}
for node in G.nodes():
    cent = centrality[node]
    # Normalize and scale to 1-100 range
    normalized = (cent - min_cent) / (max_cent - min_cent) if max_cent > min_cent else 0.5
    centrality_as_nodesize[node] = 1 + (normalized * 99)

nx.set_node_attributes(G, centrality_as_nodesize, 'nodesize')

# Compute degrees for tooltip
factory.compute_node_degrees(G)

# Create and embed visualization
plot = factory.create_network_plot(
    G,
    title="StackOverflow Networks - Eigenvector Centrality (size = influence)",
    layout='spring',
    height=400
)

factory.embed(plot, "network-centrality-output")

print("✅ Eigenvector centrality graph rendered successfully!")
