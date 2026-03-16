<script>
	/**
	 * Grokking Neural Network Demo Page
	 * 
	 * Demonstrates the "grokking" phenomenon where neural networks
	 * suddenly generalize after an extended period of memorization.
	 */
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NeuralNetworkViz from '$lib/components/NeuralNetworkViz.svelte';
	import MetricsChart from '$lib/components/MetricsChart.svelte';
	import { GrokController } from '$lib/controller/GrokController.js';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	// Get translated content
	const exampleText = exampleTranslationStore('grokking');

	// === State ===
	let controller = null;
	
	// UI state
	let mode = $state('idle'); // 'idle' | 'loading' | 'training' | 'grokked'
	let status = $state('Click Start Training to begin');
	
	// Training state
	let epoch = $state(0);
	let trainAcc = $state(0);
	let testAcc = $state(0);
	let grokDetected = $state(false);
	let grokEpoch = $state(-1);
	
	// Visualization state
	let showNeurons = $state(true);
	let showMetrics = $state(true);
	let networkVizData = $state(null);
	
	// Metrics history for chart
	let metricsHistory = $state([]);
	
	// Test prediction state
	let testA = $state(23);
	let testB = $state(44);
	let predictionResult = $state(null);

	// Network config - original parameters that produce grokking
	const config = {
		n_tokens: 67,
		hidden_size: 64
	};

	// === Setup on mount ===
	onMount(async () => {
		if (!browser) return;

		controller = new GrokController();
		
		controller.setCallbacks({
			onProgress: (result) => {
				epoch = result.epoch;
				trainAcc = result.train_acc;
				testAcc = result.test_acc;
				grokDetected = result.grok_detected;
				grokEpoch = result.grok_epoch;
				
				// Update metrics history (keep last 200 points)
				metricsHistory = [...metricsHistory.slice(-199), {
					gen: result.epoch,
					fitness: result.train_acc * 100,
					distance: result.test_acc * 100
				}];
				
				// Update network visualization
				// Show Input(2) → Hidden(64) → Output(67) so labels are correct
				if (result.activations) {
					const h = config.hidden_size;  // 64
					const n = config.n_tokens;  // 67
					
					const hiddenValues = result.activations.hidden || [];
					const outputValues = result.activations.output || [];
					
					networkVizData = {
						layer_sizes: result.layer_sizes || [2, h, n],
						activations: [
							// Input: 2 token indices (a, b) - always "active"
							{ values: [1.0, 1.0], active_count: 2 },
							{ values: hiddenValues, active_count: hiddenValues.filter(v => v > 0.1).length },
							{ values: outputValues, active_count: outputValues.filter(v => v > 0.1).length }
						],
						// Parameters: embed(67x500) + W_hidden(500x64) + W_out(64x500)
						num_params: (n * 500) + (500 * h) + (h * 500)
					};
				}
			},
			onGrokDetected: (grokEpochNum) => {
				mode = 'grokked';
				status = `GROKKING DETECTED at epoch ${grokEpochNum}!`;
			},
			onStatus: (msg) => {
				status = msg;
			},
			onComplete: () => {
				if (mode !== 'grokked') {
					mode = 'idle';
				}
			},
			onError: (error) => {
				status = `Error: ${error.message || error}`;
				mode = 'idle';
			}
		});
	});
	
	// === Actions ===
	async function initializeAndTrain() {
		if (!controller) return;
		
		mode = 'loading';
		metricsHistory = [];
		grokDetected = false;
		grokEpoch = -1;
		epoch = 0;
		trainAcc = 0;
		testAcc = 0;
		
		const success = await controller.initialize();
		if (success) {
			mode = 'training';
			await controller.startTraining(50000);
		} else {
			mode = 'idle';
		}
	}

	function stop() {
		if (controller) {
			controller.stop();
		}
		mode = 'idle';
	}

	function reset() {
		if (controller) {
			controller.reset();
		}
		mode = 'idle';
		metricsHistory = [];
		networkVizData = null;  // Reset neuron visualization
		epoch = 0;
		trainAcc = 0;
		testAcc = 0;
		grokDetected = false;
		grokEpoch = -1;
		predictionResult = null;
		status = 'Network reset. Click Start Training to begin.';
	}

	function testPrediction() {
		if (!controller || !controller.initialized) {
			predictionResult = { error: 'Train the network first!' };
			return;
		}
		
		const result = controller.getPrediction(testA, testB);
		predictionResult = result;
	}
	
	// === Cleanup ===
	onDestroy(() => {
		if (controller) {
			controller.destroy();
		}
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/ml/neuro', nextPage: '/' }}>
	<div slot="py_slot" class="flex flex-col h-full p-4 space-y-4 overflow-y-auto">
		<!-- Status Bar -->
		<div class="px-4 py-2 rounded {grokDetected ? 'bg-green-100 border-2 border-green-400' : 'bg-gray-100 border-2 border-gray-300'}">
			<p class="text-sm font-mono {grokDetected ? 'text-green-800 font-bold' : ''}">
				{#if grokDetected}
					✨ {status}
				{:else}
					{status}
				{/if}
			</p>
		</div>
		
		<!-- Training Stats -->
		<div class="grid grid-cols-4 gap-2">
			<div class="bg-blue-500 text-white rounded p-3 text-center">
				<div class="text-xs opacity-75">Epoch</div>
				<div class="text-xl font-bold">{epoch}</div>
			</div>
			<div class="bg-orange-500 text-white rounded p-3 text-center">
				<div class="text-xs opacity-75">Train Acc</div>
				<div class="text-xl font-bold">{(trainAcc * 100).toFixed(1)}%</div>
			</div>
			<div class="rounded p-3 text-center text-white {grokDetected ? 'bg-green-500' : 'bg-purple-500'}">
				<div class="text-xs opacity-75">Test Acc</div>
				<div class="text-xl font-bold">{(testAcc * 100).toFixed(1)}%</div>
			</div>
			<div class="rounded p-3 text-center text-white {grokDetected ? 'bg-green-600 animate-pulse' : 'bg-gray-500'}">
				<div class="text-xs opacity-75">Grokked?</div>
				<div class="text-xl font-bold">{grokDetected ? `✓ ${grokEpoch}` : 'No'}</div>
			</div>
		</div>
		
		<!-- Main Control Buttons -->
		<div class="grid grid-cols-3 gap-3">
			<button 
				onclick={initializeAndTrain}
				disabled={mode === 'training' || mode === 'loading'}
				class="px-4 py-3 bg-green-500 text-white font-bold rounded hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				{mode === 'loading' ? '⏳ Loading...' : '🧠 Start Training'}
			</button>
			<button 
				onclick={stop}
				disabled={mode !== 'training'}
				class="px-4 py-3 bg-red-500 text-white font-bold rounded hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
			>
				⏹️ Stop
			</button>
			<button 
				onclick={reset}
				disabled={mode === 'loading'}
				class="px-4 py-3 bg-slate-500 text-white font-bold rounded hover:bg-slate-600 disabled:bg-gray-400 transition"
			>
				🔄 Reset
			</button>
		</div>
		
		<!-- Test Prediction -->
		<div class="bg-slate-100 rounded p-3 space-y-2">
			<h4 class="font-bold text-sm">Test Prediction: (a + b) mod {config.n_tokens}</h4>
			<div class="flex items-center gap-2">
				<input 
					type="number" 
					bind:value={testA} 
					min="0" 
					max={config.n_tokens - 1}
					class="w-16 px-2 py-1 border rounded text-center"
				/>
				<span class="font-bold">+</span>
				<input 
					type="number" 
					bind:value={testB} 
					min="0" 
					max={config.n_tokens - 1}
					class="w-16 px-2 py-1 border rounded text-center"
				/>
				<span class="font-bold">mod {config.n_tokens}</span>
				<button 
					onclick={testPrediction}
					class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
				>
					Predict
				</button>
			</div>
			{#if predictionResult}
				{#if predictionResult.error}
					<p class="text-red-600 text-sm">{predictionResult.error}</p>
				{:else}
					<p class="text-sm">
						<span class="font-mono">{predictionResult.a} + {predictionResult.b} = </span>
						<span class="font-bold {predictionResult.correct ? 'text-green-600' : 'text-red-600'}">
							{predictionResult.prediction}
						</span>
						<span class="text-gray-500">(target: {predictionResult.target})</span>
						{#if predictionResult.correct}
							<span class="text-green-600">✓</span>
						{:else}
							<span class="text-red-600">✗</span>
						{/if}
					</p>
				{/if}
			{/if}
		</div>

		<!-- Toggle Buttons -->
		<div class="flex gap-2">
			<button 
				onclick={() => showNeurons = !showNeurons}
				class="flex-1 px-3 py-2 text-white text-sm font-semibold rounded transition {showNeurons ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'}"
			>
				🧠 Network
			</button>
			<button 
				onclick={() => showMetrics = !showMetrics}
				class="flex-1 px-3 py-2 text-white text-sm font-semibold rounded transition {showMetrics ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'}"
			>
				📈 Metrics
			</button>
		</div>
		
		<!-- Neural Network Visualization -->
		{#if showNeurons}
			<NeuralNetworkViz bind:vizData={networkVizData} />
		{/if}
		
		<!-- Metrics Chart -->
		{#if showMetrics}
			<MetricsChart metricsHistory={metricsHistory} label1="Train Acc" label2="Test Acc" />
		{/if}
	</div>
	
	<div slot="content_slot" class="space-y-4">
		<h2 class="text-xl font-bold">{$exampleText.title || 'Grokking Neural Networks'}</h2>
		
		<!-- What is Grokking -->
		<div class="bg-purple-50 border-2 border-purple-200 rounded p-4">
			<h3 class="font-bold text-purple-900 mb-2">{$exampleText.sections?.whatIs?.title || '🧠 What is Grokking?'}</h3>
			<p class="text-sm text-purple-800">
				{$exampleText.sections?.whatIs?.description || 'Grokking is a fascinating phenomenon where neural networks suddenly "get it" after appearing to only memorize. The network first achieves 100% training accuracy (memorization), then much later, test accuracy suddenly jumps (generalization).'}
			</p>
		</div>
		
		<!-- The Task -->
		<div class="bg-blue-50 border-2 border-blue-200 rounded p-4">
			<h3 class="font-bold text-blue-900 mb-2">{$exampleText.sections?.task?.title || '➕ The Task: Modular Arithmetic'}</h3>
			<p class="text-sm text-blue-800">
				{$exampleText.sections?.task?.description || 'The network learns modular addition: (a + b) mod 67. For example, 45 + 30 mod 67 = 8. This seems simple, but discovering the underlying pattern (instead of memorizing) requires the network to learn the structure of modular arithmetic.'}
			</p>
			<div class="mt-2 p-2 bg-white rounded font-mono text-sm">
				(a + b) mod p = c
			</div>
		</div>
		
		<!-- Why it Happens -->
		<div class="bg-amber-50 border-2 border-amber-200 rounded p-4">
			<h3 class="font-bold text-amber-900 mb-2">{$exampleText.sections?.why?.title || '⚡ Why Does Grokking Happen?'}</h3>
			<p class="text-sm text-amber-800">
				{$exampleText.sections?.why?.description || 'The key is HIGH weight decay (regularization). Without it, networks just memorize. With strong weight decay, the network is pushed toward simpler solutions that generalize. This takes time - the "grokking" moment happens when the network finally discovers the generalizing solution.'}
			</p>
			<ul class="mt-2 list-disc pl-5 text-sm text-amber-800 space-y-1">
				<li><strong>Weight Decay = 1.0</strong> (very high!)</li>
				<li>Forces simpler weight patterns</li>
				<li>Memorization uses more "capacity"</li>
				<li>Generalization is more efficient</li>
			</ul>
		</div>
		
		<!-- The Timeline -->
		<div class="bg-green-50 border-2 border-green-200 rounded p-4">
			<h3 class="font-bold text-green-900 mb-2">{$exampleText.sections?.timeline?.title || '📊 The Grokking Timeline'}</h3>
			<ol class="list-decimal pl-5 text-sm text-green-800 space-y-1">
				<li><strong>Phase 1 - Memorization:</strong> Train accuracy quickly reaches ~100%</li>
				<li><strong>Phase 2 - Plateau:</strong> Test accuracy stays low (20-40%)</li>
				<li><strong>Phase 3 - Grokking:</strong> Suddenly, test accuracy jumps to ~100%!</li>
			</ol>
			<p class="mt-2 text-sm text-green-800 italic">
				{$exampleText.sections?.timeline?.note || 'This can take thousands of epochs. Be patient and watch the charts!'}
			</p>
		</div>
		
		<!-- Architecture -->
		<div class="bg-slate-50 border-2 border-slate-200 rounded p-4">
			<h3 class="font-bold text-slate-900 mb-2">{$exampleText.sections?.architecture?.title || '🏗️ Network Architecture'}</h3>
			<p class="text-sm text-slate-800">
				{$exampleText.sections?.architecture?.description || "Based on Google's Factored MLP with tied embeddings:"}
			</p>
			<ul class="mt-2 list-disc pl-5 text-sm text-slate-800 space-y-1">
				<li><strong>Input:</strong> Two tokens (a, b) embedded to 500 dimensions</li>
				<li><strong>Hidden:</strong> 64 neurons with ReLU activation</li>
				<li><strong>Output:</strong> 67 classes (one per possible result)</li>
				<li><strong>Tied weights:</strong> Same embedding for input and output</li>
				<li><strong>Optimizer:</strong> AdamW with weight decay = 1.0</li>
			</ul>
		</div>
		
		<!-- Technical Info -->
		<div class="bg-cyan-50 border-2 border-cyan-200 rounded p-4">
			<h3 class="font-bold text-cyan-900 mb-2">🔧 Technical: PyScript</h3>
			<p class="text-sm text-cyan-800">
				The neural network is implemented in pure Python, running via PyScript's Pyodide runtime directly in your browser. Training uses asyncio to yield control periodically, keeping the UI responsive. No server required!
			</p>
		</div>
		
		<p class="text-sm">
			<a
				class="text-sky-500 hover:text-sky-700"
				href="https://pair.withgoogle.com/explorables/grokking/"
				target="_blank"
			>
				Learn more about grokking from Google's interactive article →
			</a>
		</p>
	</div>
</ExperimentCard>
