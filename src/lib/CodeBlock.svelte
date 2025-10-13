<script>
/**
 * Displays syntax-highlighted code using ACE editor in read-only mode.
 * @typedef {Object} CodeBlockProps
 * @property {string} [language='python'] - Language mode for syntax highlighting.
 * @property {string} [code=''] - Literal code to highlight when no slot content is provided.
 */
import { onMount, onDestroy } from 'svelte';

let { language = 'python', code = '' } = $props();
let editorElement;
let editor;
let slotContent = '';

onMount(async () => {
	// Load ACE using script tags
	await loadScript('https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/ace.js');

	// Wait for ace to be available
	const ace = window.ace;

	if (!ace) {
		console.error('ACE editor failed to load');
		return;
	}

	// Configure ACE CDN path
	ace.config.set(
		'basePath',
		'https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/'
	);

	// Check for slot content
	if (!code) {
		const slot = document.querySelector('script[type="py"]');
		if (slot) {
			slotContent = slot.textContent.trim();
		}
	}

	const content = code || slotContent;

	// Initialize editor in read-only mode
	editor = ace.edit(editorElement, {
		mode: `ace/mode/${language}`,
		theme: 'ace/theme/tomorrow_night_blue',
		fontSize: 14,
		showPrintMargin: false,
		highlightActiveLine: false,
		highlightGutterLine: false,
		readOnly: true,
		showGutter: true,
		maxLines: Infinity,
		minLines: 1,
		wrap: false,
		tabSize: 4
	});

	// Set value
	editor.setValue(content, -1);

	// Hide cursor
	editor.renderer.$cursorLayer.element.style.display = 'none';
});

onDestroy(() => {
	if (editor) {
		editor.destroy();
	}
});

// Helper function to load scripts dynamically
function loadScript(src) {
	return new Promise((resolve, reject) => {
		// Check if already loaded
		if (document.querySelector(`script[src="${src}"]`)) {
			resolve();
			return;
		}

		const script = document.createElement('script');
		script.src = src;
		script.onload = resolve;
		script.onerror = reject;
		document.head.appendChild(script);
	});
}
</script>

<div class="mb-4 overflow-x-auto rounded">
	<div bind:this={editorElement} class="code-block-editor"></div>
</div>

<div style="display: none">
	<slot />
</div>

<style>
	.code-block-editor {
		width: 100%;
		min-height: 50px;
	}

	:global(.code-block-editor .ace_editor) {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
	}
</style>
