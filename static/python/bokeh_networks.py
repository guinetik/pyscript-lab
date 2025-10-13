"""
NetworkX + Bokeh Network Graph Visualization

This module demonstrates interactive network graph visualization using NetworkX and Bokeh
in PyScript. It analyzes StackOverflow tag relationships to create three different views
of the network:

1. Full Network - Complete graph of StackOverflow tag relationships
2. Cliques - Subgraph showing the largest cliques (tightly connected groups)
3. Programming Languages - Subgraph focused on major programming language connections

These examples showcase:
- Building graphs from CSV data using NetworkX
- Computing network metrics (degree, centrality, cliques)
- Creating interactive network visualizations with Bokeh
- Subgraph extraction and analysis
- Spring layout algorithm for node positioning

Author: PyScript L.A.B
Adapted from: https://www.kaggle.com/code/mayeesha/network-analysis-for-dummies-stackoverflow-data/notebook
"""

from pyodide.http import open_url
from js import Bokeh, console, JSON
from typing import List, Dict, Set, Tuple, Optional

import networkx as nx
import pandas as pd
import numpy as np
import json

from bokeh.embed import json_item
from bokeh.plotting import from_networkx, figure
from bokeh.models import EdgesAndLinkedNodes, NodesAndLinkedEdges, Circle as CircleGlyph
from bokeh.transform import linear_cmap
from bokeh.palettes import Blues8, Reds8, Purples8, Oranges8, Viridis8, Spectral8, Turbo256


