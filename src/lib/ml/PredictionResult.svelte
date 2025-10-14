<!--
	PredictionResult Component

	Displays the ML model's prediction with confidence score and feedback options.
	Replaces Python-generated HTML with reactive Svelte components.
-->
<script>
	import { predictionResult, modelState } from '$lib/stores/digitRecognitionStore.js';

	/**
	 * Determine confidence color based on percentage
	 * @param {number} confidence - Confidence percentage (0-100)
	 * @returns {{bg: string, text: string}} Tailwind color classes
	 */
	function getConfidenceColors(confidence) {
		if (confidence > 60) {
			return { bg: 'green-50', text: 'green-600' };
		} else if (confidence > 30) {
			return { bg: 'yellow-50', text: 'yellow-600' };
		} else {
			return { bg: 'red-50', text: 'red-600' };
		}
	}

	// Local state for correction form
	let showCorrectionForm = $state(false);
	let correctDigit = $state('');

	/**
	 * Handle "YES" button - prediction was correct
	 */
	function handleCorrect() {
		if (window.handleCorrectPrediction) {
			window.handleCorrectPrediction();
		}
	}

	/**
	 * Handle "NO" button - show correction form
	 */
	function showCorrection() {
		showCorrectionForm = true;
	}

	/**
	 * Submit correction and retrain model
	 */
	function submitCorrection() {
		if (!correctDigit || correctDigit === '') {
			alert('Please enter the correct digit (0-9)');
			return;
		}

		const digit = parseInt(correctDigit);
		if (isNaN(digit) || digit < 0 || digit > 9) {
			alert('Please enter a valid digit between 0 and 9');
			return;
		}

		if (window.retrainWithCorrection) {
			window.retrainWithCorrection(digit);
		}
	}

	/**
	 * Reset training to original dataset
	 */
	function resetTraining() {
		if (window.resetTraining) {
			window.resetTraining();
		}
	}

	// Reset form when prediction changes
	$effect(() => {
		if ($predictionResult) {
			showCorrectionForm = false;
			correctDigit = '';
		}
	});
</script>

{#if $predictionResult}
	{@const colors = getConfidenceColors($predictionResult.confidence)}

	<div class="rounded-lg bg-{colors.bg} p-4 mb-4">
		<div class="flex items-center justify-center gap-3 mb-3">
			<p class="text-4xl">🎯</p>
			<div>
				<h3 class="text-3xl font-extrabold text-{colors.text}">
					Prediction: {$predictionResult.prediction}
				</h3>
				<p class="text-sm text-gray-600">
					Confidence: {$predictionResult.confidence.toFixed(1)}%
				</p>
				<p class="text-xs text-gray-500">
					Using K-Nearest Neighbors (k=5, distance-weighted)
				</p>
			</div>
		</div>
	</div>

	<div class="rounded-lg bg-blue-50 p-4 mb-4 border-2 border-blue-200">
		<h4 class="font-bold mb-2 text-center text-blue-900">Was this prediction correct?</h4>
		<p class="text-xs text-center text-gray-600 mb-3">Help the model learn your drawing style!</p>

		{#if !showCorrectionForm}
			<div class="flex gap-2">
				<button
					onclick={handleCorrect}
					class="flex-1 rounded bg-green-400 px-4 py-3 text-white hover:bg-green-500 font-bold text-lg">
					✓ YES
				</button>
				<button
					onclick={showCorrection}
					class="flex-1 rounded bg-red-400 px-4 py-3 text-white hover:bg-red-500 font-bold text-lg">
					✗ NO
				</button>
			</div>
		{:else}
			<div>
				<div class="mb-3">
					<label for="correct-digit-input" class="text-sm font-medium block mb-1">What's the correct digit?</label>
					<input
						type="number"
						id="correct-digit-input"
						bind:value={correctDigit}
						min="0"
						max="9"
						class="w-full px-3 py-2 border rounded"
						placeholder="Enter the correct digit (0-9)"
					/>
				</div>
				<div class="flex gap-2">
					<button
						onclick={submitCorrection}
						class="flex-1 rounded bg-orange-400 px-3 py-2 text-white hover:bg-orange-500 font-medium">
						🎓 Retrain Model
					</button>
					<button
						onclick={resetTraining}
						class="flex-1 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500 font-medium">
						🔄 Reset Training
					</button>
				</div>
			</div>
		{/if}
	</div>

	{#if $modelState.accuracy !== undefined}
		<p class="text-xs text-center text-gray-500 mt-4">
			Training examples: {$modelState.trainingExamples} | Accuracy: {$modelState.accuracy.toFixed(1)}%
		</p>
	{/if}
{/if}
