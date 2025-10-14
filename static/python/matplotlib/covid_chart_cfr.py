"""
COVID-19 Case Fatality Rate Chart

Horizontal bar chart showing case fatality rates.
Displays top 15 countries by CFR (filtered to countries with 1000+ cases
for statistical significance).
Uses shared DataLoader for cached data access.

Author: Guinetik
"""

import matplotlib.pyplot as plt
import numpy as np
from lib.data import load_csv
from matplotlib_utils import MatplotlibFactory

print("🐍 Starting Case Fatality Rate Chart example...")

# Load data using shared DataLoader (should be cached!)
df = load_csv("covid_data", "/data/covid_country.csv")

# Calculate Case Fatality Rate
df_with_cfr = df.copy()
df_with_cfr['Case Fatality Rate'] = (df_with_cfr['Deaths'] / df_with_cfr['Confirmed'] * 100)

# Filter countries with at least 1000 confirmed cases for meaningful comparison
df_filtered = df_with_cfr[df_with_cfr['Confirmed'] >= 1000]
top_cfr = df_filtered.nlargest(15, 'Case Fatality Rate')[
    ['Country/Region', 'Case Fatality Rate', 'Deaths']
].sort_values('Case Fatality Rate')

print(f"📊 Analyzing {len(df_filtered)} countries with 1000+ cases")

# Create chart using MatplotlibFactory
factory = MatplotlibFactory()
fig, ax = factory.create_figure(figsize=(10, 8))

# Create bars with heatmap coloring
colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top_cfr)))
bars = ax.barh(top_cfr['Country/Region'], top_cfr['Case Fatality Rate'], color=colors)

# Apply styling
factory.style_bar_chart(
    ax,
    title='Top 15 Countries by Case Fatality Rate\n(Countries with 1000+ confirmed cases)',
    xlabel='Case Fatality Rate (%)',
    grid=True,
    grid_axis='x'
)

# Add value labels
for i, (idx, row) in enumerate(top_cfr.iterrows()):
    ax.text(row['Case Fatality Rate'], i, f" {row['Case Fatality Rate']:.1f}%",
           va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
factory.display(fig, "covid-chart4")

print("✅ Case Fatality Rate chart rendered successfully!")
