<script>
	import { getLink } from '$lib/utils';
	import { base } from '$app/paths';
	import SiteMapStore from '$lib/stores/SiteMapStore';
	import SiteMapLink from '$lib/components/SiteMapLink.svelte';
	import { page } from '$app/stores';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';

	// Reactive store that updates when locale changes
	const exampleText = exampleTranslationStore('hello');
</script>

<ExperimentCard props={{ previousPage: '/', nextPage: '/examples/basics/repl' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>{$exampleText.examples?.example1 || 'Example 1'}</h1>
			<PyExample title={$exampleText.examples?.printHelloWorld || 'Print hello world:'}>
				<script type="py" id="hello-world-script">
                    print("hello world")
				</script>
			</PyExample>
			<button class="open-console-btn" onclick={() => window.openConsole()}>Open Console to see script output</button>
			<hr class="my-4" />
			<h1>{$exampleText.examples?.example2 || 'Example 2'}</h1>
			<PyExample title={$exampleText.examples?.currentDateTime || 'Current date and time, as computed by Python:'}>
				<script type="py" src="{base}/python/basic/date.py" id="date-script">
				</script>
			</PyExample>
			<hr class="my-4" />
			<h1>{$exampleText.examples?.example3 || 'Example 3'}</h1>
			<PyExample title={$exampleText.examples?.fibonacci || 'Fibonacci sequence, computed by Python:'}>
				<script type="py" src="{base}/python/basic/fibo.py" id="fibonacci-script">
				</script>
			</PyExample>
			<hr class="my-4" />
			<h1>{$exampleText.examples?.example4 || 'Example 4'}</h1>
			<div id="matrix-container"></div>
			<PyExample title={$exampleText.examples?.snakeTraversal || 'Snake traversal, computed by Python:'}>
				<script type="py" src="{base}/python/basic/snek.py" id="snek-script">
				</script>
			</PyExample>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'HELLO WORLD'}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				{$exampleText.description || 'PyScript allows you to run Python code directly in your web browser without any server-side processing.'}
			</p>

			<ContentSection title={$exampleText.keyFeatures?.title || 'Key Features:'}>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>{$exampleText.keyFeatures?.zeroSetup || 'Zero Server Setup:'}</strong> {$exampleText.keyFeatures?.zeroSetupDesc || 'Python runs entirely in the browser using WebAssembly'}</li>
					<li><strong>{$exampleText.keyFeatures?.stdLib || 'Standard Library Access:'}</strong> {$exampleText.keyFeatures?.stdLibDesc || 'Use familiar Python modules like datetime, sys, and more'}</li>
					<li><strong>{$exampleText.keyFeatures?.simpleIntegration || 'Simple Integration:'}</strong> {$exampleText.keyFeatures?.simpleIntegrationDesc || 'Add Python with just a tag'}</li>
					<li><strong>{$exampleText.keyFeatures?.externalScripts || 'External Scripts:'}</strong> {$exampleText.keyFeatures?.externalScriptsDesc || 'Load Python code from files using the src attribute'}</li>
					<li><strong>{$exampleText.keyFeatures?.consoleOutput || 'Console Output:'}</strong> {$exampleText.keyFeatures?.consoleOutputDesc || 'View results in the browser console or write to the DOM'}</li>
				</ul>
			</ContentSection>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.theExamples?.title || 'The Examples:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>{$exampleText.examples?.example1 || 'Example 1'}</strong>: {$exampleText.theExamples?.example1 || 'Classic "Hello World" - The simplest PyScript program'}</li>
					<li><strong>{$exampleText.examples?.example2 || 'Example 2'}</strong>: {$exampleText.theExamples?.example2 || 'Current date/time - Demonstrates external Python scripts and datetime module'}</li>
					<li><strong>{$exampleText.examples?.example3 || 'Example 3'}</strong>: {$exampleText.theExamples?.example3 || 'Fibonacci sequence - Shows algorithmic computation and list comprehension'}</li>
					<li><strong>{$exampleText.examples?.example4 || 'Example 4'}</strong>: {$exampleText.theExamples?.example4 || 'Snake traversal - Matrix manipulation and DOM manipulation from Python'}</li>
				</ul>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.gettingStarted?.title || 'Getting Started:'}</h3>
				<p class="mb-2">{$exampleText.gettingStarted?.description || 'The basic pattern for running Python in the browser is simple:'}</p>
				<pre class="rounded bg-surface-alt p-3 font-mono text-sm overflow-x-auto"><code>&lt;script type="py"&gt;
  print("Hello from Python!")
&lt;/script&gt;

&lt;!-- Or load from a file --&gt;
&lt;script type="py" src="/path/to/script.py"&gt;&lt;/script&gt;</code></pre>
				<p class="mt-3 text-sm">
					{$exampleText.gettingStarted?.footer || 'Click the "Open Console" button above to see the output of these Python scripts!'}
				</p>
			</Callout>
		</div>
	</article>
</ExperimentCard>
