<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NesEmulator from '$lib/nes/NesEmulator.svelte';
	import NeuralNetworkViz from '$lib/components/NeuralNetworkViz.svelte';
	import { NeuroController } from '$lib/controller/NeuroController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { createLogger } from '@guinetik/logger';
	import {getLink} from '$lib/utils.js';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	const logger = createLogger({
		prefix: 'NeuroPage',
		level: 'debug'
	});

	// Get translated content
	const exampleText = exampleTranslationStore('ml-neuro');

	// Controller instance
	let controller = browser ? new NeuroController() : null;

	// UI State
	let status = $state('initializing'); // 'initializing' | 'ready' | 'training' | 'playing' | 'paused' | 'error'
	let statusMessage = $state('Initializing emulator...');
	let episode = $state(0);
	let totalReward = $state(0);
	let highScore = $state(0);

	// Neural Network selection (must match Python CONFIG['simple_controls'])
	// Currently hardcoded to 6-button in Python for reference weight compatibility
	let selectedNetwork = $state('simple-feedforward');

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
	let isMuted = $state(true); // Audio muted by default

	// CTA state - show overlay until first training starts
	let hasStartedTraining = $state(false);

	// Neural network visualization state
	let networkVizData = $state(null);
	let vizEnabled = $state(false);

	// Metrics chart state
	let metricsEnabled = $state(false);
	let metricsHistory = $state({
		generation: [],
		fitness: [],
		distance: []  // Distance achieved in each generation (can vary)
	});

	// Fitness normalization: divide raw fitness by this to get intuitive scale
	// Raw fitness formula: distance^1.8 - frames^1.4 + milestones + score×10
	// Milestones add huge constant (167,500 for full level)
	// Dividing by 500 brings fitness to similar range as distance (0-3266)
	const FITNESS_SCALE = 500;

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

		onMetricsUpdate: (episodeNum, reward, bestDistance, currentDistance) => {
			logger.log('🟢 Metrics update:', { episodeNum, reward, bestDistance, currentDistance });
			episode = episodeNum;
			totalReward = reward;
			highScore = bestDistance;  // Card shows cumulative best

			// ALWAYS update metrics history (even when chart hidden)
			// This ensures we have full history when user toggles chart on
			// Chart tracks currentDistance per generation (can vary)
			updateMetricsChart(episodeNum, reward, currentDistance);
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

		// Reapply mute state after emulator restart (with delay for audioContext initialization)
		setTimeout(() => applyMuteState(), 100);

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

		// If already running (playing or training), stop Python and recreate emulator
		const emulator = window.nesEmulator;
		if (emulator && emulator.isRunning()) {
			logger.log('🔄 Full restart: stopping Python and destroying emulator');

			// Stop Python training loop first
			if (status === 'training' && controller) {
				logger.log('🛑 Stopping Python training...');
				controller.stopTraining();
			}

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

		// Apply mute state after training starts (audioContext may be initialized now)
		setTimeout(() => applyMuteState(), 500);
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
		applyMuteState();
	}

	function applyMuteState() {
		const emulator = window.nesEmulator;
		if (emulator && emulator.controller && emulator.controller.speakers) {
			const speakers = emulator.controller.speakers;
			if (speakers.audioContext) {
				if (isMuted) {
					speakers.audioContext.suspend();
				} else {
					speakers.audioContext.resume();
				}
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

		// Reset metrics history
		metricsHistory = {
			generation: [],
			fitness: [],
			distance: []
		};

		// Call controller reset
		controller.resetTraining();
	}

	async function loadReferenceWeights() {
		if (!browser) return;
		
		logger.log('🏆 Loading reference weights (gen 1213, beats World 1-1)...');
		
		if (window.loadReferenceWeights) {
			try {
				const success = await window.loadReferenceWeights();
				if (success) {
					status = 'ready';
					statusMessage = '✅ Reference weights loaded! Click Train to test.';
					logger.log('✅ Reference weights loaded successfully');
				} else {
					statusMessage = '❌ Failed to load reference weights';
					logger.error('❌ Failed to load reference weights');
				}
			} catch (err) {
				logger.error('❌ Error loading reference weights:', err);
				statusMessage = '❌ Error: ' + err.message;
			}
		} else {
			logger.error('❌ loadReferenceWeights not available - Python not ready?');
			statusMessage = '❌ Python not ready. Wait and try again.';
		}
	}

	function toggleVisualization() {
		if (!browser || !window.toggleNetworkVisualization) return;

		vizEnabled = !vizEnabled;
		window.toggleNetworkVisualization(vizEnabled);
		logger.log(`🎨 Network visualization ${vizEnabled ? 'ENABLED' : 'DISABLED'}`);
	}

	function updateMetricsChart(generation, fitness, currentDistance) {
		// Normalize fitness to intuitive scale (divide by 500)
		// Example: fitness 701,520 → 1,403 (similar scale to distance 1,679)
		const normalizedFitness = fitness / FITNESS_SCALE;

		// DEBUG: Log what we're adding to history
		console.log('📊 Adding to history:', {
			generation,
			fitness: normalizedFitness,
			currentDistance
		});

		// Append to history
		metricsHistory.generation.push(generation);
		metricsHistory.fitness.push(normalizedFitness);
		metricsHistory.distance.push(currentDistance);  // Track per-generation distance

		// Update Bokeh ColumnDataSource via JavaScript API (only if chart is visible)
		if (metricsEnabled && window.Bokeh && window.Bokeh.documents) {
			try {
				// Get Bokeh document (first one, assuming single chart)
				const docs = window.Bokeh.documents;
				if (docs.length > 0) {
					const doc = docs[0];
					const roots = doc.roots();

					// Find ColumnDataSource and plot in the model
					for (const root of roots) {
						// Update data source
						const sources = root.select({ type: window.Bokeh.Models.ColumnDataSource });
						if (sources.length > 0) {
							const source = sources[0];

							// DEBUG: Log what we're sending to Bokeh
							console.log('📈 Updating Bokeh with data:', {
								generation: metricsHistory.generation.length,
								fitness: metricsHistory.fitness.length,
								distance: metricsHistory.distance.length,
								lastDistance: metricsHistory.distance[metricsHistory.distance.length - 1]
							});

							source.data = {
								generation: [...metricsHistory.generation],
								fitness: [...metricsHistory.fitness],
								distance: [...metricsHistory.distance]  // Per-gen distance (can go up/down)
							};

							// Auto-pan: update x_range to show last 20 generations (or all if less)
							const genCount = metricsHistory.generation.length;
							const startGen = Math.max(0, genCount - 20);
							const endGen = genCount;

							// Find the plot and update x_range
							if (root.x_range) {
								root.x_range.start = startGen;
								root.x_range.end = Math.max(endGen, 10); // Min 10 for visibility
							}

							logger.log(`📈 Chart updated (showing gens ${startGen}-${endGen})`);
							break;
						}
					}
				}
			} catch (error) {
				console.error('❌ Failed to update metrics chart:', error);
			}
		}
	}

	function toggleMetrics() {
		metricsEnabled = !metricsEnabled;
		logger.log(`📈 Metrics chart ${metricsEnabled ? 'ENABLED' : 'DISABLED'}`);

		// If enabling, update chart with full history immediately
		if (metricsEnabled && metricsHistory.generation.length > 0) {
			// Use setTimeout to ensure chart is visible first
			setTimeout(() => {
				if (window.Bokeh && window.Bokeh.documents) {
					try {
						const docs = window.Bokeh.documents;
						if (docs.length > 0) {
							const doc = docs[0];
							const roots = doc.roots();

							for (const root of roots) {
								const sources = root.select({ type: window.Bokeh.Models.ColumnDataSource });
								if (sources.length > 0) {
									const source = sources[0];
									source.data = {
										generation: [...metricsHistory.generation],
										fitness: [...metricsHistory.fitness],
										distance: [...metricsHistory.distance]
									};
									logger.log(`📈 Chart loaded with ${metricsHistory.generation.length} generations of history`);
									break;
								}
							}
						}
					} catch (error) {
						console.error('❌ Failed to load chart history:', error);
					}
				}
			}, 100);
		}
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

			// Apply mute state after starting manual play
			setTimeout(() => applyMuteState(), 200);
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

	// Get translated network labels
	function getNetworkLabel(networkId) {
		switch(networkId) {
			case 'simple-4button':
				return $exampleText.ui?.simple4ButtonRecommended || neuralNetworks[0].name;
			case 'simple-feedforward':
				return $exampleText.ui?.simpleFeedforward || neuralNetworks[1].name;
			case 'conv-4button':
				return $exampleText.ui?.conv4Button || neuralNetworks[2].name;
			case 'conv':
				return $exampleText.ui?.conv6Button || neuralNetworks[3].name;
			default:
				return 'Unknown';
		}
	}

	function getNetworkDescription(networkId) {
		switch(networkId) {
			case 'simple-4button':
				return $exampleText.ui?.simple4ButtonDesc || neuralNetworks[0].description;
			case 'simple-feedforward':
				return $exampleText.ui?.simpleFeedforwardDesc || neuralNetworks[1].description;
			case 'conv-4button':
				return $exampleText.ui?.conv4ButtonDesc || neuralNetworks[2].description;
			case 'conv':
				return $exampleText.ui?.conv6ButtonDesc || neuralNetworks[3].description;
			default:
				return 'Unknown';
		}
	}

	// Track previous network selection to detect changes
	// Initialize with literal value to avoid capturing only initial state
	let previousNetwork = $state('simple-feedforward');

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
		<!-- Emulator Display with CTA Overlay (full width to match stats) -->
		<div class="relative w-full">
			{#key emulatorKey}
				<NesEmulator
					romPath={getLink('data/package.nes')}
					scale={2}
					fullWidth={true}
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
						<span>{$exampleText.ui?.startButton || 'Start Evolution!'}</span>
					</button>
				</div>
			{/if}
			
			<!-- Background Training Overlay - Shows during headless population evaluation -->
			{#if status === 'background_training'}
				<div class="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm rounded-lg">
					<div class="text-center">
						<div class="animate-pulse text-6xl mb-4">🧬</div>
						<div class="text-white text-xl font-bold mb-2">Background Training</div>
						<div class="text-white/80 text-sm">{statusMessage}</div>
						<div class="mt-4 flex justify-center">
							<div class="w-48 h-2 bg-white/20 rounded-full overflow-hidden">
								<div class="h-full bg-gradient-to-r from-green-400 to-emerald-500 animate-pulse" style="width: 100%;"></div>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Metrics Display (always under the game) -->
		<div class="grid grid-cols-3 gap-3">
			<div class="rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">{$exampleText.ui?.generationLabel || 'Generation'}</div>
				<div class="text-3xl font-bold">{episode}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-green-500 to-green-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">{$exampleText.ui?.fitnessLabel || 'Fitness'}</div>
				<div class="text-3xl font-bold">{(totalReward / FITNESS_SCALE).toFixed(1)}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">{$exampleText.ui?.bestScoreLabel || 'Best Distance'}</div>
				<div class="text-3xl font-bold">{highScore.toFixed(1)}</div>
			</div>
		</div>

		<!-- Neural Network Visualization (below stats when enabled) -->
		{#if vizEnabled}
			<NeuralNetworkViz bind:vizData={networkVizData} />
		{/if}

		<!-- Metrics Chart (below neural viz when enabled) -->
		<div
			id="metrics-chart-container"
			class="rounded-lg border-2 border-gray-300 p-2 bg-white {metricsEnabled ? '' : 'hidden'}"
		></div>

		<!-- Status Display -->
		<div
			class="rounded border-2 p-4 {status === 'error'
				? 'bg-red-50 border-red-200'
				: status === 'background_training'
					? 'bg-emerald-50 border-emerald-300 animate-pulse'
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
					: status === 'background_training'
						? 'text-emerald-700'
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
					{status === 'training' ? ($exampleText.ui?.restartButton || '🔄 Restart') : ($exampleText.ui?.trainButton || '▶️ Train')}
				</button>
				<select
					bind:value={selectedNetwork}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded border-2 border-gray-300 bg-white px-4 py-3 font-semibold text-gray-700 hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
				>
					{#each neuralNetworks as network}
						<option value={network.id}>{getNetworkLabel(network.id)}</option>
					{/each}
				</select>
				<button
					onclick={resetTraining}
					disabled={status === 'initializing'}
					class="rounded bg-red-500 px-6 py-3 font-bold text-white hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{$exampleText.ui?.resetButton || '🔄 Reset'}
				</button>
			</div>

			<!-- Row 2: Utility buttons bar (Play, Pause, Mute, Save, Load, Reference, Visualize) -->
			<div class="grid grid-cols-8 gap-2">
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
					{$exampleText.ui?.pauseButton || '⏸️ Pause'}
				</button>
				<button
					onclick={toggleMute}
					disabled={status === 'initializing'}
					class="rounded bg-orange-500 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{isMuted ? ($exampleText.ui?.volumeOffButton || '🔇') : ($exampleText.ui?.volumeOnButton || '🔊')}
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
					onclick={loadReferenceWeights}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-amber-500 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
					title="Load pre-trained weights that beat World 1-1"
				>
					🏆 Ref
				</button>
				<button
					onclick={toggleVisualization}
					disabled={status === 'initializing'}
					class="rounded px-3 py-2 text-sm font-semibold text-white transition-colors {vizEnabled ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'} disabled:bg-gray-400 disabled:cursor-not-allowed"
				>
					{vizEnabled ? '🧠 Neurons✓' : '🧠 Neurons'}
				</button>
				<button
					onclick={toggleMetrics}
					disabled={status === 'initializing'}
					class="rounded px-3 py-2 text-sm font-semibold text-white transition-colors {metricsEnabled ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'} disabled:bg-gray-400 disabled:cursor-not-allowed"
				>
					{metricsEnabled ? '📈 Metrics✓' : '📈 Metrics'}
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
				<h3 class="mb-2 text-base font-bold text-purple-900">{$exampleText.sections?.whatIsNeuroevolution?.title || '🧬 What is Neuroevolution?'}</h3>
				<p class="text-xs text-purple-800 mb-2">
					<strong>{$exampleText.sections?.whatIsNeuroevolution?.title || 'Neuroevolution'}</strong> {$exampleText.sections?.whatIsNeuroevolution?.process || 'is a method of training neural networks using principles from biological evolution. Instead of traditional learning algorithms (like backpropagation), it mimics natural selection:'}
				</p>
				<ol class="list-decimal space-y-1 pl-5 text-xs text-purple-800">
					<li><strong>{$exampleText.sections?.howItWorks?.step1?.split(':')[0] || 'Initialize'}:</strong> {$exampleText.sections?.howItWorks?.step1?.split(':').slice(1).join(':') || 'Create a neural network with random weights'}</li>
					<li><strong>{$exampleText.sections?.howItWorks?.step3?.split(':')[0] || 'Evaluate'}:</strong> {$exampleText.sections?.howItWorks?.step2?.split(':').slice(1).join(':') || 'Test the network by playing a game episode and measuring performance (fitness)'}</li>
					<li><strong>{$exampleText.sections?.howItWorks?.step5?.split(':')[0] || 'Mutate'}:</strong> {$exampleText.sections?.howItWorks?.step5?.split(':').slice(1).join(':') || 'Randomly modify the weights (like genetic mutations)'}</li>
					<li><strong>{$exampleText.sections?.howItWorks?.step4?.split(':')[0] || 'Select'}:</strong> {$exampleText.sections?.howItWorks?.step4?.split(':').slice(1).join(':') || 'Keep networks that perform well, discard poor performers (survival of the fittest)'}</li>
					<li><strong>{$exampleText.sections?.howItWorks?.step6?.split(':')[0] || 'Repeat'}:</strong> {$exampleText.sections?.howItWorks?.step6?.split(':').slice(1).join(':') || 'Continue until the network discovers winning strategies'}</li>
				</ol>
			</div>

			<!-- Network Architecture -->
			<div class="rounded-lg bg-blue-50 p-3 border-2 border-blue-200">
				<h3 class="mb-2 text-base font-bold text-blue-900">{$exampleText.sections?.networkArchitectures?.title || '🏗️ Network Architecture'}</h3>
				<p class="text-xs text-blue-800 mb-2">
					{$exampleText.sections?.networkArchitectures?.simple || '<strong>Simple Networks:</strong> 2-3 layer feedforward networks, fast but limited'}
				</p>
				<p class="text-xs text-blue-800 mb-2">
					{$exampleText.sections?.networkArchitectures?.cnn || '<strong>Convolutional Networks (CNN):</strong> Process pixel input like human vision, slower but more powerful'}
				</p>
				<p class="text-xs text-blue-800 mb-2">
					<strong>{$exampleText.sections?.networkArchitectures?.input?.split(':')[0] || 'Input'}</strong>: {$exampleText.sections?.networkArchitectures?.input?.split(':').slice(1).join(':') || 'Game screen pixels (preprocessed to 84×84 grayscale)'}
				</p>
				<p class="text-xs text-blue-800 mt-2">
					<strong>{$exampleText.sections?.networkArchitectures?.output?.split(':')[0] || 'Output'}</strong>: {$exampleText.sections?.networkArchitectures?.output?.split(':').slice(1).join(':') || '4 or 6 buttons (LEFT, RIGHT, UP, DOWN, JUMP, RUN)'}
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
				<h3 class="mb-2 text-base font-bold text-red-900">{$exampleText.sections?.technicalDetails?.title || '⚡ Technical Architecture'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-xs text-red-800">
					<li>{$exampleText.sections?.technicalDetails?.emulator || '<strong>Emulator:</strong> NES.js (JavaScript NES emulator)'}</li>
					<li>{$exampleText.sections?.technicalDetails?.preprocessing || '<strong>Preprocessing:</strong> Screen capture → grayscale 84×84 → pixel normalization'}</li>
					<li>{$exampleText.sections?.technicalDetails?.population || '<strong>Population Size:</strong> 50 networks per generation'}</li>
					<li>{$exampleText.sections?.technicalDetails?.generationTime || '<strong>Generation Time:</strong> Varies by architecture (1-5 seconds)'}</li>
					<li>{$exampleText.sections?.technicalDetails?.mutation || '<strong>Mutation Rate:</strong> 10-20% of weights mutated per generation'}</li>
					<li>{$exampleText.sections?.technicalDetails?.convergence || '<strong>Convergence:</strong> Typically finds good strategy in 20-100 generations'}</li>
				</ul>
			</div>
		</div>

		<!-- Hidden Python script containers -->
		<div id="neural-script" style="display: none;"></div>
		<div id="player-script" style="display: none;"></div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{$exampleText.title || 'Neuroevolution - Mario Learns to Play'}</h2>

		<div class="prose max-w-none space-y-4">
			<p class="text-sm">
				{$exampleText.description || 'Watch a neural network evolve to play Super Mario Bros using genetic algorithms and neuroevolution. No manual training - just evolution!'}
			</p>

			<!-- HOW TO USE (Always first) -->
			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-cyan-900">{$exampleText.userGuide?.title || '📖 User Guide'}</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-cyan-800">
					<li>{$exampleText.userGuide?.selectNetwork?.replace(/^\d+\.\s*/, '') || 'Select a neural network architecture (Simple 4-Button recommended for first time)'}</li>
					<li>{$exampleText.userGuide?.startEvolution?.replace(/^\d+\.\s*/, '') || 'Click "Start Evolution" to begin'}</li>
					<li>{$exampleText.userGuide?.watchGeneration?.replace(/^\d+\.\s*/, '') || 'Watch each generation play'}</li>
					<li>{$exampleText.userGuide?.observe?.replace(/^\d+\.\s*/, '') || 'Observe fitness metrics and best score improvements'}</li>
					<li>{$exampleText.userGuide?.speedUp?.replace(/^\d+\.\s*/, '') || 'Use speed controls to fast-forward generations'}</li>
					<li>{$exampleText.userGuide?.playBest?.replace(/^\d+\.\s*/, '') || 'Click "Play Best" to watch the evolved champion play!'}</li>
				</ol>
				<p class="mt-3 text-xs text-cyan-700">
					{$exampleText.userGuide?.tip || '💡 Tip: Smaller networks train faster. Try Simple 4-Button first to understand the process!'}
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
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/ml/neural/agent.py"
				target="_blank">View source (agent.py)</a
			>
		</p>
	</article>
</ExperimentCard>
