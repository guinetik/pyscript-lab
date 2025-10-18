<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { BokehController } from '$lib/controller/BokehController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	// Translation store
	const exampleText = exampleTranslationStore('bokeh-intro');

	// Controller instance
	let controller = browser ? new BokehController() : null;

	// UI state
	let loading = $state(true);
	let errorMessage = $state('');

	onMount(async () => {
		if (!browser || !controller) return;

		// Setup callbacks
		controller.onReady(() => {
			loading = false;
		});

		controller.onError((error) => {
			loading = false;
			errorMessage = `Error: ${error}`;
		});

		// Initialize controller
		await controller.initialize('bokeh_index');
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		controller.destroy();
	});
</script>

<svelte:head>
	<!-- Intentionally left empty, Bokeh configured in app.html -->
</svelte:head>

<ExperimentCard props={{ previousPage: '/examples/matplotlib/maps', nextPage: '/examples/bokeh/pandas' }}>
	<div slot="py_slot" class="relative flex h-full items-center justify-center">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">{$exampleText.loading || '🐍 Loading Python chart...'}</p>
				</div>
			</div>
		{/if}
		{#if errorMessage}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-red-50/90">
				<div class="rounded-lg bg-white p-4 shadow-lg border-2 border-red-500">
					<p class="text-lg text-red-700">{errorMessage}</p>
				</div>
			</div>
		{/if}
		<div id="chart" class="h-full w-full"></div>
	</div>
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Bokeh'}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">{$exampleText.whatIsBokeh?.title || '🎨 What is Bokeh?'}</h3>
				<p class="text-sm text-blue-800">
					{$exampleText.whatIsBokeh?.description || 'Bokeh is a powerful Python library...'}
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">{$exampleText.howBokeh?.title || '⚙️ How Does Bokeh Generate Charts?'}</h3>
				<p class="text-sm text-purple-800 space-y-2">
					<span class="block"
						><strong>1.</strong> {$exampleText.howBokeh?.step1 || 'Python API: You write Python code...'}</span
					>
					<span class="block"
						><strong>2.</strong> {$exampleText.howBokeh?.step2 || 'JSON Serialization...'}</span
					>
					<span class="block"
						><strong>3.</strong> {$exampleText.howBokeh?.step3 || 'BokehJS Rendering...'}</span
					>
					<span class="block"
						><strong>4.</strong> {$exampleText.howBokeh?.step4 || 'Interactivity...'}</span
					>
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">
					{$exampleText.whyBokeh?.title || '🐍 Why Use Bokeh with Python Instead of Pure JavaScript?'}
				</h3>
				<div class="text-sm text-green-800 space-y-2">
					<p class="font-semibold">{$exampleText.whyBokeh?.intro || 'Even though Bokeh ultimately renders using JavaScript:'}</p>
					<ul class="ml-4 list-disc space-y-1">
						<li>
							<strong>Data Processing Power:</strong> {$exampleText.whyBokeh?.dataProcessing?.split(': ')[1] || 'Python excels at data manipulation...'}
						</li>
						<li>
							<strong>Scientific Ecosystem:</strong> {$exampleText.whyBokeh?.scientific?.split(': ')[1] || 'Leverage Python\'s rich scientific libraries...'}
						</li>
						<li>
							<strong>High-Level API:</strong> {$exampleText.whyBokeh?.highLevel?.split(': ')[1] || 'Bokeh\'s Python API is more intuitive...'}
						</li>
						<li>
							<strong>Code Reusability:</strong> {$exampleText.whyBokeh?.reusability?.split(': ')[1] || 'Same Python code works...'}
						</li>
						<li>
							<strong>Complexity Abstraction:</strong> {$exampleText.whyBokeh?.abstraction?.split(': ')[1] || 'Bokeh handles the tedious...'}
						</li>
						<li>
							<strong>With PyScript:</strong> {$exampleText.whyBokeh?.pyscript?.split(': ')[1] || 'Run this Python code directly...'}
						</li>
					</ul>
				</div>
			</div>

			<div class="rounded-lg bg-orange-50 p-4">
				<h3 class="mb-2 font-bold text-orange-900">{$exampleText.workflow?.title || '🔄 The PyScript + Bokeh Workflow'}</h3>
				<p class="text-sm text-orange-800">
					{$exampleText.workflow?.description || 'In this example, PyScript runs the Python code...'}
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">{$exampleText.interactive?.title || '💡 Interactive Features'}</h3>
				<p class="text-sm text-amber-800">
					{$exampleText.interactive?.description || 'Try interacting with the chart above!...'}
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/bokeh_index.py"
				target="_blank">{$exampleText.viewSource || 'View source'}</a
			>
		</p>
	</article>
</ExperimentCard>
