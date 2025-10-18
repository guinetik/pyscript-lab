<script>
	import { base } from '$app/paths';
	import { t } from 'svelte-i18n';
</script>

<main class="w-full">
	<div class="flex items-center justify-center py-10 px-4">
		<div class="max-w-7xl w-full space-y-8">
			<!-- Hero Section -->
			<div class="overflow-hidden rounded-lg bg-white shadow-2xl">
				<div class="md:flex">
					<img
						class="w-full rounded-lg object-cover object-center p-1 md:w-1/2"
						src="{base}/images/pyscript.png"
						alt="PyScript"
					/>
					<div class="space-y-4 border-slate-900 p-8 sm:border-t md:border-l">
						<h1 class="text-4xl font-extrabold text-gray-900">{$t('home.title')}</h1>
						<p class="text-lg text-gray-600">
							{$t('home.subtitle')}
						</p>
						<p class="text-gray-700">
							{$t('home.description')}
						</p>
						<div class="flex gap-4 pt-4">
							<a
								href="{base}/examples/basics/hello"
								class="rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700 transition-colors"
							>
								{$t('home.startExploring')}
							</a>
							<a
								href="https://pyscript.net/"
								target="_blank"
								class="rounded-lg border-2 border-blue-600 px-6 py-3 text-blue-600 font-semibold hover:bg-blue-50 transition-colors"
							>
								{$t('home.learnMore')}
							</a>
						</div>
					</div>
				</div>
			</div>

			<!-- Features Grid -->
			<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				<!-- Basic Examples -->
				<a href="{base}/examples/basics/hello" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-blue-500">
						<div class="text-4xl mb-4">🐍</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-blue-600">{$t('home.features.basic.title')}</h3>
						<p class="text-gray-600 text-sm mb-4 flex-grow">
							{$t('home.features.basic.description')}
						</p>
						<div class="text-blue-600 font-semibold text-sm">{$t('home.features.basic.count', { values: { n: 3 } })} →</div>
					</div>
				</a>

				<!-- Bokeh Visualizations -->
				<a href="{base}/examples/bokeh" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-green-500">
						<div class="text-4xl mb-4">📊</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-green-600">{$t('home.features.bokeh.title')}</h3>
						<p class="text-gray-600 text-sm mb-4 flex-grow">
							{$t('home.features.bokeh.description')}
						</p>
						<div class="text-green-600 font-semibold text-sm">{$t('home.features.bokeh.count')} →</div>
					</div>
				</a>

				<!-- Diagrams as Code -->
				<a href="{base}/examples/diagrams/gallery" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-purple-500">
						<div class="text-4xl mb-4">🏗️</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-purple-600">{$t('home.features.diagrams.title')}</h3>
						<p class="text-gray-600 text-sm mb-4 flex-grow">
							{$t('home.features.diagrams.description')}
						</p>
						<div class="text-purple-600 font-semibold text-sm">{$t('home.features.diagrams.count')} →</div>
					</div>
				</a>

				<!-- Matplotlib Charts -->
				<a href="{base}/examples/matplotlib/intro" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-orange-500">
						<div class="text-4xl mb-4">📈</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-orange-600">{$t('home.features.matplotlib.title')}</h3>
						<p class="text-gray-600 text-sm mb-4 flex-grow">
							{$t('home.features.matplotlib.description')}
						</p>
						<div class="text-orange-600 font-semibold text-sm">{$t('home.features.matplotlib.count')} →</div>
					</div>
				</a>

				<!-- Machine Learning -->
				<a href="{base}/examples/ml" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-red-500">
						<div class="text-4xl mb-4">🤖</div>
						<h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-red-600">{$t('home.features.ml.title')}</h3>
						<p class="text-gray-600 text-sm mb-4 flex-grow">
							{$t('home.features.ml.description')}
						</p>
						<div class="text-red-600 font-semibold text-sm">{$t('home.features.ml.count')} →</div>
					</div>
				</a>

				<!-- About This Project -->
				<div class="h-full flex flex-col rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 p-6 shadow-lg text-white">
					<div class="text-4xl mb-4">💡</div>
					<h3 class="text-xl font-bold mb-2">{$t('home.features.about.title')}</h3>
					<p class="text-slate-200 text-sm mb-4 flex-grow">
						{$t('home.features.about.description')}
					</p>
					<p class="text-slate-300 text-xs">
						{$t('home.features.about.footer')}
					</p>
				</div>
			</div>

			<!-- Tech Stack -->
			<div class="rounded-lg bg-white p-8 shadow-lg">
				<h2 class="text-2xl font-bold mb-6 text-gray-900">{$t('home.techStack.title')}</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center text-2xl">🐍</div>
						<div>
							<div class="font-semibold text-gray-900">{$t('home.techStack.pyscript.title')}</div>
							<div class="text-sm text-gray-600">{$t('home.techStack.pyscript.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center text-2xl">📊</div>
						<div>
							<div class="font-semibold text-gray-900">{$t('home.techStack.dataScience.title')}</div>
							<div class="text-sm text-gray-600">{$t('home.techStack.dataScience.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center text-2xl">🎨</div>
						<div>
							<div class="font-semibold text-gray-900">{$t('home.techStack.svelte.title')}</div>
							<div class="text-sm text-gray-600">{$t('home.techStack.svelte.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center text-2xl">⚡</div>
						<div>
							<div class="font-semibold text-gray-900">{$t('home.techStack.webassembly.title')}</div>
							<div class="text-sm text-gray-600">{$t('home.techStack.webassembly.subtitle')}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>
