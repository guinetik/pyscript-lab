<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('matplotlib_intro');
</script>

<ExperimentCard props={{ previousPage: '/examples/basics/interop', nextPage: '/examples/matplotlib/charts' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>{$exampleText.examples?.example1 || 'Example 1: Simple Line Plot'}</h1>
			<PyExample title="{$exampleText.examples?.lineChart || 'A basic line chart with matplotlib:'}" src="{base}/python/matplotlib/line_plot.py">
				<script type="py" src="{base}/python/matplotlib/line_plot.py" id="matplotlib-line"></script>
			</PyExample>
			<div id="matplotlib-line-output"></div>

			<hr class="my-4" />

			<h1>{$exampleText.examples?.example2 || 'Example 2: Bar Chart'}</h1>
			<PyExample title="{$exampleText.examples?.barChart || 'A colorful bar chart:'}" src="{base}/python/matplotlib/bar_chart.py">
				<script type="py" src="{base}/python/matplotlib/bar_chart.py" id="matplotlib-bar"></script>
			</PyExample>
			<div id="matplotlib-bar-output"></div>

			<hr class="my-4" />

			<h1>{$exampleText.examples?.example3 || 'Example 3: Scatter Plot'}</h1>
			<PyExample title="{$exampleText.examples?.scatterPlot || 'Data correlation visualization:'}" src="{base}/python/matplotlib/scatter_plot.py">
				<script type="py" src="{base}/python/matplotlib/scatter_plot.py" id="matplotlib-scatter"></script>
			</PyExample>
			<div id="matplotlib-scatter-output"></div>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Matplotlib Introduction'}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				{$exampleText.description || "Matplotlib is Python's most popular plotting library, and with PyScript, you can run it directly in your browser! Create interactive visualizations, charts, and graphs without any server-side processing—all powered by WebAssembly and Pyodide."}
			</p>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.keyFeatures?.title || 'Key Features:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>{$exampleText.keyFeatures?.fullSupport || 'Full Matplotlib Support:'}</strong> {$exampleText.keyFeatures?.fullSupportDesc || 'Access the complete matplotlib API in the browser'}</li>
					<li><strong>{$exampleText.keyFeatures?.numpyIntegration || 'NumPy Integration:'}</strong> {$exampleText.keyFeatures?.numpyIntegrationDesc || 'Use NumPy arrays for data manipulation'}</li>
					<li><strong>{$exampleText.keyFeatures?.interactiveCharts || 'Interactive Charts:'}</strong> {$exampleText.keyFeatures?.interactiveChartsDesc || 'Create line plots, bar charts, scatter plots, and more'}</li>
					<li><strong>{$exampleText.keyFeatures?.customization || 'Customization:'}</strong> {$exampleText.keyFeatures?.customizationDesc || 'Full control over colors, styles, labels, and layout'}</li>
					<li><strong>{$exampleText.keyFeatures?.zeroBackend || 'Zero Backend:'}</strong> {$exampleText.keyFeatures?.zeroBackendDesc || 'All rendering happens client-side'}</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.theExamples?.title || 'The Examples:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>{$exampleText.examples?.example1 || 'Example 1:'}</strong> {$exampleText.theExamples?.example1 || 'Line Plot - Shows a sine wave with customized styling'}</li>
					<li><strong>{$exampleText.examples?.example2 || 'Example 2:'}</strong> {$exampleText.theExamples?.example2 || 'Bar Chart - Demonstrates categorical data visualization'}</li>
					<li><strong>{$exampleText.examples?.example3 || 'Example 3:'}</strong> {$exampleText.theExamples?.example3 || 'Scatter Plot - Visualizes data correlation with color mapping'}</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.gettingStarted?.title || 'Getting Started:'}</h3>
				<p class="mb-2">{$exampleText.gettingStarted?.description || 'To use Matplotlib in PyScript, you need to specify it in your config:'}</p>
				<pre class="rounded bg-white p-3 text-sm overflow-x-auto"><code>&lt;py-config&gt;
  packages = ["matplotlib", "numpy"]
&lt;/py-config&gt;

&lt;script type="py"&gt;
  from pyscript import display
  import matplotlib.pyplot as plt
  # Create your plots
  fig, ax = plt.subplots()
  # ... customize your plot
  display(fig, target="output-div")
&lt;/script&gt;</code></pre>
				<p class="mt-3 text-sm">
					<strong>{$exampleText.gettingStarted?.note || 'Note:'}</strong> {$exampleText.gettingStarted?.noteDesc || 'Matplotlib plots are rendered as static images in PyScript. For interactive plots, consider using Bokeh (see Bokeh examples).'}
				</p>
			</div>

			<div class="mb-6 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.useCases?.title || 'Use Cases:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>{$exampleText.useCases?.dashboards || 'Data visualization dashboards'}</li>
					<li>{$exampleText.useCases?.scientific || 'Scientific and educational demonstrations'}</li>
					<li>{$exampleText.useCases?.statistical || 'Statistical analysis presentations'}</li>
					<li>{$exampleText.useCases?.reporting || 'Report generation with charts'}</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
