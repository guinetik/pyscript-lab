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
- Using BokehFactory to reduce boilerplate

Author: Guinetik
Based on: PyScript official documentation examples
"""

from lib.pyscript_manager import PyScriptManager
from bokeh_utils import BokehFactory

# Entry point: Create and embed scatter plot
if __name__ == "__main__":
    # Initialize PyScriptManager for lifecycle management
    manager = PyScriptManager('bokeh_index')

    try:
        print("🐍 Starting basic Bokeh scatter example...")

        # Create factory
        factory = BokehFactory()

        # Create figure with tooltips
        fig = factory.create_figure(
            title="Interactive Bokeh Scatter Plot",
            x_axis_label="X Values",
            y_axis_label="Y Values",
            tooltips=[
                ("Point", "$index"),
                ("X", "@x{0.00}"),
                ("Y", "@y{0.00}")
            ]
        )

        # Add scatter data
        fig.circle(
            [1, 2, 3, 4, 5],  # x_data
            [6, 7, 2, 4, 5],  # y_data
            size=15,
            line_color="navy",
            fill_color="orange",
            fill_alpha=0.5
        )

        # Embed in page
        factory.embed(fig, "chart")

        print("🐍 Basic Bokeh scatter example complete!")

        # Signal that visualization is ready
        manager.signal_ready()

    except Exception as e:
        print(f"❌ Error creating Bokeh plot: {str(e)}")
        manager.signal_error(e)
