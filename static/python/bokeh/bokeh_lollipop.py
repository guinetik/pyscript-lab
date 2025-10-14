"""
Bokeh Neighbourhood Lollipop Chart Example

Shows listings by neighborhood group using lollipop chart.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import pandas as pd
from lib.data import load_csv
from bokeh_utils import BokehFactory

print("🐍 Starting Bokeh Lollipop Chart example...")

# Load data using shared DataLoader (should be cached!)
airbnb = load_csv("airbnb", "/data/airbnb_listings.csv")

# Prepare lollipop data
print("🐍 Preparing neighbourhood data...")
nbh = pd.DataFrame(airbnb.neighbourhood_group.value_counts())
nbh.reset_index(inplace=True)

# Handle pandas version differences
if 'index' in nbh.columns:
    nbh.rename(
        columns={'index': 'neighbourhood_group', 'neighbourhood_group': 'count'},
        inplace=True
    )
else:
    nbh.columns = ['neighbourhood_group', 'count']

nbh['count'] = pd.to_numeric(nbh['count'], errors='coerce')
neighbourhood_group = nbh['neighbourhood_group'].to_list()
count = nbh['count'].to_list()

# Create figure using BokehFactory
factory = BokehFactory(tools="box_select,pan,wheel_zoom,box_zoom,reset,help,hover")
dot = factory.create_figure(
    title="Listings by Neighbourhood Group",
    sizing_mode='scale_width',
    y_range=neighbourhood_group,
    x_range=[0, 10000]
)

# Create lollipop (segments + circles)
dot.segment(0, neighbourhood_group, count, neighbourhood_group,
            line_width=2, line_color="green")
dot.circle(count, neighbourhood_group, size=15,
           fill_color="orange", line_color="green", line_width=3)

# Configure axes
dot.x_range.start = 0
dot.x_range.end = 10500

# Embed the chart using BokehFactory
factory.embed(dot, "matplotlib-lollipop-output")

print("✅ Lollipop chart rendered successfully!")
