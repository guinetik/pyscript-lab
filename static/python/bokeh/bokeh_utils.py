"""
Bokeh Utilities for PyScript

Common factory functions and utilities for creating Bokeh visualizations
with less boilerplate code.

This module provides:
- Figure creation with sensible defaults
- Chart embedding with automatic JSON conversion
- NetworkX graph visualization utilities
- Common styling and configuration
- Error handling wrappers

Author: Guinetik
"""

import json
from typing import Optional, List, Tuple, Dict, Any
from bokeh.plotting import figure, from_networkx
from bokeh.embed import json_item
from bokeh.models import NodesAndLinkedEdges, Circle as CircleGlyph
from bokeh.transform import linear_cmap
from bokeh.palettes import Turbo256
from js import Bokeh, console, JSON

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class BokehFactory:
    """
    Factory for creating and embedding Bokeh charts with minimal boilerplate.

    This class handles the common patterns of:
    - Creating figures with standard tools
    - Converting to JSON
    - Embedding in the DOM

    Example:
        factory = BokehFactory()
        fig = factory.create_figure(title="My Chart", height=400)
        fig.circle([1, 2, 3], [4, 5, 6])
        factory.embed(fig, "chart-container")
    """

    # Default tools for interactive charts
    DEFAULT_TOOLS = "pan,wheel_zoom,box_zoom,reset,hover"

    def __init__(self, tools: Optional[str] = None):
        """
        Initialize the BokehFactory.

        Args:
            tools: Comma-separated string of Bokeh tools.
                   If None, uses DEFAULT_TOOLS.
        """
        self.tools = tools or self.DEFAULT_TOOLS

    def create_figure(
        self,
        title: str = "",
        height: int = 400,
        sizing_mode: str = "stretch_both",
        tools: Optional[str] = None,
        tooltips: Optional[List[Tuple[str, str]]] = None,
        **kwargs
    ) -> figure:
        """
        Create a Bokeh figure with common defaults.

        Args:
            title: Chart title
            height: Chart height in pixels
            sizing_mode: Bokeh sizing mode ('stretch_both', 'scale_width', etc.)
            tools: Override default tools for this chart
            tooltips: List of (label, value) tuples for hover tooltips
            **kwargs: Additional arguments passed to figure()

        Returns:
            Configured Bokeh figure object

        Example:
            fig = factory.create_figure(
                title="Scatter Plot",
                height=500,
                tooltips=[("X", "@x"), ("Y", "@y")]
            )
        """
        chart_tools = tools or self.tools

        fig_kwargs = {
            'title': title,
            'height': height,
            'sizing_mode': sizing_mode,
            'tools': chart_tools,
            **kwargs
        }

        if tooltips:
            fig_kwargs['tooltips'] = tooltips

        fig = figure(**fig_kwargs)

        # Apply common styling
        if title:
            fig.title.text_font_size = "16pt"
            fig.title.align = "center"

        return fig

    def embed(self, fig: figure, container_id: str) -> None:
        """
        Embed a Bokeh figure into the DOM.

        Handles JSON conversion and embedding automatically.

        Args:
            fig: Bokeh figure to embed
            container_id: ID of the HTML element to render into

        Example:
            fig = factory.create_figure(title="My Chart")
            fig.circle([1, 2, 3], [4, 5, 6])
            factory.embed(fig, "chart")
        """
        try:
            # Convert to JSON and embed
            fig_json = json.dumps(json_item(fig, container_id))
            Bokeh.embed.embed_item(JSON.parse(fig_json))
            print(f"✅ Chart embedded in #{container_id}")
        except Exception as e:
            error_msg = f"Failed to embed chart in #{container_id}: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise

    def create_and_embed(
        self,
        container_id: str,
        title: str = "",
        height: int = 400,
        sizing_mode: str = "stretch_both",
        tools: Optional[str] = None,
        tooltips: Optional[List[Tuple[str, str]]] = None,
        **kwargs
    ) -> figure:
        """
        Create a figure that will be embedded when finished.

        This is a convenience method that creates a figure and remembers
        where to embed it. After adding data, call embed_last().

        Args:
            container_id: ID of the HTML element to render into
            (other args same as create_figure)

        Returns:
            Configured Bokeh figure object

        Example:
            fig = factory.create_and_embed("chart", title="My Chart")
            fig.circle([1, 2, 3], [4, 5, 6])
            factory.embed_last()
        """
        self._last_container_id = container_id
        self._last_figure = self.create_figure(
            title=title,
            height=height,
            sizing_mode=sizing_mode,
            tools=tools,
            tooltips=tooltips,
            **kwargs
        )
        return self._last_figure

    def embed_last(self) -> None:
        """
        Embed the last figure created with create_and_embed().

        Example:
            fig = factory.create_and_embed("chart", title="My Chart")
            fig.circle([1, 2, 3], [4, 5, 6])
            factory.embed_last()  # Embeds into "chart" container
        """
        if not hasattr(self, '_last_figure') or not hasattr(self, '_last_container_id'):
            raise RuntimeError("No figure to embed. Use create_and_embed() first.")

        self.embed(self._last_figure, self._last_container_id)