class BokehNetworkGraphs:
    """
    A comprehensive network analysis and visualization class using NetworkX and Bokeh.

    This class loads StackOverflow tag network data and creates three different
    interactive network visualizations to explore the relationships between
    programming topics and technologies.

    Features:
    - Automated graph construction from CSV data
    - Network analysis (degree, centrality, cliques)
    - Interactive visualizations with tooltips
    - Spring layout algorithm for aesthetic node placement
    - Color-coded nodes by group
    - Three different network views

    Attributes:
        nodes_url (str): Path to the nodes CSV file.
        edges_url (str): Path to the edges CSV file.
        G (nx.Graph): The main NetworkX graph object.
        nodes_df (pd.DataFrame): DataFrame containing node data.
        edges_df (pd.DataFrame): DataFrame containing edge data.
        min_group (int): Minimum group value in the data (for color mapping).
        max_group (int): Maximum group value in the data (for color mapping).
    """

    # Hover tooltip configuration for all graphs
    HOVER_TOOLTIPS = [
        ("Name", "@name"),
        ("Degree", "@degree"),
        ("Node Size", "@nodesize"),
        ("Group", "@group")
    ]

    # Standard Bokeh tools for network interaction
    TOOLS = "pan,wheel_zoom,save,reset"

    def __init__(
        self,
        nodes_url: str = "/data/stack_network_nodes.csv",
        edges_url: str = "/data/stack_network_links.csv"
    ):
        """
        Initialize the BokehNetworkGraphs visualizer.

        Args:
            nodes_url (str, optional): Path to the nodes CSV file.
                                      Defaults to "/data/stack_network_nodes.csv".
            edges_url (str, optional): Path to the edges CSV file.
                                      Defaults to "/data/stack_network_links.csv".

        Example:
            >>> visualizer = BokehNetworkGraphs()
            >>> visualizer.run()
        """
        self.nodes_url = nodes_url
        self.edges_url = edges_url
        self.G = None
        self.nodes_df = None
        self.edges_df = None
        self.min_group = None
        self.max_group = None

        print("🐍 BokehNetworkGraphs initialized")
        console.log("🐍 BokehNetworkGraphs initialized")

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
            console.log(f"🐍 Loading nodes from: {self.nodes_url}")
            console.log(f"🐍 Loading edges from: {self.edges_url}")

            self.nodes_df = pd.read_csv(open_url(self.nodes_url))
            self.edges_df = pd.read_csv(open_url(self.edges_url))

            if self.nodes_df.empty or self.edges_df.empty:
                raise ValueError("Loaded DataFrames are empty")

            print(f"🐍 Loaded {len(self.nodes_df)} nodes and {len(self.edges_df)} edges")
            console.log(f"✅ Data loaded: {len(self.nodes_df)} nodes, {len(self.edges_df)} edges")

            # Determine the range of group values for color mapping
            self.min_group = int(self.nodes_df['group'].min())
            self.max_group = int(self.nodes_df['group'].max())
            group_count = self.max_group - self.min_group + 1
            print(f"🐍 Found {group_count} groups (range: {self.min_group}-{self.max_group})")
            console.log(f"🐍 Groups: {group_count} unique groups detected")

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
        5. Computes adjusted node sizes based on degree

        Note:
            After this method, self.G contains the complete graph with
            all nodes, edges, and computed attributes.
        """
        print("🐍 Building NetworkX graph...")
        console.log("🐍 Building graph structure...")

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

        # Compute adjusted node sizes based on degree
        number_to_adjust_by = 10
        adjusted_node_size = dict([
            (node, degree + number_to_adjust_by)
            for node, degree in nx.degree(self.G)
        ])
        nx.set_node_attributes(self.G, name='node_size', values=adjusted_node_size)

        print(f"✅ Graph built: {len(self.G.nodes())} nodes, {len(self.G.edges())} edges")
        console.log(f"✅ Graph: {len(self.G.nodes())} nodes, {len(self.G.edges())} edges")

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
        console.log(f"🐍 Node radii: {min_radius:.4f} to {max_radius:.4f}")

    def _create_bokeh_graph(
        self,
        graph: nx.Graph,
        title: str,
        layout: str = 'spring',
        k: float = 1.5,
        iterations: int = 100
    ) -> Tuple[any, any]:
        """
        Create a Bokeh network graph renderer from a NetworkX graph.

        This method:
        1. Computes layout positions for nodes using specified algorithm
        2. Creates Bokeh graph renderer from NetworkX graph
        3. Configures node appearance (size, color)
        4. Sets up interaction policies

        Args:
            graph (nx.Graph): NetworkX graph to visualize.
            title (str): Title for the plot.
            layout (str, optional): Layout algorithm to use. Options:
                                   'spring' - Fruchterman-Reingold force-directed
                                   'kamada_kawai' - Kamada-Kawai force-directed
                                   'circular' - Nodes in a circle
                                   'spectral' - Uses graph Laplacian
                                   'shell' - Concentric circles
                                   Defaults to 'spring'.
            k (float, optional): Spring/Kamada-Kawai layout spacing constant.
                                Defaults to 1.5.
            iterations (int, optional): Number of layout iterations (spring only).
                                       Defaults to 100.

        Returns:
            Tuple[any, any]: A tuple of (bokeh_plot, network_graph_renderer).

        Note:
            Different layouts reveal different aspects of network structure.
        """
        # Compute node radii based on nodesize (activity/number of people)
        self._compute_node_radii(graph)

        # Compute layout positions based on selected algorithm
        console.log(f"🐍 Using {layout} layout algorithm...")

        if layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(graph)
        elif layout == 'circular':
            pos = nx.circular_layout(graph)
        elif layout == 'spectral':
            pos = nx.spectral_layout(graph)
        elif layout == 'shell':
            pos = nx.shell_layout(graph)
        else:  # default to spring
            pos = nx.spring_layout(graph, k=k, iterations=iterations)

        # Create Bokeh graph from NetworkX
        network_graph = from_networkx(graph, pos)

        # Configure interaction policies
        network_graph.selection_policy = NodesAndLinkedEdges()
        network_graph.inspection_policy = NodesAndLinkedEdges()

        # Set node appearance with color mapping by group and size by radius
        # Use Turbo256 palette for better color distribution with many groups
        network_graph.node_renderer.glyph = CircleGlyph(
            radius='radius',  # Use the computed radius attribute
            fill_color=linear_cmap(
                'group',
                Turbo256,
                self.min_group,
                self.max_group
            )
        )

        # Create Bokeh plot
        plot = figure(
            sizing_mode="stretch_width",
            tooltips=self.HOVER_TOOLTIPS,
            tools=self.TOOLS,
            active_scroll='wheel_zoom',
            height=400,
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
            Uses Bokeh's JSON serialization and JavaScript embed API
            to render the plot in the browser.
        """
        try:
            p_json = json.dumps(json_item(plot, container_id))
            Bokeh.embed.embed_item(JSON.parse(p_json))
            console.log(f"✅ Plot embedded in #{container_id}")
        except Exception as e:
            error_msg = f"Failed to embed plot: {str(e)}"
            console.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            raise

    def _create_full_network_graph(self):
        """
        Create and render the full StackOverflow network graph.

        This visualization shows the complete network of StackOverflow tags
        and their relationships. Node size represents degree (number of connections),
        and color represents the tag's group category.

        Uses Kamada-Kawai layout which optimizes node placement based on graph
        distances, often revealing community structure more clearly than spring layout.

        The graph is embedded in the element with ID "chart".
        """
        print("🐍 Creating full network graph...")
        console.log("🐍 Rendering full network visualization...")

        plot, network_graph = self._create_bokeh_graph(
            self.G,
            "StackOverflow Networks - Full Graph (Kamada-Kawai Layout)",
            layout='kamada_kawai'
        )

        print("🐍 Rendering network graph 1...")
        self._embed_plot(plot, "chart")
        print("✅ Graph 1 (full network) rendered!")
        console.log("✅ Chart 1 (full network) complete")

    def _create_cliques_graph(self):
        """
        Create and render a subgraph showing the largest cliques.

        A clique is a subset of nodes where every node is connected to every
        other node (a complete subgraph). This visualization shows the largest
        cliques in the network, revealing tightly interconnected tag groups.

        Process:
        1. Find all cliques in the network
        2. Select the 3 largest cliques
        3. Create subgraph from nodes in these cliques
        4. Visualize the subgraph

        The graph is embedded in the element with ID "chart2".
        """
        print("🐍 Analyzing cliques...")
        console.log("🐍 Finding cliques in network...")

        # Find all cliques
        cliques = list(nx.find_cliques(self.G))
        clique_count = len(cliques)
        print(f"🐍 This network has {clique_count} cliques!")
        console.log(f"🐍 Found {clique_count} cliques")

        # Sort cliques by size and get the largest ones
        sorted_cliques = sorted(cliques, key=len)

        # Collect nodes from the 3 largest cliques
        max_clique_nodes = set()
        for nodelist in sorted_cliques[-4:-1]:
            for node in nodelist:
                max_clique_nodes.add(node)

        # Create subgraph
        max_clique = self.G.subgraph(max_clique_nodes)
        print(f"🐍 Clique subgraph: {len(max_clique.nodes())} nodes, {len(max_clique.edges())} edges")
        console.log(f"🐍 Clique subgraph: {len(max_clique.nodes())} nodes")

        # Compute node attributes for subgraph
        degrees = dict(nx.degree(max_clique))
        nx.set_node_attributes(max_clique, name='degree', values=degrees)

        number_to_adjust_by = 15
        adjusted_node_size = dict([
            (node, degree + number_to_adjust_by)
            for node, degree in nx.degree(max_clique)
        ])
        nx.set_node_attributes(max_clique, name='node_size', values=adjusted_node_size)

        # Create and embed visualization
        plot, graph = self._create_bokeh_graph(
            max_clique,
            "StackOverflow Networks - Largest Cliques"
        )

        print("🐍 Rendering clique graph...")
        self._embed_plot(plot, "chart2")
        print("✅ Graph 2 (cliques) rendered!")
        console.log("✅ Chart 2 (cliques) complete")

    def _create_eigenvector_centrality_graph(self):
        """
        Create and render a visualization highlighting eigenvector centrality.

        Eigenvector centrality measures a node's influence in a network based on
        the principle that connections to high-scoring nodes contribute more to
        the score than connections to low-scoring nodes. Think of it as measuring
        not just how many connections a node has, but the quality/importance of
        those connections.

        In this visualization:
        - Node SIZE represents eigenvector centrality (bigger = more influential)
        - Node COLOR still represents the group category
        - This reveals which tags are most central/influential in the network

        Process:
        1. Compute eigenvector centrality for all nodes
        2. Use centrality scores to determine node sizes
        3. Visualize with larger nodes for more central/influential tags

        The graph is embedded in the element with ID "chart3".
        """
        print("🐍 Computing eigenvector centrality...")
        console.log("🐍 Analyzing node influence with eigenvector centrality...")

        # Compute eigenvector centrality
        try:
            centrality = nx.eigenvector_centrality(self.G, max_iter=1000)
        except:
            # Fallback to numpy version if regular version fails
            centrality = nx.eigenvector_centrality_numpy(self.G)

        nx.set_node_attributes(self.G, name='centrality', values=centrality)

        # Get centrality values for logging
        centrality_values = list(centrality.values())
        min_cent = min(centrality_values)
        max_cent = max(centrality_values)
        print(f"🐍 Centrality range: {min_cent:.4f} to {max_cent:.4f}")
        console.log(f"🐍 Centrality: min={min_cent:.4f}, max={max_cent:.4f}")

        # Create a copy of the graph for this visualization
        centrality_graph = self.G.copy()

        # Override nodesize with centrality-based sizes for this visualization
        # Scale centrality to reasonable node sizes (larger range for more dramatic effect)
        centrality_as_nodesize = {}
        for node in centrality_graph.nodes():
            cent = centrality[node]
            # Normalize and scale to 1-100 range
            normalized = (cent - min_cent) / (max_cent - min_cent) if max_cent > min_cent else 0.5
            centrality_as_nodesize[node] = 1 + (normalized * 99)

        nx.set_node_attributes(centrality_graph, centrality_as_nodesize, 'nodesize')

        # Compute degrees for tooltip
        degrees = dict(nx.degree(centrality_graph))
        nx.set_node_attributes(centrality_graph, name='degree', values=degrees)

        # Create and embed visualization with larger size range for centrality
        plot, graph = self._create_bokeh_graph(
            centrality_graph,
            "StackOverflow Networks - Eigenvector Centrality"
        )

        # Update the title to add explanation
        plot.title.text = "StackOverflow Networks - Eigenvector Centrality (size = influence)"

        print("🐍 Rendering eigenvector centrality graph...")
        self._embed_plot(plot, "chart3")
        print("✅ Graph 3 (eigenvector centrality) rendered!")
        console.log("✅ Chart 3 (eigenvector centrality) complete")

    def _create_programming_languages_graph(self):
        """
        Create and render a subgraph focused on major programming languages.

        This visualization shows the network of tags connected to major
        programming languages (C, C++, C#, Java, Python, Ruby, Scala,
        Haskell, JavaScript, SQL). It reveals which technologies and
        topics are commonly associated with each language.

        Process:
        1. Define list of major programming languages
        2. Find all neighbors (connected tags) of these languages
        3. Create subgraph from these nodes
        4. Visualize the language-centric network

        The graph is embedded in the element with ID "chart4".
        """
        print("🐍 Building programming languages subgraph...")
        console.log("🐍 Extracting programming language network...")

        # Define major programming languages to analyze
        major_languages = [
            'c', 'c++', 'c#', 'java', 'python', 'ruby',
            'scala', 'haskell', 'javascript', 'sql'
        ]

        # Collect all nodes connected to these languages
        p_language_nodes = []
        for language in major_languages:
            if language in self.G:
                neighbors = self.G.neighbors(language)
                p_language_nodes.extend(neighbors)

        # Create subgraph
        programming_language_graph = self.G.subgraph(set(p_language_nodes))
        console.log(f"🐍 Language subgraph: {len(programming_language_graph.nodes())} nodes")

        # Compute node attributes for subgraph
        degrees = dict(nx.degree(programming_language_graph))
        nx.set_node_attributes(programming_language_graph, name='degree', values=degrees)

        number_to_adjust_by = 5
        adjusted_node_size = dict([
            (node, degree * number_to_adjust_by)
            for node, degree in nx.degree(programming_language_graph)
        ])
        nx.set_node_attributes(
            programming_language_graph,
            name='node_size',
            values=adjusted_node_size
        )

        # Create and embed visualization
        plot, graph = self._create_bokeh_graph(
            programming_language_graph,
            "StackOverflow Networks - Programming Languages"
        )

        print("🐍 Rendering programming languages network...")
        self._embed_plot(plot, "chart4")
        print("✅ Graph 4 (programming languages) rendered!")
        console.log("✅ Chart 4 (languages) complete")

    def run(self):
        """
        Execute the complete network visualization workflow.

        This method orchestrates the entire process:
        1. Loads network data from CSV files
        2. Builds the NetworkX graph with attributes
        3. Creates and embeds four visualizations:
           - Full network graph (chart)
           - Cliques subgraph (chart2)
           - Eigenvector centrality (chart3)
           - Programming languages subgraph (chart4)

        The graphs are embedded in elements with IDs: chart, chart2, chart3, chart4

        Example:
            >>> visualizer = BokehNetworkGraphs()
            >>> visualizer.run()

        Note:
            This process may take several seconds due to:
            - CSV data loading
            - Graph construction
            - Spring layout computation (iterative algorithm)
            - Clique finding (computationally intensive)
            - Eigenvector centrality computation
        """
        print("🐍 Starting NetworkX + Bokeh network visualization...")
        console.log("🐍 Starting network analysis...")

        try:
            # Load data
            self._load_data()

            # Build main graph
            self._build_graph()

            # Create all four visualizations
            self._create_full_network_graph()
            self._create_cliques_graph()
            self._create_eigenvector_centrality_graph()
            self._create_programming_languages_graph()

            print("✅ All network graphs complete!")
            console.log("✅ All 4 network visualizations rendered successfully!")

        except Exception as e:
            error_msg = f"Network visualization failed: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise


# Entry point: Create instance and run the example
if __name__ == "__main__":
    visualizer = BokehNetworkGraphs()
    visualizer.run()
