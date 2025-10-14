"""
COVID-19 Cases vs Deaths Scatter Plot

Scatter plot showing correlation between confirmed cases and deaths.
Uses log scale for both axes to handle wide value range.
Color-coded by WHO region.
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import matplotlib.pyplot as plt
from lib.data import load_csv
from matplotlib_utils import MatplotlibFactory
from matplotlib.patches import Patch

print("🐍 Starting Cases vs Deaths Scatter Plot example...")

# Load data using shared DataLoader (should be cached!)
df = load_csv("covid_data", "/data/covid_country.csv")

# Create chart using MatplotlibFactory
factory = MatplotlibFactory()
fig, ax = factory.create_figure(figsize=(10, 8))

# Color by WHO Region
regions = df['WHO Region'].unique()
colors_map = {region: plt.cm.tab10(i) for i, region in enumerate(regions)}
colors = [colors_map[region] for region in df['WHO Region']]

# Create scatter plot
scatter = ax.scatter(
    df['Confirmed'],
    df['Deaths'],
    c=colors,
    alpha=0.6,
    s=100,
    edgecolors='black',
    linewidth=0.5
)

# Apply styling
ax.set_xlabel('Confirmed Cases', fontsize=12, fontweight='bold')
ax.set_ylabel('Deaths', fontsize=12, fontweight='bold')
ax.set_title('COVID-19: Confirmed Cases vs Deaths',
            fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)

# Log scale for better visualization
ax.set_xscale('log')
ax.set_yscale('log')

# Add legend
legend_elements = [Patch(facecolor=colors_map[region], label=region)
                  for region in regions]
ax.legend(handles=legend_elements, loc='upper left', fontsize=8)

plt.tight_layout()
factory.display(fig, "covid-chart3")

print("✅ Cases vs Deaths scatter plot rendered successfully!")
