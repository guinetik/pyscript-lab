<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Interoperability (JS to Python)';

	// Form inputs using Svelte 5 $state rune
	let inputName = $state('');
	let inputAge = $state('');

	// Python script URL
	const pyScriptUrl = getLink('python/interop.py');

	/*
	 * BELOW WE CREATE 2 INSTANCES OF THE PYTHON RUNNER.
	 * ONE TO LOAD THE PYTHON SCRIPT WE WANT TO USE
	 * THE OTHER IS TO EXECUTING PYTHON CODE ON DEMAND.
	 * INITIALLY, I USED ONLY ONE RUNPYTHON OBJECT FOR BOTH LOADING SCRIPTS AND EXECUTING CODE,
	 * BUT MY TESTING SHOWED THAT SCOPING THESE SEPARATELY IS MORE STABLE AND EASIER TO CLEAN UP
	 * SPECIALLY WHEN DEALING WITH COMPONENT-BASED UIS
	 */

	// Define a RunPython instance to attach our script to
	let pyScriptRunner = RunPython();

	// When the screen loads, we want to load our script
	onMount(() => {
		pyScriptRunner.runScript(pyScriptUrl, 'script_gutter', false);
	});

	// when the screen is destroyed we want to destroy all python tags
	onDestroy(() => {
		if (pyScriptRunner) pyScriptRunner.destroy();
	});

	// when the user clicks the button, execute py code via our pyCodeRunner
	const callPython = () => {
		try {
			// Define a RunPython instance to attach the code we want to execute to
			let pyCodeRunner = RunPython();
			const pyCode = `run('${inputName}', ${inputAge})`;
			pyCodeRunner.runCode(pyCode, 'chart', false);
			pyCodeRunner.destroy(false);
		} catch (e) {
			alert('Python died. Try refreshing I guess :(');
		}
	};
</script>

<ExperimentCard props={{ previousPage: '/examples/basics/repl', nextPage: '/examples/bokeh' }}>
	<div slot="py_slot" id="chart" class="h-full w-full p-5" />
	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<p class="mb-4">
			PyScript's interoperability allows seamless communication between Python and JavaScript,
			enabling you to leverage both languages' strengths in a single application. Call Python
			functions from JavaScript, access browser APIs from Python, and share data bidirectionally.
		</p>

		<p class="mb-4 text-sm text-gray-600">
			<strong>Try it:</strong> Enter your name and age below. The form data will be sent to a Python function
			that processes it and generates a personalized chart.
		</p>

		<div class="mb-8 flex items-center justify-center bg-white">
			<div class="relative rounded border-2 border-grey px-1 py-2">
				<label
					class="bg-white px-2 text-grey-darker"
					style="position: absolute; top: -10px; left: 8px;"
					for="txt_name">Name</label
				>
				<input
					bind:value={inputName}
					id="txt_name"
					type="text"
					class="w-full rounded border-2 border-white py-2 leading-tight text-grey-darker focus:border-white focus:bg-white focus:outline-none"
					placeholder="Who are you?"
				/>
			</div>
			<div class="relative ml-16 rounded border-2 border-red px-1 py-2">
				<label
					class="bg-white px-2 text-red"
					style="position: absolute; top: -10px; left: 8px;"
					for="txt_age">Age</label
				>
				<input
					bind:value={inputAge}
					id="txt_age"
					type="number"
					class="w-full rounded border-2 border-white py-2 leading-tight text-grey-darker focus:border-white focus:bg-white focus:outline-none"
					placeholder="How old are you?"
				/>
			</div>
		</div>
		<button class="mt-2 w-full flex-grow bg-green-400 px-3 py-2" type="button" onclick={callPython}
			>Run</button
		>
		<p class="mt-4">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/interop.py"
				target="_blank">View source</a
			>
		</p>

		<div class="prose max-w-none mt-8">
			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">How It Works:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>Expose Python Functions:</strong> Make Python functions available to JavaScript via the <code class="rounded bg-white px-1">window</code> object</li>
					<li><strong>Access JavaScript from Python:</strong> Use the <code class="rounded bg-white px-1">js</code> module to interact with DOM and browser APIs</li>
					<li><strong>Data Conversion:</strong> Automatic conversion between Python and JavaScript data types</li>
					<li><strong>Event-Driven:</strong> Trigger Python functions from user interactions</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold">Use Cases:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>Process form data with Python's powerful libraries</li>
					<li>Update UI dynamically based on Python computations</li>
					<li>Combine JavaScript frameworks (like Svelte) with Python logic</li>
					<li>Access Python's data science ecosystem from web interfaces</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
