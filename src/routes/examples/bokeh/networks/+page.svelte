<script>
	import { base } from '$app/paths';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const exampleText = exampleTranslationStore('bokeh-networks');
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/pandas', nextPage: '/examples/bokeh/communities' }}>
	<div slot="py_slot">
		<section class="pyscript p-5 space-y-6">
			<div class="mb-4 rounded-lg bg-slate-50 p-4">
				<p class="text-sm text-slate-700">
					{$exampleText.intro || 'These interactive network graphs visualize relationships...'}
				</p>
			</div>

			<div class="space-y-4">
				<div class="rounded-lg bg-callout p-3">
					<h3 class="mb-2 text-lg font-bold">{$exampleText.fullNetwork?.title || 'Full StackOverflow Network'}</h3>
					<p class="text-sm text-blue-800 mb-3">
						{$exampleText.fullNetwork?.description || 'Shows all 115 programming languages...'}
					</p>
					<PyExample title={$exampleText.fullNetwork?.code || 'Full network using Kamada-Kawai layout:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_network_full.py" id="bokeh-network-full"></script>
					</PyExample>
					<div id="network-full-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-callout p-3">
					<h3 class="mb-2 text-lg font-bold">{$exampleText.cliques?.title || 'Clique Analysis'}</h3>
					<p class="text-sm text-purple-800 mb-3">
						{$exampleText.cliques?.description || 'A \"clique\" is a group of nodes...'}
					</p>
					<PyExample title={$exampleText.cliques?.code || 'Clique detection using the SAME cached data:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_network_cliques.py" id="bokeh-network-cliques"></script>
					</PyExample>
					<div id="network-cliques-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-callout p-3">
					<h3 class="mb-2 text-lg font-bold">{$exampleText.centrality?.title || 'Eigenvector Centrality'}</h3>
					<p class="text-sm text-orange-800 mb-3">
						{$exampleText.centrality?.description || 'Measures each node\'s influence...'}
					</p>
					<PyExample title={$exampleText.centrality?.code || 'Eigenvector centrality analysis:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_network_centrality.py" id="bokeh-network-centrality"></script>
					</PyExample>
					<div id="network-centrality-output" class="w-full"></div>
				</div>

				<div class="rounded-lg bg-callout p-3">
					<h3 class="mb-2 text-lg font-bold">{$exampleText.languages?.title || 'Programming Languages Network'}</h3>
					<p class="text-sm text-green-800 mb-3">
						{$exampleText.languages?.description || 'Focuses specifically on major programming languages...'}
					</p>
					<PyExample title={$exampleText.languages?.code || 'Programming language subgraph:'}>
						<script type="py" src="{base}/python/bokeh/bokeh_network_languages.py" id="bokeh-network-languages"></script>
					</PyExample>
					<div id="network-languages-output" class="w-full"></div>
				</div>
			</div>
		</section>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Bokeh + NetworkX'}</h2>

		<div class="space-y-4">
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.whatNetworkX?.title || 'What is NetworkX?'}</h3>
				<p class="text-sm">
					{$exampleText.whatNetworkX?.description || 'NetworkX is Python\'s most popular library...'}
				</p>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.dataset?.title || 'The Dataset'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.dataset?.intro || 'This network contains 115 nodes...'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.dataset?.name || 'Name (e.g., \"python\", \"javascript\", \"django\")'}</li>
					<li>{$exampleText.dataset?.group || 'Group/category (color coding)'}</li>
					<li>{$exampleText.dataset?.size || 'Node size (popularity/activity)'}</li>
					<li>{$exampleText.dataset?.edges || 'Edges connecting it to related technologies'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.concepts?.title || 'Network Analysis Concepts'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.concepts?.intro || 'Each visualization demonstrates key graph analysis techniques:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.concepts?.degree || 'Degree: Number of connections...'}</li>
					<li>{$exampleText.concepts?.cliques || 'Cliques: Groups where every node...'}</li>
					<li>{$exampleText.concepts?.centrality || 'Centrality: How important/influential...'}</li>
					<li>{$exampleText.concepts?.subgraphs || 'Subgraphs: Extracting portions...'}</li>
					<li>{$exampleText.concepts?.layouts || 'Layouts: Algorithms that position...'}</li>
				</ul>
			</Callout>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.layouts?.title || 'Layout Algorithms'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.layouts?.intro || 'Different layouts reveal different aspects...'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.layouts?.kamada || 'Kamada-Kawai: Optimizes distances...'}</li>
					<li>{$exampleText.layouts?.spring || 'Spring (Fruchterman-Reingold): Force-directed...'}</li>
				</ul>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.howToRead?.title || 'How to Read These Graphs'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.howToRead?.nodes || 'Nodes (circles): Technologies/languages...'}</li>
					<li>{$exampleText.howToRead?.edges || 'Edges (lines): Show relationships...'}</li>
					<li>{$exampleText.howToRead?.colors || 'Colors: Different groups/categories...'}</li>
					<li>{$exampleText.howToRead?.size || 'Size: In full/clique/language...'}</li>
					<li>{$exampleText.howToRead?.tools || 'Tools: Pan to move around...'}</li>
				</ul>
			</Callout>
		</div>

		<p class="mt-6">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/bokeh"
				target="_blank">{$exampleText.viewSource || 'View source files'}</a
			>
			<br />
			<a
				class="text-accent"
				target="_blank"
				href="https://www.kaggle.com/code/mayeesha/network-analysis-for-dummies-stackoverflow-data/notebook"
				>{$exampleText.kaggleLink || 'Adapted from this Kaggle'}</a
			>
		</p>
	</article>
</ExperimentCard>
