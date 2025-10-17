<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import MazeCanvas from '$lib/components/MazeCanvas.svelte';
	import { MazeRLController } from '$lib/controller/MazeRLController.js';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	// Page metadata
	let name = 'Q-Learning Maze Solver';

	// Controller instance
	let controller = browser ? new MazeRLController() : null;

	// UI State
	let status = $state('ready'); // 'ready' | 'training' | 'paused' | 'error'
	let statusMessage = $state('Click "Generate Maze" to begin');

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

	// Difficulty options
	const difficultySettings = {
		easy: { name: 'Easy (10×10)', rows: 10, cols: 10, cellSize: 40 },
		medium: { name: 'Medium (15×15)', rows: 15, cols: 15, cellSize: 30 },
		hard: { name: 'Hard (20×20)', rows: 20, cols: 20, cellSize: 25 },
		insane: { name: 'Insane (30×30)', rows: 30, cols: 30, cellSize: 20 }
	};

	onMount(async () => {
		if (!browser || !controller) return;

		console.log('[RL Page] Mounted');

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

			statusMessage = 'Maze generated! Click "Start Training" to begin Q-learning.';
		};

		controller.callbacks.onAgentMove = (data) => {
			agentPosition = data.position;
			steps = data.steps;
			totalReward = data.reward;
		};

		controller.callbacks.onMetricsUpdate = (metrics) => {
			episode = metrics.episode;
			steps = metrics.steps;
			totalReward = metrics.reward;
			epsilon = metrics.epsilon;
			successRate = parseFloat(metrics.successRate);
			qValues = metrics.qValues;
		};

		controller.callbacks.onEpisodeEnd = (episodeData) => {
			// Reset agent to start position
			agentPosition = { ...startPosition };
		};

		controller.callbacks.onDemoComplete = (results) => {
			console.log('[RL Page] Demo complete:', results);
			demoResults = results;
			if (results.reachedGoal) {
				showCompletionOverlay = true;
			}
		};

		// Initialize controller
		await controller.initialize();

		// Generate initial maze
		generateMaze();
	});

	onDestroy(() => {
		if (!browser || !controller) return;
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
		if (!mazeData) {
			alert('Please generate a maze first!');
			return;
		}

		if (status === 'training') {
			// Restart training
			controller.resetTraining();
			controller.startTraining();
			statusMessage = 'Training restarted';
		} else {
			controller.startTraining();
			status = 'training';
			statusMessage = 'Q-learning in progress...';
		}
	}

	function pauseTraining() {
		controller.pauseTraining();
		status = 'paused';
		statusMessage = 'Training paused. Click "Resume" to continue.';
	}

	function resumeTraining() {
		controller.resumeTraining();
		status = 'training';
		statusMessage = 'Training resumed...';
	}

	function resetTraining() {
		controller.resetTraining();
		agentPosition = { ...startPosition };
		status = 'ready';
		statusMessage = 'Training reset. Click "Start Training" to begin.';
	}

	function toggleQValues() {
		showQValues = !showQValues;
	}

	function runDemo() {
		if (!mazeData) {
			alert('Please generate a maze first!');
			return;
		}

		if (episode === 0) {
			alert('Train the agent first! The demo shows what the agent learned.');
			return;
		}

		controller.runDemo();
		status = 'ready';
		statusMessage = '🎬 Running demo with learned policy (epsilon = 0, no exploration)...';
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

			<!-- Completion Overlay -->
			{#if showCompletionOverlay && demoResults}
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
		</div>

		<!-- Metrics Display -->
		<div class="grid grid-cols-5 gap-2">
			<div class="rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">Episode</div>
				<div class="text-2xl font-bold">{episode}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-green-500 to-green-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">Steps</div>
				<div class="text-2xl font-bold">{steps}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">Reward</div>
				<div class="text-2xl font-bold">{totalReward.toFixed(0)}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">Epsilon (ε)</div>
				<div class="text-2xl font-bold">{epsilon.toFixed(2)}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-pink-500 to-pink-600 p-3 text-white shadow-lg">
				<div class="text-xs font-semibold opacity-90">Success Rate</div>
				<div class="text-2xl font-bold">{successRate.toFixed(1)}%</div>
			</div>
		</div>

		<!-- Status Display -->
		<div
			class="rounded border-2 p-3 {status === 'error'
				? 'bg-red-50 border-red-200'
				: status === 'training'
					? 'bg-green-50 border-green-200'
					: status === 'paused'
						? 'bg-yellow-50 border-yellow-200'
						: 'bg-blue-50 border-blue-200'}"
		>
			<p
				class="text-sm font-mono {status === 'error'
					? 'text-red-700'
					: status === 'training'
						? 'text-green-700'
						: status === 'paused'
							? 'text-yellow-700'
							: 'text-blue-700'}"
			>
				{statusMessage}
			</p>
		</div>

		<!-- Control Buttons -->
		<div class="space-y-3">
			<!-- Row 1: Generate + Difficulty Selector + Reset -->
			<div class="grid grid-cols-[1fr_2fr_1fr] gap-3">
				<button
					onclick={generateMaze}
					disabled={status === 'training'}
					class="rounded bg-blue-500 px-6 py-3 font-bold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🎲 Generate
				</button>
				<select
					bind:value={difficulty}
					onchange={generateMaze}
					disabled={status === 'training'}
					class="rounded border-2 border-gray-300 bg-white px-4 py-3 font-semibold text-gray-700 hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
				>
					{#each Object.entries(difficultySettings) as [key, settings]}
						<option value={key}>{settings.name}</option>
					{/each}
				</select>
				<button
					onclick={resetTraining}
					disabled={status !== 'training' && status !== 'paused'}
					class="rounded bg-red-500 px-6 py-3 font-bold text-white hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🔄 Reset
				</button>
			</div>

			<!-- Row 2: Training Controls -->
			<div class="grid grid-cols-4 gap-3">
				<button
					onclick={startTraining}
					disabled={!mazeData}
					class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'training' ? '🔄 Restart' : '▶️ Start Training'}
				</button>
				<button
					onclick={status === 'paused' ? resumeTraining : pauseTraining}
					disabled={status !== 'training' && status !== 'paused'}
					class="rounded bg-yellow-500 px-6 py-3 font-bold text-white hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'paused' ? '▶️ Resume' : '⏸️ Pause'}
				</button>
				<button
					onclick={runDemo}
					disabled={!mazeData || episode === 0}
					class="rounded bg-purple-500 px-6 py-3 font-bold text-white hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🎬 Demo
				</button>
				<button
					onclick={toggleQValues}
					disabled={!qValues || Object.keys(qValues).length === 0}
					class="rounded px-6 py-3 font-bold text-white transition-colors {showQValues ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-slate-500 hover:bg-slate-600'} disabled:bg-gray-400 disabled:cursor-not-allowed"
				>
					{showQValues ? '🎨 Hide Q-Values' : '🎨 Show Q-Values'}
				</button>
			</div>
		</div>

		<!-- Educational Info Sections -->
		<div class="space-y-3">
			<!-- Q-LEARNING BASICS -->
			<div class="rounded-lg bg-blue-50 p-3 border-2 border-blue-200">
				<h3 class="mb-2 text-base font-bold text-blue-900">🎓 What is Q-Learning?</h3>
				<p class="text-xs text-blue-800 mb-2">
					<strong>Q-Learning</strong> is a value-based reinforcement learning algorithm that learns the optimal action to take in each state by maintaining a Q-table:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs text-blue-800">
					<li><strong>Q-Table:</strong> Maps state-action pairs to expected rewards (Q-values)</li>
					<li><strong>Bellman Equation:</strong> Q(s,a) = Q(s,a) + α[r + γ·max(Q(s',a')) - Q(s,a)]</li>
					<li><strong>α (Alpha):</strong> Learning rate (0.1) - how much new info overrides old</li>
					<li><strong>γ (Gamma):</strong> Discount factor (0.95) - importance of future rewards</li>
					<li><strong>ε (Epsilon):</strong> Exploration rate (starts at 1.0, decays to 0.01)</li>
				</ul>
			</div>

			<!-- EXPLORATION VS EXPLOITATION -->
			<div class="rounded-lg bg-green-50 p-3 border-2 border-green-200">
				<h3 class="mb-2 text-base font-bold text-green-900">🔍 Exploration vs Exploitation</h3>
				<p class="text-xs text-green-800 mb-2">
					The agent uses an <strong>epsilon-greedy</strong> strategy to balance learning and performance:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-xs text-green-800">
					<li><strong>Exploration (ε = 1.0 → 0.01):</strong> Take random actions to discover new paths</li>
					<li><strong>Exploitation (1 - ε):</strong> Use learned Q-values to take best known action</li>
					<li><strong>Epsilon Decay:</strong> Gradually shift from exploration to exploitation as agent learns</li>
				</ul>
				<p class="text-xs text-green-800 mt-2">
					Watch the Epsilon (ε) metric decrease over time - as it approaches 0.01, the agent transitions from random exploration to exploiting learned strategies!
				</p>
			</div>

			<!-- REWARD STRUCTURE -->
			<div class="rounded-lg bg-purple-50 p-3 border-2 border-purple-200">
				<h3 class="mb-2 text-base font-bold text-purple-900">🎯 Reward Structure</h3>
				<ul class="list-disc space-y-1 pl-5 text-xs text-purple-800">
					<li><strong>Step Penalty:</strong> -1 per move (encourages efficiency)</li>
					<li><strong>Goal Reward:</strong> +100 for reaching the red target</li>
					<li><strong>Episode Limit:</strong> 1000 steps max to prevent infinite loops</li>
				</ul>
				<p class="text-xs text-purple-800 mt-2">
					This reward structure teaches the agent to find the <strong>shortest path</strong> to the goal!
				</p>
			</div>

			<!-- HOW IT LEARNS -->
			<div class="rounded-lg bg-amber-50 p-3 border-2 border-amber-200">
				<h3 class="mb-2 text-base font-bold text-amber-900">🧠 How Q-Learning Learns</h3>
				<ol class="list-decimal space-y-1 pl-5 text-xs text-amber-800">
					<li><strong>Initialize:</strong> Start with empty Q-table (all values = 0)</li>
					<li><strong>Episode Loop:</strong> Agent spawns at green start position</li>
					<li><strong>Choose Action:</strong> ε-greedy (explore random or exploit best Q-value)</li>
					<li><strong>Execute:</strong> Move agent, observe reward and next state</li>
					<li><strong>Update Q-Value:</strong> Apply Bellman equation to learn from experience</li>
					<li><strong>Repeat:</strong> Until reaching goal or step limit</li>
					<li><strong>Decay ε:</strong> Reduce exploration rate (ε × 0.995)</li>
					<li><strong>Next Episode:</strong> Reset agent, repeat with updated Q-values</li>
				</ol>
				<p class="text-xs text-amber-800 mt-2">
					Over time, Q-values propagate backward from the goal, creating a "gradient" that guides the agent!
				</p>
			</div>

			<!-- TECHNICAL ARCHITECTURE -->
			<div class="rounded-lg bg-red-50 p-3 border-2 border-red-200">
				<h3 class="mb-2 text-base font-bold text-red-900">⚡ Technical Architecture</h3>
				<ul class="list-disc space-y-1 pl-5 text-xs text-red-800">
					<li><strong>Maze Generation:</strong> Recursive backtracker algorithm (depth-first search)</li>
					<li><strong>State Space:</strong> Discrete grid (row, col) positions</li>
					<li><strong>Action Space:</strong> 4 discrete actions (UP, DOWN, LEFT, RIGHT)</li>
					<li><strong>Q-Table Storage:</strong> JavaScript object with "row,col:action" keys</li>
					<li><strong>Mock Implementation:</strong> Pure JavaScript (Python integration ready)</li>
					<li><strong>Visualization:</strong> Canvas rendering with Q-value heatmap overlay</li>
					<li><strong>Training Speed:</strong> ~10 episodes/second (adjustable)</li>
				</ul>
			</div>
		</div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none space-y-4">
			<p class="text-sm">
				Watch an AI agent learn to solve mazes using <strong>Q-Learning</strong>, the classic tabular reinforcement learning algorithm. Perfect introduction to RL fundamentals!
			</p>

			<!-- HOW TO USE -->
			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-cyan-900">🎯 How to Use</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-cyan-800">
					<li><strong>Generate Maze:</strong> Click "Generate" to create a random maze. Try different difficulties!</li>
					<li><strong>Start Training:</strong> Click "Start Training" to begin Q-learning</li>
					<li><strong>Watch Learning:</strong> Blue agent explores the maze, learning optimal paths</li>
					<li><strong>Show Q-Values:</strong> Click "Show Q-Values" to see learned values as a heatmap (blue = low, yellow = high)</li>
					<li><strong>Monitor Metrics:</strong> Watch Epsilon decay and Success Rate improve over episodes</li>
					<li><strong>Demo Mode:</strong> Once trained (76%+ success rate), click "Demo" to see the agent use its learned policy with zero exploration!</li>
					<li><strong>Experiment:</strong> Try different difficulties and observe how learning speed changes</li>
				</ol>
				<p class="mt-3 text-xs text-cyan-700">
					💡 <strong>Pro Tip:</strong> Demo mode sets epsilon to 0 (pure exploitation) so you can see the agent's "actual skill" without random exploration!
				</p>
			</div>

			<!-- WHY Q-LEARNING -->
			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">🌟 Why Q-Learning?</h3>
				<p class="text-sm text-green-800 mb-2">
					Q-Learning is the <strong>perfect introduction to reinforcement learning</strong> because:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
					<li><strong>Intuitive:</strong> Easy to visualize and understand</li>
					<li><strong>Model-Free:</strong> No knowledge of maze structure needed</li>
					<li><strong>Off-Policy:</strong> Learns optimal policy while exploring</li>
					<li><strong>Guaranteed Convergence:</strong> Proven to find optimal solution</li>
					<li><strong>Foundation for Deep RL:</strong> Basis for DQN, Double DQN, etc.</li>
				</ul>
			</div>

			<!-- LIMITATIONS -->
			<div class="rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-yellow-900">⚠️ Q-Table Limitations</h3>
				<p class="text-sm text-yellow-800 mb-2">
					Q-tables work great for discrete, small state spaces like mazes. But they don't scale:
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-yellow-800">
					<li><strong>Memory:</strong> A 30×30 maze has 900 states × 4 actions = 3,600 Q-values</li>
					<li><strong>Continuous States:</strong> Can't handle pixel inputs or continuous observations</li>
					<li><strong>Generalization:</strong> Each state learned independently, no transfer</li>
				</ul>
				<p class="text-sm text-yellow-800 mt-2">
					That's why complex games like Mario use <strong>neural networks</strong> (function approximation) instead of Q-tables. Check out the Neuroevolution example to see how!
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/src/lib/controller/MazeRLController.js"
				target="_blank">View source (MazeRLController.js)</a
			>
		</p>
	</article>
</ExperimentCard>
