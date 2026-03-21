<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import ContentSection from '$lib/components/ContentSection.svelte';
	import Callout from '$lib/components/Callout.svelte';
	import MazeCanvas from '$lib/components/MazeCanvas.svelte';
	import { MazeRLController } from '$lib/controller/MazeRLController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { exampleTranslationStore } from '$lib/i18n/exampleLoader.js';

	// Get translated content
	const exampleText = exampleTranslationStore('ml-rl');

	// Controller instance
	let controller = browser ? new MazeRLController() : null;

	// UI State
	let status = $state('initializing'); // 'initializing' | 'ready' | 'training' | 'paused' | 'error'
	let statusMessage = $state('Loading Python modules...');
	let pythonReady = $state(false);

	// Maze state
	let mazeData = $state(null);
	let agentPosition = $state({ row: 0, col: 0 });
	let startPosition = $state({ row: 0, col: 0 });
	let endPosition = $state({ row: 0, col: 0 });
	let qValues = $state(null);
	let showQValues = $state(false);

	// Maze settings
	let difficulty = $state('medium');
	let cellSize = $state(30);
	let canvasWidth = $state(450);
	let canvasHeight = $state(450);

	// Metrics
	let episode = $state(0);
	let steps = $state(0);
	let totalReward = $state(0);
	let epsilon = $state(1.0);
	let successRate = $state(0);

	// Demo completion overlay
	let showCompletionOverlay = $state(false);
	let demoResults = $state(null);

	// Demo countdown
	let showCountdown = $state(false);
	let countdown = $state(0);
	let isRunningDemo = $state(false);

	// Animation loop for agent tweening
	let animationFrameId = null;

	// Demo stuck detection
	let positionHistory = $state([]);
	const MAX_HISTORY = 10;
	const OSCILLATION_THRESHOLD = 3; // If same position appears 3+ times in recent history = stuck

	// Difficulty options
	const difficultySettings = {
		easy: { name: 'Easy (10×10)', rows: 10, cols: 10, cellSize: 40 },
		medium: { name: 'Medium (15×15)', rows: 15, cols: 15, cellSize: 30 },
		hard: { name: 'Hard (20×20)', rows: 20, cols: 20, cellSize: 25 },
		insane: { name: 'Insane (30×30)', rows: 30, cols: 30, cellSize: 20 }
	};

	// Function to get difficulty name
	function getDifficultyName(key) {
		return difficultySettings[key]?.name || key;
	}

	// Detect if agent is oscillating (stuck in a loop)
	function isAgentOscillating(position) {
		const posKey = `${position.row},${position.col}`;

		// Add current position to history
		positionHistory = [...positionHistory, posKey].slice(-MAX_HISTORY);

		// Count how many times current position appears in recent history
		const count = positionHistory.filter(p => p === posKey).length;

		console.log('[RL Page] Position history:', positionHistory, 'Current:', posKey, 'Count:', count);

		// If same position appears 3+ times in last 10 moves, agent is oscillating
		return count >= OSCILLATION_THRESHOLD;
	}

	// Animation loop for smooth agent movement
	function startAnimationLoop() {
		const animate = () => {
			if (controller && controller.actor) {
				// Update actor animation
				controller.actor.update();
				// Get interpolated position and update UI
				const currentPos = controller.actor.getCurrentPosition();
				agentPosition = {
					row: currentPos.row,
					col: currentPos.col
				};
			}
			animationFrameId = requestAnimationFrame(animate);
		};

		// Start the loop
		animationFrameId = requestAnimationFrame(animate);
	}

	function stopAnimationLoop() {
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
			animationFrameId = null;
		}
	}

	onMount(async () => {
		if (!browser || !controller) return;

		console.log('[RL Page] Mounted');

		// Start animation loop for smooth tweening
		startAnimationLoop();

		// Setup controller callbacks
		controller.callbacks.onMazeGenerated = (maze) => {
			console.log('[RL Page] Maze generated:', maze);
			mazeData = maze.grid;
			startPosition = maze.startPos;
			endPosition = maze.endPos;
			agentPosition = { ...maze.startPos };

			// Update canvas dimensions
			const settings = difficultySettings[difficulty];
			cellSize = settings.cellSize;
			canvasWidth = settings.cols * settings.cellSize;
			canvasHeight = settings.rows * settings.cellSize;

			statusMessage = $exampleText.ui?.generatedMessage || 'Maze generated! Click "Start Training" to begin Q-learning.';
		};

		controller.callbacks.onAgentMove = (data) => {
			console.log('[RL Page] Agent move:', data);
			if (data && data.position && controller && controller.actor) {
				const newPos = {
					row: typeof data.position.row === 'number' ? data.position.row : agentPosition.row,
					col: typeof data.position.col === 'number' ? data.position.col : agentPosition.col
				};

				// Check for oscillation during demo
				if (isRunningDemo && isAgentOscillating(newPos)) {
					console.log('[RL Page] 🔄 Agent oscillating detected! Stopping demo immediately...');
					// Stop demo immediately from Python
					if (controller.pythonExports && controller.pythonExports.stopDemo) {
						controller.pythonExports.stopDemo();
					}
					isRunningDemo = false;
					// Simulate demo complete with stuck state
					demoResults = {
						steps: data.steps,
						reward: data.reward,
						reachedGoal: false,
						elapsedTime: 0,
						oscillationDetected: true
					};
					showCompletionOverlay = true;
					statusMessage = $exampleText.ui?.stuckOscillatingMessage || '⏹️ Demo stopped - agent got stuck oscillating';
					return;
				}

				// Use tweening only in demo mode for smooth movement
				// During training, use instant position updates (frequent updates)
				if (status === 'ready') {
					// Demo mode: smooth tweening via animation loop
					controller.actor.setTarget(newPos);
				} else {
					// Training mode: instant updates, bypass tweening
					controller.actor.position = { ...newPos };
					controller.actor.targetPosition = { ...newPos };
					controller.actor.isMoving = false;
					agentPosition = newPos;
				}

				// Update metrics
				steps = typeof data.steps === 'number' ? data.steps : steps;
				totalReward = typeof data.reward === 'number' ? data.reward : totalReward;
			}
		};

		controller.callbacks.onMetricsUpdate = (metrics) => {
			console.log('[RL Page] Metrics received:', metrics, 'reward type:', typeof metrics?.reward, 'value:', metrics?.reward);
			if (metrics) {
				episode = metrics.episode ?? episode;
				steps = metrics.steps ?? steps;
				totalReward = typeof metrics.reward === 'number' ? metrics.reward : totalReward;
				epsilon = typeof metrics.epsilon === 'number' ? metrics.epsilon : epsilon;
				successRate = metrics.successRate ? parseFloat(metrics.successRate) : successRate;
				qValues = metrics.qValues ?? qValues;
			}
		};

		controller.callbacks.onEpisodeEnd = (episodeData) => {
			// Reset agent to start position
			agentPosition = { ...startPosition };
		};

		controller.callbacks.onDemoComplete = (results) => {
			console.log('[RL Page] Demo complete:', results);
			demoResults = results;
			isRunningDemo = false;

			if (results.reachedGoal) {
				showCompletionOverlay = true;
			} else {
				// Agent got stuck - show stuck detection overlay
				showCompletionOverlay = true;
			}
		};

		// Initialize controller
		try {
			await controller.initialize();
			pythonReady = true;
			status = 'ready';
			statusMessage = $exampleText.ui?.readyMessage || 'Click "Generate Maze" to begin';
			console.log('[RL Page] ✅ Python initialized and ready');
		} catch (error) {
			console.error('[RL Page] ❌ Failed to initialize Python:', error);
			status = 'error';
			statusMessage = 'Failed to load Python modules. Please refresh the page.';
			pythonReady = false;
			return;
		}

		// Generate initial maze
		generateMaze();
	});

	onDestroy(() => {
		if (!browser || !controller) return;
		stopAnimationLoop();
		controller.destroy();
		console.log('[RL Page] Destroyed');
	});

	function generateMaze() {
		controller.generateMaze(difficulty);
		// Reset training state
		episode = 0;
		steps = 0;
		totalReward = 0;
		epsilon = 1.0;
		successRate = 0;
		qValues = null;
		status = 'ready';
	}

	function startTraining() {
		if (!pythonReady) {
			alert('Python modules are still loading. Please wait...');
			return;
		}

		if (!mazeData) {
			alert('Please generate a maze first!');
			return;
		}

		// Stop demo if running
		if (isRunningDemo) {
			console.log('[RL Page] Stopping demo before training...');
			if (controller.pythonExports && controller.pythonExports.stopDemo) {
				controller.pythonExports.stopDemo();
			}
			isRunningDemo = false;
			showCompletionOverlay = false;
		}

		if (status === 'training') {
			// Restart training
			controller.stopTraining();
			setTimeout(() => {
				controller.resetTraining();
				controller.startTraining();
				status = 'training';
				statusMessage = $exampleText.ui?.trainingRestartedMessage || 'Training restarted';
			}, 100);
		} else {
			controller.startTraining();
			status = 'training';
			statusMessage = $exampleText.ui?.trainingMessage || 'Q-learning in progress...';
		}
	}

	function pauseTraining() {
		controller.pauseTraining();
		status = 'paused';
		statusMessage = $exampleText.ui?.pausedMessage || 'Training paused. Click "Resume" to continue.';
	}

	function resumeTraining() {
		controller.resumeTraining();
		status = 'training';
		statusMessage = $exampleText.ui?.resumedMessage || 'Training resumed...';
	}

	function resetTraining() {
		// Stop everything first
		if (isRunningDemo) {
			console.log('[RL Page] Stopping demo before reset...');
			if (controller.pythonExports && controller.pythonExports.stopDemo) {
				controller.pythonExports.stopDemo();
			}
			isRunningDemo = false;
		}
		
		if (status === 'training') {
			console.log('[RL Page] Stopping training before reset...');
			controller.stopTraining();
		}
		
		showCompletionOverlay = false;
		positionHistory = [];
		
		// Wait a bit for Python to stop, then reset
		setTimeout(() => {
			controller.resetTraining();
			agentPosition = { ...startPosition };
			episode = 0;
			steps = 0;
			totalReward = 0;
			epsilon = 1.0;
			successRate = 0;
			status = 'ready';
			statusMessage = $exampleText.ui?.resetMessage || 'Training reset. Click "Start Training" to begin.';
			console.log('[RL Page] ✅ Reset complete');
		}, 200);
	}

	function toggleQValues() {
		showQValues = !showQValues;
	}

	async function runDemo() {
		if (!pythonReady) {
			alert('Python modules are still loading. Please wait...');
			return;
		}

		if (!mazeData) {
			alert('Please generate a maze first!');
			return;
		}

		if (episode === 0) {
			alert('Train the agent first! The demo shows what the agent learned.');
			return;
		}

		// Stop everything first
		console.log('[RL Page] 🛑 Stopping all activities before demo...');
		
		// Stop training if active
		if (status === 'training' || status === 'paused') {
			controller.stopTraining();
			status = 'ready';
		}

		// Stop any running demo
		if (isRunningDemo) {
			console.log('[RL Page] Demo already running - stopping it first...');
			if (controller.pythonExports && controller.pythonExports.stopDemo) {
				controller.pythonExports.stopDemo();
			}
			isRunningDemo = false;
			showCompletionOverlay = false;
			await new Promise(resolve => setTimeout(resolve, 300));
		}

		statusMessage = $exampleText.ui?.stoppingTrainingMessage || '⏹️ Preparing demo...';

		// Wait for Python to fully stop any active loops
		await new Promise(resolve => setTimeout(resolve, 500));

		// Show countdown
		showCountdown = true;
		statusMessage = $exampleText.ui?.demoStartingMessage || '🎬 Demo starting...';

		// Countdown: 3...2...1
		for (let i = 3; i > 0; i--) {
			countdown = i;
			await new Promise(resolve => setTimeout(resolve, 800));
		}

		countdown = 0;
		showCountdown = false;

		// Reset position history for oscillation detection
		positionHistory = [];
		
		// Reset agent position to start
		agentPosition = { ...startPosition };
		steps = 0;
		totalReward = 0;

		// Start demo
		console.log('[RL Page] 🎬 Starting demo...');
		isRunningDemo = true;
		status = 'ready';
		statusMessage = $exampleText.ui?.demoRunningMessage || '🎬 Running demo with learned policy (epsilon = 0, no exploration)...';
		
		// Small delay then run demo
		await new Promise(resolve => setTimeout(resolve, 100));
		controller.runDemo();
	}
