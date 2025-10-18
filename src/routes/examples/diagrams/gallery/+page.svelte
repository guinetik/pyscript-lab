<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import DiagramCard from '$lib/components/DiagramCard.svelte';
	import { DiagramGalleryController } from '$lib/controller/DiagramGalleryController.js';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import { onMount, onDestroy } from 'svelte';

	// Get translated content
	const exampleText = exampleTranslationStore('gallery');

	// Controller instance
	let controller;
	let loading = $state(true);

	// Diagram examples configuration with base data
	const exampleConfigs = [
		{ id: 'chart1', key: 'example1', src: 'python/diagrams/grouped_workers.py' },
		{ id: 'chart2', key: 'example2', src: 'python/diagrams/clustered_services.py' },
		{ id: 'chart3', key: 'example3', src: 'python/diagrams/event_driven.py' },
		{ id: 'chart4', key: 'example4', src: 'python/diagrams/microservices_api.py' },
		{ id: 'chart5', key: 'example5', src: 'python/diagrams/data_pipeline.py' }
	];

	// Create derived examples with translated titles
	let examples = $derived(
		exampleConfigs.map(config => ({
			id: config.id,
			title: $exampleText?.examples?.[config.key] || `Example ${config.id.slice(-1)}`,
			src: config.src
		}))
	);

	/**
	 * Regenerate a specific diagram.
	 * @param {string} exampleId - The ID of the diagram to regenerate
	 */
	function regenerateDiagram(exampleId) {
		const container = document.getElementById(exampleId);
		if (container) {
			container.innerHTML = '<p class="text-gray-500 animate-pulse">🔄 Regenerating...</p>';
		}
		controller.regenerateDiagram(exampleId);
	}

	onMount(async () => {
		try {
			// Initialize controller
			controller = new DiagramGalleryController();
			await controller.initialize();
			loading = false;
		} catch (error) {
			console.error('Failed to initialize diagram gallery:', error);
			loading = false;
		}
	});

	onDestroy(() => {
		if (controller) {
			controller.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/communities', nextPage: '/examples/diagrams/create' }}>
	<div slot="py_slot" class="relative">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">🐍 Loading diagrams...</p>
				</div>
			</div>
		{/if}

		<!-- Example diagrams will be rendered here -->
		<div class="space-y-6 p-6">
			{#each examples as example (example.id)}
				<DiagramCard 
					id={example.id}
					title={example.title}
					src={example.src}
					onRegenerate={regenerateDiagram}
				/>
			{/each}
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Diagrams Gallery'}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">{$exampleText.sections?.whatIs?.title || '📦 What is Diagrams?'}</h3>
				<p class="text-sm text-blue-800">
					<a
						href="https://diagrams.mingrammer.com"
						target="_blank"
						class="font-bold text-blue-600 underline hover:text-blue-800"
					>{$exampleText.sections?.whatIs?.linkText || 'Diagrams'}</a> {$exampleText.sections?.whatIs?.description || 'is a Python library that lets you draw cloud system architecture diagrams using code instead of drag-and-drop tools.'}
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">{$exampleText.sections?.infrastructure?.title || '🏗️ Infrastructure as Code Philosophy'}</h3>
				<p class="text-sm text-green-800">
					{$exampleText.sections?.infrastructure?.description || 'Just like Infrastructure as Code (IaC) manages infrastructure through code, Diagrams as Code creates architecture diagrams programmatically.'}
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">{$exampleText.sections?.multiCloud?.title || '☁️ Multi-Cloud Support'}</h3>
				<p class="text-sm text-purple-800">
					{$exampleText.sections?.multiCloud?.description || 'Diagrams supports all major cloud providers (AWS, Azure, GCP, Kubernetes), on-premise solutions, and SaaS services.'}
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">{$exampleText.sections?.syntax?.title || '🔗 Simple Syntax'}</h3>
				<p class="text-sm text-green-800">
					The library uses intuitive Python syntax with operators like
					<code class="rounded bg-green-200 px-1">{$exampleText.sections?.syntax?.dataFlow || '>> '}</code>
					{$exampleText.sections?.syntax?.description?.split('for data flow,')[0] || ''}for data flow,
					<code class="rounded bg-green-200 px-1">{$exampleText.sections?.syntax?.connections || ' - '}</code>
					for connections, and list notation
					<code class="rounded bg-green-200 px-1">{$exampleText.sections?.syntax?.parallel || '[]'}</code>
					for parallel components. Clusters group related resources together.
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">{$exampleText.sections?.browserMagic?.title || '🎉 Browser Magic with viz.js!'}</h3>
				<p class="text-sm text-amber-800">
					The Diagrams library generates Graphviz DOT format, which normally requires a native
					binary. We're using <strong>viz.js</strong> (Graphviz compiled to WebAssembly) to render
					the diagrams directly in your browser! The Python code intercepts the
					<code class="bg-amber-200 px-1 rounded">{$exampleText.sections?.browserMagic?.digraph || 'graphviz.Digraph'}</code> class to capture DOT
					output.
				</p>
				<p class="text-sm text-amber-800 mt-2">
					<strong>Icon loading:</strong> {$exampleText.sections?.browserMagic?.iconLoading || 'Cloud provider icons are fetched from the diagrams GitHub repository, converted to base64 data URIs, and embedded directly into the SVG.'}
				</p>
			</div>

			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 font-bold text-cyan-900">{$exampleText.sections?.useCases?.title || '💡 Real-World Use Cases'}</h3>
				<p class="text-sm text-cyan-800">
					• {$exampleText.sections?.useCases?.useCase1 || 'Document system architecture in your repository'}<br />
					• {$exampleText.sections?.useCases?.useCase2 || 'Auto-generate diagrams from infrastructure code'}<br />
					• {$exampleText.sections?.useCases?.useCase3 || 'Create visual documentation for technical proposals'}<br />
					• {$exampleText.sections?.useCases?.useCase4 || 'Maintain architecture diagrams alongside code changes'}<br />
					• {$exampleText.sections?.useCases?.useCase5 || 'Generate diagrams in CI/CD pipelines'}<br />
				</p>
			</div>

			<div class="rounded-lg bg-rose-50 p-4">
				<h3 class="mb-2 font-bold text-rose-900">{$exampleText.sections?.gettingStarted?.title || '🚀 Getting Started Locally'}</h3>
				<p class="text-sm text-rose-800">
					{$exampleText.sections?.gettingStarted?.description || 'To use the Diagrams library in a local Python environment:'}<br />
					<code class="mt-2 block rounded bg-gray-900 p-2 text-gray-100"
						>{$exampleText.sections?.gettingStarted?.command || 'pip install diagrams'}</code
					><br />
					{$exampleText.sections?.gettingStarted?.note || "You'll also need Graphviz installed on your system. Visit diagrams.mingrammer.com for full documentation and installation instructions."}
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/diagrams/diagram_manager.py"
				target="_blank">{$exampleText.links?.managerSource || 'View Manager Source'}</a
			>
			|
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/diagrams"
				target="_blank">{$exampleText.links?.diagramFiles || 'View Diagram Files'}</a
			>
			<br />
			<a
				class="text-sky-500"
				target="_blank"
				href="https://diagrams.mingrammer.com/docs/getting-started/examples">{$exampleText.links?.officialExamples || 'Official Examples'}</a
			>
		</p>
	</article>
</ExperimentCard>
