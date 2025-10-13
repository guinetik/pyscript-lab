<main class="w-full">
	<div class="flex items-center justify-center py-10 px-4">
		<div class="max-w-7xl w-full space-y-8">
			<!-- Hero Section -->
			<div class="overflow-hidden rounded-lg bg-white shadow-2xl">
				<div class="md:flex">
					<img
						class="w-full rounded-lg object-cover object-center p-1 md:w-1/2"
						src="images/pyscript.png"
						alt="PyScript"
					/>
					<div class="space-y-4 border-slate-900 p-8 sm:border-t md:border-l">
						<h1 class="text-4xl font-extrabold text-gray-900">PyScript Lab</h1>
						<p class="text-lg text-gray-600">
							Python in the Browser. No Server Required.
						</p>
						<p class="text-gray-700">
							Explore interactive examples demonstrating real-world Python applications running
							entirely in your browser using PyScript and modern web technologies.
						</p>
						<div class="flex gap-4 pt-4">
							<a
								href="/examples/basics/hello"
								class="rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700 transition-colors"
							>
								Start Exploring
							</a>
							<a
								href="https://pyscript.net/"
								target="_blank"
								class="rounded-lg border-2 border-blue-600 px-6 py-3 text-blue-600 font-semibold hover:bg-blue-50 transition-colors"
							>
								Learn More
							</a>
						</div>
					</div>
				</div>
			</div>

			<!-- Features Grid -->
			<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				<!-- Basic Examples -->
				<a href="/examples/basics/hello" class="group block">
					<div class="rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-blue-500">
						<div class="text-4xl mb-4">🐍</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-blue-600">Basic Examples</h3>
						<p class="text-gray-600 text-sm mb-4">
							Get started with PyScript fundamentals: Hello World, REPL environments, and Python-JavaScript interoperability.
						</p>
						<div class="text-blue-600 font-semibold text-sm">3 Examples →</div>
					</div>
				</a>

				<!-- Bokeh Visualizations -->
				<a href="/examples/bokeh" class="group block">
					<div class="rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-green-500">
						<div class="text-4xl mb-4">📊</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-green-600">Bokeh Visualizations</h3>
						<p class="text-gray-600 text-sm mb-4">
							Interactive data visualizations with Bokeh: Pandas integration, network graphs, and community detection algorithms.
						</p>
						<div class="text-green-600 font-semibold text-sm">3 Examples →</div>
					</div>
				</a>

				<!-- Diagrams as Code -->
				<a href="/examples/diagrams/gallery" class="group block">
					<div class="rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-purple-500">
						<div class="text-4xl mb-4">🏗️</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-purple-600">Diagrams as Code</h3>
						<p class="text-gray-600 text-sm mb-4">
							Generate cloud architecture diagrams programmatically. Version-controlled infrastructure visualization.
						</p>
						<div class="text-purple-600 font-semibold text-sm">5 Examples →</div>
					</div>
				</a>

				<!-- Matplotlib Charts -->
				<a href="/examples/matplotlib/intro" class="group block">
					<div class="rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-orange-500">
						<div class="text-4xl mb-4">📈</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-orange-600">Matplotlib & Maps</h3>
						<p class="text-gray-600 text-sm mb-4">
							Data visualization with matplotlib and interactive world maps. COVID-19 data analysis and geographic visualization.
						</p>
						<div class="text-orange-600 font-semibold text-sm">3 Examples →</div>
					</div>
				</a>

				<!-- Machine Learning -->
				<a href="/examples/ml" class="group block">
					<div class="rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-red-500">
						<div class="text-4xl mb-4">🤖</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-red-600">Machine Learning</h3>
						<p class="text-gray-600 text-sm mb-4">
							Browser-based ML with scikit-learn: Handwritten digit recognition and sentiment analysis running client-side.
						</p>
						<div class="text-red-600 font-semibold text-sm">2 Examples →</div>
					</div>
				</a>

				<!-- About This Project -->
				<div class="rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 p-6 shadow-lg text-white">
					<div class="text-4xl mb-4">💡</div>
					<h3 class="text-xl font-bold mb-2">About This Lab</h3>
					<p class="text-slate-200 text-sm mb-4">
						Exploring PyScript's capabilities and demonstrating how Python integrates with modern JavaScript frameworks like Svelte.
					</p>
					<p class="text-slate-300 text-xs">
						All code runs in your browser. No backend servers, no API calls. Just Python + WebAssembly.
					</p>
				</div>
			</div>

			<!-- Tech Stack -->
			<div class="rounded-lg bg-white p-8 shadow-lg">
				<h2 class="text-2xl font-bold mb-6 text-gray-900">Technology Stack</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center text-2xl">🐍</div>
						<div>
							<div class="font-semibold text-gray-900">PyScript</div>
							<div class="text-sm text-gray-600">Python in Browser</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center text-2xl">📊</div>
						<div>
							<div class="font-semibold text-gray-900">Data Science</div>
							<div class="text-sm text-gray-600">Pandas, NumPy, Plotly</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center text-2xl">🎨</div>
						<div>
							<div class="font-semibold text-gray-900">Svelte 5</div>
							<div class="text-sm text-gray-600">Reactive Framework</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center text-2xl">⚡</div>
						<div>
							<div class="font-semibold text-gray-900">WebAssembly</div>
							<div class="text-sm text-gray-600">Native Performance</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>
