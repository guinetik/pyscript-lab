<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import { DigitRecognitionController } from '$lib/controller/DigitRecognitionController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import PredictionResult from '$lib/ml/PredictionResult.svelte';
	import ModelVisualization from '$lib/ml/ModelVisualization.svelte';
	import UIStatus from '$lib/ml/UIStatus.svelte';
	import TrainingExamples from '$lib/ml/TrainingExamples.svelte';
	import {
		predictionResult,
		modelState,
		uiState,
		resetStores
	} from '$lib/stores/digitRecognitionStore.js';

	// Get translated content
	const exampleText = exampleTranslationStore('ml');

	// Controller instance
	let controller = browser ? new DigitRecognitionController() : null;

	// Canvas state
	let canvas;
	let ctx;
	let isDrawing = false;

	// Training examples state
	let trainingExamplesData = $state(null);

	onMount(async () => {
		if (!browser || !controller) return;

		// Expose UIHandler for Python to call
		window.digitRecognitionUIHandler = {
			// Python ready callback (called when PyScriptManager signals ready)
			onPythonReady: () => {
				console.log('✅ Python ML module is ready!');
				// Python initialization already sets initial state, no need to duplicate
			},

			// Prediction results
			onPredictionResult: (data) => {
				if (data === null || data === undefined) {
					predictionResult.set(null);
				} else {
					// Data is already a plain JS object from to_js()
					predictionResult.set(data);
				}
			},

			// Model state updates
			onModelState: (data) => {
				modelState.set(data);
			},

			// UI status messages
			onUIState: (status, message) => {
				uiState.set({ status: String(status), message: String(message) });
			},

			// Training examples data
			onTrainingExamples: (data) => {
				trainingExamplesData = data;
			},

			// Clear and reset
			onClearAndReset: () => {
				clearCanvas();
				predictionResult.set(null);
			}
		};

		// Initialize controller (Python will set initial state when ready)
		await controller.initialize();

		// Setup canvas
		canvas = document.getElementById('drawCanvas');
		if (canvas) {
			controller.setCanvas(canvas);

			ctx = canvas.getContext('2d');
			ctx.fillStyle = 'white';
			ctx.fillRect(0, 0, canvas.width, canvas.height);
			ctx.strokeStyle = 'black';
			ctx.lineWidth = 12;
			ctx.lineCap = 'round';
			ctx.lineJoin = 'round';

			// Mouse events
			canvas.addEventListener('mousedown', startDrawing);
			canvas.addEventListener('mousemove', draw);
			canvas.addEventListener('mouseup', stopDrawing);
			canvas.addEventListener('mouseout', stopDrawing);

			// Touch events for mobile
			canvas.addEventListener('touchstart', handleTouchStart);
			canvas.addEventListener('touchmove', handleTouchMove);
			canvas.addEventListener('touchend', stopDrawing);
		}
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		controller.destroy();
	});

	// Canvas drawing functions
	function startDrawing(e) {
		isDrawing = true;
		const rect = canvas.getBoundingClientRect();
		ctx.beginPath();
		ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
	}

	function draw(e) {
		if (!isDrawing) return;
		const rect = canvas.getBoundingClientRect();
		ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
		ctx.stroke();
	}

	function stopDrawing() {
		isDrawing = false;
	}

	function handleTouchStart(e) {
		e.preventDefault();
		const touch = e.touches[0];
		const rect = canvas.getBoundingClientRect();
		isDrawing = true;
		ctx.beginPath();
		ctx.moveTo(touch.clientX - rect.left, touch.clientY - rect.top);
	}

	function handleTouchMove(e) {
		e.preventDefault();
		if (!isDrawing) return;
		const touch = e.touches[0];
		const rect = canvas.getBoundingClientRect();
		ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
		ctx.stroke();
	}

	function clearCanvas() {
		if (!ctx || !canvas) return;
		ctx.fillStyle = 'white';
		ctx.fillRect(0, 0, canvas.width, canvas.height);
		resetStores();
	}

	// Auto-clear canvas after feedback is submitted
	$effect(() => {
		if ($uiState.status === 'reinforced' || $uiState.status === 'retrained' || $uiState.status === 'reset') {
			// Clear canvas automatically after a brief delay so user can see the message
			setTimeout(() => {
				if (ctx && canvas) {
					ctx.fillStyle = 'white';
					ctx.fillRect(0, 0, canvas.width, canvas.height);
				}
			}, 100);
		}
	});

	// Controller method wrappers
	function predictDigit() {
		if (!browser || !controller) return;
		controller.predictDigit();
	}

	function showTrainingExamples() {
		if (!browser || !controller) return;
		controller.showTrainingExamples();
	}

	function hideTrainingExamples() {
		if (!browser || !controller) return;
		controller.hideTrainingExamples();
	}
</script>

