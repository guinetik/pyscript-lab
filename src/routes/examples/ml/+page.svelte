<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';
	import PredictionResult from '$lib/ml/PredictionResult.svelte';
	import ModelVisualization from '$lib/ml/ModelVisualization.svelte';
	import UIStatus from '$lib/ml/UIStatus.svelte';
	import {
		predictionResult,
		modelState,
		uiState,
		resetStores
	} from '$lib/stores/digitRecognitionStore.js';

	// Page metadata
	let name = 'Machine Learning - Digit Recognition';

	// Canvas reference
	let canvas;
	let ctx;
	let isDrawing = false;

	// Python script URL
	const pyScriptUrl = getLink('python/digit_recognition.py');

	// Define a RunPython instance to attach our script to
	let pyScriptRunner = RunPython();

	// When the screen loads, we want to load our script
	onMount(() => {
		// Expose store update functions to window for Python to call
		// Convert Pyodide proxies to plain JavaScript objects to avoid proxy destruction errors
		window.updatePredictionResult = (data) => {
			console.log('🟢 [JS] updatePredictionResult called with:', data);
			if (data === null || data === undefined) {
				console.log('🟢 [JS] Clearing prediction result');
				predictionResult.set(null);
			} else {
				// Convert proxy to plain JS object
				const plainData = {
					prediction: data.prediction,
					confidence: data.confidence,
					probabilities: Array.from(data.probabilities || []),
					imageData: Array.from(data.imageData || []),
					imageData2D: Array.from(data.imageData2D || []).map(row => Array.from(row))
				};
				console.log('🟢 [JS] Setting prediction result:', plainData);
				predictionResult.set(plainData);
			}
		};

		window.updateModelState = (data) => {
			console.log('🟢 [JS] updateModelState called with:', data);
			// Convert proxy to plain JS object
			const plainData = {
				accuracy: data.accuracy,
				trainingExamples: data.trainingExamples
			};
			console.log('🟢 [JS] Setting model state:', plainData);
			modelState.set(plainData);
		};

		window.updateUIState = (status, message) => {
			console.log('🟢 [JS] updateUIState called:', status, message);
			// Primitives don't need conversion
			uiState.set({ status: String(status), message: String(message) });
		};

		// Expose clearAndReset for Python and components to call
		window.clearAndReset = clearAndResetUI;

		// Initialize model state
		modelState.set({ accuracy: 0, trainingExamples: 0 });
		uiState.set({ status: 'ready', message: 'Draw a digit and click Predict' });

		pyScriptRunner.runScript(pyScriptUrl, 'script_gutter', false);

		// Setup canvas
		canvas = document.getElementById('drawCanvas');
		if (canvas) {
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

	// when the screen is destroyed we want to destroy all python tags
	onDestroy(() => {
		if (pyScriptRunner) pyScriptRunner.destroy();
	});

	/**
	 * Start drawing on canvas
	 */
	function startDrawing(e) {
		isDrawing = true;
		const rect = canvas.getBoundingClientRect();
		ctx.beginPath();
		ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
	}

	/**
	 * Draw on canvas
	 */
	function draw(e) {
		if (!isDrawing) return;
		const rect = canvas.getBoundingClientRect();
		ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
		ctx.stroke();
	}

	/**
	 * Stop drawing
	 */
	function stopDrawing() {
		isDrawing = false;
	}

	/**
	 * Handle touch start for mobile
	 */
	function handleTouchStart(e) {
		e.preventDefault();
		const touch = e.touches[0];
		const rect = canvas.getBoundingClientRect();
		isDrawing = true;
		ctx.beginPath();
		ctx.moveTo(touch.clientX - rect.left, touch.clientY - rect.top);
	}

	/**
	 * Handle touch move for mobile
	 */
	function handleTouchMove(e) {
		e.preventDefault();
		if (!isDrawing) return;
		const touch = e.touches[0];
		const rect = canvas.getBoundingClientRect();
		ctx.lineTo(touch.clientX - rect.left, touch.clientY - rect.top);
		ctx.stroke();
	}

	/**
	 * Clear the canvas
	 */
	function clearCanvas() {
		ctx.fillStyle = 'white';
		ctx.fillRect(0, 0, canvas.width, canvas.height);
		resetStores();
	}

	/**
	 * Clear canvas and reset UI (called from Python and components)
	 */
	function clearAndResetUI() {
		clearCanvas();
		// Also clear model viz
		predictionResult.set(null);
	}

	/**
	 * Predict the drawn digit by calling Python
	 */
	function predictDigit() {
		console.log('🔵 [JS] predictDigit() called');
		try {
			// Get canvas data as base64
			const imageData = canvas.toDataURL('image/png');
			console.log('🔵 [JS] Got canvas data, length:', imageData.length);

			// Call Python function directly through window
			if (window.predict_digit) {
				console.log('🔵 [JS] Calling window.predict_digit()');
				window.predict_digit(imageData);
				console.log('🔵 [JS] Python call completed');
			} else {
				console.error('🔴 [JS] window.predict_digit not found! Python may not be ready.');
				alert('Python is not ready yet. Please wait a moment and try again.');
			}
		} catch (e) {
			console.error('🔴 [JS] Error in predictDigit:', e);
			alert('Error: ' + e.message);
		}
	}
</script>

<ExperimentCard props={{ previousPage: '/examples/diagrams/create', nextPage: '/' }}>
	<div slot="py_slot" class="flex h-full w-full flex-col items-center justify-start p-5">
		<!-- Heading -->
		<h3 class="text-2xl font-bold mb-4 text-gray-800">Draw a Number</h3>

		<!-- Canvas for drawing -->
		<div class="mb-4 rounded-lg border-4 border-gray-300 bg-white shadow-lg">
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
				onclick={clearCanvas}>Clear</button
			>
			<button
				class="flex-1 rounded bg-green-400 px-3 py-2 text-white hover:bg-green-500"
				type="button"
				onclick={predictDigit}>Predict</button
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
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>
		<p class="mb-4">
			Draw a digit (0-9) on the canvas and click "Predict" to see what the machine learning
			model thinks you drew!
		</p>

		<!-- Model visualization - Svelte component -->
		<div class="my-6">
			<ModelVisualization />
		</div>

		<!-- Training examples toggle -->
		<div class="my-6 text-center">
			<button
				onclick={() => window.showTrainingExamples()}
				class="rounded bg-purple-400 px-4 py-2 text-white hover:bg-purple-500 font-medium">
				📚 Show Training Examples
			</button>
		</div>
		<div id="training-examples" class="my-6"></div>

		<div class="mt-6 rounded-lg bg-blue-50 p-4">
			<h3 class="mb-2 font-bold text-blue-900">How it works:</h3>
			<ul class="list-disc space-y-2 pl-5 text-sm text-blue-800">
				<li>The model is trained on scikit-learn's digits dataset (1,797 samples of 8×8 images)</li>
				<li>When you click Predict, your drawing is converted to base64</li>
				<li>Python receives the image, preprocesses it to 8×8 grayscale with adaptive thresholding</li>
				<li>A <strong>K-Nearest Neighbors (KNN)</strong> classifier predicts the digit using 5 neighbors</li>
				<li><strong>Distance weighting</strong> gives more importance to closer neighbors for better accuracy</li>
				<li><strong>Active learning:</strong> If the prediction is wrong, you can correct it and retrain the model live!</li>
				<li>All processing happens in your browser using PyScript!</li>
			</ul>
		</div>

		<div class="mt-4 rounded-lg bg-green-50 p-4">
			<h3 class="mb-2 font-bold text-green-900">💡 Active Learning with Positive & Negative Feedback</h3>
			<p class="text-sm text-green-800">
				This model learns from <strong>both</strong> correct and incorrect predictions! After each prediction, you can:
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm text-green-800 mt-2">
				<li><strong>Click YES</strong> if correct → Reinforces the model's understanding of your drawing style</li>
				<li><strong>Click NO</strong> if wrong → Lets you correct it and retrain with the right label</li>
			</ul>
			<p class="text-sm text-green-800 mt-2">
				The more feedback you give (positive or negative), the better it gets at recognizing <em>your</em> handwriting!
			</p>
		</div>

		<p class="mt-4">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/digit_recognition.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>

