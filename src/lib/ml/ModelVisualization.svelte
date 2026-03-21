<!--
	ModelVisualization Component

	Displays the model's internal view of the digit:
	- 8x8 processed image grid showing what the model sees
	- Probability distribution for all digits (0-9)
	Replaces Python-generated HTML with reactive Svelte components.
-->
<script>
	import { predictionResult, modelState } from '$lib/stores/digitRecognitionStore.js';

	/**
	 * Convert 8x8 image data to RGB intensity values
	 * @param {number} pixelValue - Pixel value in 0-16 range (sklearn format)
	 * @returns {string} RGB color string
	 */
	function getPixelColor(pixelValue) {
		const intensity = Math.floor((pixelValue / 16.0) * 255);
		return `rgb(${intensity}, ${intensity}, ${intensity})`;
	}

	/**
	 * Get background color for probability cell based on confidence
	 * @param {number} probability - Probability value (0-1)
	 * @returns {string} Tailwind color class
	 */
	function getProbabilityColor(probability) {
		const percent = probability * 100;
		if (percent > 50) return 'bg-green-100';
		if (percent > 20) return 'bg-yellow-50';
		if (percent > 5) return 'bg-orange-50';
		return 'bg-gray-50';
	}
</script>

{#if $predictionResult && $predictionResult.imageData2D}
	<!-- What the model sees: 8x8 grid -->
	<div class="rounded-lg bg-yellow-50 p-4 mb-4">
		<h4 class="font-bold text-sm mb-3 text-center">What the model sees (8×8):</h4>
		<div class="grid grid-cols-8 gap-0 mx-auto" style="width: 160px;">
			{#each $predictionResult.imageData2D as row}
				{#each row as pixelValue}
					<div
						style="width: 20px; height: 20px; background: {getPixelColor(pixelValue)};"
					></div>
				{/each}
			{/each}
		</div>
	</div>

	<!-- All predictions: Probability distribution -->
	<div class="rounded-lg bg-surface-alt p-4 mb-4">
		<h4 class="font-bold mb-3 text-center">All Predictions:</h4>
		<div class="grid grid-cols-5 gap-3 text-sm">
			{#each $predictionResult.probabilities as probability, digit}
				{@const isTopPrediction = digit === $predictionResult.prediction}
				<div
					class="text-center p-2 rounded {getProbabilityColor(probability)}"
					class:ring-2={isTopPrediction}
					class:ring-blue-500={isTopPrediction}
					class:font-bold={isTopPrediction}
				>
					<div class="text-lg font-bold">{digit}</div>
					<div class="text-xs text-gray-600">{Math.round(probability * 100)}%</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Model statistics -->
	{#if $modelState.accuracy !== undefined}
		<p class="text-xs text-center text-gray-500">
			Model accuracy: {$modelState.accuracy.toFixed(1)}% on test set | Training examples: {$modelState.trainingExamples}
		</p>
	{/if}
{/if}
