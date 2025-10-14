"""
COVID-19 Deaths Choropleth Map

Interactive world map showing total deaths by country.
Uses red color scale where darker shades indicate higher death tolls.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import asyncio
from lib.data import load_csv
from plotly_utils import PlotlyFactory

print("🐍 Starting Deaths Map example...")

# Load data with ISO-3 codes (will be cached!)
df_raw = load_csv("covid_iso3_data", "/data/covid_country_with_iso3.csv")

# Filter out rows with missing ISO-3 codes
df = df_raw[df_raw['CountryIso3'].notna() & (df_raw['CountryIso3'] != '')].copy()

print(f"🌍 Loaded {len(df)} countries with ISO-3 codes")
print(f"Total Deaths: {df['Deaths'].sum():,}")

# Create map using PlotlyFactory
factory = PlotlyFactory()
fig = factory.create_choropleth(
    locations=df['CountryIso3'],
    z=df['Deaths'],
    colorscale='Reds',
    colorbar_title='Deaths',
    title='COVID-19 Deaths by Country',
    hover_text=df['Country/Region']
)

# Display with async delay for Plotly initialization
async def display_map():
    await factory.display_async(fig, "map1")
    print("✅ Deaths map rendered successfully!")

# Run async display
await display_map()
