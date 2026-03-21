<script>
	import { base } from '$app/paths';
	import { t } from 'svelte-i18n';
</script>

<main class="w-full">
	<div class="flex items-center justify-center py-10 px-4">
		<div class="max-w-7xl w-full space-y-8">
			<!-- Hero Section -->
			<div class="overflow-hidden rounded-lg bg-surface shadow-card border border-border">
				<div class="py-16 px-8 text-center max-w-3xl mx-auto">
					<h1 class="text-5xl font-heading font-bold text-accent mb-4">{$t('home.title')}</h1>
					<p class="text-lg text-text-muted font-body mb-2">
						{$t('home.subtitle')}
					</p>
					<p class="text-text-primary font-body mb-8">
						{$t('home.description')}
					</p>
					<div class="flex gap-4 justify-center">
						<a
							href="{base}/examples/basics/hello"
							class="rounded-lg bg-accent px-6 py-3 text-white font-semibold hover:bg-accent/90 transition-colors duration-200"
						>
							{$t('home.startExploring')}
						</a>
						<a
							href="https://pyscript.net/"
							target="_blank"
							class="rounded-lg border-2 border-accent px-6 py-3 text-accent font-semibold hover:bg-accent/5 transition-colors duration-200"
						>
							{$t('home.learnMore')}
						</a>
					</div>
				</div>
			</div>

			<!-- Features Grid -->
			<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				<!-- Basic Examples -->
				<a href="{base}/examples/basics/hello" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border hover:border-accent transition-colors duration-200">
						<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">Basics</div>
						<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.basic.title')}</h3>
						<p class="text-text-muted text-sm mb-4 flex-grow">
							{$t('home.features.basic.description')}
						</p>
						<div class="text-accent font-semibold text-sm">{$t('home.features.basic.count', { values: { n: 3 } })} &rarr;</div>
					</div>
				</a>

				<!-- Bokeh Visualizations -->
				<a href="{base}/examples/bokeh" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border hover:border-accent transition-colors duration-200">
						<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">Visualizations</div>
						<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.bokeh.title')}</h3>
						<p class="text-text-muted text-sm mb-4 flex-grow">
							{$t('home.features.bokeh.description')}
						</p>
						<div class="text-accent font-semibold text-sm">{$t('home.features.bokeh.count')} &rarr;</div>
					</div>
				</a>

				<!-- Diagrams as Code -->
				<a href="{base}/examples/diagrams/gallery" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border hover:border-accent transition-colors duration-200">
						<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">Diagrams</div>
						<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.diagrams.title')}</h3>
						<p class="text-text-muted text-sm mb-4 flex-grow">
							{$t('home.features.diagrams.description')}
						</p>
						<div class="text-accent font-semibold text-sm">{$t('home.features.diagrams.count')} &rarr;</div>
					</div>
				</a>

				<!-- Matplotlib Charts -->
				<a href="{base}/examples/matplotlib/intro" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border hover:border-accent transition-colors duration-200">
						<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">Charts</div>
						<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.matplotlib.title')}</h3>
						<p class="text-text-muted text-sm mb-4 flex-grow">
							{$t('home.features.matplotlib.description')}
						</p>
						<div class="text-accent font-semibold text-sm">{$t('home.features.matplotlib.count')} &rarr;</div>
					</div>
				</a>

				<!-- Machine Learning -->
				<a href="{base}/examples/ml" class="group block h-full">
					<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border hover:border-accent transition-colors duration-200">
						<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">Machine Learning</div>
						<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.ml.title')}</h3>
						<p class="text-text-muted text-sm mb-4 flex-grow">
							{$t('home.features.ml.description')}
						</p>
						<div class="text-accent font-semibold text-sm">{$t('home.features.ml.count')} &rarr;</div>
					</div>
				</a>

				<!-- About This Project -->
				<div class="h-full flex flex-col rounded-lg bg-surface p-6 shadow-card border border-border">
					<div class="text-xs font-semibold uppercase tracking-wider text-accent mb-2">About</div>
					<h3 class="text-xl font-heading font-bold mb-2 text-text-primary">{$t('home.features.about.title')}</h3>
					<p class="text-text-muted text-sm mb-4 flex-grow">
						{$t('home.features.about.description')}
					</p>
					<p class="text-text-muted text-xs">
						{$t('home.features.about.footer')}
					</p>
				</div>
			</div>

			<!-- Tech Stack -->
			<div class="rounded-lg bg-surface p-8 shadow-card border border-border">
				<h2 class="text-2xl font-heading font-bold mb-6 text-text-primary">{$t('home.techStack.title')}</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-surface-alt flex items-center justify-center">
							<img src="{base}/images/python.svg" alt="Python" class="w-6 h-6" />
						</div>
						<div>
							<div class="font-semibold text-text-primary">{$t('home.techStack.pyscript.title')}</div>
							<div class="text-sm text-text-muted">{$t('home.techStack.pyscript.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-surface-alt flex items-center justify-center text-accent font-heading font-bold">DS</div>
						<div>
							<div class="font-semibold text-text-primary">{$t('home.techStack.dataScience.title')}</div>
							<div class="text-sm text-text-muted">{$t('home.techStack.dataScience.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-surface-alt flex items-center justify-center text-accent font-heading font-bold">Sv</div>
						<div>
							<div class="font-semibold text-text-primary">{$t('home.techStack.svelte.title')}</div>
							<div class="text-sm text-text-muted">{$t('home.techStack.svelte.subtitle')}</div>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-12 h-12 rounded-lg bg-surface-alt flex items-center justify-center text-accent font-heading font-bold">WA</div>
						<div>
							<div class="font-semibold text-text-primary">{$t('home.techStack.webassembly.title')}</div>
							<div class="text-sm text-text-muted">{$t('home.techStack.webassembly.subtitle')}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</main>
