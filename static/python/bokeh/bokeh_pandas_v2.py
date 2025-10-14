"""
Bokeh + Pandas Airbnb Data Visualization

This module demonstrates advanced data visualization using Bokeh and Pandas in PyScript.
It analyzes Airbnb listings data and creates multiple interactive visualizations:

1. Correlation Heatmap - Shows relationships between numeric variables
2. Pie Chart - Distribution of room types
3. Jittered Scatter - Price distribution by room type
4. Bar Chart - Top 10 hosts by listing count
5. Lollipop Chart - Listings by neighborhood group

These examples showcase:
- Loading and processing CSV data with Pandas
- Creating multiple chart types with Bokeh
- Color mapping and palettes
- Interactive tooltips and tools
- Responsive sizing for web displays

Author: Guinetik
Adapted from: https://www.kaggle.com/code/cindyteh/data-visualization-with-bokeh
"""

from pyodide.http import open_url
from js import Bokeh, console, JSON
from typing import Optional

import numpy as np
import pandas as pd
import json
from math import pi

from bokeh.embed import json_item
from bokeh.models import ColumnDataSource, BasicTicker, ColorBar, LinearColorMapper
from bokeh.palettes import Viridis256, brewer
from bokeh.plotting import figure
from bokeh.transform import transform, cumsum, jitter, factor_cmap
from bokeh.resources import CDN


