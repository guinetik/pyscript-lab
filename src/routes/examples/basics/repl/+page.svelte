<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';

	const exampleText = exampleTranslationStore('repl');
</script>

<ExperimentCard props={{ previousPage: '/examples/basics/hello', nextPage: '/examples/basics/interop' }}>
	<section slot="py_slot" class="pyscript p-5">
		<h1>{$exampleText.examples?.example1 || 'Example 1: Pyodide REPL'}</h1>
		<script type="py-editor" id="py-editor">
import sys
print(sys.version)
a = 42
print(a)
		</script>
		<hr class="my-4" />
		<h1>{$exampleText.examples?.example2 || 'Example 2: MicroPython REPL'}</h1>
		<script type="mpy-editor" id="mpy-editor" language="python">
import sys
print(sys.version)
a = 42
print(a)
		</script>
	</section>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'R.E.P.L'}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				{$exampleText.description || "PyScript's REPL provides an interactive Python environment directly in your browser."}
			</p>

			<ContentSection title={$exampleText.capabilities?.title || 'What You Can Do:'}>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>{$exampleText.capabilities?.interactive || 'Interactive Coding:'}</strong> {$exampleText.capabilities?.interactiveDesc || 'Write and execute Python code on the fly'}</li>
					<li><strong>{$exampleText.capabilities?.multiple || 'Multiple Interpreters:'}</strong> {$exampleText.capabilities?.multipleDesc || 'Choose between Pyodide or MicroPython'}</li>
					<li><strong>{$exampleText.capabilities?.editable || 'Editable Code:'}</strong> {$exampleText.capabilities?.editableDesc || 'Modify examples and see results instantly'}</li>
					<li><strong>{$exampleText.capabilities?.stdlib || 'Standard Library Access:'}</strong> {$exampleText.capabilities?.stdlibDesc || 'Use Python built-in modules'}</li>
				</ul>
			</ContentSection>

			<Callout>
				<h3 class="mb-2 font-heading font-bold">{$exampleText.implementation?.title || 'Implementation:'}</h3>
				<p class="mb-2">{$exampleText.implementation?.description || 'REPL editors are created using special script types:'}</p>
				<pre class="rounded bg-surface-alt p-3 font-mono text-sm overflow-x-auto"><code>&lt;script type="py-editor"&gt;
  # Your Python code here
  print("Hello from Pyodide!")
&lt;/script&gt;

&lt;script type="mpy-editor"&gt;
  # MicroPython version
  print("Hello from MicroPython!")
&lt;/script&gt;</code></pre>
			</Callout>

			<Callout type="tip">
				<h3 class="mb-2 font-heading font-bold">{$exampleText.useCases?.title || 'Use Cases:'}</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>{$exampleText.useCases?.educational || 'Educational tutorials and code demonstrations'}</li>
					<li>{$exampleText.useCases?.documentation || 'Interactive documentation'}</li>
					<li>{$exampleText.useCases?.prototyping || 'Prototyping Python algorithms'}</li>
					<li>{$exampleText.useCases?.liveCoding || 'Live coding environments'}</li>
				</ul>
			</Callout>
		</div>
	</article>
</ExperimentCard>
