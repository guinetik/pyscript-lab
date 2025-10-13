"""
Bokeh Interactive Scatter Plot Example

This module demonstrates how to create interactive data visualizations using Bokeh
in PyScript. Bokeh is a powerful Python library for creating interactive plots
that work in web browsers.

This example shows:
- Creating a basic scatter plot with Bokeh
- Adding interactive tools (pan, zoom, hover)
- Embedding Bokeh visualizations in a PyScript page
- Using tooltips to display data on hover

Author: Guinetik
Based on: PyScript official documentation examples
"""

import json
import pyodide
from typing import List, Tuple, Optional

from js import Bokeh, console, JSON
from bokeh.embed import json_item
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.models import HoverTool


class BokehScatterPlot:
    """
    A class-based example that creates an interactive scatter plot using Bokeh.

    This class demonstrates:
    - Bokeh figure creation with custom sizing
    - Interactive tools (pan, zoom, hover, reset)
    - Custom tooltips for data inspection
    - JSON serialization for browser embedding
    - Integration between Bokeh and PyScript

    The scatter plot includes interactive features:
    - Hover over points to see exact X, Y coordinates
    - Pan to move around the plot
    - Zoom in/out with mouse wheel or box zoom
    - Reset view to original state

    Attributes:
        container_id (str): ID of the HTML element where the plot will be rendered.
        x_data (List[float]): X-axis data points.
        y_data (List[float]): Y-axis data points.
        plot_title (str): Title of the plot.
        x_label (str): Label for the x-axis.
        y_label (str): Label for the y-axis.
    """

    def __init__(
        self,
        container_id: str = "chart",
        x_data: Optional[List[float]] = None,
        y_data: Optional[List[float]] = None,
        plot_title: str = "Interactive Scatter Plot",
        x_label: str = "X Axis",
        y_label: str = "Y Axis"
    ):
        """
        Initialize the BokehScatterPlot with data and configuration.

        Args:
            container_id (str, optional): ID of the HTML container element.
                                         Defaults to "chart".
            x_data (List[float], optional): X-axis coordinates for scatter points.
                                           If None, uses default demo data.
            y_data (List[float], optional): Y-axis coordinates for scatter points.
                                           If None, uses default demo data.
            plot_title (str, optional): Title displayed on the plot.
                                       Defaults to "Interactive Scatter Plot".
            x_label (str, optional): Label for the x-axis. Defaults to "X Axis".
            y_label (str, optional): Label for the y-axis. Defaults to "Y Axis".

        Example:
            >>> plotter = BokehScatterPlot()
            >>> plotter = BokehScatterPlot(
            ...     x_data=[1, 2, 3, 4, 5],
            ...     y_data=[2, 4, 6, 8, 10],
            ...     plot_title="Linear Relationship"
            ... )
        """
        self.container_id = container_id
        self.plot_title = plot_title
        self.x_label = x_label
        self.y_label = y_label

        # Use provided data or default demo data
        self.x_data = x_data if x_data is not None else [1, 2, 3, 4, 5]
        self.y_data = y_data if y_data is not None else [6, 7, 2, 4, 5]

        # Validate data
        self._validate_data()

        console.log("✅ BokehScatterPlot initialized")

    def _validate_data(self):
        """
        Validate that x and y data have the same length.

        Raises:
            ValueError: If x_data and y_data have different lengths.
        """
        if len(self.x_data) != len(self.y_data):
            error_msg = f"Data length mismatch: x_data has {len(self.x_data)} points, y_data has {len(self.y_data)} points"
            console.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

    def _create_figure(self) -> figure:
        """
        Create a Bokeh figure with interactive tools and styling.

        Creates a responsive plot with:
        - Pan tool for moving around
        - Wheel zoom for zooming in/out
        - Box zoom for selecting an area to zoom
        - Reset tool to return to original view
        - Hover tool with custom tooltips

        Returns:
            figure: A configured Bokeh figure object.
        """
        # Create figure with interactive tools
        p = figure(
            sizing_mode='stretch_both',  # Responsive sizing
            title=self.plot_title,
            x_axis_label=self.x_label,
            y_axis_label=self.y_label,
            tooltips=[
                ("Point", "$index"),
                ("X", "@x{0.00}"),  # Format to 2 decimal places
                ("Y", "@y{0.00}")
            ],
            tools="pan,wheel_zoom,box_zoom,reset,hover"
        )

        # Customize plot appearance
        p.title.text_font_size = "16pt"
        p.title.align = "center"

        console.log("✅ Bokeh figure created with interactive tools")
        return p

    def _add_scatter_points(
        self,
        plot: figure,
        size: int = 15,
        line_color: str = "navy",
        fill_color: str = "orange",
        fill_alpha: float = 0.5
    ):
        """
        Add scatter points to the Bokeh plot.

        Args:
            plot (figure): The Bokeh figure to add points to.
            size (int, optional): Size of the scatter points. Defaults to 15.
            line_color (str, optional): Color of the point borders. Defaults to "navy".
            fill_color (str, optional): Fill color of the points. Defaults to "orange".
            fill_alpha (float, optional): Transparency of the fill (0-1). Defaults to 0.5.

        Note:
            The method adds circles to the plot at the coordinates specified
            in self.x_data and self.y_data.
        """
        plot.circle(
            self.x_data,
            self.y_data,
            size=size,
            line_color=line_color,
            fill_color=fill_color,
            fill_alpha=fill_alpha
        )

        console.log(f"✅ Added {len(self.x_data)} scatter points to plot")

    def _embed_plot(self, plot: figure):
        """
        Embed the Bokeh plot into the HTML page.

        This method:
        1. Converts the Bokeh figure to a JSON representation
        2. Parses the JSON for JavaScript consumption
        3. Uses Bokeh's embed API to render the plot in the browser

        Args:
            plot (figure): The Bokeh figure to embed.

        Note:
            The plot is embedded into the HTML element with ID specified
            by self.container_id.
        """
        try:
            # Convert Bokeh figure to JSON format
            p_json = json.dumps(json_item(plot, self.container_id))

            # Embed the plot using Bokeh's JavaScript API
            Bokeh.embed.embed_item(JSON.parse(p_json))

            console.log(f"✅ Plot embedded successfully in #{self.container_id}")
        except Exception as e:
            error_msg = f"Failed to embed plot: {str(e)}"
            console.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            raise

    def run(
        self,
        size: int = 15,
        line_color: str = "navy",
        fill_color: str = "orange",
        fill_alpha: float = 0.5
    ):
        """
        Create and render the complete scatter plot.

        This is the main execution method that:
        1. Creates the Bokeh figure with tools and styling
        2. Adds scatter points with custom appearance
        3. Embeds the interactive plot in the web page

        Args:
            size (int, optional): Size of scatter points. Defaults to 15.
            line_color (str, optional): Border color of points. Defaults to "navy".
            fill_color (str, optional): Fill color of points. Defaults to "orange".
            fill_alpha (float, optional): Fill transparency (0-1). Defaults to 0.5.

        Example:
            >>> plotter = BokehScatterPlot()
            >>> plotter.run()  # Use default styling
            >>> plotter.run(size=20, fill_color="red")  # Custom styling
        """
        print("🐍 Starting Bokeh scatter plot creation...")
        console.log("🐍 Starting Bokeh scatter plot creation...")

        # Create the figure
        plot = self._create_figure()

        # Add scatter points
        self._add_scatter_points(
            plot,
            size=size,
            line_color=line_color,
            fill_color=fill_color,
            fill_alpha=fill_alpha
        )

        # Embed in the page
        print("🐍 Rendering scatter plot...")
        self._embed_plot(plot)

        print("🐍 Scatter plot rendered successfully!")
        console.log("🐍 Scatter plot rendered successfully!")


# Entry point: Create instance and run the example
if __name__ == "__main__":
    print("🐍 Starting basic Bokeh scatter example...")
    console.log("🐍 Starting basic Bokeh scatter example...")

    # Create and run the scatter plot
    plotter = BokehScatterPlot(
        plot_title="Interactive Bokeh Scatter Plot",
        x_label="X Values",
        y_label="Y Values"
    )
    plotter.run()

    print("🐍 Basic Bokeh scatter example complete!")
    console.log("🐍 Basic Bokeh scatter example complete!")
