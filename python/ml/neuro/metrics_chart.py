"""
Bokeh Metrics Chart for Training Visualization
"""

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.embed import components
from bokeh.io import output_notebook, push_notebook
from js import window, document, console


class MetricsChart:
    """Live-updating Bokeh chart for training metrics."""
    
    def __init__(self, container_id='metrics-chart'):
        self.container_id = container_id
        self.source = None
        self.plot = None
        
    def initialize(self):
        """Create initial chart."""
        # Data source
        self.source = ColumnDataSource(data={
            'generation': [],
            'fitness': [],
            'distance': []
        })
        
        # Create figure
        self.plot = figure(
            title='Training Progress',
            x_axis_label='Generation',
            y_axis_label='Value',
            width=400,
            height=250,
            tools='pan,wheel_zoom,reset',
            sizing_mode='stretch_width'
        )
        
        # Fitness line
        self.plot.line(
            'generation', 'fitness',
            source=self.source,
            line_width=2,
            color='#22c55e',
            legend_label='Fitness'
        )
        
        # Distance line
        self.plot.line(
            'generation', 'distance',
            source=self.source,
            line_width=2,
            color='#3b82f6',
            legend_label='Distance'
        )
        
        # Hover tool
        hover = HoverTool(
            tooltips=[
                ('Generation', '@generation'),
                ('Fitness', '@fitness{0.0}'),
                ('Distance', '@distance{0}')
            ]
        )
        self.plot.add_tools(hover)
        
        # Style
        self.plot.legend.location = 'top_left'
        self.plot.legend.click_policy = 'hide'
        self.plot.background_fill_color = '#f8fafc'
        self.plot.border_fill_color = '#ffffff'
        
        console.log("[MetricsChart] Initialized")
        return self.plot
        
    def update(self, generation, fitness, distance):
        """Add new data point."""
        if self.source is None:
            return
            
        # Append to data
        self.source.stream({
            'generation': [generation],
            'fitness': [fitness],
            'distance': [distance]
        })
        
        # Auto-scroll to show recent data
        if generation > 20:
            self.plot.x_range.start = generation - 20
            self.plot.x_range.end = generation + 2
            
    def clear(self):
        """Clear chart data."""
        if self.source is None:
            return
            
        self.source.data = {
            'generation': [],
            'fitness': [],
            'distance': []
        }


# Global instance
_chart = None


def get_chart():
    """Get or create chart instance."""
    global _chart
    if _chart is None:
        _chart = MetricsChart()
    return _chart


def init_chart():
    """Initialize chart from JS."""
    chart = get_chart()
    return chart.initialize()


def update_chart(generation, fitness, distance):
    """Update chart from JS."""
    chart = get_chart()
    chart.update(generation, fitness, distance)


def clear_chart():
    """Clear chart from JS."""
    chart = get_chart()
    chart.clear()


# Expose to window
def setup_chart_bridge():
    """Set up JS bridge for chart."""
    window.initMetricsChart = init_chart
    window.updateMetricsChart = update_chart
    window.clearMetricsChart = clear_chart
    console.log("[MetricsChart] JS bridge registered")
