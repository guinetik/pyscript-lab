<script>
/**
 * DiagramCard Component
 * 
 * Displays a single diagram example with its rendered output and source code.
 * 
 * @typedef {Object} DiagramCardProps
 * @property {string} id - Unique identifier for the diagram (e.g., "chart1")
 * @property {string} title - Display title for the diagram
 * @property {string} src - Path to the Python source file
 * @property {Function} onRegenerate - Callback function to regenerate the diagram
 */
import CodeBlock from './CodeBlock.svelte';

let { id, title, src, onRegenerate } = $props();

/**
 * Handle regenerate button click
 */
function handleRegenerate() {
	if (onRegenerate) {
		onRegenerate(id);
	}
}
</script>

<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
	<div class="mb-4 flex items-center justify-between">
		<h3 class="text-lg font-bold">{title}</h3>
		<button
			onclick={handleRegenerate}
			class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
		>
			🔄 Regenerate
		</button>
	</div>
	<div
		{id}
		class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
	></div>
	<div class="mt-4">
		<CodeBlock {src} />
	</div>
</div>

