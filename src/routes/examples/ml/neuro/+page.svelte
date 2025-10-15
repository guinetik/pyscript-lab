<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NesEmulator from '$lib/nes/NesEmulator.svelte';
	import NeuralNetworkViz from '$lib/components/NeuralNetworkViz.svelte';
	import { NeuroController } from '$lib/controller/NeuroController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { createLogger } from '@guinetik/logger';
	import {getLink} from '$lib/utils.js';

	const logger = createLogger({
		prefix: 'NeuroPage',
		level: 'debug'
	});

	// Page metadata
	let name = 'Neuroevolution';

	// Controller instance
	let controller = browser ? new NeuroController() : null;

	// UI State
	let status = $state('initializing'); // 'initializing' | 'ready' | 'training' | 'playing' | 'paused' | 'error'
	let statusMessage = $state('Initializing emulator...');
	let episode = $state(0);
	let totalReward = $state(0);
	let highScore = $state(0);

	// Neural Network selection
	let selectedNetwork = $state('simple-4button');

	// Available neural networks
	const neuralNetworks = [
		{ id: 'simple-4button', name: '🔥 Simple 4-Button (Recommended)', description: 'Simplified controls: LEFT, RIGHT, JUMP, RUN. Faster learning!' },
		{ id: 'simple-feedforward', name: 'Simple 6-Button (Full)', description: 'Full controls including UP/DOWN (rarely useful in Mario)' },
		{ id: 'conv-4button', name: 'CNN 4-Button', description: 'Convolutional network with simplified controls' },
		{ id: 'conv', name: 'CNN 6-Button', description: 'Convolutional network with full controls' },
	];

	// Emulator state
	let emulatorReady = false;
	let savedState = $state(null); // Store saved state in memory
	let hasState = $state(false);
	let emulatorKey = $state(0); // Key to force emulator remount
	let isMuted = $state(false); // Audio mute state

	// CTA state - show overlay until first training starts
	let hasStartedTraining = $state(false);

	// Neural network visualization state
	let networkVizData = $state(null);
	let vizEnabled = $state(false);

	onMount(async () => {
		if (!browser || !controller) return;

		logger.log('🎮 RL Page mounted');

		// Expose UI handler for Python to call
		window.rlUIHandler = {
			onPythonReady: () => {
				logger.log('✅ Python RL module is ready!');
			},

			onStatusUpdate: (newStatus, message) => {
				logger.log('🟢 Status update:', newStatus, message);
				status = newStatus;
				statusMessage = message;
			},

			onMetricsUpdate: (episodeNum, reward, high) => {
				logger.log('🟢 Metrics update:', { episodeNum, reward, high });
				episode = episodeNum;
				totalReward = reward;
				highScore = high;
			},

			onError: (message) => {
				logger.error('🔴 Error:', message);
				status = 'error';
				statusMessage = message;
			}
		};

		// Expose save/load state functions for Python
		window.saveStateJS = saveState;
		window.loadStateJS = loadState;

		// Expose network visualization callback for Python
		window.onNetworkVisualization = (data) => {
			logger.log('📊 Received network visualization data:', data);
			networkVizData = data;
		};

		// Initialize controller (loads both Python modules)
		await controller.initialize();
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		controller.destroy();
	});

	async function handleEmulatorReady(emulator) {
		logger.log('✅ [JS] NES Emulator ready!', emulator);
		logger.log('   Is loaded:', emulator.isLoaded());
		logger.log('   NES object:', emulator.nes);
		emulatorReady = true;

		statusMessage = 'Emulator ready. Click "Play Game" to test or "Start Training" to begin AI learning.';
		status = 'ready';

		// Check if we should auto-start playing after restart
		const autoplay = sessionStorage.getItem('rl_autoplay');
		if (autoplay === 'true') {
			sessionStorage.removeItem('rl_autoplay');
			logger.log('🎮 Auto-starting manual play after restart');
			// Small delay to ensure everything is ready
			setTimeout(() => playManual(), 100);
		}
	}

	function handleEmulatorError(error) {
		console.error('❌ [JS] Emulator error:', error);
		status = 'error';
		statusMessage = `Error: ${error.message}`;
	}

	function startTraining() {
		logger.log('🔵 [JS] startTraining() called with network:', selectedNetwork);

		if (!browser || !controller) return;

		if (!emulatorReady) {
			alert('Emulator not ready yet!');
			return;
		}

		// Hide CTA after first training start
		hasStartedTraining = true;

		// If already running (playing or training), nuke and recreate emulator
		const emulator = window.nesEmulator;
		if (emulator && emulator.isRunning()) {
			logger.log('🔄 Full restart: destroying and recreating emulator');
			status = 'initializing';
			statusMessage = 'Restarting emulator...';
			emulatorReady = false;
			emulatorKey++; // Force NesEmulator component to remount
			// Wait for emulator to be ready again before starting training
			// The handleEmulatorReady will be called when new instance is ready
			return;
		}

		// Pass selected neural network to Python
		controller.startTraining(selectedNetwork);
	}

	function pauseGame() {
		logger.log('⏸️ [JS] pauseGame() called');

		const emulator = window.nesEmulator;
		if (emulator && emulator.isRunning()) {
			emulator.stop();

			// If training was running, notify Python
			if (status === 'training' && controller) {
				controller.pauseTraining();
			}

			// Update status
			if (status === 'playing') {
				status = 'ready';
				statusMessage = 'Manual play paused. Click Play Game to resume.';
			} else if (status === 'training') {
				status = 'paused';
				statusMessage = 'Training paused. Click Start Training to resume.';
			}
		}
	}

	function toggleMute() {
		isMuted = !isMuted;
		logger.log(`🔊 ${isMuted ? 'Muting' : 'Unmuting'} audio`);

		const emulator = window.nesEmulator;
		if (emulator && emulator.controller && emulator.controller.speakers) {
			const speakers = emulator.controller.speakers;
			if (speakers.audioContext) {
				// Create gain node if it doesn't exist
				if (!speakers.gainNode) {
					speakers.gainNode = speakers.audioContext.createGain();
					speakers.scriptNode.disconnect();
					speakers.scriptNode.connect(speakers.gainNode);
					speakers.gainNode.connect(speakers.audioContext.destination);
				}

				// Set gain (0 = muted, 1 = full volume)
				speakers.gainNode.gain.value = isMuted ? 0 : 1;
			}
		}
	}

	function resetTraining() {
		if (!browser || !controller) return;

		// Reset UI stats immediately
		episode = 0;
		totalReward = 0;
		highScore = 0;

		// Reset visualization
		networkVizData = null;
		vizEnabled = false;

		// Call controller reset
		controller.resetTraining();
	}

	function toggleVisualization() {
		if (!browser || !window.toggleNetworkVisualization) return;

		vizEnabled = !vizEnabled;
		window.toggleNetworkVisualization(vizEnabled);
		logger.log(`🎨 Network visualization ${vizEnabled ? 'ENABLED' : 'DISABLED'}`);
	}

	function playManual() {
		logger.log('🔵 [JS] playManual() called');

		if (!emulatorReady) {
			alert('Emulator not ready yet!');
			return;
		}

		const emulator = window.nesEmulator;
		if (emulator) {
			// If already playing, nuke and recreate emulator
			if (status === 'playing') {
				logger.log('🔄 Full restart: destroying and recreating emulator');
				status = 'initializing';
				statusMessage = 'Restarting emulator...';
				emulatorReady = false;
				emulatorKey++; // Force NesEmulator component to remount
				// After remount, handleEmulatorReady will be called and we'll auto-start playing
				// We'll use a flag to remember we want to play
				sessionStorage.setItem('rl_autoplay', 'true');
				return;
			}

			// Stop any training
			if (status === 'training' && window.pauseRLTraining) {
				window.pauseRLTraining();
			}

			// Enable keyboard controls and start
			emulator.enableKeyboard();
			logger.log('▶️ Starting emulator for manual play');
			emulator.start();

			status = 'playing';
			statusMessage = 'Manual play mode active! Use keyboard to control the Character.';
		}
	}

	function saveState() {
		logger.log('💾 [JS] saveState() called');

		const emulator = window.nesEmulator;
		if (emulator && emulator.controller) {
			const stateObj = emulator.controller.saveState();
			if (stateObj) {
				// nes.toJSON() returns an object, we need to stringify it
				const stateJson = JSON.stringify(stateObj, null, 2);

				// Save stringified version to memory
				savedState = stateJson;
				hasState = true;

				// Print JSON to console for copying
				logger.log('📋 State saved! Size:', stateJson.length, 'bytes');
				logger.log('First 500 chars:', stateJson.substring(0, 500));

				// Download as file
				try {
					const blob = new Blob([stateJson], { type: 'application/json' });
					const url = URL.createObjectURL(blob);
					const a = document.createElement('a');
					a.href = url;
					a.download = 'nes_state.json';
					a.click();
					URL.revokeObjectURL(url);
					statusMessage = `State saved! (${(stateJson.length / 1024).toFixed(0)}KB) Check downloads.`;
				} catch (error) {
					console.error('Could not download file:', error);
					statusMessage = 'State JSON printed to console';
				}
			}
		}
	}

	function loadState() {
		logger.log('📂 [JS] loadState() called - opening file picker');

		// Create file input for picking JSON file
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json,application/json';

		input.onchange = async (e) => {
			const file = e.target.files[0];
			if (!file) {
				logger.log('No file selected');
				return;
			}

			try {
				// Read file contents as text
				const text = await file.text();

				// Parse JSON to validate and get object
				const stateObj = JSON.parse(text);

				// Save stringified version to memory
				savedState = text;
				hasState = true;

				logger.log('✅ State file parsed:', (text.length / 1024).toFixed(0), 'KB');
				statusMessage = `State loaded from ${file.name}! Applying...`;

				// Immediately apply the state to the emulator if it's ready
				const emulator = window.nesEmulator;
				if (emulator && emulator.controller && emulator.controller.isLoaded) {
					// fromJSON expects an object, not a string
					const loaded = emulator.controller.loadState(stateObj);
					if (loaded) {
						logger.log('✅ State applied to emulator');
						statusMessage = `State from ${file.name} applied! Game resumed.`;
					} else {
						logger.log('⚠️ Failed to apply state to emulator');
						statusMessage = `State loaded but couldn't be applied. Emulator may not be ready.`;
					}
				} else {
					statusMessage = `State loaded. Start the game to apply it.`;
				}
			} catch (error) {
				console.error('❌ Failed to load state file:', error);
				statusMessage = `Error loading state: ${error.message}`;
			}
		};

		// Trigger file picker
		input.click();
	}

	// Track previous network selection to detect changes
	let previousNetwork = $state(selectedNetwork);

	// Watch for neural network changes
	$effect(() => {
		if (selectedNetwork !== previousNetwork && previousNetwork !== null) {
			logger.log('🔄 Neural network changed:', previousNetwork, '→', selectedNetwork);

			// Reset training stats when switching networks
			episode = 0;
			totalReward = 0;
			highScore = 0;

			// If training is active, notify user they need to restart
			if (status === 'training') {
				status = 'paused';
				statusMessage = '⚠️ Neural network changed. Click "Start Training" to train with new model.';
				if (controller) {
					controller.pauseTraining();
				}
			}

			previousNetwork = selectedNetwork;
		}
	});

	// Computed status display
	$effect(() => {
		logger.log('Status changed:', status, statusMessage);
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/sentiment', nextPage: '/' }}>
	<div slot="py_slot" class="flex h-full flex-col p-5 space-y-4">
		<!-- Emulator Display with CTA Overlay -->
		<div class="flex justify-center relative">
			{#key emulatorKey}
				<NesEmulator
					romPath={getLink('data/package.nes')}
					scale={2}
					onReady={handleEmulatorReady}
					onError={handleEmulatorError}
				/>
			{/key}

			<!-- CTA Overlay - Only shows before first training -->
			{#if !hasStartedTraining && status === 'ready'}
				<div class="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-lg">
					<button
						onclick={startTraining}
						class="px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-xl font-bold rounded-xl shadow-2xl hover:from-green-600 hover:to-emerald-700 transform hover:scale-105 transition-all duration-200 flex items-center gap-3"
					>
						<span class="text-2xl">🧬</span>
						<span>Start Evolution!</span>
					</button>
				</div>
			{/if}
		</div>

		<!-- Neural Network Visualization -->
		{#if vizEnabled}
			<NeuralNetworkViz bind:vizData={networkVizData} />
		{/if}

		<!-- Metrics Display -->
		<div class="grid grid-cols-3 gap-3">
			<div class="rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">Generation</div>
				<div class="text-3xl font-bold">{episode}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-green-500 to-green-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">Fitness</div>
				<div class="text-3xl font-bold">{totalReward.toFixed(1)}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">Best Distance</div>
				<div class="text-3xl font-bold">{highScore.toFixed(1)}</div>
			</div>
		</div>

		<!-- Status Display -->
		<div
			class="rounded border-2 p-4 {status === 'error'
				? 'bg-red-50 border-red-200'
				: status === 'training'
					? 'bg-green-50 border-green-200'
					: status === 'playing'
						? 'bg-purple-50 border-purple-200'
						: status === 'paused'
							? 'bg-yellow-50 border-yellow-200'
							: status === 'ready'
								? 'bg-blue-50 border-blue-200'
								: 'bg-gray-50 border-gray-200'}"
		>
			<p
				class="text-sm font-mono {status === 'error'
					? 'text-red-700'
					: status === 'training'
						? 'text-green-700'
						: status === 'playing'
							? 'text-purple-700'
							: status === 'paused'
								? 'text-yellow-700'
								: status === 'ready'
									? 'text-blue-700'
									: 'text-gray-600'}"
			>
				{statusMessage}
			</p>
		</div>

		<!-- Control Buttons -->
		<div class="space-y-3">
			<!-- Row 1: Start Training + Neural Network Selector + Reset -->
			<div class="grid grid-cols-[1fr_2fr_1fr] gap-3">
				<button
					onclick={startTraining}
					disabled={status === 'initializing'}
					class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'training' ? '🔄 Restart' : '▶️ Start Training'}
				</button>
				<select
					bind:value={selectedNetwork}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded border-2 border-gray-300 bg-white px-4 py-3 font-semibold text-gray-700 hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
				>
					{#each neuralNetworks as network}
						<option value={network.id}>{network.name}</option>
					{/each}
				</select>
				<button
					onclick={resetTraining}
					disabled={status === 'initializing'}
					class="rounded bg-red-500 px-6 py-3 font-bold text-white hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🔄 Reset
				</button>
			</div>

			<!-- Row 2: Utility buttons bar (Play, Pause, Mute, Save, Load, Visualize) -->
			<div class="grid grid-cols-6 gap-2">
				<button
					onclick={playManual}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-purple-500 px-3 py-2 text-sm font-semibold text-white hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🎮 Play
				</button>
				<button
					onclick={pauseGame}
					disabled={status !== 'training' && status !== 'playing'}
					class="rounded bg-yellow-500 px-3 py-2 text-sm font-semibold text-white hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					⏸️ Pause
				</button>
				<button
					onclick={toggleMute}
					disabled={status === 'initializing'}
					class="rounded bg-orange-500 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{isMuted ? '🔇' : '🔊'}
				</button>
				<button
					onclick={saveState}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-blue-500 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					💾 Save
				</button>
				<button
					onclick={loadState}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-cyan-500 px-3 py-2 text-sm font-semibold text-white hover:bg-cyan-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					📂 Load{hasState ? '✓' : ''}
				</button>
				<button
					onclick={toggleVisualization}
					disabled={status === 'initializing'}
					class="rounded px-3 py-2 text-sm font-semibold text-white transition-colors {vizEnabled ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'} disabled:bg-gray-400 disabled:cursor-not-allowed"
				>
					{vizEnabled ? '🎨 Viz✓' : '🎨 Viz'}
				</button>
			</div>
		</div>

		<!-- Keyboard Controls (only show when playing) -->
		{#if status === 'playing'}
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 p-4 text-white shadow-lg">
				<h3 class="mb-3 text-lg font-bold">⌨️ Keyboard Controls</h3>
				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<div class="font-semibold">Arrow Keys</div>
						<div class="opacity-90">Move Character</div>
					</div>
					<div>
						<div class="font-semibold">Z</div>
						<div class="opacity-90">Jump (Button A)</div>
					</div>
					<div>
						<div class="font-semibold">X</div>
						<div class="opacity-90">Run/Fire (Button B)</div>
					</div>
					<div>
						<div class="font-semibold">Enter</div>
						<div class="opacity-90">Start/Pause</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Technical Info Sections -->
		<div class="space-y-3">
			<!-- NEUROEVOLUTION -->
			<div class="rounded-lg bg-purple-50 p-3 border-2 border-purple-200">
				<h3 class="mb-2 text-base font-bold text-purple-900">🧬 What is Neuroevolution?</h3>
				<p class="text-xs text-purple-800 mb-2">
					<strong>Neuroevolution</strong> is a method of training neural networks using principles from biological evolution. Instead of traditional learning algorithms (like backpropagation), it mimics natural selection:
				</p>
				<ol class="list-decimal space-y-1 pl-5 text-xs text-purple-800">
					<li><strong>Initialize:</strong> Create a neural network with random weights</li>
					<li><strong>Evaluate:</strong> Test the network by playing a game episode and measuring performance (fitness)</li>
					<li><strong>Mutate:</strong> Randomly modify the weights (like genetic mutations)</li>
					<li><strong>Select:</strong> Keep networks that perform well, discard poor performers (survival of the fittest)</li>
					<li><strong>Repeat:</strong> Continue until the network discovers winning strategies</li>
				</ol>
			</div>

			<!-- Network Architecture -->
			<div class="rounded-lg bg-blue-50 p-3 border-2 border-blue-200">
				<h3 class="mb-2 text-base font-bold text-blue-900">🏗️ Network Architecture</h3>
				<p class="text-xs text-blue-800 mb-2">
					<strong>4-Button Networks (Recommended):</strong> Output only essential buttons (LEFT, RIGHT, JUMP, RUN). UP/DOWN disabled since they're rarely useful in Mario 1-1. 33% smaller action space = faster evolution and less wasted exploration!
				</p>
				<p class="text-xs text-blue-800 mb-2">
					<strong>Simple Feedforward:</strong> 120 inputs → 32 hidden (ReLU) → 4/6 outputs (Sigmoid). Fixed 3-layer topology. 4-button version has ~2,758 weights vs 6-button's ~4,070 weights. Best for quick convergence.
				</p>
				<p class="text-xs text-blue-800 mb-2">
					<strong>Convolutional (CNN):</strong> 16×7 vision grid → 4 conv filters (3×3 kernels) → 280 features → 32 hidden → 4/6 outputs. Preserves spatial structure to detect patterns like gaps, enemies, and platforms. Better for visual pattern recognition.
				</p>
				<p class="text-xs text-blue-800 mt-2">
					<strong>Behavioral Priors:</strong> Networks initialize with smart biases: RIGHT (+1.0), A/Jump (+1.5), B/Run (+1.0), LEFT (-2.0). 6-button also has UP/DOWN (-10.0) heavily discouraged. Gives intelligent starting behavior!
				</p>
				<p class="text-xs text-blue-800 mt-2">
					<strong>Top-3 Button Cap:</strong> Action decoder limits simultaneous button presses to 3 max, preventing input conflicts (LEFT+RIGHT) and ensuring prioritization. Conflict resolution automatically zeros out weaker opposing directional inputs.
				</p>
			</div>

			<!-- Vision System -->
			<div class="rounded-lg bg-indigo-50 p-3 border-2 border-indigo-200">
				<h3 class="mb-2 text-base font-bold text-indigo-900">👁️ Vision System (16×7 Grid)</h3>
				<p class="text-xs text-indigo-800 mb-1">
					The agent extracts game state from NES RAM into a <strong>16×7 tile grid</strong> centered on Mario:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs text-indigo-800">
					<li><strong>Horizontal:</strong> 4 tiles behind, 11 tiles ahead (optimal lookahead for jump planning)</li>
					<li><strong>Vertical:</strong> 3 above, 1 current row, 3 below (sufficient vertical awareness)</li>
					<li><strong>Tile Encoding:</strong> Empty (0.0), Solid blocks (1.0), Enemies (-1.0)</li>
					<li><strong>Context Features:</strong> +8 engineered inputs (enemy_left_dist, enemy_right_dist, ground_dist, pit_dist, obstacle_dist, is_on_ground, y_position, enemy_nearby)</li>
					<li><strong>Total Input:</strong> 112 vision + 8 context = 120 values per decision</li>
				</ul>
				<p class="text-xs text-indigo-800 mt-2">
					For CNN: Vision reshaped to 7×16 2D grid before conv layers. For feedforward/NEAT: Flattened to 1D then concatenated with context.
				</p>
			</div>

			<!-- Fitness & Evolution -->
			<div class="rounded-lg bg-amber-50 p-3 border-2 border-amber-200">
				<h3 class="mb-2 text-base font-bold text-amber-900">🏆 Fitness Function & Evolution Strategy</h3>
				<p class="text-xs text-amber-800 mb-1">
					<strong>Fitness Formula:</strong> distance<sup>1.5</sup> + (score × 2) + milestones - death_penalties
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs text-amber-800">
					<li><strong>Distance Rewards:</strong> Exponential (x<sup>1.5</sup>) to heavily favor progress right</li>
					<li><strong>Score Multiplier:</strong> 2× for enemy stomps (encourages combat over avoidance)</li>
					<li><strong>Milestone Bonuses:</strong> +200 at 50px, +500 at 100px, +1000 at 200px, +2000 at 400px, +5000 at 800px</li>
					<li><strong>Death Penalties:</strong> -50 for enemy hits, -100 for getting stuck (no progress for 60 frames)</li>
					<li><strong>Adaptive Mutation:</strong> 0.05 rate when improving fitness, 0.1 normal, 0.3 when performance drops or stuck</li>
					<li><strong>Elite Preservation:</strong> Best network saved as "champion", restored if fitness drops below 30% of best</li>
					<li><strong>Local Minima Escape:</strong> Full reset with priors after 5 consecutive generations at same distance</li>
				</ul>
			</div>

			<!-- Technical Architecture -->
			<div class="rounded-lg bg-red-50 p-3 border-2 border-red-200">
				<h3 class="mb-2 text-base font-bold text-red-900">⚡ Technical Architecture</h3>
				<ul class="list-disc space-y-1 pl-5 text-xs text-red-800">
					<li><strong>PyScript 2025.2.1:</strong> Runs Python natively via WebAssembly (Pyodide)</li>
					<li><strong>JSNES:</strong> NES emulator in JavaScript running at 60fps</li>
					<li><strong>Modular Python:</strong> GameController (emulator interactions) + NeuralController (abstract network interface) + PlayerAgent (training loop orchestration)</li>
					<li><strong>NumPy:</strong> Matrix operations for neural network forward passes and mutations</li>
					<li><strong>Event-Driven:</strong> Python sends data-only to JavaScript via <code>window</code> callbacks, Svelte handles all UI rendering reactively</li>
					<li><strong>Decision Rate:</strong> ~15 decisions/second (67ms intervals) to balance performance and responsiveness</li>
					<li><strong>Progressive Timeout:</strong> Starts at 30s per generation, increases by 10s each generation (capped at 200s)</li>
					<li>All computation happens <strong>client-side</strong> in your browser - no servers, no cloud! Your CPU trains the AI.</li>
				</ul>
			</div>
		</div>

		<!-- Hidden Python script containers -->
		<div id="neural-script" style="display: none;"></div>
		<div id="player-script" style="display: none;"></div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none space-y-4">
			<p class="text-sm">
				Watch an AI agent learn to play Super Mario Bros through <strong>neuroevolution</strong> - evolving neural networks that discover winning strategies through trial and error!
			</p>

			<!-- HOW TO USE (Always first) -->
			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-cyan-900">🎯 How to Use</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-cyan-800">
					<li><strong>Click "Start Evolution":</strong> Begin training immediately! The default 4-button network learns faster than full controls.</li>
					<li><strong>Choose Network Type:</strong> Default is 4-button (recommended) for faster learning. Can switch to 6-button for full controls or CNN for spatial pattern recognition.</li>
					<li><strong>Toggle Visualization (🎨 Viz):</strong> Click to see live neural network activations! Watch neurons light up as the network processes vision and makes decisions.</li>
					<li><strong>Play Game:</strong> Try playing yourself first to appreciate the difficulty - use arrow keys, Z (jump), X (run).</li>
					<li><strong>Watch Metrics:</strong> Generation counts evolution cycles, Fitness shows current performance, Best Distance is furthest progress.</li>
					<li><strong>Observe Vision:</strong> Open browser console (F12) to see the network's 16×7 tile grid vision, updated every 5 seconds.</li>
					<li><strong>Utility Buttons:</strong> Use Play, Pause, Mute, Save/Load State for testing and checkpointing.</li>
				</ol>
				<p class="mt-3 text-xs text-cyan-700">
					💡 <strong>Pro Tip:</strong> 4-button networks have 32% fewer parameters and 75% smaller action space - they evolve winning strategies much faster!
				</p>
			</div>

			<!-- NEURAL NETWORKS -->
			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">🧠 Neural Network Basics</h3>
				<p class="text-sm text-green-800 mb-2">
					A <strong>neural network</strong> is a computational model inspired by biological brains. It consists of layers of artificial neurons that process information:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
					<li><strong>Input Layer:</strong> Receives raw data (in our case, Mario's vision of the game world)</li>
					<li><strong>Hidden Layers:</strong> Process and transform the data through mathematical operations</li>
					<li><strong>Output Layer:</strong> Produces decisions (which buttons to press)</li>
				</ul>
				<p class="text-sm text-green-800 mt-2">
					Each neuron connection has a <strong>weight</strong> - a number that determines how much influence one neuron has on another. Learning means adjusting these weights to make better decisions.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/ml/rl/agent.py"
				target="_blank">View source (agent.py)</a
			>
		</p>
	</article>
</ExperimentCard>