class BokehAirbnbPandas:
    """
    A comprehensive data visualization class using Bokeh and Pandas.

    This class loads Airbnb listing data and creates five different types of
    interactive visualizations to explore the dataset from multiple angles.

    Features:
    - Automated data loading from CSV
    - Five different chart types
    - Interactive tools (pan, zoom, hover, etc.)
    - Responsive sizing for web display
    - Color-coded visualizations
    - Statistical analysis (correlation)

    Attributes:
        data_url (str): URL or path to the CSV data file.
        airbnb (pd.DataFrame): The loaded Airbnb dataset.
        tools (str): Bokeh tools configuration string.
    """

    # Standard tools available for all charts
    TOOLS = "box_select,pan,wheel_zoom,box_zoom,reset,help,hover"

    def __init__(self, data_url: str = "/data/airbnb_listings.csv"):
        """
        Initialize the BokehAirbnbPandas visualizer.

        Args:
            data_url (str, optional): Path or URL to the Airbnb CSV data file.
                                     Defaults to "/data/airbnb_listings.csv".

        Example:
            >>> visualizer = BokehAirbnbPandas()
            >>> visualizer = BokehAirbnbPandas(data_url="/data/custom_listings.csv")
        """
        self.data_url = data_url
        self.airbnb = None
        self.tools = self.TOOLS

        print("🐍 BokehAirbnbPandas initialized")
        print("🐍 BokehAirbnbPandas initialized")

    def _load_data(self):
        """
        Load the Airbnb dataset from the specified URL.

        This method:
        1. Fetches the CSV file using pyodide.http
        2. Loads it into a Pandas DataFrame
        3. Validates the data was loaded successfully
        4. Logs the number of rows loaded

        Raises:
            Exception: If data loading fails or results in an empty DataFrame.
        """
        try:
            print("🐍 Loading Airbnb data from CSV...")
            print(f"🐍 Loading data from: {self.data_url}")

            url_content = open_url(self.data_url)
            self.airbnb = pd.read_csv(url_content)

            if self.airbnb.empty:
                raise ValueError("Loaded DataFrame is empty")

            print(f"🐍 Successfully loaded {len(self.airbnb)} rows of data")
            print(f"✅ Loaded {len(self.airbnb)} rows, {len(self.airbnb.columns)} columns")

        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise

    def _create_correlation_heatmap(self):
        """
        Create an interactive correlation heatmap.

        This visualization shows the correlation coefficients between all numeric
        variables in the dataset. Useful for identifying relationships between
        features like price, reviews, availability, etc.

        The heatmap uses:
        - Viridis256 color palette for value mapping
        - Hover tooltips showing exact correlation values
        - Interactive tools for exploration

        Returns:
            The chart is embedded in the element with ID "chart"
        """
        print("🐍 Creating correlation heatmap...")
        print("🐍 Creating correlation heatmap...")

        # Select only numeric columns for correlation
        numeric_cols = self.airbnb.select_dtypes(include=[np.number])
        corrmat = numeric_cols.corr()

        # Prepare correlation matrix for Bokeh
        corrmat.index.name = 'AllColumns1'
        corrmat.columns.name = 'AllColumns2'
        corrmat = corrmat.stack().rename("value").reset_index()

        # Color mapper for correlation values (-1 to 1)
        mapper = LinearColorMapper(
            palette=Viridis256,
            low=corrmat.value.min(),
            high=corrmat.value.max()
        )

        # Create figure
        p = figure(
            tools=self.tools,
            tooltips="@value{0.00}",
            sizing_mode='scale_width',
            height=400,
            title="Airbnb Correlation Heatmap",
            x_range=list(corrmat.AllColumns1.drop_duplicates()),
            y_range=list(corrmat.AllColumns2.drop_duplicates()),
            toolbar_location="right",
            x_axis_location="below"
        )

        # Create heatmap rectangles
        p.rect(
            x="AllColumns1",
            y="AllColumns2",
            width=1,
            height=1,
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

        # Embed the chart
        p_json = json.dumps(json_item(p, "chart"))
        Bokeh.embed.embed_item(JSON.parse(p_json))

        print("✅ Correlation heatmap rendered")
        print("✅ Chart 1 (heatmap) rendered")

    def _create_room_type_pie_chart(self):
        """
        Create a pie chart showing the distribution of room types.

        This visualization displays what percentage of listings fall into each
        room type category (e.g., Entire home/apt, Private room, Shared room).

        Features:
        - Wedge slices proportional to count
        - Color-coded using Spectral palette
        - Interactive tooltips showing room type and count
        - Legend showing all categories

        Returns:
            The chart is embedded in the element with ID "chart2"
        """
        print("🐍 Creating room type pie chart...")
        print("🐍 Creating room type pie chart...")

        # Prepare data for pie chart
        room = pd.DataFrame(self.airbnb.room_type.value_counts())
        room.reset_index(inplace=True)

        # Handle newer pandas versions where column names might differ
        if 'index' in room.columns:
            room.rename(columns={'index': 'room_type', 'room_type': 'count'}, inplace=True)
        else:
            # Pandas 2.0+ uses 'room_type' and 'count' by default
            room.columns = ['room_type', 'count']

        # Ensure count is numeric
        room['count'] = pd.to_numeric(room['count'], errors='coerce')
        room['angle'] = room['count'] / room['count'].sum() * 2 * pi
        room['color'] = brewer['Spectral'][len(room)]
        room = room.to_dict('list')

        # Create pie chart
        source = ColumnDataSource(room)
        p = figure(
            height=400,
            sizing_mode='scale_width',
            title="Distribution of Room Types",
            tools=self.tools,
            tooltips="@room_type: @count",
            x_range=(-0.5, 1.0)
        )

        # Create wedges
        p.wedge(
            x=0,
            y=1,
            radius=0.4,
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

        # Embed the chart
        p_json = json.dumps(json_item(p, "chart2"))
        Bokeh.embed.embed_item(JSON.parse(p_json))

        print("✅ Pie chart rendered")
        print("✅ Chart 2 (pie chart) rendered")

    def _create_price_jitter_plot(self):
        """
        Create a jittered scatter plot showing price distribution by room type.

        This visualization shows how prices vary within each room type category.
        Jittering (random vertical displacement) prevents points from overlapping,
        making it easier to see the density of listings at different price points.

        Features:
        - Jittered points to show distribution density
        - Semi-transparent points (alpha=0.3) to show overlaps
        - Y-axis shows room type categories
        - X-axis shows price range

        Returns:
            The chart is embedded in the element with ID "chart3"
        """
        print("🐍 Creating price jitter plot...")
        print("🐍 Creating price jitter plot...")

        # Prepare data
        data = self.airbnb[['room_type', 'price']].copy()
        cats = list(self.airbnb.room_type.unique())
        source = ColumnDataSource(data)

        print(f"🐍 Jitter plot - Found {len(cats)} room type categories")
        print(f"🐍 Jitter plot - Data shape: {len(data)} rows")

        # Create figure with tooltips
        p = figure(
            sizing_mode='scale_width',
            height=400,
            tools=self.tools,
            y_range=cats,
            title="Price Distribution by Room Type",
            tooltips=[("Room Type", "@room_type"), ("Price", "$@price{0,0}")]
        )

        # Create jittered scatter plot
        p.circle(
            x='price',
            y=jitter('room_type', width=0.3, range=p.y_range),
            source=source,
            alpha=0.3,
            size=5
        )

        # Set x-axis range
        p.x_range.start = 0
        p.x_range.end = 10100
        p.x_range.range_padding = 0

        # Remove horizontal grid lines for cleaner look
        p.ygrid.grid_line_color = None

        # Add axis labels
        p.xaxis.axis_label = 'Price ($)'
        p.yaxis.axis_label = 'Room Type'

        # Embed the chart
        p_json = json.dumps(json_item(p, "chart3"))
        Bokeh.embed.embed_item(JSON.parse(p_json))

        print("✅ Price jitter plot rendered")
        print("✅ Chart 3 (jitter plot) rendered")

    def _create_top_hosts_bar_chart(self):
        """
        Create a bar chart showing the top 10 hosts by listing count.

        This visualization identifies the most active hosts on the platform
        by showing how many listings each of the top 10 hosts manages.

        Features:
        - Vertical bars for each host
        - Color-coded bars using Set3 palette
        - Hover tooltips showing host ID and count
        - Sorted by listing count (descending)

        Returns:
            The chart is embedded in the element with ID "chart4"
        """
        print("🐍 Creating top hosts bar chart...")
        print("🐍 Creating top hosts bar chart...")

        # Prepare data for bar chart
        host = pd.DataFrame(self.airbnb.host_id.value_counts()[:10])
        host.reset_index(inplace=True)

        # Handle newer pandas versions where column names might differ
        if 'index' in host.columns:
            host.rename(columns={'index': 'host_id', 'host_id': 'count'}, inplace=True)
        else:
            # Pandas 2.0+ uses 'host_id' and 'count' by default
            host.columns = ['host_id', 'count']

        # Ensure count is numeric and host_id is string
        host['count'] = pd.to_numeric(host['count'], errors='coerce')
        host['host_id'] = host['host_id'].astype(str)
        host_id = host['host_id'].to_list()
        count = host['count'].to_list()

        # Create data source
        source = ColumnDataSource(data=dict(host_id=host_id, count=count))

        # Create figure
        p = figure(
            x_range=host_id,
            height=400,
            sizing_mode='scale_width',
            tools=self.tools,
            tooltips="Host @host_id: @count listings",
            title="Top 10 Hosts by Listing Count"
        )

        # Create vertical bars
        p.vbar(
            x='host_id',
            top='count',
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

        # Embed the chart
        p_json = json.dumps(json_item(p, "chart4"))
        Bokeh.embed.embed_item(JSON.parse(p_json))

        print("✅ Bar chart rendered")
        print("✅ Chart 4 (bar chart) rendered")

    def _create_neighbourhood_lollipop_chart(self):
        """
        Create a lollipop chart showing listings by neighborhood group.

        A lollipop chart is a variation of a bar chart where bars are replaced
        with lines and dots. It's effective for showing rankings and comparisons
        while using less visual weight than traditional bars.

        Features:
        - Green segments (sticks) from 0 to the count
        - Orange circles (lollipops) at the end of each stick
        - Horizontal orientation for easy label reading
        - Sorted by listing count

        Returns:
            The chart is embedded in the element with ID "chart5"
        """
        print("🐍 Creating neighbourhood lollipop chart...")
        print("🐍 Creating neighbourhood lollipop chart...")

        # Prepare data for lollipop chart
        nbh = pd.DataFrame(self.airbnb.neighbourhood_group.value_counts())
        nbh.reset_index(inplace=True)

        # Handle newer pandas versions where column names might differ
        if 'index' in nbh.columns:
            nbh.rename(
                columns={
                    'index': 'neighbourhood_group',
                    'neighbourhood_group': 'count'
                },
                inplace=True
            )
        else:
            # Pandas 2.0+ uses 'neighbourhood_group' and 'count' by default
            nbh.columns = ['neighbourhood_group', 'count']

        # Ensure count is numeric
        nbh['count'] = pd.to_numeric(nbh['count'], errors='coerce')
        neighbourhood_group = nbh['neighbourhood_group'].to_list()
        count = nbh['count'].to_list()

        # Create figure
        dot = figure(
            title="Listings by Neighbourhood Group",
            sizing_mode='scale_width',
            height=400,
            tools=self.tools,
            y_range=neighbourhood_group,
            x_range=[0, 10000]
        )

        # Create lollipop sticks (segments)
        dot.segment(
            0,
            neighbourhood_group,
            count,
            neighbourhood_group,
            line_width=2,
            line_color="green"
        )

        # Create lollipop heads (circles)
        dot.circle(
            count,
            neighbourhood_group,
            size=15,
            fill_color="orange",
            line_color="green",
            line_width=3
        )

        # Configure x-axis range
        dot.x_range.start = 0
        dot.x_range.end = 10500

        # Embed the chart
        p_json = json.dumps(json_item(dot, "chart5"))
        Bokeh.embed.embed_item(JSON.parse(p_json))

        print("✅ Lollipop chart rendered")
        print("✅ Chart 5 (lollipop chart) rendered")

    def run(self):
        """
        Execute the complete visualization workflow.

        This method orchestrates the entire process:
        1. Loads the Airbnb dataset from CSV
        2. Creates and embeds all five visualizations:
           - Correlation heatmap
           - Room type pie chart
           - Price jitter plot
           - Top hosts bar chart
           - Neighbourhood lollipop chart

        The charts are embedded in elements with IDs: chart, chart2, chart3, chart4, chart5

        Example:
            >>> visualizer = BokehAirbnbPandas()
            >>> visualizer.run()
        """
        print("🐍 Starting Bokeh + Pandas Airbnb visualization...")
        print("🐍 Starting Bokeh + Pandas example...")

        try:
            # Load data
            self._load_data()

            # Create all visualizations
            self._create_correlation_heatmap()
            self._create_room_type_pie_chart()
            self._create_price_jitter_plot()
            self._create_top_hosts_bar_chart()
            self._create_neighbourhood_lollipop_chart()

            print("✅ All visualizations completed successfully!")
            print("✅ All 5 charts rendered successfully!")

        except Exception as e:
            error_msg = f"Visualization failed: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise


# Entry point: Create instance and run the example
if __name__ == "__main__":
    visualizer = BokehAirbnbPandas()
    visualizer.run()
