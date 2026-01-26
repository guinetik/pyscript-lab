<!--
	UIStatus Component

	Displays various UI states for the digit recognition system:
	- Ready state (model trained and waiting)
	- Success messages (reinforcement, retraining, reset)
	- Error messages
	Replaces Python-generated status HTML with reactive Svelte components.
-->
<script>
	import { uiState, modelState } from '$lib/stores/digitRecognitionStore.js';

	/**
	 * Clear canvas and reset to ready state
	 */
	function clearAndReset() {
		if (window.clearAndReset) {
			window.clearAndReset();
		}
	}

	/**
	 * Get status configuration based on current UI state
	 * @param {string} status - Current status from store
	 * @returns {Object} Configuration for displaying the status
	 */
	function getStatusConfig(status) {
		const configs = {
			ready: {
				icon: '🐍',
				bgColor: 'blue-100',
				borderColor: 'blue-300',
				titleColor: 'blue-900',
				title: 'Python is ready!',
				showButton: false
			},
			error: {
				icon: '❌',
				bgColor: 'red-100',
				borderColor: 'red-300',
				titleColor: 'red-600',
				title: 'Error!',
				showButton: false
			},
			reinforced: {
				icon: '✅',
				bgColor: 'green-100',
				borderColor: 'green-400',
				titleColor: 'green-900',
				title: 'Great! Model Learned!',
				showButton: true,
				buttonText: 'Draw Another Digit'
			},
			retrained: {
				icon: '✅',
				bgColor: 'green-100',
				borderColor: 'green-400',
				titleColor: 'green-900',
				title: 'Model Retrained!',
				showButton: true,
				buttonText: 'Draw Another Digit'
			},
			reset: {
				icon: '🔄',
				bgColor: 'blue-100',
				borderColor: 'blue-400',
				titleColor: 'blue-900',
				title: 'Training Reset!',
				showButton: true,
				buttonText: 'Draw a Digit'
			}
		};
		return configs[status] || configs.ready;
	}

	$: config = getStatusConfig($uiState.status);
</script>

<div class="rounded-lg bg-{config.bgColor} p-4 text-center border-2 border-{config.borderColor}">
	<p class="text-3xl mb-2">{config.icon}</p>
	<p class="font-bold mb-1 text-{config.titleColor}">{config.title}</p>
	<p class="text-sm text-gray-700">{$uiState.message}</p>

	{#if $uiState.status === 'ready' && $modelState.accuracy !== undefined}
		<p class="text-xs text-gray-500 mt-2">
			Model trained with {$modelState.accuracy.toFixed(1)}% accuracy
		</p>
		<p class="text-xs text-gray-500">Training examples: {$modelState.trainingExamples}</p>
	{:else if ($uiState.status === 'reinforced' || $uiState.status === 'retrained' || $uiState.status === 'reset') && $modelState.accuracy !== undefined}
		<p class="text-xs text-gray-600 mt-2">
			Training examples: {$modelState.trainingExamples} | Accuracy: {$modelState.accuracy.toFixed(1)}%
		</p>
	{/if}

	{#if config.showButton}
		<button
			onclick={clearAndReset}
			class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500"
		>
			{config.buttonText}
		</button>
	{/if}
</div>
