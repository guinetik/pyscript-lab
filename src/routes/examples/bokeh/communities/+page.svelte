<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Community Detection';

	// Python runner instance
	let pyScriptRunner;
	let loading = $state(true);

	onMount(() => {
		if (!pyScriptRunner) {
			pyScriptRunner = RunPython();
			pyScriptRunner.runScript(getLink('python/bokeh_communities.py'), 'script_gutter', false);

			// Hide loading after a delay (3 charts take time to render)
			setTimeout(() => {
				loading = false;
			}, 10000);
		}
	});

	onDestroy(() => {
		if (pyScriptRunner) {
			pyScriptRunner.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/networks', nextPage: '/examples/diagrams/gallery' }}>
	<div slot="py_slot" class="relative">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">🐍 Analyzing communities...</p>
				</div>
			</div>
		{/if}
		<div id="chart" class="h-auto w-full"></div>
		<div id="chart2" class="h-auto w-full"></div>
		<div id="chart3" class="h-auto w-full"></div>
	</div>
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<p class="text-sm">
				Community detection identifies clusters of closely related technologies in the
				StackOverflow network using graph analysis algorithms.
			</p>

			<div class="rounded-lg bg-indigo-50 p-4">
				<h3 class="mb-2 font-bold text-indigo-900">🎨 What Are Communities?</h3>
				<p class="text-sm text-indigo-800">
					In network science, a "community" is a group of nodes (technologies) that are more
					densely connected to each other than to the rest of the network. Think of them as natural
					clusters - like how web technologies (HTML, CSS, JavaScript) naturally group together, or
					how data science tools (Python, pandas, NumPy) form their own cluster. The algorithm
					automatically discovers these groupings by analyzing connection patterns.
				</p>
			</div>

			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 font-bold text-cyan-900">🌐 Full Network with Communities</h3>
				<p class="text-sm text-cyan-800">
					The first graph shows all technologies colored by their detected community. Each color
					represents a different community. Technologies in the same community are shown in the
					same color family. The "modularity score" measures how well-defined the communities are -
					higher scores (closer to 1.0) mean clearer community boundaries.
				</p>
			</div>

			<div class="rounded-lg bg-emerald-50 p-4">
				<h3 class="mb-2 font-bold text-emerald-900">⭐ Largest Community</h3>
				<p class="text-sm text-emerald-800">
					This zooms into the biggest community to show its internal structure. You can see which
					technologies form the core of this cluster and how they interconnect. The node colors now
					represent each technology's "degree" (how many connections it has) - darker colors mean
					more central/important nodes in the community.
				</p>
			</div>

			<div class="rounded-lg bg-violet-50 p-4">
				<h3 class="mb-2 font-bold text-violet-900">📊 Community Size Comparison</h3>
				<p class="text-sm text-violet-800">
					This bar chart compares the sizes of all detected communities. Some communities are large
					ecosystems with many technologies, while others are smaller specialized clusters. The
					variation in sizes reveals how the technology landscape is structured - a few major
					ecosystems with many smaller specialized niches.
				</p>
			</div>

			<div class="rounded-lg bg-rose-50 p-4">
				<h3 class="mb-2 font-bold text-rose-900">🔬 The Algorithm</h3>
				<p class="text-sm text-rose-800">
					This analysis uses the <strong>Greedy Modularity Optimization</strong> algorithm, which
					works by iteratively grouping nodes to maximize "modularity" - a measure of how much more
					densely connected nodes are within communities compared to between communities. It's a
					fast and effective way to discover natural groupings in large networks.
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">💡 Real-World Applications</h3>
				<p class="text-sm text-amber-800">
					Community detection is used in social networks (friend groups), biology (protein
					interactions), recommendation systems (product categories), and cybersecurity (attack
					patterns). In this example, it reveals technology ecosystems - helping developers
					understand which skills naturally complement each other.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/bokeh_communities.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>
