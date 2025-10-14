"""
Bokeh Programming Languages Network Graph Example

Shows a subgraph focused on major programming languages and their connected
technologies. Reveals which tools and frameworks are commonly associated with
each language. Uses shared DataLoader and NetworkGraphFactory.

Author: Guinetik
"""

import networkx as nx
from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory

print("🐍 Starting Programming Languages Graph example...")

# Load data using shared DataLoader (should be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
factory = NetworkGraphFactory()
G = factory.build_graph(nodes_df, edges_df)

# Define major programming languages to analyze
print("🐍 Extracting programming language network...")
major_languages = [
    'c', 'c++', 'c#', 'java', 'python', 'ruby',
    'scala', 'haskell', 'javascript', 'sql'
]

# Collect all nodes connected to these languages
p_language_nodes = []
for language in major_languages:
    if language in G:
        neighbors = G.neighbors(language)
        p_language_nodes.extend(neighbors)

# Create subgraph
language_graph = G.subgraph(set(p_language_nodes))
print(f"🐍 Language subgraph: {len(language_graph.nodes())} nodes")

# Compute node attributes for subgraph
factory.compute_node_degrees(language_graph)
adjusted = {
    node: degree * 5
    for node, degree in nx.degree(language_graph)
}
nx.set_node_attributes(language_graph, name='node_size', values=adjusted)

# Create and embed visualization
plot = factory.create_network_plot(
    language_graph,
    title="StackOverflow Networks - Programming Languages",
    layout='spring',
    height=400
)

factory.embed(plot, "network-languages-output")

print("✅ Programming languages graph rendered successfully!")
