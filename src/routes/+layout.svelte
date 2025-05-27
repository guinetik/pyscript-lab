<script>
	import '../app.css';
	import Nav from '../lib/Nav.svelte';

	let { children } = $props();
</script>

<Nav activePage="repl" />

<main class="flex h-[calc(100%-120px)] w-full flex-col justify-center">
	{@render children()}
</main>