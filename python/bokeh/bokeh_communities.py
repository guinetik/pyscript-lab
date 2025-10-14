"""
Community Detection in StackOverflow Networks

This module demonstrates community detection algorithms using NetworkX and Bokeh
in PyScript. Communities are groups of nodes that are more densely connected to
each other than to the rest of the network.

This example creates three visualizations:
1. Full Network with Communities - All nodes colored by detected community
2. Largest Community - Detailed view of the biggest community
3. Community Size Comparison - Bar chart showing relative community sizes

These examples showcase:
- Community detection using greedy modularity optimization
- Network modularity metrics
- Multiple coordinated visualizations
- Interactive network graphs with Bokeh
- Kamada-Kawai layout algorithm

Author: Guinetik
"""

from pyodide.http import open_url
from js import Bokeh, console, JSON
from typing import List, Dict, Set, Tuple, Optional

import networkx as nx
import pandas as pd
import json

from bokeh.embed import json_item
from bokeh.plotting import from_networkx, figure
from bokeh.models import Circle as CircleGlyph, ColumnDataSource
from bokeh.palettes import Category20_20, Turbo256, Spectral11
from bokeh.transform import linear_cmap
import networkx.algorithms.community as nx_comm


class BokehCommunityDetection:
    """
    A comprehensive community detection and visualization class using NetworkX and Bokeh.

    This class loads StackOverflow tag network data, detects communities using
    greedy modularity optimization, and creates three interactive visualizations
    to explore the community structure.

    Features:
    - Automated community detection
    - Modularity score calculation
    - Three coordinated visualizations
    - Interactive tooltips and tools
    - Kamada-Kawai layout for clear structure
    - Node sizes proportional to activity

    Attributes:
        nodes_url (str): Path to the nodes CSV file.
        edges_url (str): Path to the edges CSV file.
        G (nx.Graph): The main NetworkX graph object.
        nodes_df (pd.DataFrame): DataFrame containing node data.
        edges_df (pd.DataFrame): DataFrame containing edge data.
        communities (List[Set]): List of detected communities (sets of nodes).
        modularity (float): Modularity score of the community partition.
        node_to_community (Dict): Mapping of node names to community IDs.
    """

    # Hover tooltip configuration
    HOVER_TOOLTIPS = [
        ("Name", "@name"),
        ("Community", "@community"),
        ("Degree", "@degree")
    ]

    # Standard Bokeh tools
    TOOLS = "pan,wheel_zoom,save,reset"

    def __init__(
        self,
        nodes_url: str = "/data/stack_network_nodes.csv",
        edges_url: str = "/data/stack_network_links.csv"
    ):
        """
        Initialize the BokehCommunityDetection visualizer.

        Args:
            nodes_url (str, optional): Path to the nodes CSV file.
                                      Defaults to "/data/stack_network_nodes.csv".
            edges_url (str, optional): Path to the edges CSV file.
                                      Defaults to "/data/stack_network_links.csv".

        Example:
            >>> visualizer = BokehCommunityDetection()
            >>> visualizer.run()
        """
        self.nodes_url = nodes_url
        self.edges_url = edges_url
        self.G = None
        self.nodes_df = None
        self.edges_df = None
        self.communities = None
        self.modularity = None
        self.node_to_community = {}

        print("🐍 BokehCommunityDetection initialized")
        print("🐍 BokehCommunityDetection initialized")

    def _load_data(self):
        """
        Load network data from CSV files.

        This method:
        1. Loads nodes CSV with tag names, groups, and sizes
        2. Loads edges CSV with source-target relationships and weights
        3. Validates the data was loaded successfully
        4. Logs the number of nodes and edges

        Raises:
            Exception: If data loading fails or results in empty DataFrames.
        """
        try:
            print("🐍 Loading StackOverflow network data...")
            print(f"🐍 Loading nodes from: {self.nodes_url}")
            print(f"🐍 Loading edges from: {self.edges_url}")

            self.nodes_df = pd.read_csv(open_url(self.nodes_url))
            self.edges_df = pd.read_csv(open_url(self.edges_url))

            if self.nodes_df.empty or self.edges_df.empty:
                raise ValueError("Loaded DataFrames are empty")

            print(f"🐍 Loaded {len(self.nodes_df)} nodes and {len(self.edges_df)} edges")
            print(f"✅ Data loaded: {len(self.nodes_df)} nodes, {len(self.edges_df)} edges")

        except Exception as e:
            error_msg = f"Failed to load network data: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise

    def _build_graph(self):
        """
        Build the NetworkX graph from loaded data.

        This method:
        1. Creates an empty NetworkX Graph
        2. Adds nodes with attributes (name, group, nodesize)
        3. Adds edges with weights
        4. Computes and sets degree for each node

        Note:
            After this method, self.G contains the complete graph with
            all nodes, edges, and basic attributes.
        """
        print("🐍 Building NetworkX graph...")
        print("🐍 Building graph structure...")

        # Create empty graph
        self.G = nx.Graph()

        # Add nodes with attributes
        for index, row in self.nodes_df.iterrows():
            self.G.add_node(
                row["name"],
                group=row["group"],
                nodesize=row["nodesize"],
                name=row["name"]
            )

        # Add edges with weights
        for index, row in self.edges_df.iterrows():
            self.G.add_edge(row["source"], row["target"], weight=row["value"])

        # Compute and set node degrees
        degrees = dict(nx.degree(self.G))
        nx.set_node_attributes(self.G, name='degree', values=degrees)

        print(f"✅ Graph built: {len(self.G.nodes())} nodes, {len(self.G.edges())} edges")
        print(f"✅ Graph: {len(self.G.nodes())} nodes, {len(self.G.edges())} edges")

    def _detect_communities(self):
        """
        Detect communities using greedy modularity optimization.

        This method:
        1. Runs greedy modularity community detection algorithm
        2. Creates node-to-community mapping
        3. Sets community as node attribute
        4. Calculates modularity score
        5. Logs community statistics

        Note:
            Greedy modularity optimization iteratively merges communities
            to maximize the modularity metric, which measures how well
            the network is divided into communities.
        """
        print("🐍 Detecting communities using greedy modularity...")
        print("🐍 Running community detection algorithm...")

        # Detect communities
        self.communities = list(nx_comm.greedy_modularity_communities(self.G))
        num_communities = len(self.communities)
        print(f"🐍 Found {num_communities} communities!")
        print(f"✅ Detected {num_communities} communities")

        # Create node-to-community mapping
        self.node_to_community = {}
        for comm_id, community in enumerate(self.communities):
            for node in community:
                self.node_to_community[node] = comm_id

        # Set community as node attribute
        nx.set_node_attributes(self.G, self.node_to_community, 'community')

        # Calculate modularity score
        self.modularity = nx_comm.modularity(self.G, self.communities)
        print(f"🐍 Network modularity: {self.modularity:.3f}")
        print(f"✅ Modularity score: {self.modularity:.3f}")

        # Log community sizes
        print("🐍 Community sizes:")
        for i, community in enumerate(self.communities):
            size = len(community)
            print(f"   Community {i+1}: {size} nodes")
            print(f"🐍 Community {i+1}: {size} nodes")

    def _compute_node_radii(self, graph: nx.Graph, min_radius: float = 0.005, max_radius: float = 0.03):
        """
        Compute normalized node radii based on nodesize attribute.

        Args:
            graph (nx.Graph): NetworkX graph with nodesize attributes.
            min_radius (float): Minimum node radius.
            max_radius (float): Maximum node radius.

        Note:
            Sets 'radius' attribute on each node based on normalized nodesize.
        """
        # Get all nodesize values
        nodesizes = [graph.nodes[n].get('nodesize', 1) for n in graph.nodes()]
        min_nodesize = min(nodesizes)
        max_nodesize = max(nodesizes)

        # Normalize and set radius for each node
        radii = {}
        for node in graph.nodes():
            nodesize = graph.nodes[node].get('nodesize', 1)
            # Normalize to 0-1 range, then scale to desired radius range
            if max_nodesize > min_nodesize:
                normalized = (nodesize - min_nodesize) / (max_nodesize - min_nodesize)
            else:
                normalized = 0.5
            radii[node] = min_radius + (normalized * (max_radius - min_radius))

        nx.set_node_attributes(graph, radii, 'radius')
        print(f"🐍 Node radii: {min_radius:.4f} to {max_radius:.4f}")

    def _create_bokeh_graph(
        self,
        graph: nx.Graph,
        title: str,
        color_field: str = 'community',
        color_palette = Turbo256,
        color_min: int = 0,
        color_max: int = None
    ) -> Tuple[any, any]:
        """
        Create a Bokeh network graph renderer from a NetworkX graph.

        This method:
        1. Computes node radii based on nodesize
        2. Uses Kamada-Kawai layout for optimal node placement
        3. Creates Bokeh graph renderer
        4. Configures node appearance (size, color)

        Args:
            graph (nx.Graph): NetworkX graph to visualize.
            title (str): Title for the plot.
            color_field (str, optional): Node attribute to use for coloring.
                                        Defaults to 'community'.
            color_palette: Bokeh color palette. Defaults to Turbo256.
            color_min (int, optional): Minimum value for color mapping. Defaults to 0.
            color_max (int, optional): Maximum value for color mapping.
                                      If None, uses number of communities.

        Returns:
            Tuple[any, any]: A tuple of (bokeh_plot, network_graph_renderer).

        Note:
            Uses Kamada-Kawai layout which optimizes node placement based on
            graph distances for clearer community structure visualization.
        """
        # Compute node radii based on nodesize
        self._compute_node_radii(graph)

        # Use Kamada-Kawai layout for better community structure visualization
        print("🐍 Using Kamada-Kawai layout algorithm...")
        pos = nx.kamada_kawai_layout(graph)

        # Create Bokeh graph from NetworkX
        network_graph = from_networkx(graph, pos)

        # Set default color_max if not provided
        if color_max is None:
            color_max = len(self.communities) if self.communities else 10

        # Set node appearance
        network_graph.node_renderer.glyph = CircleGlyph(
            radius='radius',
            fill_color=linear_cmap(color_field, color_palette, color_min, color_max)
        )

        # Create Bokeh plot
        plot = figure(
            sizing_mode="stretch_width",
            height=600,
            tooltips=self.HOVER_TOOLTIPS,
            tools=self.TOOLS + ",hover",
            active_scroll='wheel_zoom',
            title=title
        )

        # Add graph renderer to plot
        plot.renderers.append(network_graph)

        return plot, network_graph

    def _embed_plot(self, plot: any, container_id: str):
        """
        Embed a Bokeh plot into the HTML page.

        Args:
            plot: The Bokeh plot to embed.
            container_id (str): ID of the HTML container element.

        Note:
            Uses Bokeh's JSON serialization and JavaScript embed API.
        """
        try:
            p_json = json.dumps(json_item(plot, container_id))
            Bokeh.embed.embed_item(JSON.parse(p_json))
            print(f"✅ Plot embedded in #{container_id}")
        except Exception as e:
            error_msg = f"Failed to embed plot: {str(e)}"
            console.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            raise

    def _create_full_network_graph(self):
        """
        Create and render the full network with communities colored.

        This visualization shows all nodes in the network, with each node
        colored according to its detected community. Node size represents
        activity/popularity (nodesize attribute).

        The graph is embedded in the element with ID "chart".
        """
        print("🐍 Creating full network with communities...")
        print("🐍 Rendering community network visualization...")

        num_communities = len(self.communities)
        plot, network_graph = self._create_bokeh_graph(
            self.G,
            f"StackOverflow Communities (Modularity: {self.modularity:.3f}, {num_communities} communities)",
            color_field='community',
            color_palette=Turbo256,
            color_min=0,
            color_max=num_communities
        )

        print("🐍 Rendering community network graph...")
        self._embed_plot(plot, "chart")
        print("✅ Community network graph rendered!")
        print("✅ Chart 1 (full network) complete")

    def _create_largest_community_graph(self):
        """
        Create and render a detailed view of the largest community.

        This visualization focuses on the single largest detected community,
        showing its internal structure. Nodes are colored by degree (number
        of connections) to reveal the most connected nodes within the community.

        The graph is embedded in the element with ID "chart2".
        """
        print("🐍 Analyzing largest community...")
        print("🐍 Extracting largest community...")

        # Find largest community
        largest_community = max(self.communities, key=len)
        largest_subgraph = self.G.subgraph(largest_community)

        print(f"🐍 Largest community: {len(largest_community)} nodes, {len(largest_subgraph.edges())} edges")
        print(f"🐍 Largest: {len(largest_community)} nodes, {len(largest_subgraph.edges())} edges")

        # Sample some nodes for logging
        sample_nodes = list(largest_community)[:10]
        print(f"🐍 Sample members: {', '.join(sample_nodes)}")

        # Compute degrees for the subgraph
        degrees_sub = dict(nx.degree(largest_subgraph))
        nx.set_node_attributes(largest_subgraph, name='degree', values=degrees_sub)

        # Create visualization with degree-based coloring
        plot, graph = self._create_bokeh_graph(
            largest_subgraph,
            f"Largest Community ({len(largest_community)} nodes)",
            color_field='degree',
            color_palette=Category20_20,
            color_min=min(degrees_sub.values()),
            color_max=max(degrees_sub.values())
        )

        print("🐍 Rendering largest community graph...")
        self._embed_plot(plot, "chart2")
        print("✅ Largest community graph rendered!")
        print("✅ Chart 2 (largest community) complete")

    def _create_community_comparison_chart(self):
        """
        Create and render a bar chart comparing community sizes.

        This visualization provides a quantitative comparison of all detected
        communities, showing how many nodes belong to each community. This
        helps identify dominant communities and overall community distribution.

        Features:
        - Vertical bars for each community
        - Color-coded by community ID
        - Hover tooltips showing exact sizes
        - Sorted by community number

        The graph is embedded in the element with ID "chart3".
        """
        print("🐍 Creating community comparison chart...")
        print("🐍 Building community size comparison...")

        num_communities = len(self.communities)
        community_sizes = [len(c) for c in self.communities]

        # Prepare data for bar chart
        comm_data = {
            'community': [f"Community {i+1}" for i in range(num_communities)],
            'size': community_sizes,
            'community_id': list(range(num_communities))
        }
        source = ColumnDataSource(comm_data)

        # Create bar chart
        p = figure(
            x_range=comm_data['community'],
            height=400,
            sizing_mode='stretch_width',
            tools="hover,pan,wheel_zoom,save,reset",
            tooltips=[("Community", "@community"), ("Size", "@size nodes")],
            title="Community Size Comparison"
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

        print("🐍 Rendering community comparison...")
        self._embed_plot(p, "chart3")
        print("✅ Community comparison rendered!")
        print("✅ Chart 3 (comparison) complete")

    def run(self):
        """
        Execute the complete community detection and visualization workflow.

        This method orchestrates the entire process:
        1. Loads network data from CSV files
        2. Builds the NetworkX graph
        3. Detects communities using greedy modularity
        4. Creates and embeds three visualizations:
           - Full network colored by community
           - Largest community detailed view
           - Community size comparison chart

        The graphs are embedded in elements with IDs: chart, chart2, chart3

        Example:
            >>> visualizer = BokehCommunityDetection()
            >>> visualizer.run()

        Note:
            Community detection can take several seconds for large networks.
            The greedy modularity algorithm is efficient but may not find
            the globally optimal partition.
        """
        print("🐍 Starting Community Detection example...")
        print("🐍 Starting community detection analysis...")

        try:
            # Load data
            self._load_data()

            # Build graph
            self._build_graph()

            # Detect communities
            self._detect_communities()

            # Create all three visualizations
            self._create_full_network_graph()
            self._create_largest_community_graph()
            self._create_community_comparison_chart()

            print("✅ All community detection visualizations complete!")
            print("✅ All 3 community visualizations rendered successfully!")

        except Exception as e:
            error_msg = f"Community detection failed: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise


# Entry point: Create instance and run the example
if __name__ == "__main__":
    visualizer = BokehCommunityDetection()
    visualizer.run()
