<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('matplotlib_maps');
</script>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/charts', nextPage: '/examples/bokeh' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<h1 class="text-2xl font-bold mb-2">{$exampleText.headerTitle || 'COVID-19 Interactive World Map'}</h1>
				<p class="text-gray-600">{$exampleText.headerDescription || 'Geographic visualization of pandemic data using Plotly choropleth maps'}</p>
			</div>

			<div class="space-y-6">
				<div class="rounded-lg border-2 border-red-200 bg-surface p-4">
					<h3 class="text-lg font-bold mb-2 text-red-900">{$exampleText.maps?.map1?.title || 'Map 1: Total Deaths'}</h3>
					<p class="text-sm text-red-800 mb-3">
						{$exampleText.maps?.map1?.description || 'Darker red indicates higher death toll. Hover over countries for details.'}
					</p>
					<PyExample title="{$exampleText.maps?.map1?.pyTitle || 'Deaths choropleth with red color scale:'}">
						<script type="py" src="{base}/python/matplotlib/covid_map_deaths.py" id="covid-map-deaths"></script>
					</PyExample>
					<div id="map1" class="w-full mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-blue-200 bg-surface p-4">
					<h3 class="text-lg font-bold mb-2 text-blue-900">{$exampleText.maps?.map2?.title || 'Map 2: Confirmed Cases'}</h3>
					<p class="text-sm text-blue-800 mb-3">
						{$exampleText.maps?.map2?.description || 'Darker blue indicates more confirmed cases. Shows total outbreak size using the SAME cached data.'}
					</p>
					<PyExample title="{$exampleText.maps?.map2?.pyTitle || 'Confirmed cases choropleth with blue color scale:'}">
						<script type="py" src="{base}/python/matplotlib/covid_map_cases.py" id="covid-map-cases"></script>
					</PyExample>
					<div id="map2" class="w-full mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-orange-200 bg-surface p-4">
					<h3 class="text-lg font-bold mb-2 text-orange-900">{$exampleText.maps?.map3?.title || 'Map 3: Case Fatality Rate'}</h3>
					<p class="text-sm text-orange-800 mb-3">
						{$exampleText.maps?.map3?.description || 'Shows death rate as percentage of confirmed cases (countries with 1000+ cases for statistical significance).'}
					</p>
					<PyExample title="{$exampleText.maps?.map3?.pyTitle || 'CFR choropleth with filtering and calculation:'}">
						<script type="py" src="{base}/python/matplotlib/covid_map_cfr.py" id="covid-map-cfr"></script>
					</PyExample>
					<div id="map3" class="w-full mt-3"></div>
				</div>

				<div class="rounded-lg border-2 border-yellow-200 bg-surface p-4">
					<h3 class="text-lg font-bold mb-2 text-yellow-900">{$exampleText.maps?.map4?.title || 'Map 4: New Cases Activity'}</h3>
					<p class="text-sm text-yellow-800 mb-3">
						{$exampleText.maps?.map4?.description || 'Recent new cases, showing areas of active transmission.'}
					</p>
					<PyExample title="{$exampleText.maps?.map4?.pyTitle || 'New cases choropleth with orange color scale:'}">
						<script type="py" src="{base}/python/matplotlib/covid_map_new.py" id="covid-map-new"></script>
					</PyExample>
					<div id="map4" class="w-full mt-3"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'COVID-19 World Map'}</h2>

		<div class="space-y-4">
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.choropleth?.title || 'What is a Choropleth Map?'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.choropleth?.description || 'A choropleth map is a thematic map where areas are colored or shaded according to a statistical variable. In our case, we\'re coloring countries based on COVID-19 metrics.'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li><strong>{$exampleText.choropleth?.items?.geographic || 'Geographic Representation: Each country is a polygon with accurate boundaries'}</strong></li>
					<li>{$exampleText.choropleth?.items?.color || 'Color Encoding: The color intensity represents data magnitude'}</li>
					<li>{$exampleText.choropleth?.items?.interactive || 'Interactive: Hover to see exact values and country names'}</li>
					<li>{$exampleText.choropleth?.items?.zoom || 'Zoom & Pan: Click and drag to explore different regions'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.plotly?.title || 'What is Plotly?'}</h3>
				<p class="text-sm">
					{$exampleText.plotly?.description || 'Plotly is an interactive graphing library for Python. Unlike Matplotlib (which creates static images), Plotly generates interactive HTML visualizations that users can explore. It excels at geographic visualizations with built-in support for choropleth maps, and handles country matching automatically using ISO-3 codes.'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.mapExplanations?.title || 'The Four Maps Explained'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.mapExplanations?.items?.deaths || 'Deaths Map (Red): Shows the human toll. Absolute numbers highlight heavily populated countries.'}</li>
					<li>{$exampleText.mapExplanations?.items?.cases || 'Confirmed Cases (Blue): Visualizes total outbreak size. Useful for understanding scale of spread.'}</li>
					<li>{$exampleText.mapExplanations?.items?.cfr || 'Case Fatality Rate (Yellow-Red): Death rate relative to cases. Indicates healthcare capacity and population vulnerability.'}</li>
					<li>{$exampleText.mapExplanations?.items?.newCases || 'New Cases (Orange): Shows active transmission areas, identifying current hotspots.'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.technical?.title || 'Technical Implementation'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.technical?.items?.iso3 || 'ISO-3 Country Codes: Uses standardized codes (USA, GBR, FRA) for reliable country matching'}</li>
					<li>{$exampleText.technical?.items?.projection || 'Natural Earth Projection: A visually pleasing pseudo-cylindrical map projection'}</li>
					<li>{$exampleText.technical?.items?.plotly || 'Plotly Choropleth: Built-in geographic support with country geometries'}</li>
					<li>{$exampleText.technical?.items?.caching || 'Data Caching: All 4 maps share the same loaded CSV (efficient!)'}</li>
					<li>{$exampleText.technical?.items?.async || 'Async Display: 0.5s delay ensures Plotly library fully initializes'}</li>
				</ul>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.insights?.title || 'Geographic Insights'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.insights?.items?.patterns || 'Spatial Patterns: Maps reveal regional clusters not visible in tables'}</li>
					<li>{$exampleText.insights?.items?.absolute || 'Absolute vs Relative: Deaths map shows population, CFR normalizes by cases'}</li>
					<li>{$exampleText.insights?.items?.temporal || 'Temporal Dimension: New cases map captures the dynamic nature of the pandemic'}</li>
					<li>{$exampleText.insights?.items?.missing || 'Missing Data: Gray/white countries indicate no data or no ISO-3 match'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.interactive?.title || 'Interactive Features'}</h3>
				<p class="text-sm mb-2">{$exampleText.interactive?.intro || 'Try these interactions with the maps:'}</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.interactive?.items?.hover || 'Hover over any country to see detailed statistics'}</li>
					<li>{$exampleText.interactive?.items?.pan || 'Click and drag to pan the map'}</li>
					<li>{$exampleText.interactive?.items?.zoom || 'Use scroll wheel to zoom in/out'}</li>
					<li>{$exampleText.interactive?.items?.reset || 'Double-click to reset view'}</li>
					<li>{$exampleText.interactive?.items?.download || 'Click the camera icon (top-right) to download as PNG'}</li>
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
