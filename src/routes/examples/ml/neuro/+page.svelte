<script>
	import { onMount, onDestroy } from 'svelte';
	import { NES, Button } from '$lib/nes/NES.js';
	
	let canvas;
	let nes = null;
	let status = 'Loading...';
	let muted = true;
	
	onMount(async () => {
		try {
			// Create NES instance
			nes = new NES(canvas);
			status = 'Initializing JSNes...';
			
			// Initialize
			await nes.init();
			status = 'Loading ROM...';
			
			// Load ROM
			await nes.loadROM('/data/package.nes');
			status = 'Loading saved state...';
			
			// Load saved state
			await nes.loadState('/data/nes_state.json');
			status = 'Ready';
			
			// Start muted by default
			nes.setMuted(muted);
			
			// Start emulation
			nes.start();
			status = 'Running';
			
		} catch (err) {
			console.error('Failed to initialize NES:', err);
			status = `Error: ${err.message}`;
		}
	});
	
	onDestroy(() => {
		if (nes) {
			nes.destroy();
			nes = null;
		}
	});
	
	function toggleMute() {
		muted = !muted;
		if (nes) {
			nes.setMuted(muted);
		}
	}
</script>

<div class="container mx-auto p-8">
	<h1 class="text-3xl font-bold mb-4">Mario AI</h1>
	<p class="text-gray-600 mb-4">Status: {status}</p>
	
	<div class="flex gap-4 mb-4">
		<button 
			class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
			onclick={toggleMute}
		>
			{muted ? '🔇 Unmute' : '🔊 Mute'}
		</button>
	</div>
	
	<canvas 
		bind:this={canvas}
		width="256"
		height="240"
		class="border border-gray-300 bg-black"
		style="image-rendering: pixelated; width: 512px; height: 480px;"
	></canvas>
</div>
