"""
COVID-19 Regional Deaths Pie Chart

Pie chart showing death distribution by WHO region.
Groups deaths across Americas, Europe, Africa, etc.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import matplotlib.pyplot as plt
from lib.data import load_csv
from matplotlib_utils import MatplotlibFactory

print("🐍 Starting Regional Deaths Pie Chart example...")

# Load data using shared DataLoader (should be cached!)
df = load_csv("covid_data", "/data/covid_country.csv")

# Group by WHO region
region_deaths = df.groupby('WHO Region')['Deaths'].sum().sort_values(ascending=False)

print(f"🌍 Found {len(region_deaths)} WHO regions")

# Create chart using MatplotlibFactory
factory = MatplotlibFactory()
fig, ax = factory.create_figure(figsize=(10, 8))

# Create pie chart
colors = plt.cm.Set3(range(len(region_deaths)))
wedges, texts, autotexts = ax.pie(
    region_deaths,
    labels=region_deaths.index,
    autopct='%1.1f%%',
    colors=colors,
    startangle=90
)

ax.set_title('COVID-19 Deaths Distribution by WHO Region',
            fontsize=14, fontweight='bold', pad=20)

# Make percentage text bold and white
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(10)

plt.tight_layout()
factory.display(fig, "covid-chart2")

print("✅ Regional Deaths pie chart rendered successfully!")
