<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { SentimentAnalysisController } from '$lib/controller/SentimentAnalysisController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { createLogger } from '@guinetik/logger';

	const logger = createLogger({
		prefix: 'SentimentAnalysisPage',
		level: 'debug'
	});

	// Page metadata
	let name = 'Sentiment Analysis';

	// Controller
	let controller = browser ? new SentimentAnalysisController() : null;

	// Reactive state
	let textInput = '';
	let isInitializing = $state(true);
	let modelStats = $state(null);
	let prediction = $state(null);
	let error = $state(null);
	let updateMessage = $state(null);
	let showFeedback = $state(false);
	let showCorrectionForm = $state(false);
	let correctSentimentValue = $state(1); // Default to positive

	// Sentiment display configuration
	const sentimentConfig = {
		positive: { emoji: '😊', color: 'green', label: 'Positive' },
		negative: { emoji: '😞', color: 'red', label: 'Negative' },
		neutral: { emoji: '😐', color: 'yellow', label: 'Neutral' }
	};

	/**
	 * Example sentences to try
	 */
	const examples = [
		"I absolutely love this product! It's amazing!",
		'This is terrible and I hate it.',
		"It's okay, nothing special really.",
		'Best purchase ever! Highly recommend!',
		'Waste of money, very disappointing.'
	];

	onMount(async () => {
		logger.log('🟣 [Svelte] onMount() called');

		if (!browser || !controller) {
			console.warn('⚠️ [Svelte] Skipping mount - browser or controller not available');
			return;
		}

		// Expose UIHandler object for Python to call
		logger.log('🟣 [Svelte] Creating UIHandler...');
		window.sentimentUIHandler = {
			onModelReady: (data) => {
				logger.log('🟣 [UIHandler] onModelReady called:', data);
				// Data is already plain object from controller
				modelStats = data;
				isInitializing = false;
				logger.log('🟣 [UIHandler] modelStats set:', modelStats);
			},

			onPrediction: (data) => {
				logger.log('🟣 [UIHandler] onPrediction called:', data);
				// Data is already plain object from controller
				prediction = data;
				error = null;
				updateMessage = null;
				showFeedback = true;
				showCorrectionForm = false;
				logger.log('🟣 [UIHandler] prediction set:', prediction);
			},

			onModelUpdate: (data) => {
				logger.log('🟣 [UIHandler] onModelUpdate called:', data);
				// Data is already plain object from controller
				modelStats = data.stats;
				prediction = null;
				showFeedback = false;
				showCorrectionForm = false;

				if (data.action === 'reinforced') {
					updateMessage = {
						type: 'success',
						text: `Model reinforced! Learned that this was ${data.sentiment}.`
					};
				} else if (data.action === 'retrained') {
					updateMessage = {
						type: 'success',
						text: `Model retrained! Corrected from ${data.old_sentiment} to ${data.new_sentiment}.`
					};
				} else if (data.action === 'reset') {
					updateMessage = {
						type: 'info',
						text: 'Model reset to original training data.'
					};
				}

				setTimeout(() => {
					updateMessage = null;
				}, 3000);
			},

			onError: (message) => {
				logger.log('🟣 [UIHandler] onError called:', message);
				error = String(message);
				isInitializing = false;
			}
		};

		logger.log('🟣 [Svelte] UIHandler exposed to window');
		logger.log('🟣 [Svelte] Initializing controller...');
		await controller.initialize();
		logger.log('🟣 [Svelte] Controller initialized');
	});

	onDestroy(() => {
		if (!browser || !controller) return;

		// Clean up UIHandler
		delete window.sentimentUIHandler;

		// Destroy controller
		controller.destroy();
	});

	function analyzeSentiment() {
		if (!browser || !controller) return;
		if (!textInput || textInput.trim() === '') {
			error = 'Please enter some text to analyze!';
			return;
		}
		error = null;
		controller.analyzeSentiment(textInput);
	}

	function tryExample(text) {
		textInput = text;
		analyzeSentiment();
	}

	function confirmCorrect() {
		if (!browser || !controller) return;
		controller.confirmPrediction();
	}

	function showCorrection() {
		showCorrectionForm = true;
	}

	function submitCorrection() {
		if (!browser || !controller) return;
		controller.correctPrediction(parseInt(correctSentimentValue));
	}

	function resetTraining() {
		if (!browser || !controller) return;
		controller.resetModel();
	}

	function clearAndReset() {
		textInput = '';
		prediction = null;
		error = null;
		updateMessage = null;
		showFeedback = false;
		showCorrectionForm = false;
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
				placeholder="Type or paste any text here...

Example: 'I love this product!'"
			></textarea>
		</div>

		<!-- Analyze Button -->
		<div class="mb-6 flex-shrink-0">
			<button
				class="w-full rounded-lg bg-blue-500 px-6 py-3 text-lg font-semibold text-white shadow-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				type="button"
				onclick={analyzeSentiment}
				disabled={isInitializing}
			>
				{#if isInitializing}
					⏳ Loading Model...
				{:else}
					🔍 Analyze Sentiment
				{/if}
			</button>
		</div>

		<!-- Result Area -->
		<div class="flex-1 overflow-auto">
			<!-- Error Message -->
			{#if error}
				<div class="rounded-lg bg-red-100 p-4 text-center border-2 border-red-300 mb-4">
					<p class="text-2xl font-bold mb-2 text-red-600">Error!</p>
					<p class="text-sm text-red-700">{error}</p>
				</div>
			{/if}

			<!-- Update Message -->
			{#if updateMessage}
				<div
					class="rounded-lg p-4 text-center border-2 mb-4 {updateMessage.type === 'success'
						? 'bg-green-100 border-green-400'
						: 'bg-blue-100 border-blue-400'}"
				>
					<p class="text-3xl mb-2">{updateMessage.type === 'success' ? '✅' : '🔄'}</p>
					<p class="font-bold mb-1 {updateMessage.type === 'success' ? 'text-green-900' : 'text-blue-900'}">
						{updateMessage.text}
					</p>
					{#if modelStats}
						<p class="text-xs text-gray-600 mt-2">
							Training examples: {modelStats.training_count} | Accuracy: {(modelStats.accuracy * 100).toFixed(1)}%
						</p>
					{/if}
					<button
						onclick={clearAndReset}
						class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500"
					>
						Analyze Another Text
					</button>
				</div>
			{/if}

			<!-- Prediction Result -->
			{#if prediction && !updateMessage}
				{@const config = sentimentConfig[prediction.sentiment]}
				<div class="rounded-lg bg-{config.color}-50 p-6 mb-4 border-2 border-{config.color}-200">
					<div class="text-center mb-4">
						<div class="text-6xl mb-2">{config.emoji}</div>
						<h3 class="text-3xl font-bold text-{config.color}-700 mb-2">{config.label}</h3>
						<p class="text-lg text-gray-600">{(prediction.confidence * 100).toFixed(1)}% confident</p>
					</div>

					<div class="mt-4">
						<h4 class="font-semibold text-sm text-gray-700 mb-2">All Scores:</h4>
						<div class="space-y-2">
							<div class="flex items-center justify-between">
								<span class="text-sm">😊 Positive</span>
								<div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
									<div
										class="bg-green-500 h-2 rounded-full"
										style="width: {prediction.probabilities.positive * 100}%"
									></div>
								</div>
								<span class="text-sm font-medium"
									>{(prediction.probabilities.positive * 100).toFixed(1)}%</span
								>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm">😐 Neutral</span>
								<div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
									<div
										class="bg-yellow-500 h-2 rounded-full"
										style="width: {prediction.probabilities.neutral * 100}%"
									></div>
								</div>
								<span class="text-sm font-medium"
									>{(prediction.probabilities.neutral * 100).toFixed(1)}%</span
								>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm">😞 Negative</span>
								<div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
									<div
										class="bg-red-500 h-2 rounded-full"
										style="width: {prediction.probabilities.negative * 100}%"
									></div>
								</div>
								<span class="text-sm font-medium"
									>{(prediction.probabilities.negative * 100).toFixed(1)}%</span
								>
							</div>
						</div>
					</div>
				</div>

				<!-- Feedback Section -->
				{#if showFeedback}
					<div class="rounded-lg bg-blue-50 p-4 border-2 border-blue-200">
						<h4 class="font-bold mb-2 text-center text-blue-900">Was this prediction correct?</h4>
						<p class="text-xs text-center text-gray-600 mb-3">Help improve the model!</p>

						{#if !showCorrectionForm}
							<div class="flex gap-2">
								<button
									onclick={confirmCorrect}
									class="flex-1 rounded bg-green-400 px-4 py-3 text-white hover:bg-green-500 font-bold text-lg"
								>
									✓ YES
								</button>
								<button
									onclick={showCorrection}
									class="flex-1 rounded bg-red-400 px-4 py-3 text-white hover:bg-red-500 font-bold text-lg"
								>
									✗ NO
								</button>
							</div>
						{:else}
							<div>
								<div class="mb-3">
									<label class="text-sm font-medium block mb-1">What's the correct sentiment?</label>
									<select
										bind:value={correctSentimentValue}
										class="w-full px-3 py-2 border rounded"
									>
										<option value="1">😊 Positive</option>
										<option value="2">😐 Neutral</option>
										<option value="0">😞 Negative</option>
									</select>
								</div>
								<div class="flex gap-2">
									<button
										onclick={submitCorrection}
										class="flex-1 rounded bg-orange-400 px-3 py-2 text-white hover:bg-orange-500 font-medium"
									>
										🎓 Retrain Model
									</button>
									<button
										onclick={resetTraining}
										class="flex-1 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500 font-medium"
									>
										🔄 Reset Training
									</button>
								</div>
							</div>
						{/if}
					</div>
				{/if}

				{#if modelStats}
					<p class="text-xs text-center text-gray-500 mt-4">
						Training examples: {modelStats.training_count} | Model: TF-IDF + Logistic Regression
					</p>
				{/if}
			{/if}

			<!-- Loading State -->
			{#if isInitializing && !error}
				<div class="rounded-lg bg-gray-100 p-4 text-center border-2 border-gray-300">
					<p class="text-3xl mb-2 animate-pulse">⏳</p>
					<p class="font-bold mb-1">Loading Sentiment Analyzer...</p>
					<p class="text-sm text-gray-600">Initializing machine learning model</p>
				</div>
			{/if}

			<!-- Ready State (when no prediction and no error) -->
			{#if !isInitializing && !prediction && !error && !updateMessage && modelStats}
				<div class="rounded-lg bg-blue-100 p-4 text-center border-2 border-blue-300">
					<p class="text-3xl mb-2">🤖</p>
					<p class="font-bold mb-1">Sentiment Analyzer Ready!</p>
					<p class="text-sm text-gray-600">Enter text above and click Analyze</p>
					<p class="text-xs text-gray-500 mt-2">
						Training examples: {modelStats.training_count} | Accuracy: {(modelStats.accuracy * 100).toFixed(1)}%
					</p>
				</div>
			{/if}
			<div id="sentiment-analysis-script"></div>
		</div>
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
						class="block w-full rounded border border-purple-200 bg-white p-2 text-left text-sm hover:bg-purple-100 disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={isInitializing}
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
				<li>
					The model uses <strong>TF-IDF (Term Frequency-Inverse Document Frequency)</strong> to convert
					text to numbers
				</li>
				<li>
					A <strong>Logistic Regression</strong> classifier predicts sentiment based on word patterns
				</li>
				<li>Trained on 45 example sentences (15 positive, 15 negative, 15 neutral)</li>
				<li>Shows confidence scores for all three sentiment categories</li>
				<li>All processing happens in your browser using PyScript!</li>
			</ul>
		</div>

		<div class="mt-4 rounded-lg bg-green-50 p-4">
			<h3 class="mb-2 font-bold text-green-900">💡 Active Learning</h3>
			<p class="text-sm text-green-800">After each prediction, you can provide feedback:</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-green-800">
				<li><strong>Click YES</strong> if correct → Reinforces the model</li>
				<li>
					<strong>Click NO</strong> if wrong → Correct it and retrain with the right label
				</li>
			</ul>
			<p class="mt-2 text-sm text-green-800">
				The model learns from your feedback and improves over time!
			</p>
		</div>

		<div class="mt-4 rounded-lg bg-orange-50 p-4">
			<h3 class="mb-2 font-bold text-orange-900">🏗️ Architecture</h3>
			<p class="text-sm text-orange-800">
				This example demonstrates proper separation of concerns:
			</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-orange-800">
				<li>
					<strong>Python</strong> - Pure ML logic, no HTML. Uses <code>to_js()</code> to convert Python dicts to JavaScript objects before calling window callbacks.
				</li>
				<li>
					<strong>Controller</strong> - Business logic layer. Receives plain JS objects and delegates to UIHandler.
				</li>
				<li>
					<strong>Svelte UIHandler</strong> - Pure UI rendering with reactive state. Updates UI based on plain objects.
				</li>
			</ul>
			<p class="mt-2 text-xs text-orange-700">
				<strong>Key lesson:</strong> Python dicts must be explicitly converted using <code>to_js(dict, dict_converter=Object.fromEntries)</code> to work properly with JavaScript.
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
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/ml/sentiment_analysis.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>
