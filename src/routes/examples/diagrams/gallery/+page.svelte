<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import DiagramCard from '$lib/components/DiagramCard.svelte';
	import { DiagramGalleryController } from '$lib/controller/DiagramGalleryController.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Diagrams Gallery';

	// Controller instance
	let controller;
	let loading = $state(true);

	// Diagram examples configuration
	const examples = [
		{
			id: 'chart1',
			title: 'Example 1: Grouped Workers',
			src: 'python/diagrams/grouped_workers.py'
		},
		{
			id: 'chart2',
			title: 'Example 2: Clustered Web Services',
			src: 'python/diagrams/clustered_services.py'
		},
		{
			id: 'chart3',
			title: 'Example 3: Event-Driven Architecture',
			src: 'python/diagrams/event_driven.py'
		},
		{
			id: 'chart4',
			title: 'Example 4: Microservices API',
			src: 'python/diagrams/microservices_api.py'
		},
		{
			id: 'chart5',
			title: 'Example 5: Data Analytics Pipeline',
			src: 'python/diagrams/data_pipeline.py'
		}
	];

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
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">📦 What is Diagrams?</h3>
				<p class="text-sm text-blue-800">
					<a
						href="https://diagrams.mingrammer.com"
						target="_blank"
						class="font-bold text-blue-600 underline hover:text-blue-800"
					>Diagrams</a> is a Python library that lets you draw cloud system architecture diagrams
					using code instead of drag-and-drop tools. Created by mingrammer, it provides a simple,
					declarative way to create professional architecture diagrams that can be version controlled
					alongside your infrastructure code.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🏗️ Infrastructure as Code Philosophy</h3>
				<p class="text-sm text-green-800">
					Just like Infrastructure as Code (IaC) manages infrastructure through code, Diagrams as
					Code creates architecture diagrams programmatically. This means your diagrams can be
					version controlled, reviewed in pull requests, and automatically updated alongside your
					infrastructure changes. No more outdated diagrams in documentation!
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">☁️ Multi-Cloud Support</h3>
				<p class="text-sm text-purple-800">
					Diagrams supports all major cloud providers (AWS, Azure, GCP, Kubernetes), on-premise
					solutions, and SaaS services. You can mix and match components from different providers
					to accurately represent hybrid and multi-cloud architectures. The library includes
					hundreds of official provider icons.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🔗 Simple Syntax</h3>
				<p class="text-sm text-green-800">
					The library uses intuitive Python syntax with operators like
					<code class="rounded bg-green-200 px-1">{'>> '}</code>
					for data flow,
					<code class="rounded bg-green-200 px-1">{' - '}</code>
					for connections, and list notation
					<code class="rounded bg-green-200 px-1">{'[]'}</code>
					for parallel components. Clusters group related resources together.
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">🎉 Browser Magic with viz.js!</h3>
				<p class="text-sm text-amber-800">
					The Diagrams library generates Graphviz DOT format, which normally requires a native
					binary. We're using <strong>viz.js</strong> (Graphviz compiled to WebAssembly) to render
					the diagrams directly in your browser! The Python code intercepts the
					<code class="bg-amber-200 px-1 rounded">graphviz.Digraph</code> class to capture DOT
					output.
				</p>
				<p class="text-sm text-amber-800 mt-2">
					<strong>Icon loading:</strong> Cloud provider icons are fetched from the diagrams GitHub
					repository, converted to base64 data URIs, and embedded directly into the SVG. This
					happens automatically in JavaScript before rendering!
				</p>
			</div>

			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 font-bold text-cyan-900">💡 Real-World Use Cases</h3>
				<p class="text-sm text-cyan-800">
					• Document system architecture in your repository<br />
					• Auto-generate diagrams from infrastructure code<br />
					• Create visual documentation for technical proposals<br />
					• Maintain architecture diagrams alongside code changes<br />
					• Generate diagrams in CI/CD pipelines<br />
				</p>
			</div>

			<div class="rounded-lg bg-rose-50 p-4">
				<h3 class="mb-2 font-bold text-rose-900">🚀 Getting Started Locally</h3>
				<p class="text-sm text-rose-800">
					To use the Diagrams library in a local Python environment:<br />
					<code class="mt-2 block rounded bg-gray-900 p-2 text-gray-100"
						>pip install diagrams</code
					><br />
					You'll also need Graphviz installed on your system. Visit
					<a
						href="https://diagrams.mingrammer.com"
						target="_blank"
						class="font-bold text-rose-600 underline">diagrams.mingrammer.com</a
					> for full documentation and installation instructions.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/diagrams/diagram_manager.py"
				target="_blank">View Manager Source</a
			>
			|
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/tree/master/static/python/diagrams"
				target="_blank">View Diagram Files</a
			>
			<br />
			<a
				class="text-sky-500"
				target="_blank"
				href="https://diagrams.mingrammer.com/docs/getting-started/examples">Official Examples</a
			>
		</p>
	</article>
</ExperimentCard>
