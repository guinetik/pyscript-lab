<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import PyExample from '$lib/PyExample.svelte';
	export let name = 'COVID-19 Data Charts';
</script>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/intro', nextPage: '/examples/matplotlib/maps' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>COVID-19 Global Data Analysis</h1>
			<p class="mb-4 text-gray-600">Visualizing pandemic data from 187 countries/regions</p>

			<PyExample title="Loading and analyzing COVID-19 data:">
				<script type="py" id="covid-data">
from pyscript import display
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pyodide.http import open_url

# Load the COVID data
df = pd.read_csv(open_url('/data/covid_country.csv'))

print(f"📊 Loaded data for {len(df)} countries/regions")
print(f"Total Deaths: {df['Deaths'].sum():,}")
print(f"Total Confirmed Cases: {df['Confirmed'].sum():,}")

# 1. TOP 20 COUNTRIES BY DEATHS - Horizontal Bar Chart (Heatmap style)
top_deaths = df.nlargest(20, 'Deaths')[['Country/Region', 'Deaths']].sort_values('Deaths')

fig1, ax1 = plt.subplots(figsize=(10, 8))
colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(top_deaths)))
bars = ax1.barh(top_deaths['Country/Region'], top_deaths['Deaths'], color=colors)
ax1.set_xlabel('Total Deaths', fontsize=12, fontweight='bold')
ax1.set_title('Top 20 Countries by COVID-19 Deaths', fontsize=14, fontweight='bold', pad=20)
ax1.grid(axis='x', alpha=0.3)

# Add value labels
for i, (idx, row) in enumerate(top_deaths.iterrows()):
    ax1.text(row['Deaths'], i, f" {int(row['Deaths']):,}",
             va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
display(fig1, target="covid-chart1")

# 2. DEATHS BY WHO REGION - Pie Chart
region_deaths = df.groupby('WHO Region')['Deaths'].sum().sort_values(ascending=False)

fig2, ax2 = plt.subplots(figsize=(10, 8))
colors2 = plt.cm.Set3(range(len(region_deaths)))
wedges, texts, autotexts = ax2.pie(region_deaths, labels=region_deaths.index, autopct='%1.1f%%',
                                     colors=colors2, startangle=90)
ax2.set_title('COVID-19 Deaths Distribution by WHO Region', fontsize=14, fontweight='bold', pad=20)

# Make percentage text bold
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(10)

plt.tight_layout()
display(fig2, target="covid-chart2")

# 3. CONFIRMED CASES VS DEATHS - Scatter Plot
fig3, ax3 = plt.subplots(figsize=(10, 8))

# Color by WHO Region
regions = df['WHO Region'].unique()
colors_map = {region: plt.cm.tab10(i) for i, region in enumerate(regions)}
colors3 = [colors_map[region] for region in df['WHO Region']]

scatter = ax3.scatter(df['Confirmed'], df['Deaths'],
                     c=colors3, alpha=0.6, s=100, edgecolors='black', linewidth=0.5)

ax3.set_xlabel('Confirmed Cases', fontsize=12, fontweight='bold')
ax3.set_ylabel('Deaths', fontsize=12, fontweight='bold')
ax3.set_title('COVID-19: Confirmed Cases vs Deaths', fontsize=14, fontweight='bold', pad=20)
ax3.grid(True, alpha=0.3)

# Log scale for better visualization
ax3.set_xscale('log')
ax3.set_yscale('log')

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=colors_map[region], label=region) for region in regions]
ax3.legend(handles=legend_elements, loc='upper left', fontsize=8)

plt.tight_layout()
display(fig3, target="covid-chart3")

# 4. TOP 15 COUNTRIES BY CASE FATALITY RATE
df['Case Fatality Rate'] = (df['Deaths'] / df['Confirmed'] * 100)
# Filter countries with at least 1000 confirmed cases for meaningful comparison
df_filtered = df[df['Confirmed'] >= 1000]
top_cfr = df_filtered.nlargest(15, 'Case Fatality Rate')[['Country/Region', 'Case Fatality Rate', 'Deaths']].sort_values('Case Fatality Rate')

