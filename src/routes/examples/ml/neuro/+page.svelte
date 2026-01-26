<script>
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NeuralNetworkViz from '$lib/components/NeuralNetworkViz.svelte';
	import MetricsChart from '$lib/components/MetricsChart.svelte';
	import { NeuroController } from '$lib/controller/NeuroController.js';

	// === State ===
	let canvas;
	let controller = null;
	
	// UI state
	let mode = $state('idle'); // 'idle' | 'playing' | 'ai' | 'training'
	let status = $state('Click a button to begin');
	let muted = $state(true);
	
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
	let networkVizData = $state(null);
	
	// Metrics history for chart
	let metricsHistory = $state([]);
	
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
		
		await controller.startTraining();
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
		
		<!-- Secondary Controls -->
		<div class="grid grid-cols-4 gap-2">
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
		</div>
		
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
		<h2 class="text-xl font-bold">Mario AI - Neuroevolution</h2>
		
		<!-- Neural Network Visualization -->
		{#if showNeurons}
			<NeuralNetworkViz bind:vizData={networkVizData} />
		{/if}
		
		<!-- Metrics Chart -->
		{#if showMetrics}
			<MetricsChart metricsHistory={metricsHistory} />
		{/if}
		
		<!-- Info Sections -->
		<div class="space-y-3">
			<!-- What is Neuroevolution -->
			<div class="bg-purple-50 border-2 border-purple-200 rounded p-4">
				<h3 class="font-bold text-purple-900 mb-2">🧬 What is Neuroevolution?</h3>
				<p class="text-sm text-purple-800">
					<strong>Neuroevolution</strong> trains neural networks using genetic algorithms instead of 
					traditional backpropagation. Networks "evolve" through mutation and selection - just like 
					biological evolution!
				</p>
				<ol class="list-decimal pl-5 mt-2 text-sm text-purple-800 space-y-1">
					<li><strong>Create</strong> random neural network weights</li>
					<li><strong>Evaluate</strong> by playing the game (fitness = distance traveled)</li>
					<li><strong>Select</strong> the best performers</li>
					<li><strong>Mutate</strong> weights to create new generation</li>
					<li><strong>Repeat</strong> until it beats the level!</li>
				</ol>
			</div>
			
			<!-- Network Architecture -->
			<div class="bg-blue-50 border-2 border-blue-200 rounded p-4">
				<h3 class="font-bold text-blue-900 mb-2">🏗️ Network Architecture</h3>
				<p class="text-sm text-blue-800">
					<strong>Input:</strong> 80 values (7×10 tile vision + 10 row encoding)<br>
					<strong>Hidden:</strong> 9 neurons with ReLU activation<br>
					<strong>Output:</strong> 6 buttons (LEFT, RIGHT, A, B + filtered UP/DOWN)
				</p>
			</div>
			
			<!-- Training Pipeline -->
			<div class="bg-amber-50 border-2 border-amber-200 rounded p-4">
				<h3 class="font-bold text-amber-900 mb-2">⚡ Training Pipeline</h3>
				<p class="text-sm text-amber-800">
					<strong>Foreground:</strong> Shows best performer playing<br>
					<strong>Background:</strong> Runs population evaluation (headless, fast)<br>
					<strong>Python:</strong> Handles neural network evolution via PyScript
				</p>
			</div>
		</div>
	</div>
</ExperimentCard>