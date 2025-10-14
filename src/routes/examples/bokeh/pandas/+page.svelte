<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	export let name = 'Bokeh + Pandas';
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh', nextPage: '/examples/bokeh/networks' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<p class="text-sm text-slate-700">
					These interactive charts analyze over 20,000 AirBnb listings using Python's Pandas library
					and Bokeh visualization tools.
				</p>
			</div>

			<div class="space-y-4">
				<div class="rounded-lg bg-blue-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-blue-900">📊 Correlation Heatmap</h3>
					<p class="text-sm text-blue-800 mb-3">
						Shows how different listing features relate to each other. Yellow squares indicate strong
						positive relationships (when one increases, the other does too), while purple squares show
						negative relationships.
					</p>
					<PyExample title="Correlation analysis using Pandas and Bokeh:">
						<script type="py" src="{base}/python/bokeh/bokeh_heatmap.py" id="bokeh-heatmap"></script>
					</PyExample>
					<div id="matplotlib-heatmap-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-green-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-green-900">🥧 Room Type Distribution</h3>
					<p class="text-sm text-green-800 mb-3">
						A pie chart showing the breakdown of different accommodation types (entire homes,
						private rooms, shared rooms). This helps understand what kinds of spaces are most
						commonly listed.
					</p>
					<PyExample title="Room distribution using the SAME cached data:">
						<script type="py" src="{base}/python/bokeh/bokeh_pie.py" id="bokeh-pie"></script>
					</PyExample>
					<div id="matplotlib-pie-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-purple-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-purple-900">💰 Price Analysis</h3>
					<p class="text-sm text-purple-800 mb-3">
						Displays how prices vary across different room types. Each dot represents a listing,
						allowing you to see the price range and distribution for each accommodation category.
					</p>
					<PyExample title="Price distribution with jittered scatter:">
						<script type="py" src="{base}/python/bokeh/bokeh_jitter.py" id="bokeh-jitter"></script>
					</PyExample>
					<div id="matplotlib-jitter-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-orange-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-orange-900">🏠 Top Hosts</h3>
					<p class="text-sm text-orange-800 mb-3">
						Bar chart showing the 10 most active hosts by number of listings. This reveals which
						hosts manage the most properties on the platform.
					</p>
					<PyExample title="Top 10 hosts by listing count:">
						<script type="py" src="{base}/python/bokeh/bokeh_bar.py" id="bokeh-bar"></script>
					</PyExample>
					<div id="matplotlib-bar-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-pink-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-pink-900">📍 Neighborhood Activity</h3>
					<p class="text-sm text-pink-800 mb-3">
						Lollipop chart displaying listing counts by neighborhood. The length of each line shows
						how many properties are available in different areas of the city.
					</p>
					<PyExample title="Listings by neighborhood group:">
						<script type="py" src="{base}/python/bokeh/bokeh_lollipop.py" id="bokeh-lollipop"></script>
					</PyExample>
					<div id="matplotlib-lollipop-output" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">🐼 What is Pandas?</h3>
				<p class="text-sm text-blue-800">
					Pandas is Python's most popular data analysis library. It provides DataFrames - powerful
					table-like structures that make it easy to clean, transform, and analyze large datasets.
					Think of it as Excel on steroids, but programmable and capable of handling millions of rows.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">📊 The Dataset</h3>
				<p class="text-sm text-green-800 mb-2">
					We're analyzing <strong>20,837 AirBnb listings</strong> from a real-world dataset. Each row
					contains information like:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
					<li>Host ID and listing count</li>
					<li>Neighborhood and borough</li>
					<li>Room type (entire home, private room, shared)</li>
					<li>Price per night</li>
					<li>Number of reviews and review scores</li>
					<li>Availability throughout the year</li>
				</ul>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">🔍 Data Analysis Patterns</h3>
				<p class="text-sm text-purple-800 mb-2">
					Each chart demonstrates common Pandas operations:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-purple-800">
					<li><strong>Correlation:</strong> <code>df.corr()</code> finds relationships between numeric columns</li>
					<li><strong>Value Counts:</strong> <code>df.column.value_counts()</code> aggregates categories</li>
					<li><strong>Filtering:</strong> <code>df[df.price &lt; 500]</code> selects subsets of data</li>
					<li><strong>Grouping:</strong> <code>df.groupby('room_type').mean()</code> aggregates by category</li>
					<li><strong>Sorting:</strong> <code>df.sort_values('price')</code> orders rows</li>
				</ul>
			</div>

			<div class="rounded-lg bg-orange-50 p-4">
				<h3 class="mb-2 font-bold text-orange-900">💡 Loading Data</h3>
				<p class="text-sm text-orange-800">
					The CSV is loaded using Pandas' <code>read_csv()</code> function with PyScript's HTTP fetch.
					The first chart loads the data, then subsequent charts reuse the cached DataFrame - no
					redundant network requests!
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">🎨 Why Bokeh?</h3>
				<p class="text-sm text-amber-800">
					Bokeh excels at creating interactive visualizations directly from Pandas DataFrames.
					Unlike static charts, Bokeh plots let you pan, zoom, and hover to explore the data.
					It's perfect for exploratory data analysis and dashboards.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/bokeh"
				target="_blank">View source files</a
			>
		</p>
	</article>
</ExperimentCard>
