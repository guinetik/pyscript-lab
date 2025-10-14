"""
Bokeh Top Hosts Bar Chart Example

Shows top 10 hosts by listing count using vertical bars.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import pandas as pd
from lib.data import load_csv
from bokeh_utils import BokehFactory
from bokeh.models import ColumnDataSource
from bokeh.palettes import brewer
from bokeh.transform import factor_cmap

print("🐍 Starting Bokeh Bar Chart example...")

# Load data using shared DataLoader (should be cached!)
airbnb = load_csv("airbnb", "/data/airbnb_listings.csv")

# Prepare bar chart data
print("🐍 Preparing top hosts data...")
host = pd.DataFrame(airbnb.host_id.value_counts()[:10])
host.reset_index(inplace=True)

# Handle pandas version differences
if 'index' in host.columns:
    host.rename(columns={'index': 'host_id', 'host_id': 'count'}, inplace=True)
else:
    host.columns = ['host_id', 'count']

host['count'] = pd.to_numeric(host['count'], errors='coerce')
host['host_id'] = host['host_id'].astype(str)
host_id = host['host_id'].to_list()
count = host['count'].to_list()

# Create figure using BokehFactory
factory = BokehFactory(tools="box_select,pan,wheel_zoom,box_zoom,reset,help,hover")
p = factory.create_figure(
    title="Top 10 Hosts by Listing Count",
    tooltips="Host @host_id: @count listings",
    sizing_mode='scale_width',
    x_range=host_id
)

# Add vertical bars
source = ColumnDataSource(data=dict(host_id=host_id, count=count))
p.vbar(
    x='host_id', top='count',
    width=0.9,
    source=source,
    line_color='white',
    fill_color=factor_cmap(
        'host_id',
        palette=brewer['Set3'][len(count)],
        factors=host_id
    )
)

# Configure axes
p.xgrid.grid_line_color = None
p.y_range.start = 0
p.y_range.end = 300
p.xaxis.axis_label = 'Host ID'
p.yaxis.axis_label = 'Number of Listings'

# Embed the chart using BokehFactory
factory.embed(p, "matplotlib-bar-output")

print("✅ Bar chart rendered successfully!")
