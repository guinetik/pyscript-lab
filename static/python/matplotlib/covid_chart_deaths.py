"""
COVID-19 Top Deaths Chart

Horizontal bar chart showing top 20 countries by death toll.
Uses heatmap-style coloring where intensity increases with death count.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import matplotlib.pyplot as plt
import numpy as np
from lib.data import load_csv
from matplotlib_utils import MatplotlibFactory

print("🐍 Starting Top Deaths Chart example...")

# Load data using shared DataLoader (will be cached!)
df = load_csv("covid_data", "/data/covid_country.csv")

print(f"📊 Loaded data for {len(df)} countries/regions")
print(f"Total Deaths: {df['Deaths'].sum():,}")

# Prepare data - top 20 countries by deaths
top_deaths = df.nlargest(20, 'Deaths')[['Country/Region', 'Deaths']].sort_values('Deaths')

# Create chart using MatplotlibFactory
factory = MatplotlibFactory()
fig, ax = factory.create_figure(figsize=(10, 8))

# Create bars with heatmap coloring
colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(top_deaths)))
bars = ax.barh(top_deaths['Country/Region'], top_deaths['Deaths'], color=colors)

# Apply styling
factory.style_bar_chart(
    ax,
    title='Top 20 Countries by COVID-19 Deaths',
    xlabel='Total Deaths',
    grid=True,
    grid_axis='x'
)

# Add value labels
for i, (idx, row) in enumerate(top_deaths.iterrows()):
    ax.text(row['Deaths'], i, f" {int(row['Deaths']):,}",
           va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
factory.display(fig, "covid-chart1")

print("✅ Top Deaths chart rendered successfully!")
