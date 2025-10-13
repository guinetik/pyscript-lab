<script>
/**
 * Displays syntax-highlighted code using ACE editor in read-only mode.
 * @typedef {Object} CodeBlockProps
 * @property {string} [language='python'] - Language mode for syntax highlighting.
 * @property {string} [code=''] - Literal code to highlight when no slot content is provided.
 * @property {string} [src=''] - Path to a file to fetch and display.
 */
import { onMount, onDestroy } from 'svelte';
import { getLink } from '$lib/utils.js';

let { language = 'python', code = '', src = '' } = $props();
let editorElement;
let editor;
let slotContent = '';

onMount(async () => {
	try {
		// Load ACE using script tags (shared across all instances)
		await loadAce();

		// Wait for ace to be available
		const ace = window.ace;

		if (!ace) {
			console.error('ACE editor failed to load');
			return;
		}

		// Configure ACE CDN path (idempotent, safe to call multiple times)
		ace.config.set(
			'basePath',
			'https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/'
		);

		// Determine content source priority: src > code > slot
		let content = '';
		
		if (src) {
			// Fetch from file
			try {
				const response = await fetch(getLink(src));
				if (response.ok) {
					content = await response.text();
				} else {
					console.error(`Failed to fetch ${src}: ${response.status}`);
					content = `// Error: Failed to load ${src}`;
				}
			} catch (error) {
				console.error(`Error fetching ${src}:`, error);
				content = `// Error: ${error.message}`;
			}
		} else if (code) {
			// Use provided code
			content = code;
		} else {
			// Check for slot content
			const slot = document.querySelector('script[type="py"]');
			if (slot) {
				content = slot.textContent.trim();
			}
		}

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
	} catch (error) {
		console.error('Error initializing CodeBlock:', error);
	}
});

onDestroy(() => {
	if (editor) {
		editor.destroy();
	}
});

/**
 * Load ACE editor script with global singleton pattern.
 * Multiple components can call this safely - only loads once.
 * Stores loading promise on window to ensure singleton across all instances.
 * @returns {Promise<void>}
 */
function loadAce() {
	// If ACE is already loaded, return immediately
	if (window.ace) {
		return Promise.resolve();
	}

	// If already loading, return the existing promise
	if (window.__aceLoadingPromise) {
		return window.__aceLoadingPromise;
	}

	// Start loading ACE
	window.__aceLoadingPromise = new Promise((resolve, reject) => {
		// Check if script tag already exists
		const existingScript = document.querySelector('script[src*="ace-builds"]');
		if (existingScript) {
			// Script exists, wait for window.ace
			const checkAce = () => {
				if (window.ace) {
					resolve();
				} else {
					setTimeout(checkAce, 100);
				}
			};
			checkAce();
			return;
		}

		// Create and load script
		const script = document.createElement('script');
		script.src = 'https://cdn.jsdelivr.net/npm/ace-builds@1.32.2/src-min-noconflict/ace.js';
		script.onload = () => {
			// Wait a bit for ACE to initialize
			setTimeout(() => {
				if (window.ace) {
					resolve();
				} else {
					reject(new Error('ACE loaded but window.ace not available'));
				}
			}, 100);
		};
		script.onerror = () => reject(new Error('Failed to load ACE editor'));
		document.head.appendChild(script);
	});

	return window.__aceLoadingPromise;
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
