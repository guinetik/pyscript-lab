 <script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Bokeh + Pandas';

	// Python runner instance
	let pyScriptRunner;
	let loading = $state(true);

	onMount(() => {
		if (!pyScriptRunner) {
			pyScriptRunner = RunPython();
			pyScriptRunner.runScript(getLink('python/bokeh_pandas_v2.py'), 'script_gutter', false);

			// Hide loading after a delay (5 charts take time to render)
			setTimeout(() => {
				loading = false;
			}, 8000);
		}
	});

	onDestroy(() => {
		if (pyScriptRunner) {
			pyScriptRunner.destroy();
		}
	});
</script>

<ExperimentCard
	props={{ previousPage: '/examples/bokeh', nextPage: '/examples/bokeh/networks' }}
>
	<div slot="py_slot" class="relative">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">🐍 Loading Python charts...</p>
				</div>
			</div>
		{/if}
		<div id="chart" class="h-auto w-full"></div>
		<div id="chart2" class="w-full"></div>
		<div id="chart3" class="h-full w-full"></div>
		<div id="chart4" class="h-min w-full"></div>
		<div id="chart5" class="h-max w-full"></div>
	</div>
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<p class="text-sm">
				These interactive charts analyze over 20,000 AirBnb listings using Python's Pandas library
				and Bokeh visualization tools.
			</p>

			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">📊 Correlation Heatmap</h3>
				<p class="text-sm text-blue-800">
					Shows how different listing features relate to each other. Yellow squares indicate strong
					positive relationships (when one increases, the other does too), while purple squares show
					negative relationships. For example, you might see how price correlates with location or
					number of reviews.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🥧 Room Type Distribution</h3>
				<p class="text-sm text-green-800">
					A pie chart showing the breakdown of different accommodation types (entire homes,
					private rooms, shared rooms). This helps understand what kinds of spaces are most
					commonly listed.
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">💰 Price Analysis</h3>
				<p class="text-sm text-purple-800">
					Displays how prices vary across different room types. Each dot represents a listing,
					allowing you to see the price range and distribution for each accommodation category.
				</p>
			</div>

			<div class="rounded-lg bg-orange-50 p-4">
				<h3 class="mb-2 font-bold text-orange-900">🏠 Top Hosts</h3>
				<p class="text-sm text-orange-800">
					Bar chart showing the 10 most active hosts by number of listings. This reveals which
					hosts manage the most properties on the platform.
				</p>
			</div>

			<div class="rounded-lg bg-pink-50 p-4">
				<h3 class="mb-2 font-bold text-pink-900">📍 Neighborhood Activity</h3>
				<p class="text-sm text-pink-800">
					Lollipop chart displaying listing counts by neighborhood. The length of each line shows
					how many properties are available in different areas of the city.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/bokeh_pandas_v2.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>
