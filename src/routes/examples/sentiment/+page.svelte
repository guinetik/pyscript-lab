<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import { SentimentAnalysisController } from '$lib/controller/SentimentAnalysisController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import { createLogger } from '@guinetik/logger';

	const logger = createLogger({
		prefix: 'SentimentAnalysisPage',
		level: 'debug'
	});

	// Get translated content
	const exampleText = exampleTranslationStore('sentiment');

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
	 * Create derived examples array with translated examples from all categories.
	 * Gathers examples from positive, negative, and neutral categories.
	 */
	let examples = $derived.by(() => {
		const examplesData = $exampleText?.examples;
		if (!examplesData) return [];
		
		const allExamples = [];
		
		// Gather all examples from nested structure
		['positive', 'negative', 'neutral'].forEach(category => {
			if (examplesData[category]) {
				Object.values(examplesData[category]).forEach(example => {
					if (example) allExamples.push(example);
				});
			}
		});
		
		// Fallback for old flat structure if new structure not found
		if (allExamples.length === 0) {
			['example1', 'example2', 'example3', 'example4', 'example5'].forEach(key => {
				const example = examplesData[key];
				if (example) allExamples.push(example);
			});
		}
		
		return allExamples;
	});

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
				{$exampleText.ui?.inputLabel || 'Enter text to analyze:'}
			</label>
			<textarea
				id="text-input"
				bind:value={textInput}
				rows="5"
				class="w-full rounded-lg border-2 border-gray-300 bg-white p-4 text-base text-black shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
				placeholder={$exampleText.ui?.placeholder || "Type or paste any text here...\n\nExample: 'I love this product!'"}
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
					{$exampleText.ui?.loadingModel || '⏳ Loading Model...'}
				{:else}
					{$exampleText.ui?.analyzeSentiment || '🔍 Analyze Sentiment'}
				{/if}
			</button>
		</div>

		<!-- Result Area -->
		<div class="flex-1 overflow-auto">
			<!-- Error Message -->
			{#if error}
				<div class="rounded-lg bg-red-100 p-4 text-center border-2 border-red-300 mb-4">
					<p class="text-2xl font-bold mb-2 text-red-600">{$exampleText.ui?.error || 'Error!'}</p>
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
							{$exampleText.ui?.modelInfo?.replace('{count}', modelStats.training_count) || `Training examples: ${modelStats.training_count} | Model: TF-IDF + Logistic Regression`} | Accuracy: {(modelStats.accuracy * 100).toFixed(1)}%
						</p>
					{/if}
					<button
						onclick={clearAndReset}
						class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500"
					>
						{$exampleText.ui?.analyzeAnother || 'Analyze Another Text'}
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
						<h4 class="font-semibold text-sm text-gray-700 mb-2">{$exampleText.ui?.allScores || 'All Scores:'}</h4>
						<div class="space-y-2">
							<div class="flex items-center justify-between">
								<span class="text-sm">{$exampleText.ui?.positiveOption || '😊 Positive'}</span>
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
								<span class="text-sm">{$exampleText.ui?.neutralOption || '😐 Neutral'}</span>
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
								<span class="text-sm">{$exampleText.ui?.negativeOption || '😞 Negative'}</span>
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
						<h4 class="font-bold mb-2 text-center text-blue-900">{$exampleText.ui?.feedbackQuestion || 'Was this prediction correct?'}</h4>
						<p class="text-xs text-center text-gray-600 mb-3">{$exampleText.ui?.feedbackHint || 'Help improve the model!'}</p>

						{#if !showCorrectionForm}
							<div class="flex gap-2">
								<button
									onclick={confirmCorrect}
									class="flex-1 rounded bg-green-400 px-4 py-3 text-white hover:bg-green-500 font-bold text-lg"
								>
{$exampleText.ui?.yesButton || '✓ YES'}
								</button>
								<button
									onclick={showCorrection}
									class="flex-1 rounded bg-red-400 px-4 py-3 text-white hover:bg-red-500 font-bold text-lg"
								>
{$exampleText.ui?.noButton || '✗ NO'}
								</button>
							</div>
						{:else}
							<div>
								<div class="mb-3">
									<label class="text-sm font-medium block mb-1">{$exampleText.ui?.correctLabel || "What's the correct sentiment?"}</label>
									<select
										bind:value={correctSentimentValue}
										class="w-full px-3 py-2 border rounded"
									>
										<option value="1">{$exampleText.ui?.positiveOption || '😊 Positive'}</option>
										<option value="2">{$exampleText.ui?.neutralOption || '😐 Neutral'}</option>
										<option value="0">{$exampleText.ui?.negativeOption || '😞 Negative'}</option>
									</select>
								</div>
								<div class="flex gap-2">
									<button
										onclick={submitCorrection}
										class="flex-1 rounded bg-orange-400 px-3 py-2 text-white hover:bg-orange-500 font-medium"
									>
										{$exampleText.ui?.retrainButton || '🎓 Retrain Model'}
									</button>
									<button
										onclick={resetTraining}
										class="flex-1 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500 font-medium"
									>
										{$exampleText.ui?.resetButton || '🔄 Reset Training'}
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
					<p class="font-bold mb-1">{$exampleText.ui?.loadingAnalyzer || 'Loading Sentiment Analyzer...'}</p>
					<p class="text-sm text-gray-600">{$exampleText.ui?.initializingModel || 'Initializing machine learning model'}</p>
				</div>
			{/if}

			<!-- Ready State (when no prediction and no error) -->
			{#if !isInitializing && !prediction && !error && !updateMessage && modelStats}
				<div class="rounded-lg bg-blue-100 p-4 text-center border-2 border-blue-300">
					<p class="text-3xl mb-2">🤖</p>
					<p class="font-bold mb-1">{$exampleText.ui?.readyTitle || 'Sentiment Analyzer Ready!'}</p>
					<p class="text-sm text-gray-600">{$exampleText.ui?.readyMessage || 'Enter text above and click Analyze'}</p>
					<p class="text-xs text-gray-500 mt-2">
						{$exampleText.ui?.modelInfo?.replace('{count}', modelStats.training_count) || `Training examples: ${modelStats.training_count} | Model: TF-IDF + Logistic Regression`} | Accuracy: {(modelStats.accuracy * 100).toFixed(1)}%
					</p>
				</div>
			{/if}
			<div id="sentiment-analysis-script"></div>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Sentiment Analysis'}</h2>
		<p class="mb-4">
			{$exampleText.description || 'Analyze the sentiment of any text using machine learning! The model classifies text as Positive, Negative, or Neutral with confidence scores.'}
		</p>

		<Callout>
			<h3 class="mb-3 font-heading font-bold">{$exampleText.examples?.sectionTitle || 'Try These Examples:'}</h3>
			<div class="space-y-2">
				{#each examples as example, i}
					<button
						onclick={() => tryExample(example)}
						class="block w-full rounded border border-border bg-surface p-2 text-left text-sm hover:bg-surface-alt disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={isInitializing}
					>
						<span class="font-medium text-accent">Example {i + 1}:</span>
						<span class="text-text-primary">{example}</span>
					</button>
				{/each}
			</div>
		</Callout>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.howItWorks?.title || 'How it works:'}</h3>
			<ul class="list-disc space-y-2 pl-5 text-sm">
				<li>
					{$exampleText.sections?.howItWorks?.bullet1 || 'The model uses TF-IDF (Term Frequency-Inverse Document Frequency) to convert text to numbers'}
				</li>
				<li>
					{$exampleText.sections?.howItWorks?.bullet2 || 'A Logistic Regression classifier predicts sentiment based on word patterns'}
				</li>
				<li>{$exampleText.sections?.howItWorks?.bullet3 || 'Trained on 45 example sentences (15 positive, 15 negative, 15 neutral)'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet4 || 'Shows confidence scores for all three sentiment categories'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet5 || 'All processing happens in your browser using PyScript!'}</li>
			</ul>
		</Callout>

		<Callout type="tip">
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.activeLearning?.title || '💡 Active Learning'}</h3>
			<p class="text-sm">{$exampleText.sections?.activeLearning?.description || 'After each prediction, you can provide feedback:'}</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm">
				<li>
					{$exampleText.sections?.activeLearning?.feedbackYes || 'Click YES if correct → Reinforces the model'}
				</li>
				<li>
					{$exampleText.sections?.activeLearning?.feedbackNo || 'Click NO if wrong → Correct it and retrain with the right label'}
				</li>
			</ul>
			<p class="mt-2 text-sm">
				{$exampleText.sections?.activeLearning?.conclusion || 'The model learns from your feedback and improves over time!'}
			</p>
		</Callout>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.architecture?.title || '🏗️ Architecture'}</h3>
			<p class="text-sm">
				{$exampleText.sections?.architecture?.description || 'This example demonstrates proper separation of concerns:'}
			</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm">
				<li>
					<strong>{$exampleText.sections?.architecture?.python?.split(' - ')[0] || 'Python'}</strong> - {$exampleText.sections?.architecture?.python?.split(' - ')[1] || 'Pure ML logic, no HTML. Uses to_js() to convert Python dicts to JavaScript objects before calling window callbacks.'}
				</li>
				<li>
					<strong>{$exampleText.sections?.architecture?.controller?.split(' - ')[0] || 'Controller'}</strong> - {$exampleText.sections?.architecture?.controller?.split(' - ')[1] || 'Business logic layer. Receives plain JS objects and delegates to UIHandler.'}
				</li>
				<li>
					<strong>{$exampleText.sections?.architecture?.svelte?.split(' - ')[0] || 'Svelte UIHandler'}</strong> - {$exampleText.sections?.architecture?.svelte?.split(' - ')[1] || 'Pure UI rendering with reactive state. Updates UI based on plain objects.'}
				</li>
			</ul>
			<p class="mt-2 text-xs">
				<strong>Key lesson:</strong> {$exampleText.sections?.architecture?.keyLesson || 'Python dicts must be explicitly converted using to_js(dict, dict_converter=Object.fromEntries) to work properly with JavaScript.'}
			</p>
		</Callout>

		<Callout type="warning">
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.note?.title || '📝 Note'}</h3>
			<p class="text-sm">
				{$exampleText.sections?.note?.description || "This is a simple demonstration model. For production use, you'd want to train on a much larger dataset (thousands of examples) for better accuracy and generalization."}
			</p>
		</Callout>

		{#if $exampleText.sections?.useCases}
			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.useCases?.title || '💼 Real-World Use Cases'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.sections?.useCases?.description || 'Sentiment analysis is widely used in:'}
				</p>
				<ul class="space-y-1 text-sm">
					{#if $exampleText.sections?.useCases?.case1}
						<li>• {$exampleText.sections?.useCases?.case1}</li>
					{/if}
					{#if $exampleText.sections?.useCases?.case2}
						<li>• {$exampleText.sections?.useCases?.case2}</li>
					{/if}
					{#if $exampleText.sections?.useCases?.case3}
						<li>• {$exampleText.sections?.useCases?.case3}</li>
					{/if}
					{#if $exampleText.sections?.useCases?.case4}
						<li>• {$exampleText.sections?.useCases?.case4}</li>
					{/if}
					{#if $exampleText.sections?.useCases?.case5}
						<li>• {$exampleText.sections?.useCases?.case5}</li>
					{/if}
				</ul>
			</Callout>
		{/if}

		<p class="mt-4">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/ml/sentiment_analysis.py"
				target="_blank">{$exampleText.links?.viewSource || 'View source'}</a
			>
		</p>
	</article>
</ExperimentCard>
