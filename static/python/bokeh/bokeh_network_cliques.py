"""
Bokeh Cliques Network Graph Example

Shows the largest cliques in the StackOverflow network. A clique is a group
where every node is connected to every other node - revealing tightly related
technologies. Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory

print("🐍 Starting Cliques Graph example...")

# Load data using shared DataLoader (should be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Find and analyze cliques
print("🐍 Analyzing cliques...")
cliques = list(nx.find_cliques(G))
print(f"🐍 Found {len(cliques)} cliques")

# Sort cliques by size and get the largest ones
sorted_cliques = sorted(cliques, key=len)

# Collect nodes from the 3 largest cliques
max_clique_nodes = set()
for nodelist in sorted_cliques[-4:-1]:
    for node in nodelist:
        max_clique_nodes.add(node)

# Create subgraph
max_clique = G.subgraph(max_clique_nodes)
print(f"🐍 Clique subgraph: {len(max_clique.nodes())} nodes, {len(max_clique.edges())} edges")

# Compute node attributes for subgraph
factory.compute_node_degrees(max_clique)
factory.compute_adjusted_node_sizes(max_clique, adjustment=15)

# Create and embed visualization
plot = factory.create_network_plot(
    max_clique,
    title="StackOverflow Networks - Largest Cliques",
    layout='spring',
    height=400
)

factory.embed(plot, "network-cliques-output")

print("✅ Cliques graph rendered successfully!")