def quick_scatter(
    x_data: List[float],
    y_data: List[float],
    container_id: str = "chart",
    title: str = "Scatter Plot",
    x_label: str = "X",
    y_label: str = "Y",
    size: int = 15,
    color: str = "orange",
    **kwargs
) -> None:
    """
    Create and embed a simple scatter plot in one call.

    Convenience function for the most common use case.

    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        container_id: HTML element ID to render into
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        size: Point size
        color: Point color
        **kwargs: Additional arguments for figure()

    Example:
        quick_scatter([1, 2, 3], [4, 5, 6], container_id="my-chart")
    """
    factory = BokehFactory()
    fig = factory.create_figure(
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        **kwargs
    )

    fig.circle(x_data, y_data, size=size, fill_color=color, line_color="navy", fill_alpha=0.5)

    factory.embed(fig, container_id)


class NetworkGraphFactory:
    """
    Factory for creating NetworkX graph visualizations with Bokeh.

    Handles common patterns:
    - Building graphs from DataFrames
    - Computing node attributes (degree, centrality, etc.)
    - Creating network visualizations with different layouts
    - Node sizing and coloring

    Example:
        factory = NetworkGraphFactory()
        G = factory.build_graph(nodes_df, edges_df)
        factory.compute_node_degrees(G)
        fig = factory.create_network_plot(G, "My Network", layout='kamada_kawai')
        factory.embed(fig, "chart")
    """

    DEFAULT_HOVER_TOOLTIPS = [
        ("Name", "@name"),
        ("Degree", "@degree"),
        ("Node Size", "@nodesize"),
        ("Group", "@group")
    ]

    DEFAULT_TOOLS = "pan,wheel_zoom,save,reset"

    def __init__(self):
        """Initialize the NetworkGraphFactory."""
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is required for NetworkGraphFactory")
        self.min_group = None
        self.max_group = None
        self.bokeh_factory = BokehFactory()

    def build_graph(
        self,
        nodes_df: Any,
        edges_df: Any,
        node_name_col: str = "name",
        node_attrs: Optional[List[str]] = None,
        edge_source_col: str = "source",
        edge_target_col: str = "target",
        edge_weight_col: Optional[str] = "value"
    ) -> Any:
        """
        Build a NetworkX graph from node and edge DataFrames.

        Args:
            nodes_df: DataFrame with node data
            edges_df: DataFrame with edge data
            node_name_col: Column name for node identifier
            node_attrs: List of column names to add as node attributes
            edge_source_col: Column name for edge source
            edge_target_col: Column name for edge target
            edge_weight_col: Column name for edge weight (None to skip)

        Returns:
            NetworkX Graph object
        """
        print("🐍 Building NetworkX graph...")

        G = nx.Graph()

        # Add nodes with attributes
        default_attrs = ['group', 'nodesize'] if node_attrs is None else node_attrs
        for _, row in nodes_df.iterrows():
            attrs = {attr: row[attr] for attr in default_attrs if attr in row}
            attrs['name'] = row[node_name_col]
            G.add_node(row[node_name_col], **attrs)

        # Add edges
        for _, row in edges_df.iterrows():
            edge_attrs = {}
            if edge_weight_col and edge_weight_col in row:
                edge_attrs['weight'] = row[edge_weight_col]
            G.add_edge(row[edge_source_col], row[edge_target_col], **edge_attrs)

        # Store group range for color mapping
        if 'group' in nodes_df.columns:
            self.min_group = int(nodes_df['group'].min())
            self.max_group = int(nodes_df['group'].max())

        print(f"✅ Graph built: {len(G.nodes())} nodes, {len(G.edges())} edges")
        return G

    def compute_node_degrees(self, G: Any) -> None:
        """
        Compute and set degree for all nodes.

        Args:
            G: NetworkX graph
        """
        degrees = dict(nx.degree(G))
        nx.set_node_attributes(G, name='degree', values=degrees)

    def compute_adjusted_node_sizes(
        self,
        G: Any,
        adjustment: int = 10,
        attr_name: str = 'node_size'
    ) -> None:
        """
        Compute adjusted node sizes based on degree.

        Args:
            G: NetworkX graph
            adjustment: Number to add to degree for minimum size
            attr_name: Attribute name to store sizes under
        """
        adjusted = {
            node: degree + adjustment
            for node, degree in nx.degree(G)
        }
        nx.set_node_attributes(G, name=attr_name, values=adjusted)

    def compute_node_radii(
        self,
        G: Any,
        min_radius: float = 0.005,
        max_radius: float = 0.03
    ) -> None:
        """
        Compute normalized node radii based on nodesize attribute.

        Args:
            G: NetworkX graph with nodesize attributes
            min_radius: Minimum node radius
            max_radius: Maximum node radius
        """
        nodesizes = [G.nodes[n].get('nodesize', 1) for n in G.nodes()]
        min_nodesize = min(nodesizes)
        max_nodesize = max(nodesizes)

        radii = {}
        for node in G.nodes():
            nodesize = G.nodes[node].get('nodesize', 1)
            if max_nodesize > min_nodesize:
                normalized = (nodesize - min_nodesize) / (max_nodesize - min_nodesize)
            else:
                normalized = 0.5
            radii[node] = min_radius + (normalized * (max_radius - min_radius))

        nx.set_node_attributes(G, radii, 'radius')

    def compute_layout(
        self,
        G: Any,
        layout: str = 'spring',
        k: float = 1.5,
        iterations: int = 100
    ) -> Dict:
        """
        Compute layout positions for graph nodes.

        Args:
            G: NetworkX graph
            layout: Layout algorithm ('spring', 'kamada_kawai', 'circular', 'spectral', 'shell')
            k: Spring/Kamada-Kawai spacing constant
            iterations: Number of iterations for spring layout

        Returns:
            Dictionary mapping nodes to (x, y) positions
        """
        print(f"🐍 Computing {layout} layout...")

        if layout == 'kamada_kawai':
            return nx.kamada_kawai_layout(G)
        elif layout == 'circular':
            return nx.circular_layout(G)
        elif layout == 'spectral':
            return nx.spectral_layout(G)
        elif layout == 'shell':
            return nx.shell_layout(G)
        else:  # default to spring
            return nx.spring_layout(G, k=k, iterations=iterations)

    def create_network_plot(
        self,
        G: Any,
        title: str,
        layout: str = 'spring',
        k: float = 1.5,
        iterations: int = 100,
        height: int = 400,
        tooltips: Optional[List[Tuple[str, str]]] = None,
        tools: Optional[str] = None
    ) -> figure:
        """
        Create a Bokeh network visualization from a NetworkX graph.

        Args:
            G: NetworkX graph
            title: Plot title
            layout: Layout algorithm to use
            k: Layout spacing constant
            iterations: Spring layout iterations
            height: Plot height
            tooltips: Custom tooltips (uses defaults if None)
            tools: Custom tools (uses defaults if None)

        Returns:
            Bokeh figure with network graph
        """
        # Ensure node radii are computed
        self.compute_node_radii(G)

        # Compute layout
        pos = self.compute_layout(G, layout=layout, k=k, iterations=iterations)

        # Create Bokeh graph from NetworkX
        network_graph = from_networkx(G, pos)

        # Configure interaction policies
        network_graph.selection_policy = NodesAndLinkedEdges()
        network_graph.inspection_policy = NodesAndLinkedEdges()

        # Set node appearance with color mapping and size
        if self.min_group is not None and self.max_group is not None:
            network_graph.node_renderer.glyph = CircleGlyph(
                radius='radius',
                fill_color=linear_cmap(
                    'group',
                    Turbo256,
                    self.min_group,
                    self.max_group
                )
            )
        else:
            network_graph.node_renderer.glyph = CircleGlyph(radius='radius')

        # Create plot
        plot_tooltips = tooltips or self.DEFAULT_HOVER_TOOLTIPS
        plot_tools = tools or self.DEFAULT_TOOLS

        plot = figure(
            sizing_mode="stretch_width",
            tooltips=plot_tooltips,
            tools=plot_tools,
            active_scroll='wheel_zoom',
            height=height,
            title=title
        )

        # Add graph renderer
        plot.renderers.append(network_graph)

        return plot

    def embed(self, plot: figure, container_id: str) -> None:
        """
        Embed a Bokeh plot into the DOM.

        Args:
            plot: Bokeh figure to embed
            container_id: ID of HTML element to render into
        """
        self.bokeh_factory.embed(plot, container_id)

    def detect_communities(self, G: Any) -> tuple:
        """
        Detect communities using greedy modularity optimization.

        Args:
            G: NetworkX graph

        Returns:
            Tuple of (communities_list, modularity_score, node_to_community_dict)
        """
        print("🐍 Detecting communities using greedy modularity...")

        import networkx.algorithms.community as nx_comm

        # Detect communities
        communities = list(nx_comm.greedy_modularity_communities(G))
        num_communities = len(communities)
        print(f"🐍 Found {num_communities} communities")

        # Create node-to-community mapping
        node_to_community = {}
        for comm_id, community in enumerate(communities):
            for node in community:
                node_to_community[node] = comm_id

        # Set community as node attribute
        nx.set_node_attributes(G, node_to_community, 'community')

        # Calculate modularity score
        modularity = nx_comm.modularity(G, communities)
        print(f"🐍 Network modularity: {modularity:.3f}")

        # Log community sizes
        for i, community in enumerate(communities):
            print(f"🐍 Community {i+1}: {len(community)} nodes")

        return communities, modularity, node_to_community

    def get_largest_community(self, G: Any, communities: list) -> Any:
        """
        Extract the largest community as a subgraph.

        Args:
            G: NetworkX graph
            communities: List of community sets

        Returns:
            Subgraph of the largest community
        """
        largest = max(communities, key=len)
        subgraph = G.subgraph(largest)
        print(f"🐍 Largest community: {len(largest)} nodes, {len(subgraph.edges())} edges")

        # Recompute degrees for subgraph
        degrees = dict(nx.degree(subgraph))
        nx.set_node_attributes(subgraph, name='degree', values=degrees)

        return subgraph
