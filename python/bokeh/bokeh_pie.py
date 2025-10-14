"""
Bokeh Room Type Pie Chart Example

Shows distribution of room types using shared data loading.
Tests if DataLoader singleton caches data across separate PyScript files.

Author: Guinetik
"""

import pandas as pd
from math import pi
from lib.data import load_csv
from bokeh_utils import BokehFactory
from bokeh.models import ColumnDataSource
from bokeh.palettes import brewer
from bokeh.transform import cumsum

print("🐍 Starting Bokeh Pie Chart example...")

# Load data using shared DataLoader
# This should be instant if heatmap already loaded it!
airbnb = load_csv("airbnb", "/data/airbnb_listings.csv")

# Prepare pie chart data
print("🐍 Preparing room type data...")
room = pd.DataFrame(airbnb.room_type.value_counts())
room.reset_index(inplace=True)

# Handle pandas version differences
if 'index' in room.columns:
    room.rename(columns={'index': 'room_type', 'room_type': 'count'}, inplace=True)
else:
    room.columns = ['room_type', 'count']

room['count'] = pd.to_numeric(room['count'], errors='coerce')
room['angle'] = room['count'] / room['count'].sum() * 2 * pi
room['color'] = brewer['Spectral'][len(room)]

# Create figure using BokehFactory
factory = BokehFactory(tools="box_select,pan,wheel_zoom,box_zoom,reset,help,hover")
p = factory.create_figure(
    title="Distribution of Room Types",
    tooltips="@room_type: @count",
    sizing_mode='scale_width',
    x_range=(-0.5, 1.0)
)

# Create wedges
source = ColumnDataSource(room.to_dict('list'))
p.wedge(
    x=0, y=1, radius=0.4,
    start_angle=cumsum('angle', include_zero=True),
    end_angle=cumsum('angle'),
    line_color="white",
    fill_color='color',
    legend_field='room_type',
    source=source
)

# Hide axes for cleaner pie chart
p.axis.axis_label = None
p.axis.visible = False
p.grid.grid_line_color = None

# Embed the chart using BokehFactory
factory.embed(p, "matplotlib-pie-output")

print("✅ Pie chart rendered successfully!")
