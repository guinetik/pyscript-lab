"""
COVID-19 Interactive World Maps - Geographic Visualization

Demonstrates Plotly choropleth maps for geographic data visualization.
Creates 4 interactive world maps showing different COVID-19 metrics:
- Total Deaths
- Confirmed Cases
- Case Fatality Rate
- New Cases Activity

Uses Natural Earth projection for visually pleasing representation.
All maps are interactive: hover, zoom, pan, and download features.

Data Source: covid_country.csv (187 countries/regions)

Author: PyScript Lab
"""
from pyscript import display, document
import pandas as pd
from pyodide.http import open_url
import asyncio

# Import plotly after ensuring it's loaded
import plotly.graph_objects as go


class CovidWorldMapsVisualizer:
    """
    COVID-19 Geographic Data Visualization Suite
    
    Generates interactive Plotly choropleth maps showing COVID-19 metrics
    across countries. Each map is rendered to a specific target element.
    
    Attributes:
        df (pd.DataFrame): The loaded COVID-19 dataset
    """
    
    def __init__(self):
        """
        Initialize the visualizer by loading data and generating all maps.
        """
        self.df = None
        self.load_data()
    
    def load_data(self):
        """
        Load COVID-19 data from CSV file with ISO-3 country codes.
        
        Uses ISO-3 codes for reliable country matching in Plotly.
        Filters out countries without valid ISO-3 codes.
        """
        df_raw = pd.read_csv(open_url('/data/covid_country_with_iso3.csv'))
        
        # Filter out rows with missing ISO-3 codes
        self.df = df_raw[df_raw['CountryIso3'].notna() & (df_raw['CountryIso3'] != '')].copy()
        
        print(f"🌍 Loaded {len(self.df)} countries with ISO-3 codes (filtered {len(df_raw) - len(self.df)} without codes)")
    
    def _create_base_layout(self, title):
        """
        Create base layout configuration for choropleth maps.
        
        Args:
            title (str): The title text for the map
            
        Returns:
            dict: Layout configuration for Plotly figure
        """
        return dict(
            title_text=title,
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth'
            ),
            height=500,
            width=None,
            autosize=True,
            margin={"r":10,"t":50,"l":10,"b":10}
        )
    
    def _create_and_display_choropleth(self, locations_iso3, z, colorscale, colorbar_title,
                                       title, target_id, hover_text=None):
        """
        Factory method to create and display a choropleth map.

        Eliminates repetition by centralizing figure creation and display logic.
        Uses ISO-3 codes for reliable country matching.

        Args:
            locations_iso3 (pd.Series): ISO-3 country codes (e.g., 'USA', 'GBR')
            z (pd.Series): Data values to visualize
            colorscale (str): Plotly colorscale name (e.g., 'Reds', 'Blues')
            colorbar_title (str): Title for the color legend
            title (str): Map title
            target_id (str): DOM element ID to display the map
            hover_text (pd.Series, optional): Text to show on hover (country names)
        """
        # Convert pandas Series to lists to ensure proper serialization
        locations_list = locations_iso3.tolist()
        z_list = z.tolist()
        text_list = hover_text.tolist() if hover_text is not None else locations_list

        fig = go.Figure(data=go.Choropleth(
            locations=locations_list,
            z=z_list,
            locationmode='ISO-3',
            colorscale=colorscale,
            text=text_list,
            colorbar_title=colorbar_title
        ))

        fig.update_layout(**self._create_base_layout(title))
        display(fig, target=target_id)
    
    async def generate_deaths_map(self):
        """
        Generate interactive choropleth map of total deaths by country.

        Uses red color scale where darker shades indicate higher death tolls.
        Displays in 'map1' element.
        """
        await asyncio.sleep(0.5)  # Give Plotly time to fully initialize

        self._create_and_display_choropleth(
            locations_iso3=self.df['CountryIso3'],
            z=self.df['Deaths'],
            colorscale='Reds',
            colorbar_title="Deaths",
            title='COVID-19 Deaths by Country',
            target_id="map1",
            hover_text=self.df['Country/Region']
        )
    
    async def generate_confirmed_cases_map(self):
        """
        Generate interactive choropleth map of confirmed cases by country.

        Uses blue color scale where darker shades indicate more confirmed cases.
        Displays in 'map2' element.
        """
        await asyncio.sleep(0.5)  # Give Plotly time to fully initialize
        
        self._create_and_display_choropleth(
            locations_iso3=self.df['CountryIso3'],
            z=self.df['Confirmed'],
            colorscale='Blues',
            colorbar_title="Confirmed",
            title='COVID-19 Confirmed Cases by Country',
            target_id="map2",
            hover_text=self.df['Country/Region']
        )
    
    async def generate_case_fatality_rate_map(self):
        """
        Generate interactive choropleth map of case fatality rates.

        Filters to countries with 1000+ cases for statistical significance.
        Uses yellow-orange-red color scale. Displays in 'map3' element.
        """
        await asyncio.sleep(0.5)  # Give Plotly time to fully initialize
        df_filtered = self.df[self.df['Confirmed'] >= 1000].copy()
        df_filtered['CFR'] = (df_filtered['Deaths'] / df_filtered['Confirmed'] * 100)
        
        self._create_and_display_choropleth(
            locations_iso3=df_filtered['CountryIso3'],
            z=df_filtered['CFR'],
            colorscale='YlOrRd',
            colorbar_title="CFR %",
            title='COVID-19 Case Fatality Rate by Country (1000+ cases)',
            target_id="map3",
            hover_text=df_filtered['Country/Region']
        )
    
    async def generate_new_cases_map(self):
        """
        Generate interactive choropleth map of new/active cases.

        Shows weekly growth and current hotspots. Uses orange color scale.
        Displays in 'map4' element.
        """
        await asyncio.sleep(0.5)  # Give Plotly time to fully initialize
        df_active = self.df[self.df['New cases'] > 0].copy()
        
        self._create_and_display_choropleth(
            locations_iso3=df_active['CountryIso3'],
            z=df_active['New cases'],
            colorscale='Oranges',
            colorbar_title="New Cases",
            title='COVID-19 New Cases by Country',
            target_id="map4",
            hover_text=df_active['Country/Region']
        )
    
    async def generate_all_maps(self):
        """
        Generate all maps concurrently (like Promise.all).
        
        Uses asyncio.gather() to run all map generation methods
        in parallel, allowing better perceived performance.
        Can be called from JavaScript via window.generateAllCovidMaps()
        """
        await asyncio.gather(
            self.generate_deaths_map(),
            self.generate_confirmed_cases_map(),
            self.generate_case_fatality_rate_map(),
            self.generate_new_cases_map()
        )
        print("✅ All world maps generated successfully!")
        print("💡 Hover over countries to see detailed data")


# Instantiate and expose to JavaScript
from pyscript import window
from js import console

visualizer = CovidWorldMapsVisualizer()

# Expose individual map generation methods to window
window.generateDeathsMap = visualizer.generate_deaths_map
window.generateConfirmedCasesMap = visualizer.generate_confirmed_cases_map
window.generateCaseFatalityRateMap = visualizer.generate_case_fatality_rate_map
window.generateNewCasesMap = visualizer.generate_new_cases_map
window.generateAllCovidMaps = visualizer.generate_all_maps

print("✅ COVID Maps module loaded - methods exposed to window")

