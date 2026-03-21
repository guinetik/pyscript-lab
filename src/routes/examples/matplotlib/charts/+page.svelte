<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('matplotlib_charts');
</script>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/intro', nextPage: '/examples/matplotlib/maps' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<h1 class="text-2xl font-bold mb-2">{$exampleText.headerTitle || 'COVID-19 Global Data Analysis'}</h1>
				<p class="text-gray-600">{$exampleText.headerDescription || 'Visualizing pandemic data from 187 countries/regions using Matplotlib and Pandas'}</p>
			</div>

			<div class="space-y-6">
				<div class="rounded-lg border-2 border-blue-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-2 text-blue-900">{$exampleText.charts?.chart1?.title || '📊 Chart 1: Top 20 Countries by Deaths'}</h3>
					<p class="text-sm text-blue-800 mb-3">
						{$exampleText.charts?.chart1?.description || 'A "heatmap-style" horizontal bar chart showing countries with the highest death tolls. The color intensity increases with death count.'}
					</p>
					<PyExample title="{$exampleText.charts?.chart1?.pyTitle || 'Top 20 deaths with heatmap coloring:'}">
						<script type="py" src="{base}/python/matplotlib/covid_chart_deaths.py" id="covid-deaths"></script>
					</PyExample>
					<div id="covid-chart1" class="flex justify-center mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-green-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-2 text-green-900">{$exampleText.charts?.chart2?.title || '🌍 Chart 2: Deaths by WHO Region'}</h3>
					<p class="text-sm text-green-800 mb-3">
						{$exampleText.charts?.chart2?.description || 'Pie chart showing how deaths are distributed across WHO regions (Americas, Europe, Africa, etc.)'}
					</p>
					<PyExample title="{$exampleText.charts?.chart2?.pyTitle || 'Regional distribution using the SAME cached data:'}">
						<script type="py" src="{base}/python/matplotlib/covid_chart_regions.py" id="covid-regions"></script>
					</PyExample>
					<div id="covid-chart2" class="flex justify-center mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-purple-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-2 text-purple-900">{$exampleText.charts?.chart3?.title || '🔍 Chart 3: Confirmed Cases vs Deaths (Log Scale)'}</h3>
					<p class="text-sm text-purple-800 mb-3">
						{$exampleText.charts?.chart3?.description || 'Scatter plot revealing the relationship between confirmed cases and deaths. Log scale makes patterns visible across countries of vastly different sizes.'}
					</p>
					<PyExample title="{$exampleText.charts?.chart3?.pyTitle || 'Scatter plot with log scale:'}">
						<script type="py" src="{base}/python/matplotlib/covid_chart_scatter.py" id="covid-scatter"></script>
					</PyExample>
					<div id="covid-chart3" class="flex justify-center mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-orange-200 bg-white p-4">
					<h3 class="text-lg font-bold mb-2 text-orange-900">{$exampleText.charts?.chart4?.title || '⚠️ Chart 4: Case Fatality Rate Analysis'}</h3>
					<p class="text-sm text-orange-800 mb-3">
						{$exampleText.charts?.chart4?.description || 'Case Fatality Rate analysis showing which countries had the highest death-to-case ratios (filtered to countries with 1000+ cases for statistical significance)'}
					</p>
					<PyExample title="{$exampleText.charts?.chart4?.pyTitle || 'CFR analysis with filtering:'}">
						<script type="py" src="{base}/python/matplotlib/covid_chart_cfr.py" id="covid-cfr"></script>
					</PyExample>
					<div id="covid-chart4" class="flex justify-center mt-3"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'COVID-19 Data Charts'}</h2>

		<div class="space-y-4">
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.dataset?.title || '📊 The Dataset'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.dataset?.intro || 'The covid_country.csv dataset contains:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.dataset?.items?.countries || '187 countries/regions with cumulative statistics'}</li>
					<li>{$exampleText.dataset?.items?.stats || 'Confirmed cases, deaths, recoveries, and active cases'}</li>
					<li>{$exampleText.dataset?.items?.weekly || 'Weekly new cases and changes'}</li>
					<li>{$exampleText.dataset?.items?.cfr || 'Case fatality rates (death rate)'}</li>
					<li>{$exampleText.dataset?.items?.regions || 'WHO regional categorization (Americas, Europe, Africa, etc.)'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.about?.title || '📈 What is Matplotlib?'}</h3>
				<p class="text-sm">
					{$exampleText.about?.description || 'Matplotlib is Python\'s foundational plotting library. It provides complete control over every aspect of your charts - from basic line plots to complex multi-panel visualizations. Unlike Bokeh (which focuses on interactivity), Matplotlib excels at creating publication-quality static figures with precise customization.'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.chartTypes?.title || '🔬 Chart Types Used'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.chartTypes?.items?.bar || 'Horizontal Bar Charts: Great for comparing categories when labels are long'}</li>
					<li>{$exampleText.chartTypes?.items?.pie || 'Pie Charts: Show proportions of a whole (regional distribution)'}</li>
					<li>{$exampleText.chartTypes?.items?.scatter || 'Scatter Plots: Reveal correlations between two variables'}</li>
					<li>{$exampleText.chartTypes?.items?.log || 'Log Scales: Handle data spanning multiple orders of magnitude'}</li>
					<li>{$exampleText.chartTypes?.items?.colorMap || 'Color Maps: Use color intensity to represent data values (heatmap effect)'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.insights?.title || '💡 Data Insights'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.insights?.items?.deathTolls || 'The Americas and Europe regions had the highest death tolls'}</li>
					<li>{$exampleText.insights?.items?.correlation || 'Larger outbreaks don\'t always correlate linearly with deaths (different healthcare responses)'}</li>
					<li>{$exampleText.insights?.items?.cfr || 'Case Fatality Rate varies significantly based on healthcare capacity, testing rates, and demographics'}</li>
					<li>{$exampleText.insights?.items?.testing || 'Countries with robust testing may show lower CFR due to detecting more mild cases'}</li>
				</ul>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.techniques?.title || '🎯 Technical Techniques'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.techniques?.items?.pandas || 'Pandas Operations: nlargest(), groupby(), filtering with boolean indexing'}</li>
					<li>{$exampleText.techniques?.items?.color || 'Color Mapping: plt.cm.Reds, plt.cm.Set3, plt.cm.YlOrRd for visual hierarchy'}</li>
					<li>{$exampleText.techniques?.items?.log || 'Log Scales: set_xscale(\'log\') for handling wide value ranges'}</li>
					<li>{$exampleText.techniques?.items?.caching || 'Data Caching: All 4 charts share the same loaded CSV (efficient!)'}</li>
					<li>{$exampleText.techniques?.items?.clientSide || 'Client-Side Processing: All analysis happens in your browser via WebAssembly'}</li>
				</ul>
			</Callout>
		</div>

		<p class="mt-6">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/matplotlib"
				target="_blank">{$exampleText.viewSource || 'View source files'}</a
			>
		</p>
	</article>
</ExperimentCard>
