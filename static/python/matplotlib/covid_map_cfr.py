"""
COVID-19 Case Fatality Rate Choropleth Map

Interactive world map showing case fatality rates.
Filters to countries with 1000+ cases for statistical significance.
Uses yellow-orange-red color scale.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import asyncio
from lib.data import load_csv
from plotly_utils import PlotlyFactory

print("🐍 Starting Case Fatality Rate Map example...")

# Load data with ISO-3 codes (should be cached!)
df_raw = load_csv("covid_iso3_data", "/data/covid_country_with_iso3.csv")

# Filter out rows with missing ISO-3 codes
df = df_raw[df_raw['CountryIso3'].notna() & (df_raw['CountryIso3'] != '')].copy()

# Filter to countries with 1000+ cases for statistical significance
df_filtered = df[df['Confirmed'] >= 1000].copy()

# Calculate Case Fatality Rate
df_filtered['CFR'] = (df_filtered['Deaths'] / df_filtered['Confirmed'] * 100)

print(f"📊 Analyzing {len(df_filtered)} countries with 1000+ cases")

# Create map using PlotlyFactory
factory = PlotlyFactory()
fig = factory.create_choropleth(
    locations=df_filtered['CountryIso3'],
    z=df_filtered['CFR'],
    colorscale='YlOrRd',
    colorbar_title='CFR %',
    title='COVID-19 Case Fatality Rate by Country (1000+ cases)',
    hover_text=df_filtered['Country/Region']
)

# Display with async delay for Plotly initialization
async def display_map():
    await factory.display_async(fig, "map3")
    print("✅ Case Fatality Rate map rendered successfully!")

# Run async display
await display_map()
