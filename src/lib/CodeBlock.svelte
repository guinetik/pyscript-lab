<script>
	import { onMount } from 'svelte';
	import Prism from 'prismjs';
	import 'prismjs/components/prism-python';
	import 'prismjs/themes/prism-tomorrow.css';

	let { language = 'python', code = '' } = $props();
	let highlighted = $state('');
	let codeElement;
	let slotContent = '';

	function updateHighlight(content) {
		if (!content) return;
		try {
			highlighted = Prism.highlight(
				content,
				Prism.languages[language] || Prism.languages.plain,
				language
			);
		} catch (e) {
			// Fallback to plain text if highlighting fails
			highlighted = content;
		}
	}

	$effect(() => {
		updateHighlight(code || slotContent);
	});

	onMount(() => {
		if (!code) {
			// Only look for slot content if no code prop is provided
			const slot =
				codeElement?.parentElement?.nextElementSibling?.querySelector('script[type="py"]');
			if (slot) {
				slotContent = slot.textContent.trim();
				updateHighlight(slotContent);
			}
		}
	});
</script>

<pre class="mb-4 overflow-x-auto rounded bg-gray-800 p-3 text-gray-100">
<code bind:this={codeElement} class="language-{language}">{@html highlighted}</code>
</pre>

<div style="display: none">
	<slot />
</div>

<style>
	:global(pre[class*='language-']) {
		margin: 0;
		padding: 1rem;
	}
</style>