fig4, ax4 = plt.subplots(figsize=(10, 8))
colors4 = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top_cfr)))
bars = ax4.barh(top_cfr['Country/Region'], top_cfr['Case Fatality Rate'], color=colors4)
ax4.set_xlabel('Case Fatality Rate (%)', fontsize=12, fontweight='bold')
ax4.set_title('Top 15 Countries by Case Fatality Rate\n(Countries with 1000+ confirmed cases)',
              fontsize=14, fontweight='bold', pad=20)
ax4.grid(axis='x', alpha=0.3)

# Add value labels
for i, (idx, row) in enumerate(top_cfr.iterrows()):
    ax4.text(row['Case Fatality Rate'], i, f" {row['Case Fatality Rate']:.1f}%",
             va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
display(fig4, target="covid-chart4")

print("✅ All visualizations generated successfully!")
				</script>
			</PyExample>

			<div class="space-y-8 mt-6">
				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">📊 Chart 1: Top 20 Countries by Deaths</h3>
					<div id="covid-chart1" class="flex justify-center"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">🌍 Chart 2: Deaths by WHO Region</h3>
					<div id="covid-chart2" class="flex justify-center"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">🔍 Chart 3: Confirmed Cases vs Deaths (Log Scale)</h3>
					<div id="covid-chart3" class="flex justify-center"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">⚠️ Chart 4: Case Fatality Rate Analysis</h3>
					<div id="covid-chart4" class="flex justify-center"></div>
				</div>
			</div>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				This page demonstrates data visualization using real COVID-19 data from 187 countries.
				Using pandas for data manipulation and matplotlib for visualization, we create multiple
				perspectives on the global pandemic impact.
			</p>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-blue-900">📈 What You're Seeing:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-blue-800">
					<li><strong>Chart 1:</strong> A "heatmap-style" horizontal bar chart showing countries with the highest death tolls. The color intensity increases with death count.</li>
					<li><strong>Chart 2:</strong> Pie chart showing how deaths are distributed across WHO regions (Americas, Europe, Africa, etc.)</li>
					<li><strong>Chart 3:</strong> Scatter plot revealing the relationship between confirmed cases and deaths. Log scale makes patterns visible across countries of vastly different sizes.</li>
					<li><strong>Chart 4:</strong> Case Fatality Rate analysis showing which countries had the highest death-to-case ratios (filtered to countries with 1000+ cases for statistical significance)</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">🔬 Technical Implementation:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm">
					<li><strong>Pandas:</strong> CSV loading, data filtering, grouping, and aggregation</li>
					<li><strong>Matplotlib:</strong> Multiple chart types (horizontal bars, pie, scatter)</li>
					<li><strong>Color Mapping:</strong> Using colormaps (Reds, Set3, tab10, YlOrRd) to enhance visual communication</li>
					<li><strong>Log Scales:</strong> Handling data that spans multiple orders of magnitude</li>
					<li><strong>Client-Side Processing:</strong> All data analysis happens in your browser!</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">💡 Data Insights:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-green-800">
					<li>The data includes confirmed cases, deaths, recoveries, and weekly changes</li>
					<li>Countries are categorized by WHO regions for regional analysis</li>
					<li>Case Fatality Rate (CFR) varies significantly based on healthcare capacity, testing rates, and population demographics</li>
					<li>The scatter plot reveals that larger outbreaks don't always correlate linearly with deaths (different healthcare responses)</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-yellow-900">📊 Dataset Details:</h3>
				<p class="text-sm text-yellow-800 mb-2">
					<strong>Source:</strong> The covid_country.csv dataset contains:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-yellow-800">
					<li>187 countries/regions</li>
					<li>Columns: Confirmed, Deaths, Recovered, Active, New cases, Death rate, WHO Region</li>
					<li>Snapshot data showing cumulative statistics and weekly trends</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-purple-900">🎯 Key Takeaways:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-purple-800">
					<li>Pandas and matplotlib work seamlessly in PyScript for data analysis</li>
					<li>Complex visualizations can be generated entirely client-side</li>
					<li>Multiple chart types can reveal different aspects of the same dataset</li>
					<li>Real-world data often requires filtering and transformation before visualization</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
