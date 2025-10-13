<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import CodeBlock from '$lib/CodeBlock.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { DiagramRenderer } from '$lib/DiagramRenderer.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Diagrams Gallery';

	// Python runner instance
	let pyScriptRunner;
	let loading = $state(true);

	onMount(async () => {
		// Load viz.js dynamically
		const { instance } = await import('https://cdn.jsdelivr.net/npm/@viz-js/viz@3.2.0/+esm');
		const viz = await instance();
		console.log('✅ Viz.js loaded and ready!');

		// Create DiagramRenderer instance
		const diagramRenderer = new DiagramRenderer(viz);
		console.log('✅ DiagramRenderer created!');

		// Expose to window for Python to call
		window.diagramRenderer = diagramRenderer;
		window.fetchAndRenderDiagram = (chartId, dotContent, imageMappingJson) => {
			diagramRenderer.render(chartId, dotContent, imageMappingJson);
		};
		window.renderDiagram = (chartId, dotContent) => {
			diagramRenderer.renderSimple(chartId, dotContent);
		};

		console.log('✅ DiagramRenderer ready!');

		if (!pyScriptRunner) {
			pyScriptRunner = RunPython();
			pyScriptRunner.runScript(getLink('python/diagrams_example.py'), 'script_gutter', false);

			setTimeout(() => {
				loading = false;
			}, 5000);
		}
	});

	onDestroy(() => {
		if (pyScriptRunner) {
			pyScriptRunner.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/bokeh/communities', nextPage: '/examples/diagrams/create' }}>
	<div slot="py_slot" class="relative">
		{#if loading}
			<div class="absolute inset-0 z-10 flex items-center justify-center bg-slate-300/50">
				<div class="rounded-lg bg-white p-4 shadow-lg">
					<p class="text-lg">🐍 Loading diagrams...</p>
				</div>
			</div>
		{/if}

		<!-- Example diagrams will be rendered here -->
		<div class="space-y-6 p-6">
			<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-bold">Example 1: Grouped Workers</h3>
					<button
						onclick={() => {
							const container = document.getElementById('chart1');
							container.innerHTML = '<p class=\"text-gray-500 animate-pulse\">🔄 Regenerating...</p>';
							setTimeout(() => window.regenerateDiagram1(), 100);
						}}
						class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
					>
						🔄 Regenerate
					</button>
				</div>
				<div
					id="chart1"
					class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
				></div>
				<div class="mt-4">
					<CodeBlock code={`from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Grouped Workers", show=False):
    ELB("lb") >> [EC2("worker1"),
                  EC2("worker2"),
                  EC2("worker3"),
                  EC2("worker4"),
                  EC2("worker5")] >> RDS("events")`} />
				</div>
			</div>

			<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-bold">Example 2: Clustered Web Services</h3>
					<button
						onclick={() => {
							const container = document.getElementById('chart2');
							container.innerHTML = '<p class=\"text-gray-500 animate-pulse\">🔄 Regenerating...</p>';
							setTimeout(() => window.regenerateDiagram2(), 100);
						}}
						class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
					>
						🔄 Regenerate
					</button>
				</div>
				<div
					id="chart2"
					class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
				></div>
				<div class="mt-4">
					<CodeBlock code={`from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import ElastiCache, RDS
from diagrams.aws.network import ELB, Route53

with Diagram("Clustered Web Services", show=False):
    dns = Route53("dns")
    lb = ELB("lb")

    with Cluster("Services"):
        svc_group = [ECS("web1"),
                     ECS("web2"),
                     ECS("web3")]

    with Cluster("DB Cluster"):
        db_primary = RDS("userdb")
        db_primary - [RDS("userdb ro")]

    memcached = ElastiCache("memcached")

    dns >> lb >> svc_group
    svc_group >> db_primary
    svc_group >> memcached`} />
				</div>
			</div>

			<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-bold">Example 3: Event-Driven Architecture</h3>
					<button
						onclick={() => {
							const container = document.getElementById('chart3');
							container.innerHTML = '<p class=\"text-gray-500 animate-pulse\">🔄 Regenerating...</p>';
							setTimeout(() => window.regenerateDiagram3(), 100);
						}}
						class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
					>
						🔄 Regenerate
					</button>
				</div>
				<div
					id="chart3"
					class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
				></div>
				<div class="mt-4">
					<CodeBlock code={`from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import SNS, SQS

with Diagram("Event-Driven Architecture", show=False):
    source = EC2("event source")

    with Cluster("Event Processing"):
        topic = SNS("topic")
        queue = SQS("queue")
        workers = [Lambda("handler1"),
                  Lambda("handler2"),
                  Lambda("handler3")]

    db = Dynamodb("state")

    source >> topic >> queue >> workers >> db`} />
				</div>
			</div>

			<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-bold">Example 4: Microservices API</h3>
					<button
						onclick={() => {
							const container = document.getElementById('chart4');
							container.innerHTML = '<p class=\"text-gray-500 animate-pulse\">🔄 Regenerating...</p>';
							setTimeout(() => window.regenerateDiagram4(), 100);
						}}
						class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
					>
						🔄 Regenerate
					</button>
				</div>
				<div
					id="chart4"
					class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
				></div>
				<div class="mt-4">
					<CodeBlock code={`from diagrams import Cluster, Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway

with Diagram("Microservices API", show=False):
    api = APIGateway("api")

    with Cluster("Microservices"):
        svc1 = Lambda("users")
        svc2 = Lambda("orders")
        svc3 = Lambda("products")

    with Cluster("Data Layer"):
        db1 = Dynamodb("users-db")
        db2 = Dynamodb("orders-db")
        db3 = Dynamodb("products-db")

    api >> [svc1, svc2, svc3]
    svc1 >> db1
    svc2 >> db2
    svc3 >> db3`} />
				</div>
			</div>

			<div class="rounded-lg border-2 border-gray-200 bg-white p-6">
				<div class="mb-4 flex items-center justify-between">
					<h3 class="text-lg font-bold">Example 5: Data Analytics Pipeline</h3>
					<button
						onclick={() => {
							const container = document.getElementById('chart5');
							container.innerHTML = '<p class=\"text-gray-500 animate-pulse\">🔄 Regenerating...</p>';
							setTimeout(() => window.regenerateDiagram5(), 100);
						}}
						class="rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 transition-colors"
					>
						🔄 Regenerate
					</button>
				</div>
				<div
					id="chart5"
					class="flex min-h-[200px] items-center justify-center overflow-auto rounded bg-gray-50 p-4"
				></div>
				<div class="mt-4">
					<CodeBlock code={`from diagrams import Cluster, Diagram
from diagrams.aws.analytics import Athena
from diagrams.aws.compute import Lambda
from diagrams.aws.database import ElastiCache
from diagrams.aws.storage import S3

with Diagram("Data Analytics Pipeline", show=False):
    source = S3("raw-data")

    with Cluster("Processing"):
        etl = Lambda("transform")
        processed = S3("processed")

    analytics = Athena("analytics")
    cache = ElastiCache("cache")

    source >> etl >> processed >> analytics
    analytics >> cache`} />
				</div>
			</div>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="space-y-4">
			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 font-bold text-blue-900">📦 What is Diagrams?</h3>
				<p class="text-sm text-blue-800">
					<a
						href="https://diagrams.mingrammer.com"
						target="_blank"
						class="font-bold text-blue-600 underline hover:text-blue-800"
					>Diagrams</a> is a Python library that lets you draw cloud system architecture diagrams
					using code instead of drag-and-drop tools. Created by mingrammer, it provides a simple,
					declarative way to create professional architecture diagrams that can be version controlled
					alongside your infrastructure code.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🏗️ Infrastructure as Code Philosophy</h3>
				<p class="text-sm text-green-800">
					Just like Infrastructure as Code (IaC) manages infrastructure through code, Diagrams as
					Code creates architecture diagrams programmatically. This means your diagrams can be
					version controlled, reviewed in pull requests, and automatically updated alongside your
					infrastructure changes. No more outdated diagrams in documentation!
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 font-bold text-purple-900">☁️ Multi-Cloud Support</h3>
				<p class="text-sm text-purple-800">
					Diagrams supports all major cloud providers (AWS, Azure, GCP, Kubernetes), on-premise
					solutions, and SaaS services. You can mix and match components from different providers
					to accurately represent hybrid and multi-cloud architectures. The library includes
					hundreds of official provider icons.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 font-bold text-green-900">🔗 Simple Syntax</h3>
				<p class="text-sm text-green-800">
					The library uses intuitive Python syntax with operators like
					<code class="rounded bg-green-200 px-1">{'>> '}</code>
					for data flow,
					<code class="rounded bg-green-200 px-1">{' - '}</code>
					for connections, and list notation
					<code class="rounded bg-green-200 px-1">{'[]'}</code>
					for parallel components. Clusters group related resources together.
				</p>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 font-bold text-amber-900">🎉 Browser Magic with viz.js!</h3>
				<p class="text-sm text-amber-800">
					The Diagrams library generates Graphviz DOT format, which normally requires a native
					binary. We're using <strong>viz.js</strong> (Graphviz compiled to WebAssembly) to render
					the diagrams directly in your browser! The Python code intercepts the
					<code class="bg-amber-200 px-1 rounded">graphviz.Digraph</code> class to capture DOT
					output.
				</p>
				<p class="text-sm text-amber-800 mt-2">
					<strong>Icon loading:</strong> Cloud provider icons are fetched from the diagrams GitHub
					repository, converted to base64 data URIs, and embedded directly into the SVG. This
					happens automatically in JavaScript before rendering!
				</p>
			</div>

			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 font-bold text-cyan-900">💡 Real-World Use Cases</h3>
				<p class="text-sm text-cyan-800">
					• Document system architecture in your repository<br />
					• Auto-generate diagrams from infrastructure code<br />
					• Create visual documentation for technical proposals<br />
					• Maintain architecture diagrams alongside code changes<br />
					• Generate diagrams in CI/CD pipelines<br />
				</p>
			</div>

			<div class="rounded-lg bg-rose-50 p-4">
				<h3 class="mb-2 font-bold text-rose-900">🚀 Getting Started Locally</h3>
				<p class="text-sm text-rose-800">
					To use the Diagrams library in a local Python environment:<br />
					<code class="mt-2 block rounded bg-gray-900 p-2 text-gray-100"
						>pip install diagrams</code
					><br />
					You'll also need Graphviz installed on your system. Visit
					<a
						href="https://diagrams.mingrammer.com"
						target="_blank"
						class="font-bold text-rose-600 underline">diagrams.mingrammer.com</a
					> for full documentation and installation instructions.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/diagrams_example.py"
				target="_blank">View source</a
			>
			<br />
			<a
				class="text-sky-500"
				target="_blank"
				href="https://diagrams.mingrammer.com/docs/getting-started/examples">Official Examples</a
			>
		</p>
	</article>
</ExperimentCard>
