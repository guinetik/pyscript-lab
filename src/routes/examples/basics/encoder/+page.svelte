<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { EncodingController } from '$lib/controller/EncodingController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	// Page metadata
	let name = 'Advanced Interop - Text Encoder';

	// Controller instance
	let controller = browser ? new EncodingController() : null;

	// UI state
	let inputText = $state('');
	let outputText = $state('');
	let selectedFormat = $state('md5');
	let isReady = $state(false);
	let errorMessage = $state('');
	let statusMessage = $state('Initializing Python module...');

	// Available formats
	let formats = $state([]);

	onMount(async () => {
		if (!browser || !controller) return;

		// Setup callbacks
		controller.onReady(() => {
			isReady = true;
			statusMessage = '✅ Python module ready!';
			formats = controller.getFormats();
		});

		controller.onError((error) => {
			errorMessage = `Error: ${error}`;
			statusMessage = '❌ Failed to load Python module';
		});

		// Initialize controller
		await controller.initialize();
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		controller.destroy();
	});

	/**
	 * Handle encode button click
	 */
	function handleEncode() {
		if (!isReady || !controller) {
			outputText = 'Error: Python module not ready yet';
			return;
		}

		if (!inputText.trim()) {
			outputText = 'Please enter some text to encode';
			return;
		}

		// Call Python encoding function
		outputText = controller.encode(inputText, selectedFormat);
	}

	/**
	 * Clear all fields
	 */
	function handleClear() {
		inputText = '';
		outputText = '';
	}

	/**
	 * Copy output to clipboard
	 */
	async function handleCopy() {
		if (!outputText) return;

		try {
			await navigator.clipboard.writeText(outputText);
			// Show brief feedback
			const originalText = outputText;
			outputText = '✓ Copied to clipboard!';
			setTimeout(() => {
				outputText = originalText;
			}, 1000);
		} catch (error) {
			console.error('Failed to copy:', error);
		}
	}
</script>

