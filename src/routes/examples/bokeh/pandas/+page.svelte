<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('bokeh-pandas');
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh', nextPage: '/examples/bokeh/networks' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<p class="text-sm text-slate-700">
					{$exampleText.intro || 'These interactive charts analyze over 20,000 AirBnb listings...'}
				</p>
			</div>

			<div class="space-y-4">
				<div class="rounded-lg bg-blue-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-blue-900">{$exampleText.heatmap?.title || '📊 Correlation Heatmap'}</h3>
					<p class="text-sm text-blue-800 mb-3">
						{$exampleText.heatmap?.description || 'Shows how different listing features relate...'}
					</p>
					<PyExample title={$exampleText.heatmap?.code || 'Correlation analysis using Pandas and Bokeh:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_heatmap.py" id="bokeh-heatmap"></script>
					</PyExample>
					<div id="matplotlib-heatmap-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-green-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-green-900">{$exampleText.pie?.title || '🥧 Room Type Distribution'}</h3>
					<p class="text-sm text-green-800 mb-3">
						{$exampleText.pie?.description || 'A pie chart showing the breakdown...'}
					</p>
					<PyExample title={$exampleText.pie?.code || 'Room distribution using the SAME cached data:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_pie.py" id="bokeh-pie"></script>
					</PyExample>
					<div id="matplotlib-pie-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-purple-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-purple-900">{$exampleText.jitter?.title || '💰 Price Analysis'}</h3>
					<p class="text-sm text-purple-800 mb-3">
						{$exampleText.jitter?.description || 'Displays how prices vary...'}
					</p>
					<PyExample title={$exampleText.jitter?.code || 'Price distribution with jittered scatter:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_jitter.py" id="bokeh-jitter"></script>
					</PyExample>
					<div id="matplotlib-jitter-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-orange-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-orange-900">{$exampleText.bar?.title || '🏠 Top Hosts'}</h3>
					<p class="text-sm text-orange-800 mb-3">
						{$exampleText.bar?.description || 'Bar chart showing the 10 most active hosts...'}
					</p>
					<PyExample title={$exampleText.bar?.code || 'Top 10 hosts by listing count:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_bar.py" id="bokeh-bar"></script>
					</PyExample>
					<div id="matplotlib-bar-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-pink-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-pink-900">{$exampleText.lollipop?.title || '📍 Neighborhood Activity'}</h3>
					<p class="text-sm text-pink-800 mb-3">
						{$exampleText.lollipop?.description || 'Lollipop chart displaying listing counts...'}
					</p>
					<PyExample title={$exampleText.lollipop?.code || 'Listings by neighborhood group:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_lollipop.py" id="bokeh-lollipop"></script>
					</PyExample>
					<div id="matplotlib-lollipop-output" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Bokeh + Pandas'}</h2>

		<div class="space-y-4">
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.whatPandas?.title || '🐼 What is Pandas?'}</h3>
				<p class="text-sm">
					{$exampleText.whatPandas?.description || 'Pandas is Python\'s most popular data analysis library...'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.dataset?.title || '📊 The Dataset'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.dataset?.intro || 'We\'re analyzing 20,837 AirBnb listings...'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.dataset?.hostId || 'Host ID and listing count'}</li>
					<li>{$exampleText.dataset?.neighborhood || 'Neighborhood and borough'}</li>
					<li>{$exampleText.dataset?.roomType || 'Room type (entire home, private room, shared)'}</li>
					<li>{$exampleText.dataset?.price || 'Price per night'}</li>
					<li>{$exampleText.dataset?.reviews || 'Number of reviews and review scores'}</li>
					<li>{$exampleText.dataset?.availability || 'Availability throughout the year'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.patterns?.title || '🔍 Data Analysis Patterns'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.patterns?.intro || 'Each chart demonstrates common Pandas operations:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.patterns?.correlation || 'Correlation: df.corr() finds relationships...'}</li>
					<li>{$exampleText.patterns?.valueCounts || 'Value Counts: df.column.value_counts()...'}</li>
					<li>{$exampleText.patterns?.filtering || 'Filtering: df[df.price < 500]...'}</li>
					<li>{$exampleText.patterns?.grouping || 'Grouping: df.groupby(\'room_type\').mean()...'}</li>
					<li>{$exampleText.patterns?.sorting || 'Sorting: df.sort_values(\'price\')...'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.loading?.title || '💡 Loading Data'}</h3>
				<p class="text-sm">
					{$exampleText.loading?.description || 'The CSV is loaded using Pandas\' read_csv()...'}
				</p>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.whyBokeh?.title || '🎨 Why Bokeh?'}</h3>
				<p class="text-sm">
					{$exampleText.whyBokeh?.description || 'Bokeh excels at creating interactive visualizations...'}
				</p>
			</Callout>
		</div>

		<p class="mt-6">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/bokeh"
				target="_blank">{$exampleText.viewSource || 'View source files'}</a
			>
		</p>
	</article>
</ExperimentCard>
