<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { InteropController } from '$lib/controller/InteropController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	// Translation store
	const exampleText = exampleTranslationStore('interop');

	// Controller instance
	let controller = browser ? new InteropController() : null;

	// Form inputs using Svelte 5 $state rune
	let inputName = $state('');
	let inputAge = $state('');

	// Reactive state for UI
	let readyState = $state(null);
	let greetingData = $state(null);
	let errorMessage = $state(null);

	// Sentiment display configuration for visual feedback
	const categoryConfig = {
		student: { color: 'bg-purple-50 border-purple-200', emoji: '🎓', textColor: 'text-purple-900' },
		junior: { color: 'bg-blue-50 border-blue-200', emoji: '🚀', textColor: 'text-blue-900' },
		mid: { color: 'bg-green-50 border-green-200', emoji: '⚡', textColor: 'text-green-900' },
		senior: { color: 'bg-orange-50 border-orange-200', emoji: '👨‍💻', textColor: 'text-orange-900' },
		veteran: { color: 'bg-red-50 border-red-200', emoji: '🦕', textColor: 'text-red-900' },
		legend: { color: 'bg-yellow-50 border-yellow-200', emoji: '👴', textColor: 'text-yellow-900' }
	};

	onMount(async () => {
		if (!browser || !controller) return;

		// Expose UIHandler for Python to call
		window.interopUIHandler = {
			// Called when Python is ready
			onReady: (data) => {
				readyState = data;
				greetingData = null;
				errorMessage = null;
			},

			// Called when greeting is generated
			onGreeting: (data) => {
				greetingData = data;
				errorMessage = null;
			},

			// Called on validation errors
			onError: (data) => {
				errorMessage = data.message;
				greetingData = null;
			}
		};

		// Initialize controller
		await controller.initialize();
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		controller.destroy();
	});

	// Call Python via controller
	const callPython = () => {
		if (!browser || !controller) return;

		// Clear previous state
		errorMessage = null;
		greetingData = null;

		// Call controller method
		controller.greetUser(inputName, inputAge);
	};
</script>

<ExperimentCard
	props={{ previousPage: '/examples/basics/repl', nextPage: '/examples/matplotlib/intro' }}
