<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Sentiment Analysis';

	// Text input
	let textInput = '';

	// Python script URL
	const pyScriptUrl = getLink('python/sentiment_analysis.py');

	// Define a RunPython instance to attach our script to
	let pyScriptRunner = RunPython();

	// When the screen loads, we want to load our script
	onMount(() => {
		pyScriptRunner.runScript(pyScriptUrl, 'script_gutter', false);
	});

	// when the screen is destroyed we want to destroy all python tags
	onDestroy(() => {
		if (pyScriptRunner) pyScriptRunner.destroy();
	});

	/**
	 * Analyze the sentiment of the input text
	 */
	function analyzeSentiment() {
		const text = document.getElementById('text-input').value;
		if (text && text.trim()) {
			window.predictSentiment(text);
		}
	}

	/**
	 * Example sentences to try
	 */
	const examples = [
		"I absolutely love this product! It's amazing!",
		"This is terrible and I hate it.",
		"It's okay, nothing special really.",
		"Best purchase ever! Highly recommend!",
		"Waste of money, very disappointing."
	];

	function tryExample(text) {
		document.getElementById('text-input').value = text;
		analyzeSentiment();
	}
</script>

<ExperimentCard props={{ previousPage: '/examples/ml', nextPage: '/' }}>
	<div slot="py_slot" class="flex h-full w-full flex-col p-6">
		<!-- Text Input Area -->
		<div class="mb-4 flex-shrink-0">
			<label for="text-input" class="mb-2 block text-lg font-semibold text-gray-800">
				Enter text to analyze:
			</label>
			<textarea
				id="text-input"
				bind:value={textInput}
				rows="5"
				class="w-full rounded-lg border-2 border-gray-300 bg-white p-4 text-base text-black shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
				placeholder="Type or paste any text here...&#10;&#10;Example: 'I love this product!'"
			></textarea>
		</div>

		<!-- Analyze Button -->
		<div class="mb-6 flex-shrink-0">
			<button
				class="w-full rounded-lg bg-blue-500 px-6 py-3 text-lg font-semibold text-white shadow-md hover:bg-blue-600 transition-colors"
				type="button"
				onclick={analyzeSentiment}
			>
				🔍 Analyze Sentiment
			</button>
		</div>

		<!-- Result will appear here -->
		<div id="result" class="flex-1 overflow-auto"></div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>
		<p class="mb-4">
			Analyze the sentiment of any text using machine learning! The model classifies text as
			Positive, Negative, or Neutral with confidence scores.
		</p>

		<div class="my-6 rounded-lg bg-purple-50 p-4">
			<h3 class="mb-3 font-bold text-purple-900">Try These Examples:</h3>
			<div class="space-y-2">
				{#each examples as example, i}
					<button
						onclick={() => tryExample(example)}
						class="block w-full rounded border border-purple-200 bg-white p-2 text-left text-sm hover:bg-purple-100"
					>
						<span class="font-medium text-purple-700">Example {i + 1}:</span>
						<span class="text-gray-700">{example}</span>
					</button>
				{/each}
			</div>
		</div>

		<div class="mt-6 rounded-lg bg-blue-50 p-4">
			<h3 class="mb-2 font-bold text-blue-900">How it works:</h3>
			<ul class="list-disc space-y-2 pl-5 text-sm text-blue-800">
				<li>The model uses <strong>TF-IDF (Term Frequency-Inverse Document Frequency)</strong> to convert text to numbers</li>
				<li>A <strong>Logistic Regression</strong> classifier predicts sentiment based on word patterns</li>
				<li>Trained on 45 example sentences (15 positive, 15 negative, 15 neutral)</li>
				<li>Shows confidence scores for all three sentiment categories</li>
				<li>All processing happens in your browser using PyScript!</li>
			</ul>
		</div>

		<div class="mt-4 rounded-lg bg-green-50 p-4">
			<h3 class="mb-2 font-bold text-green-900">💡 Active Learning</h3>
			<p class="text-sm text-green-800">
				After each prediction, you can provide feedback:
			</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-green-800">
				<li><strong>Click YES</strong> if correct → Reinforces the model</li>
				<li><strong>Click NO</strong> if wrong → Correct it and retrain with the right label</li>
			</ul>
			<p class="mt-2 text-sm text-green-800">
				The model learns from your feedback and improves over time!
			</p>
		</div>

		<div class="mt-4 rounded-lg bg-yellow-50 p-4">
			<h3 class="mb-2 font-bold text-yellow-900">📝 Note</h3>
			<p class="text-sm text-yellow-800">
				This is a simple demonstration model. For production use, you'd want to train on a much
				larger dataset (thousands of examples) for better accuracy and generalization.
			</p>
		</div>

		<p class="mt-4">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/sentiment_analysis.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>
