<script>
	/**
	 * TrainingExamples Component
	 *
	 * Displays training examples from the digit recognition dataset.
	 * Renders 8x8 pixel grids showing how the model "sees" digits.
	 */
	export let data;
	export let onHide;

	/**
	 * Convert pixel value to grayscale RGB color
	 * @param {number} value - Pixel value in 0-16 range
	 * @param {number} pixelRange - Maximum pixel value (usually 16)
	 */
	function getPixelColor(value, pixelRange) {
		const intensity = Math.floor((value / pixelRange) * 255);
		return `rgb(${intensity},${intensity},${intensity})`;
	}
</script>

{#if data && data.visible && data.examples}
	<div class="rounded-lg bg-callout p-4 border-2 border-border my-6">
		<h3 class="font-bold text-center mb-3 text-purple-900">Training Data Examples</h3>
		<p class="text-sm text-center mb-4 text-purple-700">
			Here's what the model was trained on:
		</p>

		<!-- Training 4s -->
		<div class="mb-4">
			<h4 class="font-bold text-center mb-2 text-purple-800">Training 4s:</h4>
			<div class="flex justify-center gap-2 flex-wrap">
				{#each data.examples.fours as fourData}
					<div class="grid grid-cols-8 gap-0" style="width: 80px;">
						{#each fourData.flat() as pixelValue}
							<div
								style="width: 10px; height: 10px; background: {getPixelColor(
									pixelValue,
									data.pixelRange
								)};"
							></div>
						{/each}
					</div>
				{/each}
			</div>
		</div>

		<!-- Training 9s -->
		<div class="mb-4">
			<h4 class="font-bold text-center mb-2 text-purple-800">Training 9s:</h4>
			<div class="flex justify-center gap-2 flex-wrap">
				{#each data.examples.nines as nineData}
					<div class="grid grid-cols-8 gap-0" style="width: 80px;">
						{#each nineData.flat() as pixelValue}
							<div
								style="width: 10px; height: 10px; background: {getPixelColor(
									pixelValue,
									data.pixelRange
								)};"
							></div>
						{/each}
					</div>
				{/each}
			</div>
		</div>

		<button
			onclick={onHide}
			class="w-full mt-2 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500 font-medium"
		>
			Hide Examples
		</button>
	</div>
{/if}
