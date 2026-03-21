<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { EncodingController } from '$lib/controller/EncodingController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';

	// Translation store
	const exampleText = exampleTranslationStore('encoder');

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
			outputText = $exampleText.errorNotReady || 'Error: Python module not ready yet';
			return;
		}

		if (!inputText.trim()) {
			outputText = $exampleText.errorEmpty || 'Please enter some text to encode';
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
			outputText = $exampleText.copiedFeedback || '✓ Copied to clipboard!';
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
				{$exampleText.inputLabel || 'Input Text'}
			</label>
			<textarea
				id="input-text"
				bind:value={inputText}
				placeholder={$exampleText.inputPlaceholder || 'Enter text to encode...'}
				class="w-full rounded-lg border-2 border-blue-900 bg-white p-3 font-mono text-sm focus:border-blue-700 focus:outline-none"
				rows="6"
			></textarea>
		</div>

		<!-- Format selector -->
		<div class="mb-4">
			<label for="format-select" class="mb-2 block font-medium text-gray-700">
				{$exampleText.formatLabel || 'Encoding Format'}
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
				{$exampleText.encodeButton || 'Encode'}
			</button>
			<button
				onclick={handleClear}
				class="rounded-lg bg-gray-400 px-4 py-2 font-medium text-white hover:bg-gray-500"
			>
				{$exampleText.clearButton || 'Clear'}
			</button>
			<button
				onclick={handleCopy}
				disabled={!outputText}
				class="rounded-lg bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
			>
				{$exampleText.copyButton || 'Copy'}
			</button>
		</div>

		<!-- Output section -->
		<div>
			<label for="output-text" class="mb-2 block font-medium text-gray-700">
				{$exampleText.outputLabel || 'Output'}
			</label>
			<textarea
				id="output-text"
				bind:value={outputText}
				readonly
				placeholder={$exampleText.outputPlaceholder || 'Encoded result will appear here...'}
				class="w-full rounded-lg border-2 border-gray-300 bg-gray-50 p-3 font-mono text-sm focus:outline-none"
				rows="6"
			></textarea>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Advanced Interop - Text Encoder'}</h2>

		<p class="mb-4">
			{$exampleText.description || 'This example demonstrates advanced PyScript interoperability...'}
		</p>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.encodings?.title || 'Available Encodings'}</h3>
			<ul class="list-disc space-y-1 pl-5 text-sm">
				<li><strong>MD5 Hash</strong> - {$exampleText.encodings?.md5?.split(' - ')[1] || '128-bit cryptographic hash'}</li>
				<li><strong>SHA-1 Hash</strong> - {$exampleText.encodings?.sha1?.split(' - ')[1] || '160-bit cryptographic hash'}</li>
				<li><strong>SHA-256 Hash</strong> - {$exampleText.encodings?.sha256?.split(' - ')[1] || '256-bit secure cryptographic hash'}</li>
				<li><strong>Base64</strong> - {$exampleText.encodings?.base64?.split(' - ')[1] || 'Binary-to-text encoding'}</li>
				<li><strong>ROT13 Cipher</strong> - {$exampleText.encodings?.rot13?.split(' - ')[1] || 'Simple letter substitution cipher'}</li>
			</ul>
		</Callout>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.whyPython?.title || 'Why Python?'}</h3>
			<p class="text-sm mb-2">
				{$exampleText.whyPython?.description || 'These operations are trivial in Python thanks to built-in libraries:'}
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm">
				<li><code>{$exampleText.whyPython?.hashlib?.split(' - ')[0] || 'hashlib'}</code> - {$exampleText.whyPython?.hashlib?.split(' - ')[1] || 'Cryptographic hashing'}</li>
				<li><code>{$exampleText.whyPython?.base64?.split(' - ')[0] || 'base64'}</code> - {$exampleText.whyPython?.base64?.split(' - ')[1] || 'Base64 encoding/decoding'}</li>
				<li><code>{$exampleText.whyPython?.codecs?.split(' - ')[0] || 'codecs'}</code> - {$exampleText.whyPython?.codecs?.split(' - ')[1] || 'Text encoding transformations'}</li>
			</ul>
			<p class="text-sm mt-2">
				{$exampleText.whyPython?.footer || 'In JavaScript, you would need...'}
			</p>
		</Callout>

		<Callout type="tip">
			<h3 class="mb-2 font-heading font-bold">{$exampleText.pyscriptManager?.title || 'What\'s New: PyScriptManager'}</h3>
			<p class="text-sm mb-2">
				{$exampleText.pyscriptManager?.description || 'This example uses the new PyScriptManager system:'}
			</p>
			<ul class="list-disc space-y-1 pl-5 text-sm">
				<li><strong>Event-driven</strong> - {$exampleText.pyscriptManager?.eventDriven?.split(' - ')[1] || 'No polling'}</li>
				<li><strong>Instant readiness</strong> - {$exampleText.pyscriptManager?.instant?.split(' - ')[1] || 'Python signals when ready'}</li>
				<li><strong>Error handling</strong> - {$exampleText.pyscriptManager?.errorHandling?.split(' - ')[1] || 'Captures errors'}</li>
				<li><strong>Multiple exports</strong> - {$exampleText.pyscriptManager?.multiple?.split(' - ')[1] || '6 functions loaded'}</li>
			</ul>
			<p class="text-sm mt-2">
				{$exampleText.pyscriptManager?.footer || 'Check the browser console...'}
			</p>
		</Callout>

		<Callout>
			<h3 class="mb-2 font-heading font-bold">{$exampleText.architecture?.title || 'Architecture'}</h3>
			<p class="text-sm mb-2">{$exampleText.architecture?.description || 'Clean separation of concerns:'}</p>
			<ul class="list-disc space-y-1 pl-5 text-sm">
				<li>
					<strong>Python</strong> - {$exampleText.architecture?.python?.split(' - ')[1] || 'Uses PyScriptManager'}
				</li>
				<li>
					<strong>Controller</strong> - {$exampleText.architecture?.controller?.split(' - ')[1] || 'Manages lifecycle'}
				</li>
				<li>
					<strong>Svelte</strong> - {$exampleText.architecture?.svelte?.split(' - ')[1] || 'Pure UI rendering'}
				</li>
			</ul>
		</Callout>

		<p class="mt-4">
			<a
				class="text-accent hover:underline"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/basic/encoder.py"
				target="_blank">{$exampleText.viewPythonSource || 'View Python source'}</a
			>
			·
			<a
				class="text-accent hover:underline"
				href="https://github.com/guinetik/pyscript-lab/blob/master/src/lib/PyScriptManager.js"
				target="_blank">{$exampleText.viewPyscriptManager || 'View PyScriptManager'}</a
			>
		</p>
	</article>
</ExperimentCard>
