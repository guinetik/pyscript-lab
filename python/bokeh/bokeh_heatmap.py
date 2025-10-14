"""
Bokeh Correlation Heatmap Example

Demonstrates creating a correlation heatmap using shared data loading.
This example tests the DataLoader singleton pattern - if multiple charts
on the same page use the same dataset, it should only load once.

Author: Guinetik
"""

import numpy as np
from lib.data import load_csv
from bokeh_utils import BokehFactory
from bokeh.models import ColumnDataSource, BasicTicker, ColorBar, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.transform import transform

print("🐍 Starting Bokeh Heatmap example...")

# Load data using shared DataLoader
# If another chart already loaded "airbnb", this will be instant!
airbnb = load_csv("airbnb", "/data/airbnb_listings.csv")

# Prepare correlation data
print("🐍 Calculating correlations...")
numeric_cols = airbnb.select_dtypes(include=[np.number])
corrmat = numeric_cols.corr()

# Format for Bokeh
corrmat.index.name = 'AllColumns1'
corrmat.columns.name = 'AllColumns2'
corrmat = corrmat.stack().rename("value").reset_index()

# Color mapper for correlation values
mapper = LinearColorMapper(
    palette=Viridis256,
    low=corrmat.value.min(),
    high=corrmat.value.max()
)

# Create figure using BokehFactory
factory = BokehFactory(tools="box_select,pan,wheel_zoom,box_zoom,reset,help,hover")
p = factory.create_figure(
    title="Airbnb Correlation Heatmap",
    tooltips="@value{0.00}",
    sizing_mode='scale_width',
    x_range=list(corrmat.AllColumns1.drop_duplicates()),
    y_range=list(corrmat.AllColumns2.drop_duplicates()),
    toolbar_location="right",
    x_axis_location="below"
)

# Add heatmap rectangles
p.rect(
    x="AllColumns1", y="AllColumns2",
    width=1, height=1,
    source=ColumnDataSource(corrmat),
    line_color=None,
    fill_color=transform('value', mapper)
)

# Add color bar legend
color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    ticker=BasicTicker(desired_num_ticks=10)
)
p.add_layout(color_bar, 'right')

# Rotate x-axis labels for readability
p.xaxis.major_label_orientation = "vertical"

# Embed the chart using BokehFactory
factory.embed(p, "matplotlib-heatmap-output")

print("✅ Heatmap rendered successfully!")
