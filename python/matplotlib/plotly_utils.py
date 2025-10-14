"""
Plotly Utilities for PyScript

Common factory functions and utilities for creating Plotly visualizations
with less boilerplate code. Focuses on choropleth maps and geographic data.

This module provides:
- Choropleth map factory
- Common layout configurations
- Display helpers

Author: Guinetik
"""

import plotly.graph_objects as go
from pyscript import display
from typing import Optional, Dict, Any
import asyncio


class PlotlyFactory:
    """
    Factory for creating and displaying Plotly visualizations with minimal boilerplate.

    Handles common patterns:
    - Choropleth map creation
    - Layout configuration
    - Display to specific DOM elements

    Example:
        factory = PlotlyFactory()
        fig = factory.create_choropleth(
            locations=iso3_codes,
            z=values,
            colorscale='Reds',
            title='My Map'
        )
        factory.display(fig, "map-container")
    """

    def __init__(self):
        """Initialize the PlotlyFactory."""
        pass

    def create_base_layout(
        self,
        title: str,
        height: int = 500,
        projection: str = 'natural earth',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create base layout configuration for choropleth maps.

        Args:
            title: The title text for the map
            height: Map height in pixels
            projection: Map projection type (e.g., 'natural earth', 'mercator')
            **kwargs: Additional layout parameters

        Returns:
            Layout configuration dictionary
        """
        layout = {
            'title_text': title,
            'geo': {
                'showframe': False,
                'showcoastlines': True,
                'projection_type': projection
            },
            'height': height,
            'width': None,
            'autosize': True,
            'margin': {"r": 10, "t": 50, "l": 10, "b": 10}
        }
        layout.update(kwargs)
        return layout

    def create_choropleth(
        self,
        locations,
        z,
        colorscale: str,
        colorbar_title: str,
        title: str,
        hover_text: Optional[Any] = None,
        locationmode: str = 'ISO-3',
        **kwargs
    ) -> go.Figure:
        """
        Create a choropleth map figure.

        Args:
            locations: Country codes (ISO-3, country names, etc.)
            z: Data values to visualize
            colorscale: Plotly colorscale name (e.g., 'Reds', 'Blues')
            colorbar_title: Title for the color legend
            title: Map title
            hover_text: Text to show on hover (optional)
            locationmode: How to interpret location codes ('ISO-3', 'country names', etc.)
            **kwargs: Additional choropleth parameters

        Returns:
            Plotly Figure object

        Example:
            fig = factory.create_choropleth(
                locations=['USA', 'GBR', 'FRA'],
                z=[100, 200, 300],
                colorscale='Blues',
                colorbar_title='Value',
                title='My Map'
            )
        """
        # Convert pandas Series to lists if needed
        locations_list = locations.tolist() if hasattr(locations, 'tolist') else list(locations)
        z_list = z.tolist() if hasattr(z, 'tolist') else list(z)
        text_list = hover_text.tolist() if hover_text is not None and hasattr(hover_text, 'tolist') else (
            list(hover_text) if hover_text is not None else locations_list
        )

        fig = go.Figure(data=go.Choropleth(
            locations=locations_list,
            z=z_list,
            locationmode=locationmode,
            colorscale=colorscale,
            text=text_list,
            colorbar_title=colorbar_title,
            **kwargs
        ))

        fig.update_layout(**self.create_base_layout(title))
        return fig

    async def display_async(self, fig: go.Figure, target_id: str, delay: float = 0.5) -> None:
        """
        Async display a Plotly figure in a specific DOM element.

        Includes a delay to allow Plotly to fully initialize.

        Args:
            fig: Plotly figure object
            target_id: ID of the HTML element to render into
            delay: Seconds to wait before displaying (for Plotly initialization)

        Example:
            fig = factory.create_choropleth(...)
            await factory.display_async(fig, "my-map")
        """
        await asyncio.sleep(delay)
        try:
            display(fig, target=target_id)
            print(f"✅ Map displayed in #{target_id}")
        except Exception as e:
            print(f"❌ Failed to display map in #{target_id}: {str(e)}")
            raise

    def display(self, fig: go.Figure, target_id: str) -> None:
        """
        Display a Plotly figure in a specific DOM element (synchronous).

        Args:
            fig: Plotly figure object
            target_id: ID of the HTML element to render into

        Example:
            fig = factory.create_choropleth(...)
            factory.display(fig, "my-map")
        """
        try:
            display(fig, target=target_id)
            print(f"✅ Map displayed in #{target_id}")
        except Exception as e:
            print(f"❌ Failed to display map in #{target_id}: {str(e)}")
            raise


async def quick_choropleth(
    locations,
    z,
    title: str,
    target_id: str,
    colorscale: str = 'Reds',
    colorbar_title: str = 'Value',
    hover_text: Optional[Any] = None
) -> None:
    """
    Create and display a choropleth map in one call.

    Convenience function for the most common use case.

    Args:
        locations: Country codes
        z: Data values
        title: Map title
        target_id: HTML element ID to render into
        colorscale: Plotly colorscale name
        colorbar_title: Color legend title
        hover_text: Hover text (optional)

    Example:
        await quick_choropleth(
            ['USA', 'GBR', 'FRA'],
            [100, 200, 300],
            "My Map",
            "map-div"
        )
    """
    factory = PlotlyFactory()
    fig = factory.create_choropleth(
        locations=locations,
        z=z,
        colorscale=colorscale,
        colorbar_title=colorbar_title,
        title=title,
        hover_text=hover_text
    )
    await factory.display_async(fig, target_id)