<ExperimentCard props={{ previousPage: '/examples/diagrams/create', nextPage: '/' }}>
	<div slot="py_slot" class="flex h-full w-full flex-col items-center justify-start p-5">
		<!-- Heading -->
		<h3 class="text-2xl font-bold mb-4 text-gray-800">{$exampleText.ui?.drawHeading || 'Draw a Number'}</h3>

		<!-- Canvas for drawing -->
		<div class="mb-4 rounded-lg border-4 border-border bg-surface shadow-card">
			<canvas
				id="drawCanvas"
				width="320"
				height="320"
				class="cursor-crosshair"
				style="touch-action: none;"
			></canvas>
		</div>

		<!-- Buttons -->
		<div class="flex w-full gap-4">
			<button
				class="flex-1 rounded bg-red-400 px-3 py-2 text-white hover:bg-red-500"
				type="button"
				onclick={clearCanvas}>{$exampleText.ui?.clearButton || 'Clear'}</button
			>
			<button
				class="flex-1 rounded bg-green-400 px-3 py-2 text-white hover:bg-green-500"
				type="button"
				onclick={predictDigit}>{$exampleText.ui?.predictButton || 'Predict'}</button
			>
		</div>

		<!-- Prediction result - Svelte components -->
		<div class="my-6 w-full">
			{#if $predictionResult}
				<PredictionResult />
			{:else}
				<UIStatus />
			{/if}
		</div>
	</div>
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Machine Learning - Digit Recognition'}</h2>
		<p class="mb-4">
			{$exampleText.description || 'Draw a digit (0-9) on the canvas and click "Predict" to see what the machine learning model thinks you drew!'}
		</p>

		<!-- Model visualization - Svelte component -->
		<div class="my-6">
			<ModelVisualization />
		</div>

		<!-- Training examples toggle -->
		<div class="my-6 text-center">
			<button
				onclick={showTrainingExamples}
				class="rounded bg-purple-400 px-4 py-2 text-white hover:bg-purple-500 font-medium">
				{$exampleText.ui?.trainingExamplesButton || '📚 Show Training Examples'}
			</button>
		</div>

		<!-- Training examples component -->
		<TrainingExamples data={trainingExamplesData} onHide={hideTrainingExamples} />

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.howItWorks?.title || 'How it works:'}</h3>
			<ul class="list-disc space-y-2 pl-5 text-sm">
				<li>{$exampleText.sections?.howItWorks?.bullet1 || "The model is trained on scikit-learn's digits dataset (1,797 samples of 8×8 images)"}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet2 || 'When you click Predict, your drawing is converted to base64'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet3 || 'Python receives the image, preprocesses it to 8×8 grayscale with adaptive thresholding'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet4 || 'A K-Nearest Neighbors (KNN) classifier predicts the digit using 5 neighbors'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet5 || 'Distance weighting gives more importance to closer neighbors for better accuracy'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet6 || 'Active learning: If the prediction is wrong, you can correct it and retrain the model live!'}</li>
				<li>{$exampleText.sections?.howItWorks?.bullet7 || 'All processing happens in your browser using PyScript!'}</li>
			</ul>
		</Callout>

		<Callout type="tip">
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.activeLearning?.title || 'Active Learning with Positive & Negative Feedback'}</h3>
			<p class="text-sm">
				{$exampleText.sections?.activeLearning?.description || 'This model learns from both correct and incorrect predictions! After each prediction, you can:'}
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm mt-2">
				<li>{$exampleText.sections?.activeLearning?.feedbackYes || 'Click YES if correct → Reinforces the model\'s understanding of your drawing style'}</li>
				<li>{$exampleText.sections?.activeLearning?.feedbackNo || 'Click NO if wrong → Lets you correct it and retrain with the right label'}</li>
			</ul>
			<p class="text-sm mt-2">
				{$exampleText.sections?.activeLearning?.conclusion || 'The more feedback you give (positive or negative), the better it gets at recognizing your handwriting!'}
			</p>
		</Callout>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.sections?.architecture?.title || 'Architecture'}</h3>
			<p class="text-sm">
				{$exampleText.sections?.architecture?.description || 'This example demonstrates proper separation of concerns with event-driven initialization:'}
			</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm">
				<li>
					<strong>{$exampleText.sections?.architecture?.component1?.split(' - ')[0] || 'PyScriptManager'}</strong> - {$exampleText.sections?.architecture?.component1?.split(' - ')[1] || 'Event-driven lifecycle management (no polling!)'}
				</li>
				<li>
					<strong>{$exampleText.sections?.architecture?.component2?.split(' - ')[0] || 'Python'}</strong> - {$exampleText.sections?.architecture?.component2?.split(' - ')[1] || 'Pure ML logic, signals ready when initialized, sends only data via callbacks'}
				</li>
				<li>
					<strong>{$exampleText.sections?.architecture?.component3?.split(' - ')[0] || 'DigitRecognitionController'}</strong> - {$exampleText.sections?.architecture?.component3?.split(' - ')[1] || 'Manages communication layer between Python and UI'}
				</li>
				<li>
					<strong>{$exampleText.sections?.architecture?.component4?.split(' - ')[0] || 'Svelte Components'}</strong> - {$exampleText.sections?.architecture?.component4?.split(' - ')[1] || 'Pure UI rendering with reactive state'}
				</li>
			</ul>
		</Callout>

		<p class="mt-4">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/ml/digit_recognition.py"
				target="_blank">{$exampleText.links?.viewSource || 'View source'}</a
			>
		</p>
	</article>
</ExperimentCard>
