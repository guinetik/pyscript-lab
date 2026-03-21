<script>
	/**
	 * DNA particle helix with true rotating 3D projection.
	 * Uses a throttled canvas loop so the helix geometry rotates, not the canvas plane.
	 *
	 * @typedef {import('$lib/breeding/breedingGenArtCanvas.js').BreedingData} BreedingData
	 */

	import { onMount, onDestroy } from 'svelte';
	import { drawBreedingHelix } from '$lib/breeding/breedingGenArtCanvas.js';

	/** @type {{ breedingData?: BreedingData | null }} */
	let { breedingData = null } = $props();

	/** @type {HTMLCanvasElement | undefined} */
	let canvasEl = $state();
	/** @type {HTMLDivElement | undefined} */
	let wrapEl = $state();

	const TARGET_FPS = 14;
	const FRAME_INTERVAL_MS = 1000 / TARGET_FPS;
	const ROTATION_SPEED = 0.0007;

	let frameId = 0;
	let lastDrawMs = 0;
	let phaseOffset = 0;
	let prefersReducedMotion = false;

	/**
	 * Draw a single frame.
	 * @param {number} phase
	 * @returns {void}
	 */
	function paint(phase = phaseOffset) {
		if (!canvasEl) return;
		drawBreedingHelix(canvasEl, breedingData, phase);
	}

	/**
	 * Stop the animation loop.
	 * @returns {void}
	 */
	function stopLoop() {
		if (frameId) {
			cancelAnimationFrame(frameId);
			frameId = 0;
		}
	}

	/**
	 * Animate the projected helix rotation.
	 * @param {number} now
	 * @returns {void}
	 */
	function animate(now) {
		if (prefersReducedMotion) {
			frameId = 0;
			return;
		}
		frameId = requestAnimationFrame(animate);
		if (document.hidden) return;
		if (now - lastDrawMs < FRAME_INTERVAL_MS) return;
		lastDrawMs = now;
		const phase = phaseOffset + now * ROTATION_SPEED;
		paint(phase);
	}

	/**
	 * Restart animation timing.
	 * @returns {void}
	 */
	function startLoop() {
		stopLoop();
		if (prefersReducedMotion) return;
		lastDrawMs = 0;
		frameId = requestAnimationFrame(animate);
	}

	$effect(() => {
		void breedingData?.generation;
		void canvasEl;
		phaseOffset = breedingData?.generation ? breedingData.generation * 0.22 : 0;
		paint();
	});

	/** @type {ResizeObserver | undefined} */
	let ro;

	onMount(() => {
		prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		if (typeof ResizeObserver !== 'undefined' && wrapEl) {
			ro = new ResizeObserver(() => paint());
			ro.observe(wrapEl);
		}
		startLoop();
	});

	onDestroy(() => {
		stopLoop();
		ro?.disconnect();
	});
</script>

<div
	bind:this={wrapEl}
	class="breeding-helix-root relative w-full overflow-hidden rounded-2xl border border-violet-500/30 bg-[#0a0412] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
	aria-label="Breeding lineage as rotating 3D particle helix"
>
	<canvas
		bind:this={canvasEl}
		class="block h-[240px] w-full"
		width="800"
		height="240"
	></canvas>
</div>
