<script>
	import { getLink } from '$lib/utils';
	import SiteMapStore from '$lib/stores/SiteMapStore';
	import SiteMapLink from '$lib/components/SiteMapLink.svelte';
	import { page } from '$app/stores';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import PyExample from '$lib/components/PyExample.svelte';
	export let name = 'HELLO WORLD';
</script>

<ExperimentCard props={{ previousPage: '/', nextPage: '/examples/basics/repl' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
            <h1>Example 1</h1>
            <PyExample title="Print hello world:">
				<script type="py" id="hello-world-script">
                    print("hello world")
				</script>
			</PyExample>
            <button class="open-console-btn" onclick={() => window.openConsole()}>🖥️ Open Console to see script output</button>
            <hr class="my-4" />
            <h1>Example 2</h1>
			<PyExample title="Current date and time, as computed by Python:">
				<script type="py" src="/python/basic/date.py" id="date-script">
				</script>
			</PyExample>
            <hr class="my-4" />
            <h1>Example 3</h1>
            <PyExample title="Fibonacci sequence, computed by Python:">
                <script type="py" src="/python/basic/fibo.py" id="fibonacci-script">
                </script>
            </PyExample>
            <hr class="my-4" />
            <h1>Example 4</h1>
			<div id="matrix-container"></div>
            <PyExample title="Snake traversal, computed by Python:">
                <script type="py" src="/python/basic/snek.py" id="snek-script">
                </script>
            </PyExample>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				PyScript allows you to run Python code directly in your web browser without any server-side
				processing. These examples demonstrate Python's capabilities, from basic "Hello World" output
				to date handling, Fibonacci sequences, and matrix traversals—all running entirely in your browser.
			</p>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">Key Features:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>Zero Server Setup:</strong> Python runs entirely in the browser using WebAssembly</li>
					<li><strong>Standard Library Access:</strong> Use familiar Python modules like <code class="rounded bg-white px-1">datetime</code>, <code class="rounded bg-white px-1">sys</code>, and more</li>
					<li><strong>Simple Integration:</strong> Add Python with just a <code class="rounded bg-white px-1">&lt;script type="py"&gt;</code> tag</li>
					<li><strong>External Scripts:</strong> Load Python code from files using the <code class="rounded bg-white px-1">src</code> attribute</li>
					<li><strong>Console Output:</strong> View results in the browser console or write to the DOM</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold">The Examples:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>Example 1:</strong> Classic "Hello World" - The simplest PyScript program</li>
					<li><strong>Example 2:</strong> Current date/time - Demonstrates external Python scripts and datetime module</li>
					<li><strong>Example 3:</strong> Fibonacci sequence - Shows algorithmic computation and list comprehension</li>
					<li><strong>Example 4:</strong> Snake traversal - Matrix manipulation and DOM manipulation from Python</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold">Getting Started:</h3>
				<p class="mb-2">The basic pattern for running Python in the browser is simple:</p>
				<pre class="rounded bg-white p-3 text-sm overflow-x-auto"><code>&lt;script type="py"&gt;
  print("Hello from Python!")
&lt;/script&gt;

&lt;!-- Or load from a file --&gt;
&lt;script type="py" src="/path/to/script.py"&gt;&lt;/script&gt;</code></pre>
				<p class="mt-3 text-sm">
					Click the "🖥️ Open Console" button above to see the output of these Python scripts!
				</p>
			</div>
		</div>
	</article>
</ExperimentCard> 