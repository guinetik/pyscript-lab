<script>
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NeuralNetworkViz from '$lib/components/NeuralNetworkViz.svelte';
	import MetricsChart from '$lib/components/MetricsChart.svelte';
	import BreedingViz from '$lib/components/BreedingViz.svelte';
	import { NeuroController } from '$lib/controller/NeuroController.js';

	// === State ===
	let canvas;
	let controller = null;
	
	// UI state
	let mode = $state('idle'); // 'idle' | 'playing' | 'ai' | 'training'
	let status = $state('Click a button to begin');
	let muted = $state(true);
	
	// Training mode selection
	let trainingMode = $state('simple'); // 'simple' | 'sbx' | 'uniform' | 'optimize'
	const trainingModes = [
		{ value: 'simple', label: 'Simple (Elite + Mutation)', description: 'Preserve top elites and fill the rest with mutated elite copies' },
		{ value: 'sbx', label: 'SBX Breeding', description: 'Preserve the champion, then breed every other slot with two-parent SBX plus mutation' },
		{ value: 'uniform', label: 'Uniform Breeding', description: 'Preserve the champion, then breed every other slot with uniform crossover plus mutation' },
		{ value: 'optimize', label: 'Optimize (Reference Seed)', description: 'Seed from reference weights, preserve the champion, then continue with mutation-only evolution' }
	];
	
	// Training state
	let generation = $state(0);
	let fitness = $state(0);
	let bestDistance = $state(0);
	let trainerState = $state('IDLE'); // IDLE | BACKGROUND | FOREGROUND
	let foregroundFramesRemaining = $state(0);
	
	// Stats
	let stats = $state({ x: 0, frames: 0, farthestX: 0 });
	
	// Visualization toggles
	let showNeurons = $state(false);
	let showMetrics = $state(false);
	let showBreeding = $state(false);
	let networkVizData = $state(null);
	let breedingData = $state(null);

	/** Last live neuron snapshot while not in background training — shown frozen during BACKGROUND (no redraw churn). */
	let frozenNetworkViz = $state(null);

	const trainingBackground = $derived(mode === 'training' && trainerState === 'BACKGROUND');
	const neuronDisplayViz = $derived(trainingBackground ? frozenNetworkViz : networkVizData);
	
	// Metrics history for chart
	let metricsHistory = $state([]);

	$effect(() => {
		if (!trainingBackground && networkVizData) {
			frozenNetworkViz = networkVizData;
		}
	});
	
	// === Setup on mount ===
	onMount(async () => {
		if (!browser) return;

		controller = new NeuroController();
		
		controller.setCallbacks({
			onProgress: (gen, fit, dist) => {
				generation = gen;
				fitness = fit;
				bestDistance = dist;
				status = `Training: Gen ${gen} | Fitness: ${fit.toFixed(0)} | Dist: ${dist}`;
				metricsHistory = [...metricsHistory.slice(-99), { gen, fitness: fit, distance: dist }];
			},
			onBreeding: (data) => {
				breedingData = data;
			},
			onState: (newState) => {
				trainerState = newState;
				if (newState === 'IDLE') {
					mode = 'idle';
					status = 'Training stopped';
				} else if (newState === 'BACKGROUND') {
					status = 'Training in background...';
				} else if (newState === 'FOREGROUND') {
					status = 'Showing best agent...';
				}
			},
			onStats: (newStats) => {
				stats = newStats;
			},
			onViz: (data) => {
				networkVizData = data;
			},
			onComplete: (success) => {
				mode = 'idle';
				trainerState = 'IDLE';
				status = success ? 'LEVEL COMPLETE! Mario beat the level!' : 'Training finished';
			},
			onStatus: (msg) => {
				status = msg;
			}
		});

		await controller.initialize(canvas);
		controller.toggleMute(muted);
	});
	
	// === Actions ===
	async function startPlay() {
		mode = 'playing';
		await controller.startPlay();
	}

	async function startAI() {
		mode = 'ai';
		showNeurons = true;
		await controller.startAI();
	}

	async function startTraining() {
		mode = 'training';
		generation = 0;
		fitness = 0;
		bestDistance = 0;
		trainerState = 'IDLE';
		metricsHistory = [];
		showNeurons = true;
		showMetrics = true;
		showBreeding = true;
		breedingData = null;
		
		await controller.startTraining(trainingMode);
	}

	function stop() {
		controller.stop();
		mode = 'idle';
		trainerState = 'IDLE';
	}

	function toggleMute() {
		muted = !muted;
		controller.toggleMute(muted);
	}
	
	// === Cleanup ===
	onDestroy(() => {
		if (controller) {
			controller.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/ml', nextPage: '/examples/ml/rl', split: 'balanced' }}>
	<div slot="py_slot" class="flex flex-col h-full p-4 space-y-4 overflow-y-auto">
		<!-- Game Canvas -->
		<div class="relative bg-black rounded-lg overflow-hidden w-full">
			<canvas 
				bind:this={canvas}
				width="256"
				height="240"
				class="w-full h-auto block"
				style="image-rendering: pixelated; aspect-ratio: 256/240;"
			></canvas>
			
			<!-- Overlay for Background Training (hidden during foreground display) -->
			{#if mode === 'training' && trainerState === 'BACKGROUND'}
				<div class="absolute inset-0 bg-black/70 flex items-center justify-center">
					<div class="text-center text-white">
						<div class="text-4xl mb-2 animate-pulse">🧬</div>
						<div class="font-bold text-lg">Training in Background</div>
						<div class="text-sm opacity-75 mt-2">Generation {generation}</div>
						<div class="text-xs opacity-50 mt-1">Best Distance: {bestDistance}</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Status Bar -->
		<div class="px-4 py-2 rounded bg-gray-100 border-2 border-gray-300">
			<p class="text-sm font-mono">{status}</p>
		</div>
		
		<!-- Stats Display -->
		{#if mode === 'ai' || mode === 'playing'}
			<div class="grid grid-cols-3 gap-2">
				<div class="bg-blue-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Position</div>
					<div class="text-xl font-bold">{stats.x}</div>
				</div>
				<div class="bg-green-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Farthest</div>
					<div class="text-xl font-bold">{stats.farthestX}</div>
				</div>
				<div class="bg-purple-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Frames</div>
					<div class="text-xl font-bold">{stats.frames}</div>
				</div>
			</div>
		{/if}
		
		<!-- Training Stats -->
		{#if mode === 'training'}
			<div class="grid grid-cols-4 gap-2">
				<div class="rounded p-3 text-center text-white {trainerState === 'BACKGROUND' ? 'bg-orange-500' : 'bg-cyan-500'}">
					<div class="text-xs opacity-75">Phase</div>
					<div class="text-lg font-bold">{trainerState}</div>
				</div>
				<div class="bg-blue-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Generation</div>
					<div class="text-xl font-bold">{generation}</div>
				</div>
				<div class="bg-green-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Fitness</div>
					<div class="text-xl font-bold">{fitness.toFixed(0)}</div>
				</div>
				<div class="bg-purple-500 text-white rounded p-3 text-center">
					<div class="text-xs opacity-75">Best Distance</div>
					<div class="text-xl font-bold">{bestDistance}</div>
				</div>
			</div>
			
			{#if trainerState === 'FOREGROUND'}
				<div class="bg-cyan-100 border-2 border-cyan-400 rounded p-2 text-center">
					<span class="text-cyan-800 font-bold">🎮 Best agent playing...</span>
				</div>
			{/if}
		{/if}
		
		<!-- Main Control Buttons -->
		<div class="grid grid-cols-3 gap-3">
			<button 
				onclick={startPlay}
				disabled={mode !== 'idle'}
				class="px-4 py-3 bg-purple-500 text-white font-bold rounded hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				🎮 Play
			</button>
			<button 
				onclick={startAI}
				disabled={mode !== 'idle'}
				class="px-4 py-3 bg-green-500 text-white font-bold rounded hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				🤖 Start AI
			</button>
			<button
				onclick={startTraining}
				disabled={mode !== 'idle'}
				class="px-4 py-3 bg-orange-500 text-white font-bold rounded hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				🧬 Train
			</button>
		</div>

		<!-- Training Mode Selector -->
		<div class="bg-orange-50 border-2 border-orange-200 rounded p-3">
			<label for="training-mode-select" class="block text-sm font-bold text-orange-900 mb-2">🧬 Training Mode</label>
			<select
				id="training-mode-select"
				bind:value={trainingMode}
				disabled={mode !== 'idle'}
				class="w-full px-3 py-2 rounded border-2 border-orange-300 bg-white text-sm font-medium disabled:bg-gray-100 disabled:cursor-not-allowed"
			>
				{#each trainingModes as tm}
					<option value={tm.value}>{tm.label}</option>
				{/each}
			</select>
			<p class="text-xs text-orange-700 mt-1">
				{trainingModes.find(tm => tm.value === trainingMode)?.description}
			</p>
		</div>

		<!-- Secondary Controls -->
		<div class="grid grid-cols-5 gap-2">
			<button 
				onclick={stop}
				disabled={mode === 'idle'}
				class="px-3 py-2 bg-red-500 text-white text-sm font-semibold rounded hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				⏹️ Stop
			</button>
			<button 
				onclick={toggleMute}
				class="px-3 py-2 bg-slate-500 text-white text-sm font-semibold rounded hover:bg-slate-600 transition"
			>
				{muted ? '🔇 Muted' : '🔊 Sound'}
			</button>
			<button 
				onclick={() => showNeurons = !showNeurons}
				class="px-3 py-2 text-white text-sm font-semibold rounded transition {showNeurons ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'}"
			>
				🧠 Neurons
			</button>
			<button 
				onclick={() => showMetrics = !showMetrics}
				class="px-3 py-2 text-white text-sm font-semibold rounded transition {showMetrics ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'}"
			>
				📈 Metrics
			</button>
			<button 
				onclick={() => showBreeding = !showBreeding}
				class="px-3 py-2 text-white text-sm font-semibold rounded transition {showBreeding ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'}"
			>
				🧬 Lineage
			</button>
		</div>

		<!-- Metrics live here (left column) so the doc panel stays readable -->
		{#if showMetrics}
			<MetricsChart metricsHistory={metricsHistory} />
		{/if}
		
		<!-- Keyboard Controls Help -->
		{#if mode === 'playing'}
			<div class="bg-purple-50 border-2 border-purple-200 rounded p-3">
				<h3 class="font-bold text-purple-900 mb-2">⌨️ Keyboard Controls</h3>
				<div class="grid grid-cols-2 gap-2 text-sm text-purple-800">
					<div><kbd class="bg-purple-100 px-1 rounded">←→↑↓</kbd> Move</div>
					<div><kbd class="bg-purple-100 px-1 rounded">Z</kbd> Jump</div>
					<div><kbd class="bg-purple-100 px-1 rounded">X</kbd> Run</div>
					<div><kbd class="bg-purple-100 px-1 rounded">Enter</kbd> Start</div>
				</div>
			</div>
		{/if}
	</div>
	
	<div slot="content_slot" class="space-y-4">
		<div>
			<h2 class="text-xl font-bold text-slate-900">Mario AI — Neuroevolution</h2>
			<p class="mt-1 text-sm text-slate-600 leading-relaxed">
				PyScript runs a full population in Python; the NES game view and charts are in the browser. Use
				<strong>Play</strong> for human control, <strong>Start AI</strong> for a single network playing live, and
				<strong>Train</strong> to evolve a population. Training turns on <strong>Neurons</strong>,
				<strong>Metrics</strong> (chart under the buttons on the left), and <strong>Lineage</strong> by default — you
				can toggle them anytime.
			</p>
		</div>
		
		<!-- Neural Network Visualization -->
		{#if showNeurons}
			<NeuralNetworkViz vizData={neuronDisplayViz} paused={trainingBackground} />
		{/if}

		{#if showBreeding}
			<BreedingViz breedingData={breedingData} />
		{/if}
		
		<!-- Info Sections -->
		<div class="space-y-3">
			<div class="bg-purple-50 border-2 border-purple-200 rounded p-4">
				<h3 class="font-bold text-purple-900 mb-2">🧬 What is neuroevolution?</h3>
				<p class="text-sm text-purple-800 leading-relaxed">
					Instead of gradients (backprop), we <strong>score</strong> many networks by how far Mario gets, then
					<strong>breed and mutate</strong> the best ones to form the next generation. Fitness here is tied to
					in-game performance (distance, survival, etc.), computed while each agent plays a short episode.
				</p>
				<ol class="list-decimal pl-5 mt-3 text-sm text-purple-800 space-y-1.5">
					<li><strong>Initialize</strong> a population (random weights, or reference weights in Optimize mode)</li>
					<li><strong>Evaluate</strong> every agent in the population (many runs happen in the background)</li>
					<li><strong>Rank</strong> by fitness and record the best-ever “champion”</li>
					<li><strong>Evolve</strong> — copy elites / champion, crossover or mutate the rest (mode-dependent)</li>
					<li><strong>Repeat</strong> until the level is cleared or you stop training</li>
				</ol>
			</div>

			<div class="bg-amber-50 border-2 border-amber-300 rounded p-4">
				<h3 class="font-bold text-amber-950 mb-2">⚡ Background vs foreground training</h3>
				<p class="text-sm text-amber-950/90 leading-relaxed mb-2">
					Training alternates phases so you get speed <em>and</em> feedback:
				</p>
				<ul class="text-sm text-amber-950/90 space-y-2 list-disc pl-5">
					<li>
						<strong>BACKGROUND</strong> — The canvas shows a 🧬 overlay while the trainer evaluates the whole
						population headlessly (no visible Mario). Python steps through agents quickly; this is where most
						generations advance.
					</li>
					<li>
						<strong>FOREGROUND</strong> — The best current agent plays on the canvas so you can see behavior.
						The status line shows you’re watching the top performer, not the whole population at once.
					</li>
					<li>
						<strong>IDLE</strong> — Training stopped; you can change the training mode and start again.
					</li>
				</ul>
				<p class="text-xs text-amber-900/80 mt-3 leading-relaxed">
					Champion weights are carried forward so the next background batch keeps improving from the best network
					seen so far — not only from the last generation’s rank order.
				</p>
			</div>
			
			<div class="bg-emerald-50 border-2 border-emerald-200 rounded p-4">
				<h3 class="font-bold text-emerald-900 mb-2">🔄 Training modes (dropdown)</h3>
				<ul class="text-sm text-emerald-800 space-y-2 leading-relaxed">
					<li><strong>Simple:</strong> Preserve the top ~10% as unchanged elites; remaining slots are roulette-selected elite offspring with Gaussian mutation (every generation).</li>
					<li><strong>SBX:</strong> Preserve slot 0 (champion); all other slots are two-parent Simulated Binary Crossover plus mutation each generation.</li>
					<li><strong>Uniform:</strong> Same as SBX but with uniform crossover between parents, then mutation.</li>
					<li><strong>Optimize:</strong> Seed from shipped reference weights, preserve only the champion, then mutation-only fine-tuning (good when you already have a strong prior).</li>
				</ul>
			</div>

			<div class="bg-slate-100 border-2 border-slate-300 rounded p-4">
				<h3 class="font-bold text-slate-900 mb-2">🎛️ Panels & toggles</h3>
				<ul class="text-sm text-slate-800 space-y-2 leading-relaxed list-disc pl-5">
					<li><strong>Metrics</strong> — Fitness and best distance over time; lives <strong>under the buttons</strong> on the left when enabled.</li>
					<li><strong>Neurons</strong> — Live network diagram; animation pauses during <strong>BACKGROUND</strong> to keep the tab responsive while PyScript works.</li>
					<li><strong>Lineage</strong> — 3D particle helix with real rotating projection plus a small table of <strong>preserved</strong> champions/elites only.</li>
					<li><strong>Neurons + BACKGROUND</strong> — The diagram shows the <strong>last foreground</strong> snapshot; it does not repaint on every headless eval tick.</li>
				</ul>
			</div>
			
			<div class="bg-blue-50 border-2 border-blue-200 rounded p-4">
				<h3 class="font-bold text-blue-900 mb-2">🏗️ Network architecture</h3>
				<p class="text-sm text-blue-800 leading-relaxed">
					<strong>Input:</strong> 80 values — 7×10 tile vision plus row encoding<br>
					<strong>Hidden:</strong> 9 neurons, ReLU<br>
					<strong>Output:</strong> 6 actions (LEFT, RIGHT, A, B, filtered UP/DOWN)<br>
					<strong>Population:</strong> 100 agents evolved each step; all logic runs in Python via PyScript.
				</p>
			</div>
			
			<div class="bg-violet-50 border-2 border-violet-200 rounded p-4">
				<h3 class="font-bold text-violet-900 mb-2">🐍 Python & data flow</h3>
				<p class="text-sm text-violet-900 leading-relaxed">
					The trainer emits progress (generation, fitness, distance), optional breeding lineage JSON for the helix,
					and tensor snapshots for the neuron view. The UI never guesses evolution details — it reflects what the
					backend reported for the last generation.
				</p>
			</div>
		</div>
	</div>
</ExperimentCard>