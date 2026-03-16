<script>
	import '../app.css';
	import Nav from '../lib/components/Nav.svelte';
	import { initializeI18n } from '$lib/i18n';
	import { isLoading } from 'svelte-i18n';

	let { children } = $props();

	// Initialize i18n
	initializeI18n();

	// Update HTML lang attribute when locale changes
	$effect(() => {
		if (!$isLoading && typeof document !== 'undefined') {
			import('svelte-i18n').then(({ locale }) => {
				locale.subscribe(value => {
					if (value) {
						document.documentElement.lang = value;
					}
				});
			});
		}
	});
</script>

{#if $isLoading}
	<div class="flex h-screen w-full items-center justify-center">
		<div class="text-center">
			<div class="mb-4 text-4xl">🐍</div>
			<div class="text-xl font-semibold text-gray-700">Loading...</div>
		</div>
	</div>
{:else}
	<Nav />

	<main class="flex min-h-[calc(100vh-120px)] w-full flex-col">
		<div class="flex-1 min-h-0 flex flex-col">
			{@render children()}
		</div>
	</main>
{/if}