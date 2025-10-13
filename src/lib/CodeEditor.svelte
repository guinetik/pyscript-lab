<script>
	import { onMount, onDestroy } from 'svelte';

	let {
		value = $bindable(''),
		placeholder = 'Enter your code here...',
		readonly = false,
		height = '400px'
	} = $props();

	let editorElement;
	let editor;

	onMount(async () => {
		// Load ACE using script tags
		await loadScript('https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/ace.js');
		await loadScript('https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/ext-language_tools.js');

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

		// Initialize editor
		editor = ace.edit(editorElement, {
			mode: 'ace/mode/python',
			theme: 'ace/theme/tomorrow_night_blue',
			fontSize: 14,
			showPrintMargin: false,
			highlightActiveLine: true,
			readOnly: readonly,
			tabSize: 4,
			useSoftTabs: true,
			wrap: true,
			enableBasicAutocompletion: true,
			enableLiveAutocompletion: true,
			enableSnippets: true
		});

		// Set initial value
		editor.setValue(value, -1);

		// Update binding when editor changes
		editor.session.on('change', () => {
			value = editor.getValue();
		});

		// Watch for external value changes
		$effect(() => {
			if (editor && editor.getValue() !== value) {
				const cursorPosition = editor.getCursorPosition();
				editor.setValue(value, -1);
				editor.moveCursorToPosition(cursorPosition);
			}
		});
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

<div
	bind:this={editorElement}
	class="ace-editor-container rounded border-2 border-gray-300 focus-within:border-blue-500"
	style="height: {height}; width: 100%;"
></div>

<style>
	.ace-editor-container {
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
	}

	:global(.ace_editor) {
		font-size: 14px !important;
	}

	:global(.ace_autocomplete) {
		width: 350px !important;
		font-size: 13px !important;
	}
</style>
