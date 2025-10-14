"""
Bokeh Price Jitter Plot Example

Shows price distribution by room type using jittered scatter plot.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

from lib.data import load_csv
from bokeh_utils import BokehFactory
from bokeh.models import ColumnDataSource
from bokeh.transform import jitter

print("🐍 Starting Bokeh Jitter Plot example...")

# Load data using shared DataLoader (should be cached!)
airbnb = load_csv("airbnb", "/data/airbnb_listings.csv")

# Prepare data
print("🐍 Preparing jitter plot data...")
data = airbnb[['room_type', 'price']].copy()
cats = list(airbnb.room_type.unique())
source = ColumnDataSource(data)

# Create figure using BokehFactory
factory = BokehFactory(tools="box_select,pan,wheel_zoom,box_zoom,reset,help,hover")
p = factory.create_figure(
    title="Price Distribution by Room Type",
    tooltips=[("Room Type", "@room_type"), ("Price", "$@price{0,0}")],
    sizing_mode='scale_width',
    y_range=cats
)

# Add jittered scatter
p.circle(
    x='price',
    y=jitter('room_type', width=0.3, range=p.y_range),
    source=source,
    alpha=0.3,
    size=5
)

# Configure axes
p.x_range.start = 0
p.x_range.end = 10100
p.x_range.range_padding = 0
p.ygrid.grid_line_color = None
p.xaxis.axis_label = 'Price ($)'
p.yaxis.axis_label = 'Room Type'

# Embed the chart using BokehFactory
factory.embed(p, "matplotlib-jitter-output")

print("✅ Jitter plot rendered successfully!")