<ExperimentCard props={{ previousPage: '/examples/basics/interop', nextPage: '/examples/matplotlib/intro' }}>
	<div slot="py_slot" class="flex h-full w-full flex-col p-6">
		<!-- Status message -->
		<div class="mb-4 rounded-lg bg-blue-50 p-3 text-center text-sm">
			{statusMessage}
		</div>

		{#if errorMessage}
			<div class="mb-4 rounded-lg bg-red-50 p-3 text-center text-sm text-red-700">
				{errorMessage}
			</div>
		{/if}

		<!-- Input section -->
		<div class="mb-4">
			<label for="input-text" class="mb-2 block font-medium text-gray-700">
				Input Text
			</label>
			<textarea
				id="input-text"
				bind:value={inputText}
				placeholder="Enter text to encode..."
				class="w-full rounded-lg border-2 border-blue-900 bg-white p-3 font-mono text-sm focus:border-blue-700 focus:outline-none"
				rows="6"
			></textarea>
		</div>

		<!-- Format selector -->
		<div class="mb-4">
			<label for="format-select" class="mb-2 block font-medium text-gray-700">
				Encoding Format
			</label>
			<select
				id="format-select"
				bind:value={selectedFormat}
				disabled={!isReady}
				class="w-full rounded-lg border-2 border-blue-900 p-2 focus:border-blue-700 focus:outline-none disabled:bg-gray-100 disabled:border-gray-300"
			>
				{#each formats as format}
					<option value={format.value}>{format.label}</option>
				{/each}
			</select>
		</div>

		<!-- Buttons -->
		<div class="mb-4 flex gap-3">
			<button
				onclick={handleEncode}
				disabled={!isReady}
				class="flex-1 rounded-lg bg-green-500 px-4 py-2 font-medium text-white hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
			>
				Encode
			</button>
			<button
				onclick={handleClear}
				class="rounded-lg bg-gray-400 px-4 py-2 font-medium text-white hover:bg-gray-500"
			>
				Clear
			</button>
			<button
				onclick={handleCopy}
				disabled={!outputText}
				class="rounded-lg bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
			>
				Copy
			</button>
		</div>

		<!-- Output section -->
		<div>
			<label for="output-text" class="mb-2 block font-medium text-gray-700">
				Output
			</label>
			<textarea
				id="output-text"
				bind:value={outputText}
				readonly
				placeholder="Encoded result will appear here..."
				class="w-full rounded-lg border-2 border-gray-300 bg-gray-50 p-3 font-mono text-sm focus:outline-none"
				rows="6"
			></textarea>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<p class="mb-4">
			This example demonstrates <strong>advanced PyScript interoperability</strong> using the new
			<code>PyScriptManager</code> system. Unlike polling-based approaches, this uses
			<strong>event-driven communication</strong> for instant Python module initialization.
		</p>

		<div class="my-6 rounded-lg bg-purple-50 p-4">
			<h3 class="mb-2 font-bold text-purple-900">🔐 Available Encodings</h3>
			<ul class="list-disc space-y-1 pl-5 text-sm text-purple-800">
				<li><strong>MD5 Hash</strong> - 128-bit cryptographic hash (legacy, not secure)</li>
				<li><strong>SHA-1 Hash</strong> - 160-bit cryptographic hash</li>
				<li><strong>SHA-256 Hash</strong> - 256-bit secure cryptographic hash</li>
				<li><strong>Base64 Encode/Decode</strong> - Binary-to-text encoding</li>
				<li><strong>ROT13 Cipher</strong> - Simple letter substitution cipher</li>
			</ul>
		</div>

		<div class="my-6 rounded-lg bg-blue-50 p-4">
			<h3 class="mb-2 font-bold text-blue-900">💡 Why Python?</h3>
			<p class="text-sm text-blue-800 mb-2">
				These operations are <strong>trivial in Python</strong> thanks to built-in libraries:
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm text-blue-800">
				<li><code>hashlib</code> - Cryptographic hashing (MD5, SHA family)</li>
				<li><code>base64</code> - Base64 encoding/decoding</li>
				<li><code>codecs</code> - Text encoding transformations</li>
			</ul>
			<p class="text-sm text-blue-800 mt-2">
				In JavaScript, you'd need the Web Crypto API (async, verbose) or external libraries.
				Python's "batteries included" philosophy shines here!
			</p>
		</div>

		<div class="my-6 rounded-lg bg-green-50 p-4">
			<h3 class="mb-2 font-bold text-green-900">🚀 What's New: PyScriptManager</h3>
			<p class="text-sm text-green-800 mb-2">
				This example uses the new <code>PyScriptManager</code> system:
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
				<li><strong>Event-driven</strong> - No polling with setTimeout</li>
				<li><strong>Instant readiness</strong> - Python signals when ready</li>
				<li><strong>Error handling</strong> - Captures and reports Python errors</li>
				<li><strong>Multiple exports</strong> - 6 encoding functions loaded at once</li>
			</ul>
			<p class="text-sm text-green-800 mt-2">
				Check the browser console to see the lifecycle events in action!
			</p>
		</div>

		<div class="my-6 rounded-lg bg-orange-50 p-4">
			<h3 class="mb-2 font-bold text-orange-900">🏗️ Architecture</h3>
			<p class="text-sm text-orange-800 mb-2">Clean separation of concerns:</p>
			<ul class="list-disc space-y-1 pl-5 text-sm text-orange-800">
				<li>
					<strong>Python</strong> (<code>encoder.py</code>) - Uses <code>PyScriptManager</code> to
					export functions
				</li>
				<li>
					<strong>Controller</strong> (<code>EncodingController.js</code>) - Manages lifecycle with
					events
				</li>
				<li>
					<strong>Svelte</strong> - Pure UI rendering with reactive state
				</li>
			</ul>
		</div>

		<p class="mt-4">
			<a
				class="text-sky-500 hover:underline"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/basic/encoder.py"
				target="_blank">View Python source</a
			>
			·
			<a
				class="text-sky-500 hover:underline"
				href="https://github.com/guinetik/pyscript-lab/blob/master/src/lib/PyScriptManager.js"
				target="_blank">View PyScriptManager</a
			>
		</p>
	</article>
</ExperimentCard>
