<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	export let name = 'Community Detection';
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/networks', nextPage: '/examples/diagrams/gallery' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<p class="text-sm text-slate-700">
					Community detection identifies clusters of closely related technologies in the
					StackOverflow network using graph analysis algorithms.
				</p>
			</div>

			<div class="space-y-4">
				<div class="rounded-lg bg-cyan-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-cyan-900">🌐 Full Network with Communities</h3>
					<p class="text-sm text-cyan-800 mb-3">
						Shows all technologies colored by their detected community. Each color
						represents a different community. Technologies in the same community are shown in the
						same color family. The "modularity score" measures how well-defined the communities are -
						higher scores (closer to 1.0) mean clearer community boundaries.
					</p>
					<PyExample title="Community detection using greedy modularity:">
						<script type="py" src="{base}/python/bokeh/bokeh_community_full.py" id="bokeh-community-full"></script>
					</PyExample>
					<div id="community-full-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-emerald-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-emerald-900">⭐ Largest Community</h3>
					<p class="text-sm text-emerald-800 mb-3">
						Zooms into the biggest community to show its internal structure. You can see which
						technologies form the core of this cluster and how they interconnect. The node colors now
						represent each technology's "degree" (how many connections it has) - darker colors mean
						more central/important nodes in the community.
					</p>
					<PyExample title="Largest community with degree-based coloring:">
						<script type="py" src="{base}/python/bokeh/bokeh_community_largest.py" id="bokeh-community-largest"></script>
					</PyExample>
					<div id="community-largest-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-violet-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-violet-900">📊 Community Size Comparison</h3>
					<p class="text-sm text-violet-800 mb-3">
						Compares the sizes of all detected communities. Some communities are large
						ecosystems with many technologies, while others are smaller specialized clusters. The
						variation in sizes reveals how the technology landscape is structured - a few major
						ecosystems with many smaller specialized niches.
					</p>
					<PyExample title="Bar chart comparison of community sizes:">
						<script type="py" src="{base}/python/bokeh/bokeh_community_comparison.py" id="bokeh-community-comparison"></script>
					</PyExample>
					<div id="community-comparison-output" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-indigo-50 p-4">
				<h3 class="mb-2 font-bold text-indigo-900">🎨 What Are Communities?</h3>
				<p class="text-sm text-indigo-800">
					In network science, a "community" is a group of nodes (technologies) that are more
					densely connected to each other than to the rest of the network. Think of them as natural
					clusters - like how web technologies (HTML, CSS, JavaScript) naturally group together, or
					how data science tools (Python, pandas, NumPy) form their own cluster.
				</p>
			</div>

			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">🔬 The Algorithm</h3>
				<p class="text-sm text-blue-800 mb-2">
					This analysis uses <strong>Greedy Modularity Optimization</strong>:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-blue-800">
					<li>Iteratively groups nodes to maximize "modularity"</li>
					<li>Modularity measures how densely connected nodes are within communities vs. between</li>
					<li>Fast and effective for discovering natural groupings in large networks</li>
					<li>Deterministic - same graph always produces same communities</li>
				</ul>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">📊 Modularity Score</h3>
				<p class="text-sm text-purple-800">
					The modularity score ranges from -0.5 to 1.0. Higher scores indicate stronger community
					structure. A score above 0.3 is generally considered significant, meaning the network has
					well-defined communities. The score shown in the first visualization tells you how clear
					the community boundaries are.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🔍 Understanding the Results</h3>
				<p class="text-sm text-green-800 mb-2">
					What you can learn from these visualizations:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
					<li><strong>Technology Ecosystems:</strong> See which skills naturally complement each other</li>
					<li><strong>Community Size:</strong> Identify major platforms vs. specialized niches</li>
					<li><strong>Hub Nodes:</strong> In the largest community, high-degree nodes are key technologies</li>
					<li><strong>Career Paths:</strong> Communities suggest logical skill development trajectories</li>
				</ul>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">💡 Real-World Applications</h3>
				<p class="text-sm text-amber-800">
					Community detection is used in social networks (friend groups), biology (protein
					interactions), recommendation systems (product categories), cybersecurity (attack
					patterns), and organizational analysis. In this example, it reveals technology
					ecosystems helping developers understand which skills naturally complement each other.
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
