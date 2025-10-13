<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import CodeEditor from '$lib/components/CodeEditor.svelte';
	import { DiagramCreatorController } from '$lib/controller/DiagramCreatorController.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Create Diagrams';

	// Controller instance
	let controller = $state(null);

	// UI State
	let codeInput = $state(`from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Simple Web Service", show=False):
    ELB("load balancer") >> EC2("web server") >> RDS("database")`);

	let status = $state('ready'); // 'ready' | 'processing' | 'success' | 'error'
	let statusMessage = $state('Click "Run Diagram" to generate visualization');
	let loading = $state(true);

	/**
	 * Handle status updates from Python
	 */
	function handleStatusUpdate(event) {
		status = event.detail.status;
		statusMessage = event.detail.message;
	}

	/**
	 * Run diagram generation
	 */
	function runDiagram() {
		if (controller) {
			controller.runDiagram(codeInput);
		}
	}

	/**
	 * Load a template
	 */
	function loadTemplate(template) {
		codeInput = template.code;
		// Reset status
		status = 'ready';
		statusMessage = 'Template loaded. Click "Run Diagram" to generate.';
		// Clear output
		const outputDiv = document.getElementById('user-diagram-output');
		if (outputDiv) {
			outputDiv.innerHTML = '<p class="text-gray-400">Click "Run Diagram" to see your visualization</p>';
		}
	}

	/**
	 * Save diagram as SVG
	 */
	function saveDiagram() {
		if (controller) {
			controller.saveDiagram();
		}
	}

	onMount(async () => {
		try {
			// Listen for status updates (browser only)
			if (typeof window !== 'undefined') {
				window.addEventListener('diagramStatusUpdate', handleStatusUpdate);
			}

			// Initialize controller
			controller = new DiagramCreatorController();
			await controller.initialize();

			loading = false;
		} catch (error) {
			console.error('Failed to initialize diagram creator:', error);
			loading = false;
			status = 'error';
			statusMessage = 'Failed to initialize. Please refresh the page.';
		}
	});

	onDestroy(() => {
		// Clean up event listener (browser only)
		if (typeof window !== 'undefined') {
			window.removeEventListener('diagramStatusUpdate', handleStatusUpdate);
		}

		if (controller) {
			controller.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/diagrams/gallery', nextPage: '/examples/ml' }}>
	<div slot="py_slot" class="flex h-full flex-col p-5">
		{#if loading}
			<div class="flex items-center justify-center p-8">
				<p class="text-lg">🐍 Loading diagram creator...</p>
			</div>
		{:else}
			<!-- Templates -->
			<div class="mb-4">
				<label class="mb-2 block text-sm font-bold text-gray-700">Quick Start Templates:</label>
				<div class="flex flex-wrap gap-2">
					{#each controller?.getTemplates() || [] as template}
						<button
							onclick={() => loadTemplate(template)}
							class="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600 transition-colors"
						>
							{template.name}
						</button>
					{/each}
				</div>
			</div>

		<!-- Code Editor -->
		<div class="mb-4 flex-1 flex flex-col">
			<label class="mb-2 block text-sm font-bold text-gray-700">Diagram Code:</label>
			<div class="flex-1 min-h-[300px]">
				<CodeEditor bind:value={codeInput} height="100%" placeholder="Enter your Diagrams code here..." />
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="mb-4 grid grid-cols-2 gap-3">
			<button
				onclick={runDiagram}
				disabled={status === 'processing'}
				class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
			>
				{status === 'processing' ? '⏳ Generating...' : '▶️ Run Diagram'}
			</button>
			<button
				onclick={saveDiagram}
				disabled={status !== 'success'}
				class="rounded bg-blue-500 px-6 py-3 font-bold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
			>
				💾 Save SVG
			</button>
		</div>

		<!-- Status Display -->
		<div class="mb-4 rounded border-2 p-3 {status === 'error' ? 'bg-red-50 border-red-200' : status === 'success' ? 'bg-green-50 border-green-200' : status === 'processing' ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}">
			<p class="text-sm font-mono {status === 'error' ? 'text-red-700' : status === 'success' ? 'text-green-700' : status === 'processing' ? 'text-blue-700' : 'text-gray-600'}">
				{statusMessage}
			</p>
		</div>

		<!-- Output Area -->
		<div class="rounded-lg border-2 border-gray-200 bg-white p-4">
			<h3 class="text-lg font-bold mb-3">Your Diagram:</h3>
			<div
				id="user-diagram-output"
				class="flex min-h-[300px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
			>
				<p class="text-gray-400">Click "Run Diagram" to see your visualization</p>
			</div>
		</div>

			<!-- Hidden Python script container -->
			<div id="diagram-creator-script" style="display: none;"></div>
		{/if}
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				Create your own cloud architecture diagrams using Python code! This interactive editor
				lets you experiment with the Diagrams library and see results instantly.
			</p>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-blue-900">How to Use:</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-blue-800">
					<li><strong>Choose a template</strong> or write your own code</li>
					<li><strong>Edit the code</strong> in the editor</li>
					<li><strong>Click "Run Diagram"</strong> to generate the visualization</li>
					<li><strong>Iterate and experiment</strong> - try different providers and layouts!</li>
				</ol>
			</div>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">Available Providers:</h3>
				<div class="text-sm text-gray-700">
					<p class="mb-2">You can use components from these cloud providers:</p>
					<ul class="list-disc space-y-1 pl-5">
						<li><code class="rounded bg-white px-1">diagrams.aws.*</code> - Amazon Web Services</li>
						<li><code class="rounded bg-white px-1">diagrams.azure.*</code> - Microsoft Azure</li>
						<li><code class="rounded bg-white px-1">diagrams.gcp.*</code> - Google Cloud Platform</li>
						<li><code class="rounded bg-white px-1">diagrams.k8s.*</code> - Kubernetes</li>
						<li><code class="rounded bg-white px-1">diagrams.onprem.*</code> - On-Premise / Generic</li>
					</ul>
				</div>
			</div>

			<div class="mb-6 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">Tips:</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-green-800">
					<li>Use <code class="rounded bg-green-200 px-1">&gt;&gt;</code> to show data flow direction</li>
					<li>Use <code class="rounded bg-green-200 px-1">-</code> for bidirectional connections</li>
					<li>Use lists <code class="rounded bg-green-200 px-1">[service1, service2]</code> for parallel components</li>
					<li>Always set <code class="rounded bg-green-200 px-1">show=False</code> in the Diagram constructor</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-yellow-900">Example Pattern:</h3>
				<pre class="rounded bg-white p-3 text-xs overflow-x-auto"><code>from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS

with Diagram("My Architecture", show=False):
    web = EC2("web server")
    db = RDS("database")
    web >> db  # web connects to database</code></pre>
			</div>
		</div>
	</article>
</ExperimentCard>
