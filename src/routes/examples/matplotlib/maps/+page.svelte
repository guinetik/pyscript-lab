<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	export let name = 'COVID-19 World Map';
</script>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/charts', nextPage: '/examples/bokeh' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>COVID-19 Interactive World Map</h1>
			<p class="mb-4 text-gray-600">Geographic visualization of pandemic data using Plotly</p>

			<PyExample title="Creating an interactive choropleth world map:">
				<script type="py" id="covid-world-map">
from pyscript import display
import plotly.graph_objects as go
import pandas as pd
from pyodide.http import open_url

# Load the COVID data
df = pd.read_csv(open_url('/data/covid_country.csv'))

print(f"🌍 Loaded data for {len(df)} countries/regions")

# 1. WORLD MAP - TOTAL DEATHS using graph_objects
fig1 = go.Figure(data=go.Choropleth(
    locations = df['Country/Region'],
    z = df['Deaths'],
    locationmode = 'country names',
    colorscale = 'Reds',
    text = df['Country/Region'],
    colorbar_title = "Deaths",
))

fig1.update_layout(
    title_text='COVID-19 Deaths by Country',
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

display(fig1, target="map1")

# 2. WORLD MAP - CONFIRMED CASES
fig2 = go.Figure(data=go.Choropleth(
    locations = df['Country/Region'],
    z = df['Confirmed'],
    locationmode = 'country names',
    colorscale = 'Blues',
    text = df['Country/Region'],
    colorbar_title = "Confirmed",
))

fig2.update_layout(
    title_text='COVID-19 Confirmed Cases by Country',
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

display(fig2, target="map2")

# 3. WORLD MAP - CASE FATALITY RATE (for countries with 1000+ cases)
df_filtered = df[df['Confirmed'] >= 1000].copy()
df_filtered['CFR'] = (df_filtered['Deaths'] / df_filtered['Confirmed'] * 100)

fig3 = go.Figure(data=go.Choropleth(
    locations = df_filtered['Country/Region'],
    z = df_filtered['CFR'],
    locationmode = 'country names',
    colorscale = 'YlOrRd',
    text = df_filtered['Country/Region'],
    colorbar_title = "CFR %",
))

fig3.update_layout(
    title_text='COVID-19 Case Fatality Rate by Country (1000+ cases)',
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

display(fig3, target="map3")

# 4. WORLD MAP - NEW CASES (Weekly Growth)
df_active = df[df['New cases'] > 0].copy()

fig4 = go.Figure(data=go.Choropleth(
    locations = df_active['Country/Region'],
    z = df_active['New cases'],
    locationmode = 'country names',
    colorscale = 'Oranges',
    text = df_active['Country/Region'],
    colorbar_title = "New Cases",
))

fig4.update_layout(
    title_text='COVID-19 New Cases by Country',
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

display(fig4, target="map4")

print("✅ All world maps generated successfully!")
print("💡 Hover over countries to see detailed data")
				</script>
			</PyExample>

			<div class="space-y-8 mt-6">
				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">🗺️ Map 1: Total Deaths</h3>
					<p class="text-sm text-gray-600 mb-3">Darker red indicates higher death toll. Hover over countries for details.</p>
					<div id="map1" class="w-full"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">🌐 Map 2: Confirmed Cases</h3>
					<p class="text-sm text-gray-600 mb-3">Darker blue indicates more confirmed cases. Shows total outbreak size.</p>
					<div id="map2" class="w-full"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">⚠️ Map 3: Case Fatality Rate</h3>
					<p class="text-sm text-gray-600 mb-3">Shows death rate as percentage of confirmed cases (countries with 1000+ cases).</p>
					<div id="map3" class="w-full"></div>
				</div>

				<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-3">📈 Map 4: New Cases Activity</h3>
					<p class="text-sm text-gray-600 mb-3">Recent new cases, showing areas of active transmission.</p>
					<div id="map4" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				This page demonstrates geographic data visualization using Plotly's interactive choropleth maps.
				These are real world maps where countries are colored based on COVID-19 data metrics, allowing
				you to visually identify patterns and hotspots across the globe.
			</p>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-blue-900">🗺️ What is a Choropleth Map?</h3>
				<p class="text-sm text-blue-800 mb-2">
					A choropleth map is a thematic map where areas are colored or shaded according to a statistical variable.
					In our case, we're coloring countries based on COVID-19 metrics.
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-blue-800">
					<li><strong>Geographic Representation:</strong> Each country is a polygon with accurate boundaries</li>
					<li><strong>Color Encoding:</strong> The color intensity represents data magnitude</li>
					<li><strong>Interactive:</strong> Hover to see exact values and additional data</li>
					<li><strong>Zoom & Pan:</strong> Click and drag to explore different regions</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">🎨 The Four Maps Explained:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm">
					<li><strong>Deaths Map (Red):</strong> Shows the human toll of the pandemic. Countries like USA, Brazil, and India appear darkest due to high absolute numbers.</li>
					<li><strong>Confirmed Cases Map (Blue):</strong> Visualizes total outbreak size. Useful for understanding scale of infection spread.</li>
					<li><strong>Case Fatality Rate Map (Yellow-Red):</strong> Reveals which countries had higher death rates relative to their cases. This can indicate healthcare capacity, testing rates, and population vulnerability.</li>
					<li><strong>New Cases Map (Orange):</strong> Shows areas with active transmission, helping identify current hotspots rather than historical totals.</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">🔬 Technical Implementation:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-green-800">
					<li><strong>Plotly Express:</strong> High-level plotting library with built-in geographic support</li>
					<li><strong>Country Matching:</strong> Uses country names to match data with built-in country geometries</li>
					<li><strong>Natural Earth Projection:</strong> A visually pleasing pseudo-cylindrical map projection</li>
					<li><strong>Custom Hover Data:</strong> Formatted tooltips showing multiple metrics with proper formatting</li>
					<li><strong>Color Scales:</strong> Different color schemes for different metrics (Reds for deaths, Blues for cases, etc.)</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-purple-900">💡 Data Insights from Maps:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-purple-800">
					<li><strong>Geographic Patterns:</strong> The maps reveal regional clusters and patterns not visible in tables</li>
					<li><strong>Absolute vs Relative:</strong> Total deaths map shows countries with large populations prominent, while CFR map normalizes by case count</li>
					<li><strong>Temporal Dimension:</strong> The "New Cases" map captures the dynamic nature of the pandemic</li>
					<li><strong>Missing Data:</strong> Gray/white countries indicate missing data or no mapping match</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-yellow-900">🌍 Why Geographic Visualization Matters:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-yellow-800">
					<li>Humans are naturally good at understanding spatial information</li>
					<li>Maps reveal patterns that tables and bar charts can hide</li>
					<li>Geographic context helps in understanding relationships between neighboring regions</li>
					<li>Essential for public health, logistics, and policy decisions</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-red-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-red-900">🎯 Interactive Features:</h3>
				<p class="text-sm text-red-800 mb-2">Try these interactions with the maps:</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-red-800">
					<li>Hover over any country to see detailed statistics</li>
					<li>Click and drag to pan the map</li>
					<li>Use scroll wheel to zoom in/out</li>
					<li>Double-click to reset view</li>
					<li>Click the camera icon (top-right) to download a map as PNG</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
