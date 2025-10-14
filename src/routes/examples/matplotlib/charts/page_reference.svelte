<script>
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { createLogger } from '@guinetik/logger';
	
	let loading = $state(true);
	const name = 'COVID-19 Data Charts';

	const logger = createLogger({
		prefix: 'CovidChartsPage',
		level: 'debug'
	});

	onMount(() => {
		// Wait for Python module to load, then generate charts individually
		const checkAndGenerate = setInterval(() => {
			if (typeof window !== 'undefined' && 
			    window.generateTopDeathsChart && 
			    window.generateRegionalDeathsPie &&
			    window.generateCasesVsDeathsScatter &&
			    window.generateCaseFatalityRateChart) {
				
				clearInterval(checkAndGenerate);
				
				// Call each chart generation function individually in Promise.all
				Promise.all([
					window.generateTopDeathsChart(),
					window.generateRegionalDeathsPie(),
					window.generateCasesVsDeathsScatter(),
					window.generateCaseFatalityRateChart()
				]).then(() => {
					loading = false;
					logger.log('✅ All COVID charts loaded');
				}).catch((error) => {
					console.error('❌ Error generating charts:', error);
					loading = false;
				});
			}
		}, 100);

		// Cleanup
		return () => clearInterval(checkAndGenerate);
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/intro', nextPage: '/examples/matplotlib/maps' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>COVID-19 Global Data Analysis</h1>
			<p class="mb-4 text-gray-600">Visualizing pandemic data from 187 countries/regions</p>

			<PyExample title="Loading and analyzing COVID-19 data:" src="{base}/python/matplotlib/covid_charts.py">
				<script type="py" src="{base}/python/matplotlib/covid_charts.py" id="covid-data"></script>
			</PyExample>

			{#if loading}
				<div class="mt-6 flex items-center justify-center gap-3 rounded-lg border-2 border-blue-200 bg-blue-50 p-8">
					<div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
					<p class="text-lg font-semibold text-blue-900">Generating charts...</p>
				</div>
			{/if}

			<div class="space-y-8 mt-6" class:opacity-0={loading} class:opacity-100={!loading} style="transition: opacity 0.3s ease-in-out;">
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