</script>

<ExperimentCard props={{ previousPage: '/examples/ml', nextPage: '/examples/ml/neuro' }}>
	<div slot="py_slot" class="flex h-full flex-col p-5 space-y-4">
		<!-- Maze Visualization -->
		<div class="flex justify-center relative">
			{#if mazeData}
				<MazeCanvas
					bind:maze={mazeData}
					bind:agentPosition={agentPosition}
					bind:startPosition={startPosition}
					bind:endPosition={endPosition}
					bind:qValues={qValues}
					bind:showQValues={showQValues}
					bind:cellSize={cellSize}
					bind:width={canvasWidth}
					bind:height={canvasHeight}
				/>
			{:else}
				<div class="flex items-center justify-center w-[450px] h-[450px] bg-black border-2 border-gray-600 rounded">
					<p class="text-gray-400 text-lg font-mono">Generate a maze to begin</p>
				</div>
			{/if}

			<!-- Countdown Overlay -->
			{#if showCountdown}
				<div class="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm rounded-lg">
					<div class="text-center">
						<div class="text-9xl font-bold text-white drop-shadow-lg animate-pulse">
							{countdown > 0 ? countdown : '🚀'}
						</div>
						<p class="text-white text-xl mt-4 font-semibold">Get ready!</p>
					</div>
				</div>
			{/if}

			<!-- Completion Overlay - Success -->
			{#if showCompletionOverlay && demoResults && demoResults.reachedGoal}
				<div class="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm rounded-lg">
					<div class="bg-white rounded-xl shadow-2xl p-8 max-w-md text-center">
						<div class="text-6xl mb-4">🎉</div>
						<h2 class="text-3xl font-bold text-gray-900 mb-2">Goal Reached!</h2>
						<p class="text-gray-600 mb-6">Agent successfully completed the maze using learned policy</p>

						<!-- Stats -->
						<div class="grid grid-cols-2 gap-4 mb-6">
							<div class="bg-blue-50 rounded-lg p-4">
								<div class="text-sm font-semibold text-blue-900 opacity-90">Time</div>
								<div class="text-2xl font-bold text-blue-600">{demoResults.elapsedTime.toFixed(2)}s</div>
							</div>
							<div class="bg-green-50 rounded-lg p-4">
								<div class="text-sm font-semibold text-green-900 opacity-90">Steps</div>
								<div class="text-2xl font-bold text-green-600">{demoResults.steps}</div>
							</div>
						</div>

						<!-- Buttons -->
						<div class="flex gap-3">
							<button
								onclick={() => { showCompletionOverlay = false; startTraining(); }}
								class="flex-1 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-3 font-bold text-white hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
							>
								📚 Keep Training
							</button>
							<button
								onclick={() => { showCompletionOverlay = false; runDemo(); }}
								class="flex-1 rounded-lg bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-3 font-bold text-white hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg"
							>
								🎬 Run Again
							</button>
						</div>

						<button
							onclick={() => showCompletionOverlay = false}
							class="mt-4 text-sm text-gray-500 hover:text-gray-700"
						>
							Close
						</button>
					</div>
				</div>
			{/if}

			<!-- Completion Overlay - Agent Stuck -->
			{#if showCompletionOverlay && demoResults && !demoResults.reachedGoal}
				<div class="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm rounded-lg">
					<div class="bg-white rounded-lg shadow-2xl p-5 max-w-sm text-center">
						<div class="text-5xl mb-2">{demoResults.oscillationDetected ? '🔄' : '🤔'}</div>
						<h2 class="text-2xl font-bold text-gray-900 mb-1">
							{demoResults.oscillationDetected ? 'Stuck Oscillating' : 'Got Stuck'}
						</h2>
						<p class="text-xs text-gray-600 mb-4">
							{demoResults.oscillationDetected
								? 'Agent bouncing between cells - needs more training!'
								: `Agent took ${demoResults.steps} steps but hit max limit`}
						</p>

						<!-- Buttons -->
						<div class="flex gap-2">
							<button
								onclick={() => { showCompletionOverlay = false; startTraining(); }}
								class="flex-1 rounded bg-blue-500 px-4 py-2 text-sm font-bold text-white hover:bg-blue-600 transition-all"
							>
								📚 Train
							</button>
							<button
								onclick={() => { showCompletionOverlay = false; runDemo(); }}
								class="flex-1 rounded bg-purple-500 px-4 py-2 text-sm font-bold text-white hover:bg-purple-600 transition-all"
							>
								🎬 Retry
							</button>
							<button
								onclick={() => showCompletionOverlay = false}
								class="rounded bg-gray-200 px-4 py-2 text-sm font-bold text-gray-700 hover:bg-gray-300 transition-all"
							>
								✕
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Metrics Display -->
		<div class="grid grid-cols-5 gap-2">
			<div class="rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">{$exampleText.ui?.metricEpisode || 'Episode'}</div>
				<div class="text-2xl font-bold">{typeof episode === 'number' ? episode : 0}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-green-500 to-green-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">{$exampleText.ui?.metricSteps || 'Steps'}</div>
				<div class="text-2xl font-bold">{typeof steps === 'number' ? steps : 0}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">{$exampleText.ui?.metricReward || 'Reward'}</div>
				<div class="text-2xl font-bold">{typeof totalReward === 'number' ? totalReward.toFixed(0) : '0'}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">{$exampleText.ui?.metricEpsilon || 'Epsilon (ε)'}</div>
				<div class="text-2xl font-bold">{typeof epsilon === 'number' ? epsilon.toFixed(2) : '1.00'}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-pink-500 to-pink-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">{$exampleText.ui?.metricSuccessRate || 'Success Rate'}</div>
				<div class="text-2xl font-bold">{typeof successRate === 'number' ? successRate.toFixed(1) : '0.0'}%</div>
			</div>
		</div>

		<!-- Status Display -->
		<div
			class="rounded border-2 p-3 {status === 'error'
				? 'bg-red-50 border-red-200'
				: status === 'initializing'
					? 'bg-purple-50 border-purple-200'
					: status === 'training'
						? 'bg-green-50 border-green-200'
						: status === 'paused'
							? 'bg-yellow-50 border-yellow-200'
							: 'bg-blue-50 border-blue-200'}"
		>
			<p
				class="text-sm font-mono {status === 'error'
					? 'text-red-700'
					: status === 'initializing'
						? 'text-purple-700'
						: status === 'training'
							? 'text-green-700'
							: status === 'paused'
								? 'text-yellow-700'
								: 'text-blue-700'}"
			>
				{#if status === 'initializing'}
					<span class="inline-block animate-pulse">⏳</span>
				{/if}
				{statusMessage}
			</p>
		</div>

		<!-- Control Buttons -->
		<div class="space-y-3">
			<!-- Row 1: Generate + Difficulty Selector + Reset -->
			<div class="grid grid-cols-[1fr_2fr_1fr] gap-3">
				<button
					onclick={generateMaze}
					disabled={status === 'training' || status === 'initializing' || isRunningDemo}
					class="rounded bg-blue-500 px-6 py-3 font-bold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{$exampleText.ui?.generateButton || '🎲 Generate'}
				</button>
				<select
					bind:value={difficulty}
					onchange={generateMaze}
					disabled={status === 'training' || status === 'initializing' || isRunningDemo}
					class="rounded border-2 border-gray-300 bg-white px-4 py-3 font-semibold text-gray-700 hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
				>
					{#each Object.entries(difficultySettings) as [key, settings]}
						<option value={key}>{settings.name}</option>
					{/each}
				</select>
				<button
					onclick={resetTraining}
					disabled={status === 'initializing' || status === 'error' || (status === 'ready' && episode === 0)}
					class="rounded bg-red-500 px-6 py-3 font-bold text-white hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{$exampleText.ui?.resetButton || '🔄 Reset'}
				</button>
			</div>

			<!-- Row 2: Training Controls -->
			<div class="grid grid-cols-4 gap-3">
				<button
					onclick={startTraining}
					disabled={!mazeData || !pythonReady || status === 'initializing' || isRunningDemo}
					class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'training' ? ($exampleText.ui?.restartButton || '🔄 Restart') : ($exampleText.ui?.trainButton || '▶️ Train')}
				</button>
				<button
					onclick={status === 'paused' ? resumeTraining : pauseTraining}
					disabled={status !== 'training' && status !== 'paused'}
					class="rounded bg-yellow-500 px-6 py-3 font-bold text-white hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'paused' ? ($exampleText.ui?.resumeButton || '▶️ Resume') : ($exampleText.ui?.pauseButton || '⏸️ Pause')}
				</button>
				<button
					onclick={runDemo}
					disabled={!mazeData || episode === 0 || !pythonReady || status === 'initializing'}
					class="rounded bg-purple-500 px-6 py-3 font-bold text-white hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{isRunningDemo ? '⏹️ Stop Demo' : ($exampleText.ui?.demoButton || '🎬 Demo')}
				</button>
				<button
					onclick={toggleQValues}
					disabled={!qValues || Object.keys(qValues).length === 0}
					class="rounded px-6 py-3 font-bold text-white transition-colors {showQValues ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'} disabled:bg-gray-400 disabled:cursor-not-allowed"
				>
					{showQValues ? ($exampleText.ui?.hideQValuesButton || '🎨 Hide Q-values') : ($exampleText.ui?.visualizeButton || '🎨 Visualize')}
				</button>
			</div>
		</div>

		<!-- Educational Info Sections -->
		<div class="space-y-3">
			<!-- MAZE VISUALIZATION COLORS -->
			<Callout>
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.ui?.visualizationTitle || '🎨 Visualization Colors'}</h3>
				<p class="text-xs mb-2">
					{$exampleText.ui?.visualizationDesc || 'Here\'s what each color represents in the maze:'}
				</p>
				<ul class="space-y-1 pl-5 text-xs">
					<li><span class="font-mono bg-green-200 px-2 py-1 rounded">🟢</span> {$exampleText.ui?.colorGreenWalls || 'Green walls - Maze structure boundaries'}</li>
					<li><span class="font-mono bg-green-200 px-2 py-1 rounded">●</span> {$exampleText.ui?.colorGreenCircle || 'Green circle - Start position (where agent begins)'}</li>
					<li><span class="font-mono bg-red-200 px-2 py-1 rounded">●</span> {$exampleText.ui?.colorRedCircle || 'Red circle - Goal/target position (objective)'}</li>
					<li><span class="font-mono bg-blue-200 px-2 py-1 rounded">●</span> {$exampleText.ui?.colorBlueCircle || 'Blue circle - Agent position (AI solver)'}</li>
				</ul>
				<div class="mt-2 pt-2 border-t border-border">
					<p class="text-xs font-semibold mb-1">{$exampleText.ui?.qValueHeatmap || 'Q-Value Heatmap (when "Visualize" is toggled):'}</p>
					<div class="flex items-center gap-2 text-xs">
						<span class="w-4 h-4 rounded" style="background: hsl(240, 80%, 50%);"></span>
						<span>{$exampleText.ui?.qValueLow || 'Low Q-value (blue)'}</span>
						<span>→</span>
						<span class="w-4 h-4 rounded" style="background: hsl(60, 80%, 50%);"></span>
						<span>{$exampleText.ui?.qValueHigh || 'High Q-value (yellow)'}</span>
					</div>
					<p class="text-xs mt-1">{$exampleText.ui?.qValueDesc || 'Brighter/yellower cells = agent learned these positions are more valuable (closer to goal)'}</p>
				</div>
			</Callout>

			<!-- Q-LEARNING BASICS -->
			<Callout>
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.sections?.whatIsQLearning?.title || '🎓 What is Q-Learning?'}</h3>
				<p class="text-xs mb-2">
					{$exampleText.sections?.whatIsQLearning?.description || 'Q-Learning is a value-based reinforcement learning algorithm that learns the optimal action to take in each state by maintaining a Q-table:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs">
					<li>{$exampleText.sections?.whatIsQLearning?.qTable || 'Q-Table: Maps state-action pairs to expected rewards (Q-values)'}</li>
					<li>{$exampleText.sections?.whatIsQLearning?.bellman || 'Bellman Equation: Q(s,a) = Q(s,a) + α[r + γ·max(Q(s\',a\')) - Q(s,a)]'}</li>
					<li>{$exampleText.sections?.whatIsQLearning?.alpha || 'α (Alpha): Learning rate (difficulty-adjusted) - how much new info overrides old'}</li>
					<li>{$exampleText.sections?.whatIsQLearning?.gamma || 'γ (Gamma): Discount factor (0.95) - importance of future rewards'}</li>
					<li>{$exampleText.sections?.whatIsQLearning?.epsilon || 'ε (Epsilon): Exploration rate (starts at 1.0, decays based on difficulty)'}</li>
				</ul>
			</Callout>

			<!-- EXPLORATION VS EXPLOITATION -->
			<Callout>
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.sections?.explorationVsExploitation?.title || '🔍 Exploration vs Exploitation'}</h3>
				<p class="text-xs mb-2">
					{$exampleText.sections?.explorationVsExploitation?.description || 'The agent uses an epsilon-greedy strategy to balance learning and performance:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs">
					<li>{$exampleText.sections?.explorationVsExploitation?.exploration || 'Exploration (ε = 1.0 → 0.01): Take random actions to discover new paths'}</li>
					<li>{$exampleText.sections?.explorationVsExploitation?.exploitation || 'Exploitation (1 - ε): Use learned Q-values to take best known action'}</li>
					<li>{$exampleText.sections?.explorationVsExploitation?.decay || 'Epsilon Decay: Gradually shift from exploration to exploitation as agent learns'}</li>
				</ul>
				<p class="text-xs mt-2">
					{$exampleText.sections?.explorationVsExploitation?.note || 'Watch the Epsilon (ε) metric decrease over time - as it approaches 0.01, the agent transitions from random exploration to exploiting learned strategies!'}
				</p>
			</Callout>

			<!-- REWARD STRUCTURE -->
			<Callout>
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.sections?.rewardStructure?.title || '🎯 Reward Structure'}</h3>
				<p class="text-xs mb-2">{$exampleText.sections?.rewardStructure?.description || 'The agent receives rewards for its actions:'}</p>
				<ul class="list-disc space-y-1 pl-5 text-xs">
					<li>{$exampleText.sections?.rewardStructure?.hitWall || 'Hit Wall: -1.0 (strong discouragement)'}</li>
					<li>{$exampleText.sections?.rewardStructure?.normalMove || 'Normal Move: -0.5 base penalty + directional bonus'}
						<ul class="list-circle space-y-0.5 pl-5 mt-1">
							<li>{$exampleText.sections?.rewardStructure?.closer || 'Move closer to goal: +0.1 (reward shaping guides learning)'}</li>
							<li>{$exampleText.sections?.rewardStructure?.away || 'Move away from goal: -0.1 (discourages wrong direction)'}</li>
						</ul>
					</li>
					<li>{$exampleText.sections?.rewardStructure?.goalReached || 'Goal Reached: +100 (big success!)'}</li>
					<li>{$exampleText.sections?.rewardStructure?.episodeLimit || 'Episode Limit: 1000 steps max to prevent infinite loops'}</li>
				</ul>
				<p class="text-xs mt-2">
					{$exampleText.sections?.rewardStructure?.shaping || 'The reward shaping (directional bonus) acts like a compass 🧭, guiding the agent toward the goal while still discovering the optimal path through Q-learning!'}
				</p>
			</Callout>

			<!-- HOW IT LEARNS -->
			<Callout type="tip">
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.sections?.howQLearningLearns?.title || '🧠 How Q-Learning Learns'}</h3>
				<ol class="list-decimal space-y-1 pl-5 text-xs">
					<li>{$exampleText.sections?.howQLearningLearns?.step1 || 'Initialize: Start with empty Q-table (all values = 0)'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step2 || 'Episode Loop: Agent spawns at 🟢 green position'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step3 || 'Choose Action: ε-greedy (explore random or exploit best Q-value)'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step4 || 'Execute: Move agent, observe reward and next state'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step5 || 'Update Q-Value: Apply Bellman equation to learn from experience'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step6 || 'Repeat: Until reaching 🔴 red goal or step limit (agents blink rapidly between cells)'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step7 || 'Decay ε: Reduce exploration rate based on maze difficulty'}</li>
					<li>{$exampleText.sections?.howQLearningLearns?.step8 || 'Next Episode: Reset agent, repeat with updated Q-values'}</li>
				</ol>
				<p class="text-xs mt-2">
					{$exampleText.sections?.howQLearningLearns?.insight || 'Over time, Q-values propagate backward from the goal, creating a "gradient" that guides the agent! You can see this gradient visualized when you toggle "Visualize" (brighter = higher Q-value).'}
				</p>
				<div class="mt-2 pt-2 border-t border-border">
					<p class="text-xs font-semibold mb-1">{$exampleText.sections?.howQLearningLearns?.smartFeaturesTitle || '✨ Smart Features:'}</p>
					<ul class="list-disc space-y-0.5 pl-5 text-xs">
						<li>{$exampleText.sections?.howQLearningLearns?.smartFeature1 || 'Difficulty-Adjusted Learning: Easy mazes learn faster (higher α), hard mazes explore more (higher ε decay)'}</li>
						<li>{$exampleText.sections?.howQLearningLearns?.smartFeature2 || 'Reward Shaping: Direction bonus helps agent find goal faster without knowing maze structure'}</li>
						<li>{$exampleText.sections?.howQLearningLearns?.smartFeature3 || 'Demo Mode: Click "Demo" to see pure exploitation (ε=0) - shows what agent truly learned without exploration!'}</li>
					</ul>
				</div>
			</Callout>

			<!-- TECHNICAL ARCHITECTURE -->
			<Callout>
				<h3 class="mb-2 text-base font-heading font-bold">{$exampleText.sections?.technicalArchitecture?.title || '⚡ Technical Architecture'}</h3>
				<ul class="list-disc space-y-1 pl-5 text-xs">
					<li>{$exampleText.sections?.technicalArchitecture?.mazeGeneration || 'Maze Generation: Recursive backtracker algorithm (depth-first search)'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.stateSpace || 'State Space: Discrete grid (row, col) positions'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.actionSpace || 'Action Space: 4 discrete actions (UP, DOWN, LEFT, RIGHT)'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.backend || 'Q-Learning Backend: Python (PyScript) with Q-table dictionary storage'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.rewardShaping || 'Reward Shaping: Manhattan distance bonus to guide learning'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.difficultyAdapted || 'Difficulty-Adapted Learning:'}
						<ul class="list-circle space-y-0.5 pl-5 mt-0.5">
							<li>{$exampleText.sections?.technicalArchitecture?.easy || 'Easy: α=0.35, decay=0.96 (fast learning)'}</li>
							<li>{$exampleText.sections?.technicalArchitecture?.medium || 'Medium: α=0.3, decay=0.98 (balanced)'}</li>
							<li>{$exampleText.sections?.technicalArchitecture?.hard || 'Hard: α=0.25, decay=0.985 (cautious learning)'}</li>
							<li>{$exampleText.sections?.technicalArchitecture?.insane || 'Insane: α=0.2, decay=0.99 (extensive exploration)'}</li>
						</ul>
					</li>
					<li>{$exampleText.sections?.technicalArchitecture?.animation || 'Animation System: Frame-based tweening (60fps) for demo mode smooth movement'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.visualization || 'Visualization: Canvas rendering with Q-value heatmap overlay (blue→yellow gradient)'}</li>
					<li>{$exampleText.sections?.technicalArchitecture?.trainingSpeed || 'Training Speed: ~4 episodes for 50% success on easy mode!'}</li>
				</ul>
			</Callout>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-heading font-bold text-text-primary">{$exampleText.title || 'Q-Learning Maze Solver'}</h2>

		<div class="prose max-w-none space-y-4">
			<p class="text-sm">
				{$exampleText.description || 'Watch an AI agent learn to solve mazes using Q-Learning, the classic tabular reinforcement learning algorithm. Perfect introduction to RL fundamentals!'}
			</p>

			<!-- HOW TO USE -->
			<Callout>
				<h3 class="mb-2 text-lg font-heading font-bold">{$exampleText.howToUse?.title || '🎯 How to Use'}</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm">
					<li><strong>{$exampleText.howToUse?.step1Title || 'Generate Maze:'}​</strong> {$exampleText.howToUse?.step1Desc || 'Click "Generate" to create a random maze. Try different difficulties!'}</li>
					<li><strong>{$exampleText.howToUse?.step2Title || 'Start Training:'}​</strong> {$exampleText.howToUse?.step2Desc || 'Click "Start Training" to begin Q-learning'}
						<span class="block text-xs mt-1">{$exampleText.howToUse?.step2Note || 'Watch the 🔵 blue agent blink rapidly between cells as it explores!'}</span>
					</li>
					<li><strong>{$exampleText.howToUse?.step3Title || 'Visualize Q-Values:'}​</strong> {$exampleText.howToUse?.step3Desc || 'Click "Visualize" to toggle the heatmap overlay'}
						<span class="block text-xs mt-1">{$exampleText.howToUse?.step3Note || 'Blue cells = low Q-value | Yellow cells = high Q-value (closer to goal)'}</span>
					</li>
					<li><strong>{$exampleText.howToUse?.step4Title || 'Monitor Metrics:'}​</strong> {$exampleText.howToUse?.step4Desc || 'Watch Success Rate climb and Epsilon decay as the agent learns'}</li>
					<li><strong>{$exampleText.howToUse?.step5Title || 'Demo Mode:'}​</strong> {$exampleText.howToUse?.step5Desc || 'Once trained, click "Demo" to see smooth, confident movement'}
						<span class="block text-xs mt-1">{$exampleText.howToUse?.step5Note || 'Agent moves smoothly (tweened) because it\'s using pure exploitation (ε=0)'}</span>
					</li>
					<li><strong>{$exampleText.howToUse?.step6Title || 'Compare Difficulties:'}​</strong> {$exampleText.howToUse?.step6Desc || 'Try Easy (10×10) vs Insane (30×30) to see how learning adapts!'}</li>
				</ol>
				<p class="mt-3 text-xs">
					{$exampleText.howToUse?.proTip || '💡 Pro Tip: Training = agent blinks frantically between spots (exploring). Demo = agent glides smoothly (exploiting learned knowledge)!'}
				</p>
			</Callout>

			<!-- WHY Q-LEARNING -->
			<Callout type="tip">
				<h3 class="mb-2 text-lg font-heading font-bold">{$exampleText.whyQLearning?.title || '🌟 Why Q-Learning?'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.whyQLearning?.intro || 'Q-Learning is the perfect introduction to reinforcement learning because:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.whyQLearning?.intuitive || 'Intuitive: Easy to visualize and understand'}</li>
					<li>{$exampleText.whyQLearning?.modelFree || 'Model-Free: No knowledge of maze structure needed'}</li>
					<li>{$exampleText.whyQLearning?.offPolicy || 'Off-Policy: Learns optimal policy while exploring'}</li>
					<li>{$exampleText.whyQLearning?.convergence || 'Guaranteed Convergence: Proven to find optimal solution'}</li>
					<li>{$exampleText.whyQLearning?.foundation || 'Foundation for Deep RL: Basis for DQN, Double DQN, etc.'}</li>
				</ul>
			</Callout>

			<!-- LIMITATIONS -->
			<Callout type="warning">
				<h3 class="mb-2 text-lg font-heading font-bold">{$exampleText.limitations?.title || '⚠️ Q-Table Limitations'}</h3>
				<p class="text-sm mb-2">
					{$exampleText.limitations?.intro || 'Q-tables work great for discrete, small state spaces like mazes. But they don\'t scale:'}
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm">
					<li>{$exampleText.limitations?.memory || 'Memory: A 30×30 maze has 900 states × 4 actions = 3,600 Q-values'}</li>
					<li>{$exampleText.limitations?.continuous || 'Continuous States: Can\'t handle pixel inputs or continuous observations'}</li>
					<li>{$exampleText.limitations?.generalization || 'Generalization: Each state learned independently, no transfer'}</li>
				</ul>
				<p class="text-sm mt-2">
					{$exampleText.limitations?.conclusion || 'That\'s why complex games like Mario use neural networks (function approximation) instead of Q-tables. Check out the Neuroevolution example to see how!'}
				</p>
			</Callout>
		</div>

		<p class="mt-6">
			<a
				class="text-accent"
				href="https://github.com/guinetik/pyscript-lab/blob/master/src/lib/controller/MazeRLController.js"
				target="_blank">View source (MazeRLController.js)</a
			>
		</p>
	</article>
</ExperimentCard>
