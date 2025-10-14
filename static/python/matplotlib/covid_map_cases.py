"""
COVID-19 Confirmed Cases Choropleth Map

Interactive world map showing confirmed cases by country.
Uses blue color scale where darker shades indicate more confirmed cases.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import asyncio
from lib.data import load_csv
from plotly_utils import PlotlyFactory

print("🐍 Starting Confirmed Cases Map example...")

# Load data with ISO-3 codes (should be cached!)
df_raw = load_csv("covid_iso3_data", "/data/covid_country_with_iso3.csv")

# Filter out rows with missing ISO-3 codes
df = df_raw[df_raw['CountryIso3'].notna() & (df_raw['CountryIso3'] != '')].copy()

print(f"Total Confirmed Cases: {df['Confirmed'].sum():,}")

# Create map using PlotlyFactory
factory = PlotlyFactory()
fig = factory.create_choropleth(
    locations=df['CountryIso3'],
    z=df['Confirmed'],
    colorscale='Blues',
    colorbar_title='Confirmed',
    title='COVID-19 Confirmed Cases by Country',
    hover_text=df['Country/Region']
)

# Display with async delay for Plotly initialization
async def display_map():
    await factory.display_async(fig, "map2")
    print("✅ Confirmed Cases map rendered successfully!")

# Run async display
await display_map()
