<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('bokeh-communities');
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/networks', nextPage: '/examples/diagrams/gallery' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<p class="text-sm text-slate-700">
					{$exampleText.intro || 'Community detection identifies clusters of closely related technologies in the StackOverflow network using graph analysis algorithms.'}
				</p>
			</div>

			<div class="space-y-4">
				<div class="rounded-lg bg-cyan-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-cyan-900">{$exampleText.fullCommunities?.title || '🌐 Full Network with Communities'}</h3>
					<p class="text-sm text-cyan-800 mb-3">
						{$exampleText.fullCommunities?.description || 'Shows all technologies colored by their detected community. Each color represents a different community. Technologies in the same community are shown in the same color family. The "modularity score" measures how well-defined the communities are - higher scores (closer to 1.0) mean clearer community boundaries.'}
					</p>
					<PyExample title={$exampleText.fullCommunities?.code || 'Community detection using greedy modularity:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_community_full.py" id="bokeh-community-full"></script>
					</PyExample>
					<div id="community-full-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-emerald-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-emerald-900">{$exampleText.largestCommunity?.title || '⭐ Largest Community'}</h3>
					<p class="text-sm text-emerald-800 mb-3">
						{$exampleText.largestCommunity?.description || 'Zooms into the biggest community to show its internal structure. You can see which technologies form the core of this cluster and how they interconnect. The node colors now represent each technology\'s "degree" (how many connections it has) - darker colors mean more central/important nodes in the community.'}
					</p>
					<PyExample title={$exampleText.largestCommunity?.code || 'Largest community with degree-based coloring:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_community_largest.py" id="bokeh-community-largest"></script>
					</PyExample>
					<div id="community-largest-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-violet-50 p-3">
					<h3 class="mb-2 text-lg font-bold text-violet-900">{$exampleText.comparison?.title || '📊 Community Size Comparison'}</h3>
					<p class="text-sm text-violet-800 mb-3">
						{$exampleText.comparison?.description || 'Compares the sizes of all detected communities. Some communities are large ecosystems with many technologies, while others are smaller specialized clusters. The variation in sizes reveals how the technology landscape is structured - a few major ecosystems with many smaller specialized niches.'}
					</p>
					<PyExample title={$exampleText.comparison?.code || 'Bar chart comparison of community sizes:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_community_comparison.py" id="bokeh-community-comparison"></script>
					</PyExample>
					<div id="community-comparison-output" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Community Detection'}</h2>

		<div class="space-y-4">
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.whatAreCommunities?.title || '🎨 What Are Communities?'}</h3>
				<p class="text-sm">
					{$exampleText.whatAreCommunities?.description || 'In network science, a "community" is a group of nodes (technologies) that are more densely connected to each other than to the rest of the network. Think of them as natural clusters - like how web technologies (HTML, CSS, JavaScript) naturally group together, or how data science tools (Python, pandas, NumPy) form their own cluster.'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.algorithm?.title || '🔬 The Algorithm'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.algorithm?.intro || 'This analysis uses Greedy Modularity Optimization:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.algorithm?.iterative || 'Iteratively groups nodes to maximize "modularity"'}</li>
					<li>{$exampleText.algorithm?.modularity || 'Modularity measures how densely connected nodes are within communities vs. between'}</li>
					<li>{$exampleText.algorithm?.fast || 'Fast and effective for discovering natural groupings in large networks'}</li>
					<li>{$exampleText.algorithm?.deterministic || 'Deterministic - same graph always produces same communities'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.modularity?.title || '📊 Modularity Score'}</h3>
				<p class="text-sm">
					{$exampleText.modularity?.description || 'The modularity score ranges from -0.5 to 1.0. Higher scores indicate stronger community structure. A score above 0.3 is generally considered significant, meaning the network has well-defined communities. The score shown in the first visualization tells you how clear the community boundaries are.'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.understanding?.title || '🔍 Understanding the Results'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.understanding?.intro || 'What you can learn from these visualizations:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li><strong>{$exampleText.understanding?.ecosystems?.split(':')[0] || 'Technology Ecosystems'}:</strong> {$exampleText.understanding?.ecosystems?.split(':')[1] || 'See which skills naturally complement each other'}</li>
					<li><strong>{$exampleText.understanding?.size?.split(':')[0] || 'Community Size'}:</strong> {$exampleText.understanding?.size?.split(':')[1] || 'Identify major platforms vs. specialized niches'}</li>
					<li><strong>{$exampleText.understanding?.hubs?.split(':')[0] || 'Hub Nodes'}:</strong> {$exampleText.understanding?.hubs?.split(':')[1] || 'In the largest community, high-degree nodes are key technologies'}</li>
					<li><strong>{$exampleText.understanding?.careers?.split(':')[0] || 'Career Paths'}:</strong> {$exampleText.understanding?.careers?.split(':')[1] || 'Communities suggest logical skill development trajectories'}</li>
				</ul>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.applications?.title || '💡 Real-World Applications'}</h3>
				<p class="text-sm">
					{$exampleText.applications?.description || 'Community detection is used in social networks (friend groups), biology (protein interactions), recommendation systems (product categories), cybersecurity (attack patterns), and organizational analysis. In this example, it reveals technology ecosystems helping developers understand which skills naturally complement each other.'}
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
