<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import CodeEditor from '$lib/components/CodeEditor.svelte';
	import { DiagramCreatorController } from '$lib/controller/DiagramCreatorController.js';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import { onMount, onDestroy } from 'svelte';

	// Get translated content
	const exampleText = exampleTranslationStore('create');

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
	let statusMessage = $state($exampleText.status?.ready || 'Click "Run Diagram" to generate visualization');
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
		statusMessage = $exampleText.ui?.templateLoaded || 'Template loaded. Click "Run Diagram" to generate.';
		// Clear output
		const outputDiv = document.getElementById('user-diagram-output');
		if (outputDiv) {
			outputDiv.innerHTML = `<p class="text-gray-400">${$exampleText.ui?.placeholderDefault || 'Click "Run Diagram" to see your visualization'}</p>`;
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
			statusMessage = $exampleText.status?.failed || 'Failed to initialize. Please refresh the page.';
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
		<!-- Hidden Python script container - must exist before controller initializes -->
		<div id="diagram-creator-script" style="display: none;"></div>

		{#if loading}
			<div class="flex items-center justify-center p-8">
				<p class="text-lg">{$exampleText.ui?.loadingDiagramCreator || '🐍 Loading diagram creator...'}</p>
			</div>
		{:else}
			<!-- Templates -->
			<div class="mb-4">
				<label class="mb-2 block text-sm font-bold text-gray-700">{$exampleText.ui?.quickStartTemplates || 'Quick Start Templates:'}</label>
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
			<label class="mb-2 block text-sm font-bold text-gray-700">{$exampleText.ui?.diagramCode || 'Diagram Code:'}</label>
			<div class="flex-1 min-h-[300px]">
				<CodeEditor bind:value={codeInput} height="100%" placeholder={$exampleText.ui?.placeholderEditor || 'Enter your Diagrams code here...'} />
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="mb-4 grid grid-cols-2 gap-3">
			<button
				onclick={runDiagram}
				disabled={status === 'processing'}
				class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
			>
				{status === 'processing' ? $exampleText.ui?.generating || '⏳ Generating...' : $exampleText.ui?.runDiagram || '▶️ Run Diagram'}
			</button>
			<button
				onclick={saveDiagram}
				disabled={status !== 'success'}
				class="rounded bg-blue-500 px-6 py-3 font-bold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
			>
				{$exampleText.ui?.saveSvg || '💾 Save SVG'}
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
			<h3 class="text-lg font-bold mb-3">{$exampleText.ui?.yourDiagram || 'Your Diagram:'}</h3>
			<div
				id="user-diagram-output"
				class="flex min-h-[300px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
			>
				<p class="text-gray-400">{$exampleText.ui?.placeholderDefault || 'Click "Run Diagram" to see your visualization'}</p>
			</div>
		</div>
		{/if}
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Create Diagrams'}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				{$exampleText.description || 'Create your own cloud architecture diagrams using Python code! This interactive editor lets you experiment with the Diagrams library and see results instantly.'}
			</p>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-blue-900">{$exampleText.sections?.howToUse?.title || 'How to Use:'}</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-blue-800">
					<li><strong>{$exampleText.sections?.howToUse?.step1?.split(' or ')[0] || 'Choose a template'}</strong> {$exampleText.sections?.howToUse?.step1?.includes(' or ') ? 'or write your own code' : ''}</li>
					<li><strong>{$exampleText.sections?.howToUse?.step2?.split(' in ')[0] || 'Edit the code'}</strong> {$exampleText.sections?.howToUse?.step2?.includes(' in ') ? 'in the editor' : ''}</li>
					<li><strong>{$exampleText.sections?.howToUse?.step3 || 'Click "Run Diagram" to generate the visualization'}</strong></li>
					<li><strong>{$exampleText.sections?.howToUse?.step4 || 'Iterate and experiment - try different providers and layouts!'}</strong></li>
				</ol>
			</div>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.sections?.availableProviders?.title || 'Available Providers:'}</h3>
				<div class="text-sm text-gray-700">
					<p class="mb-2">{$exampleText.sections?.availableProviders?.description || 'You can use components from these cloud providers:'}</p>
					<ul class="list-disc space-y-1 pl-5">
						<li><code class="rounded bg-white px-1">diagrams.aws.*</code> - {$exampleText.sections?.availableProviders?.aws?.split(' - ')[1] || 'Amazon Web Services'}</li>
						<li><code class="rounded bg-white px-1">diagrams.azure.*</code> - {$exampleText.sections?.availableProviders?.azure?.split(' - ')[1] || 'Microsoft Azure'}</li>
						<li><code class="rounded bg-white px-1">diagrams.gcp.*</code> - {$exampleText.sections?.availableProviders?.gcp?.split(' - ')[1] || 'Google Cloud Platform'}</li>
						<li><code class="rounded bg-white px-1">diagrams.k8s.*</code> - {$exampleText.sections?.availableProviders?.k8s?.split(' - ')[1] || 'Kubernetes'}</li>
						<li><code class="rounded bg-white px-1">diagrams.onprem.*</code> - {$exampleText.sections?.availableProviders?.onprem?.split(' - ')[1] || 'On-Premise / Generic'}</li>
					</ul>
				</div>
			</div>

			<div class="mb-6 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">{$exampleText.sections?.tips?.title || 'Tips:'}</h3>
				<ul class="list-disc space-y-2 pl-5 text-sm text-green-800">
					<li>Use <code class="rounded bg-green-200 px-1">{$exampleText.sections?.tips?.dataFlow || '>>'}</code> {$exampleText.sections?.tips?.tip1?.split('to show')[1]?.substring(0, 30) || 'to show data flow direction'}</li>
					<li>Use <code class="rounded bg-green-200 px-1">{$exampleText.sections?.tips?.connections || '-'}</code> {$exampleText.sections?.tips?.tip2?.split('for')[1] || 'for bidirectional connections'}</li>
					<li>Use lists <code class="rounded bg-green-200 px-1">{$exampleText.sections?.tips?.parallelComponents || '[service1, service2]'}</code> {$exampleText.sections?.tips?.tip3?.split('for')[1] || 'for parallel components'}</li>
					<li>Always set <code class="rounded bg-green-200 px-1">{$exampleText.sections?.tips?.showFalse || 'show=False'}</code> {$exampleText.sections?.tips?.tip4?.split('in')[1] || 'in the Diagram constructor'}</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-yellow-900">{$exampleText.sections?.examplePattern?.title || 'Example Pattern:'}</h3>
				<pre class="rounded bg-white p-3 text-xs overflow-x-auto"><code>{$exampleText.sections?.examplePattern?.code || `from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS

with Diagram("My Architecture", show=False):
    web = EC2("web server")
    db = RDS("database")
    web >> db  # web connects to database`}</code></pre>
			</div>
		</div>
		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/diagrams/diagram_creator.py"
				target="_blank">{$exampleText.links?.creatorSource || 'View Creator Source'}</a
			>
		</p>
	</article>
</ExperimentCard>
