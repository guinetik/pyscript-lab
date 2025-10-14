"""
Bokeh Community Size Comparison Example

Shows a bar chart comparing the sizes of all detected communities.
Reveals the distribution of technology clusters - some large ecosystems,
many smaller specialized niches. Uses shared DataLoader and BokehFactory.

Author: Guinetik
"""

from lib.data import load_network_data
from bokeh_utils import NetworkGraphFactory, BokehFactory
from bokeh.models import ColumnDataSource
from bokeh.transform import linear_cmap
from bokeh.palettes import Turbo256

print("🐍 Starting Community Comparison Chart example...")

# Load data using shared DataLoader (should be cached!)
data = load_network_data("stackoverflow_network")
nodes_df = data['nodes']
edges_df = data['edges']

# Create factory and build graph
graph_factory = NetworkGraphFactory()
G = graph_factory.build_graph(nodes_df, edges_df)

# Detect communities
communities, modularity, node_to_community = graph_factory.detect_communities(G)
num_communities = len(communities)
community_sizes = [len(c) for c in communities]

# Prepare data for bar chart
comm_data = {
    'community': [f"Community {i+1}" for i in range(num_communities)],
    'size': community_sizes,
    'community_id': list(range(num_communities))
}
source = ColumnDataSource(comm_data)

# Create bar chart using BokehFactory
bokeh_factory = BokehFactory()
p = bokeh_factory.create_figure(
    title="Community Size Comparison",
    height=400,
    sizing_mode='stretch_width',
    tools="hover,pan,wheel_zoom,save,reset",
    tooltips=[("Community", "@community"), ("Size", "@size nodes")],
    x_range=comm_data['community']
)

p.vbar(
    x='community',
    top='size',
    width=0.8,
    source=source,
    line_color='white',
    fill_color=linear_cmap('community_id', Turbo256, 0, num_communities)
)

# Configure axes
p.xgrid.grid_line_color = None
p.y_range.start = 0
p.xaxis.axis_label = 'Community'
p.yaxis.axis_label = 'Number of Nodes'
p.xaxis.major_label_orientation = "vertical"

bokeh_factory.embed(p, "community-comparison-output")

print("✅ Community comparison chart rendered successfully!")
