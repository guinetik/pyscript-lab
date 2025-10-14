"""
COVID-19 New Cases Choropleth Map

Interactive world map showing new/active cases by country.
Shows weekly growth and current hotspots.
Uses orange color scale.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import asyncio
from lib.data import load_csv
from plotly_utils import PlotlyFactory

print("🐍 Starting New Cases Map example...")

# Load data with ISO-3 codes (should be cached!)
df_raw = load_csv("covid_iso3_data", "/data/covid_country_with_iso3.csv")

# Filter out rows with missing ISO-3 codes
df = df_raw[df_raw['CountryIso3'].notna() & (df_raw['CountryIso3'] != '')].copy()

# Filter to countries with new cases > 0
df_active = df[df['New cases'] > 0].copy()

print(f"📈 Found {len(df_active)} countries with active new cases")

# Create map using PlotlyFactory
factory = PlotlyFactory()
fig = factory.create_choropleth(
    locations=df_active['CountryIso3'],
    z=df_active['New cases'],
    colorscale='Oranges',
    colorbar_title='New Cases',
    title='COVID-19 New Cases by Country',
    hover_text=df_active['Country/Region']
)

# Display with async delay for Plotly initialization
async def display_map():
    await factory.display_async(fig, "map4")
    print("✅ New Cases map rendered successfully!")

# Run async display
await display_map()
