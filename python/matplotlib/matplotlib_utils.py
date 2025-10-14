"""
Matplotlib Utilities for PyScript

Common factory functions and utilities for creating Matplotlib visualizations
with less boilerplate code.

This module provides:
- Chart display helpers
- Common styling utilities
- Color palette management

Author: Guinetik
"""

import matplotlib.pyplot as plt
from pyscript import display
from typing import Optional, Tuple


class MatplotlibFactory:
    """
    Factory for creating and displaying Matplotlib charts with minimal boilerplate.

    Handles common patterns:
    - Figure creation with standard sizing
    - Display to specific DOM elements
    - Common styling and formatting

    Example:
        factory = MatplotlibFactory()
        fig, ax = factory.create_figure(figsize=(10, 6))
        ax.plot([1, 2, 3], [4, 5, 6])
        factory.display(fig, "chart-container")
    """

    def __init__(self):
        """Initialize the MatplotlibFactory."""
        pass

    def create_figure(
        self,
        figsize: Tuple[int, int] = (10, 8),
        **kwargs
    ) -> Tuple:
        """
        Create a Matplotlib figure and axes.

        Args:
            figsize: Figure size as (width, height) in inches
            **kwargs: Additional arguments passed to plt.subplots()

        Returns:
            Tuple of (figure, axes)

        Example:
            fig, ax = factory.create_figure(figsize=(12, 6))
            ax.bar(['A', 'B', 'C'], [1, 2, 3])
        """
        return plt.subplots(figsize=figsize, **kwargs)

    def display(self, fig, target_id: str) -> None:
        """
        Display a Matplotlib figure in a specific DOM element.

        Args:
            fig: Matplotlib figure object
            target_id: ID of the HTML element to render into

        Example:
            fig, ax = factory.create_figure()
            ax.plot([1, 2, 3], [4, 5, 6])
            factory.display(fig, "my-chart")
        """
        try:
            display(fig, target=target_id)
            print(f"✅ Chart displayed in #{target_id}")
        except Exception as e:
            print(f"❌ Failed to display chart in #{target_id}: {str(e)}")
            raise

    def style_bar_chart(
        self,
        ax,
        title: str,
        xlabel: str,
        ylabel: Optional[str] = None,
        grid: bool = True,
        grid_axis: str = 'x'
    ) -> None:
        """
        Apply common styling to a bar chart.

        Args:
            ax: Matplotlib axes object
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label (optional)
            grid: Whether to show grid
            grid_axis: Which axis to show grid on ('x', 'y', or 'both')
        """
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        if grid:
            ax.grid(axis=grid_axis, alpha=0.3)

    def add_value_labels_barh(
        self,
        ax,
        data,
        format_str: str = "{:,}",
        fontsize: int = 9
    ) -> None:
        """
        Add value labels to horizontal bar chart.

        Args:
            ax: Matplotlib axes object
            data: Data series with values
            format_str: Format string for values
            fontsize: Font size for labels
        """
        for i, (idx, row) in enumerate(data.iterrows()):
            value = row.iloc[-1] if hasattr(row.iloc[-1], '__float__') else row.iloc[-1]
            formatted = format_str.format(int(value)) if ':,' in format_str else format_str.format(value)
            ax.text(value, i, f" {formatted}", va='center', fontsize=fontsize, fontweight='bold')


def quick_barh(
    data_dict: dict,
    title: str,
    xlabel: str,
    target_id: str,
    colormap: str = 'Reds',
    figsize: Tuple[int, int] = (10, 8)
) -> None:
    """
    Create and display a horizontal bar chart in one call.

    Convenience function for the most common use case.

    Args:
        data_dict: Dictionary with 'labels' and 'values' keys
        title: Chart title
        xlabel: X-axis label
        target_id: HTML element ID to render into
        colormap: Matplotlib colormap name
        figsize: Figure size as (width, height)

    Example:
        quick_barh(
            {'labels': ['A', 'B', 'C'], 'values': [10, 20, 30]},
            "My Chart",
            "Count",
            "chart-div"
        )
    """
    factory = MatplotlibFactory()
    fig, ax = factory.create_figure(figsize=figsize)

    import numpy as np
    colors = plt.cm.get_cmap(colormap)(np.linspace(0.3, 0.9, len(data_dict['labels'])))

    ax.barh(data_dict['labels'], data_dict['values'], color=colors)
    factory.style_bar_chart(ax, title, xlabel)

    plt.tight_layout()
    factory.display(fig, target_id)