>
	<div slot="py_slot" class="flex h-full w-full flex-col items-center justify-start p-6 overflow-auto">
		<!-- Ready State -->
		{#if readyState && !greetingData && !errorMessage}
			<div class="w-full rounded-lg bg-blue-100 p-6 text-center border-2 border-blue-300">
				<p class="text-4xl mb-3">🐍</p>
				<p class="text-2xl font-bold mb-2 text-blue-900">{readyState.message}</p>
				<p class="text-sm text-blue-700">{readyState.subtitle}</p>
			</div>
		{/if}

		<!-- Error State -->
		{#if errorMessage}
			<div class="w-full rounded-lg bg-red-100 p-6 text-center border-2 border-red-300">
				<p class="text-4xl mb-3">❌</p>
				<p class="text-xl font-bold text-red-900">{errorMessage}</p>
			</div>
		{/if}

		<!-- Greeting Result -->
		{#if greetingData}
			{@const config = categoryConfig[greetingData.category]}
			<div class="w-full rounded-lg {config.color} p-6 border-2">
				<div class="text-center mb-4">
					<div class="text-6xl mb-3">{config.emoji}</div>
					<p class="text-3xl font-bold {config.textColor} mb-2">
						{greetingData.greeting}, <span class="text-blue-600">{greetingData.name}</span>! 👋
					</p>
					<p class="text-gray-600 mb-4">
						{$exampleText.ageDescription?.replace('{age}', greetingData.age)?.replace('{category}', greetingData.category) || `Age: ${greetingData.age} | Category: ${greetingData.category}`}
					</p>
				</div>

				<div class="mt-4 space-y-3">
					{#each greetingData.responses as response}
						<p class="text-lg {config.textColor}">{response}</p>
					{/each}

					{#if greetingData.years_coding > 0}
						<p class="text-sm text-gray-500 mt-4">
							{$exampleText.potentialCoding?.replace('{years}', greetingData.years_coding) || `🎂 Potential coding years: ~${greetingData.years_coding}`}
						</p>
					{/if}

					<p class="text-xs text-gray-400 mt-4 italic border-t pt-3">
						💬 {greetingData.disclaimer}
					</p>
				</div>
			</div>
		{/if}

		<!-- Loading/Empty State -->
		{#if !readyState && !greetingData && !errorMessage}
			<div class="w-full rounded-lg bg-gray-100 p-6 text-center border-2 border-gray-300">
				<p class="text-3xl mb-2 animate-pulse">⏳</p>
				<p class="font-bold mb-1">{$exampleText.loadingTitle || 'Loading Python...'}</p>
				<p class="text-sm text-gray-600">{$exampleText.loadingSubtitle || 'Initializing interoperability demo'}</p>
			</div>
		{/if}
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Interoperability (JS to Python)'}</h2>

		<p class="mb-4">
			{$exampleText.description || "PyScript's interoperability allows seamless communication between Python and JavaScript..."}
		</p>

		<p class="mb-4 text-sm text-gray-600">
			<strong>{$exampleText.tryIt?.split(':')[0]}:</strong> {$exampleText.tryIt?.split(':')[1] || 'Enter your name and age below...'}
		</p>

		<div class="mb-8 flex items-center justify-center bg-white">
			<div class="relative rounded border-2 border-grey px-1 py-2">
				<label
					class="bg-white px-2 text-grey-darker"
					style="position: absolute; top: -10px; left: 8px;"
					for="txt_name">{$exampleText.nameLabel || 'Name'}</label
				>
				<input
					bind:value={inputName}
					id="txt_name"
					type="text"
					class="w-full rounded border-2 border-white py-2 leading-tight text-grey-darker focus:border-white focus:bg-white focus:outline-none"
					placeholder={$exampleText.namePlaceholder || 'Who are you?'}
				/>
			</div>
			<div class="relative ml-16 rounded border-2 border-red px-1 py-2">
				<label
					class="bg-white px-2 text-red"
					style="position: absolute; top: -10px; left: 8px;"
					for="txt_age">{$exampleText.ageLabel || 'Age'}</label
				>
				<input
					bind:value={inputAge}
					id="txt_age"
					type="number"
					class="w-full rounded border-2 border-white py-2 leading-tight text-grey-darker focus:border-white focus:bg-white focus:outline-none"
					placeholder={$exampleText.agePlaceholder || 'How old are you?'}
				/>
			</div>
		</div>
		<button class="mt-2 w-full flex-grow bg-green-400 px-3 py-2" type="button" onclick={callPython}
			>{$exampleText.runButton || 'Run'}</button
		>

		<div class="mt-6 rounded-lg bg-orange-50 p-4">
			<h3 class="mb-2 font-bold text-orange-900">{$exampleText.architecture?.title || '🏗️ Architecture Highlights'}</h3>
			<p class="text-sm text-orange-800 mb-2">
				{$exampleText.architecture?.description || 'This example demonstrates proper separation of concerns:'}
			</p>
			<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-orange-800">
				<li>
					<strong>Python</strong> - {$exampleText.architecture?.python?.split(' - ')[1] || 'Pure business logic, sends only data via window callbacks (no innerHTML!)'}
				</li>
				<li>
					<strong>InteropController</strong> - {$exampleText.architecture?.controller?.split(' - ')[1] || 'Manages Python lifecycle and communication layer'}
				</li>
				<li>
					<strong>Svelte UIHandler</strong> - {$exampleText.architecture?.ui?.split(' - ')[1] || 'Pure UI rendering with reactive state based on data received'}
				</li>
			</ul>
		</div>

		<p class="mt-4">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/interop.py"
				target="_blank">{$exampleText.viewSource || 'View Python source'}</a
			>
		</p>

		<div class="prose max-w-none mt-8">
			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.howWorks?.title || 'How It Works:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>
						<strong>Controller Pattern:</strong> {$exampleText.howWorks?.pattern?.split(': ')[1] || 'InteropController manages Python setup and callbacks'}
					</li>
					<li>
						<strong>Data-Only Communication:</strong> {$exampleText.howWorks?.dataOnly?.split(': ')[1] || 'Python sends plain objects, Svelte renders the UI'}
					</li>
					<li>
						<strong>Reactive UI:</strong> {$exampleText.howWorks?.reactive?.split(': ')[1] || 'Svelte automatically updates when data changes'}
					</li>
					<li><strong>Event-Driven:</strong> {$exampleText.howWorks?.eventDriven?.split(': ')[1] || 'User interactions trigger Python functions'}</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold">{$exampleText.useCases?.title || 'Use Cases:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>{$exampleText.useCases?.formData || 'Process form data with Python\'s powerful libraries'}</li>
					<li>{$exampleText.useCases?.dynamicUI || 'Update UI dynamically based on Python computations'}</li>
					<li>{$exampleText.useCases?.combine || 'Combine JavaScript frameworks (like Svelte) with Python logic'}</li>
					<li>{$exampleText.useCases?.dataSci || 'Access Python\'s data science ecosystem from web interfaces'}</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
