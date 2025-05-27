<script>
	import { getLink } from '$lib/utils';
	import SiteMapStore from '$lib/SiteMapStore';
	import SiteMapLink from '$lib/SiteMapLink.svelte';
	import { page } from '$app/stores';
	import ExperimentCard from '../../../lib/experiment_card.svelte';
	import PyExample from '$lib/PyExample.svelte';
	export let name = 'HELLO WORLD';
</script>

<ExperimentCard props={{ previousPage: '/', nextPage: '/examples/repl' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
            <h1>Example 1</h1>
            <PyExample title="Print hello world:">
				<script type="py" id="hello-world-script">
                    print("hello world")
				</script>
			</PyExample>
            <button class="open-terminal-btn" onclick={() => window.openTerminal()}>🖥️ Open Terminal to see console output</button>
            <hr class="my-4" />
            <h1>Example 2</h1>
			<PyExample title="Current date and time, as computed by Python:">
				<script type="py" src="/python/date.py" id="date-script">
				</script>
			</PyExample>
            <hr class="my-4" />
            <h1>Example 3</h1>
            <PyExample title="Fibonacci sequence, computed by Python:">
                <script type="py" src="/python/fibo.py" id="fibonacci-script">
                </script>
            </PyExample>
            <hr class="my-4" />
            <h1>Example 4</h1>
			<div id="matrix-container"></div>
            <PyExample title="Snake traversal, computed by Python:">
                <script type="py" src="/python/snek.py" id="snek-script">
                </script>
            </PyExample>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				PyScript allows you to run Python code directly in your web browser without any server-side
				processing. These examples demonstrate Python's capabilities, from basic date handling to
				dynamic sequence generation, all running entirely in your browser.
			</p>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">Key Features:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>Client-side Python execution</li>
					<li>Access to Python's standard library</li>
					<li>
						Simple integration with HTML using <code class="rounded bg-white px-1"
							>&lt;script type="py"&gt;</code
						> tags
					</li>
					<li>Real-time computation and display of results</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard> 