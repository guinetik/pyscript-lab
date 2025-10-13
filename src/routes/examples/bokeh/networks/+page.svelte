<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Bokeh + NetworkX';

	// Python runner instance
	let pyScriptRunner;
	let loading = $state(true);

	onMount(() => {
		if (!pyScriptRunner) {
			pyScriptRunner = RunPython();
			// Add cache-busting parameter
			const scriptUrl = getLink('python/bokeh_networks.py') + '?v=' + Date.now();
			pyScriptRunner.runScript(scriptUrl, 'script_gutter', false);

			// Hide loading after a delay (4 charts take time to render)
			setTimeout(() => {
				loading = false;
			}, 5000);
		}
	});

	onDestroy(() => {
		if (pyScriptRunner) {
			pyScriptRunner.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/pandas', nextPage: '/examples/bokeh/communities' }}>
	<div slot="py_slot" class="relative">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">🐍 Loading Python charts...</p>
				</div>
			</div>
		{/if}
		<div id="chart" class="h-auto w-full"></div>
		<div id="chart2" class="h-auto w-full"></div>
		<div id="chart3" class="h-auto w-full"></div>
		<div id="chart4" class="h-auto w-full"></div>
	</div>
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<p class="text-sm">
				These interactive network graphs visualize relationships between programming languages and
				technologies on StackOverflow using NetworkX graph analysis.
			</p>

			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">🕸️ Full StackOverflow Network</h3>
				<p class="text-sm text-blue-800">
					Shows all 115 programming languages and technologies as connected nodes. Each node
					represents a language/technology, and lines (edges) connect related topics. Node colors
					indicate different technology groups, and node size represents popularity/activity. Uses
					Kamada-Kawai layout algorithm which optimizes node placement based on graph distances,
					revealing community structure more clearly. You can pan, zoom, and hover over nodes to
					see details.
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">🔗 Clique Analysis</h3>
				<p class="text-sm text-purple-800">
					A "clique" is a group of nodes where everyone is connected to everyone else - showing
					technologies that are very tightly related. This chart identifies the strongest cliques
					in the network, revealing which technologies are most commonly used together. For
					example, web technologies like HTML, CSS, and JavaScript often form tight cliques.
				</p>
			</div>

			<div class="rounded-lg bg-orange-50 p-4">
				<h3 class="mb-2 font-bold text-orange-900">⭐ Eigenvector Centrality</h3>
				<p class="text-sm text-orange-800">
					Measures each node's influence in the network based on the quality of its connections.
					Larger nodes are more "central" or influential - they're not just connected to many
					nodes, but connected to other important nodes. This reveals which technologies are the
					most important hubs in the ecosystem. Think of it like academic citations: being cited
					by highly-cited papers matters more than being cited by obscure ones.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">💻 Programming Languages Network</h3>
				<p class="text-sm text-green-800">
					Focuses specifically on major programming languages (Python, Java, C++, JavaScript, etc.)
					and their immediate neighbors. This shows how these core languages relate to each other
					and what technologies surround them. The layout helps you understand the ecosystem around
					each language - which tools, frameworks, and technologies are commonly associated with
					it.
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">💡 How to Read These Graphs</h3>
				<p class="text-sm text-amber-800">
					<strong>Nodes (circles):</strong> Represent technologies/languages. Hover to see names
					and stats.<br />
					<strong>Edges (lines):</strong> Show relationships between technologies.<br />
					<strong>Colors:</strong> Different groups/categories of technologies.<br />
					<strong>Position:</strong> Related technologies are placed closer together.<br />
					<strong>Tools:</strong> Use pan to move around, wheel zoom to zoom in/out, and hover for
					details.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/bokeh_networks.py"
				target="_blank">View source</a
			>
			<br />
			<a
				class="text-sky-500"
				target="_blank"
				href="https://www.kaggle.com/code/mayeesha/network-analysis-for-dummies-stackoverflow-data/notebook"
				>Adapted from this Kaggle</a
			>
		</p>
	</article>
</ExperimentCard>
