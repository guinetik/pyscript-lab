<script>
	import ExperimentCard from '../../../lib/experiment_card.svelte';
	export let name = 'REPL';
</script>

<ExperimentCard props={{ previousPage: '/examples/hello', nextPage: '/examples/interop' }}>
	<section slot="py_slot" class="pyscript p-5">
		<h1>Example 1: Pyodide REPL</h1>
		<script type="py-editor" id="py-editor">
import sys
print(sys.version)
a = 42
print(a)
		</script>
		<hr class="my-4" />
		<h1>Example 2: MicroPython REPL</h1>
		<script type="mpy-editor" id="mpy-editor" language="python">
import sys
print(sys.version)
a = 42
print(a)
		</script>
	</section>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>
		<p>
			PyScript comes with a default REPL (read-evaluate-print-loop) html module that allows
			<br />
			This is a pseudo notebook functionality that can make some interactive python code on the fly.
		</p>
	</article>
</ExperimentCard>
