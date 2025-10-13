<script>
	import ExperimentCard from '$lib/components/ExperimentCard.svelte';
	import NesEmulator from '$lib/nes/NesEmulator.svelte';
	import { getLink } from '$lib/utils.js';
	import RunPython from '$lib/RunPython.js';
	import { onMount, onDestroy } from 'svelte';

	// Page metadata
	let name = 'Reinforcement Learning';

	// Python runner instance
	let pyScriptRunner = RunPython();

	// UI State
	let status = $state('initializing'); // 'initializing' | 'ready' | 'training' | 'playing' | 'paused'
	let statusMessage = $state('Initializing emulator...');
	let episode = $state(0);
	let totalReward = $state(0);
	let highScore = $state(0);

	// Emulator state
	let emulatorReady = false;
	let savedState = $state(null); // Store saved state in memory
	let hasState = $state(false);

	onMount(async () => {
		console.log('🎮 RL Page mounted');

		// Expose JS callback functions for Python to call
		window.updateRLStatus = (newStatus, message) => {
			console.log('🟢 [JS] updateRLStatus called:', newStatus, message);
			status = newStatus;
			statusMessage = message;
		};

		window.updateRLMetrics = (episodeNum, reward, high) => {
			episode = episodeNum;
			totalReward = reward;
			highScore = high;
		};

		// Expose save/load state functions for Python
		window.saveStateJS = saveState;
		window.loadStateJS = loadState;

		// Load Python neural network module first
		const neuralUrl = getLink('python/neural.py');
		await pyScriptRunner.runScript(neuralUrl, 'neural-script', false);
		console.log('✅ [JS] Neural network module loaded');

		// Load Python Mario agent script
		const marioAgentUrl = getLink('python/mario_agent.py');
		await pyScriptRunner.runScript(marioAgentUrl, 'mario-script', false);
		console.log('✅ [JS] Mario agent loaded');
	});

	onDestroy(() => {
		if (pyScriptRunner) {
			pyScriptRunner.destroy();
		}
	});

	async function handleEmulatorReady(emulator) {
		console.log('✅ [JS] NES Emulator ready!', emulator);
		console.log('   Is loaded:', emulator.isLoaded());
		console.log('   NES object:', emulator.nes);
		emulatorReady = true;

		statusMessage = 'Emulator ready. Click "Play Game" to test or "Start Training" to begin AI learning.';
		status = 'ready';
	}

	function handleEmulatorError(error) {
		console.error('❌ [JS] Emulator error:', error);
		status = 'error';
		statusMessage = `Error: ${error.message}`;
	}

	function startTraining() {
		console.log('🔵 [JS] startTraining() called');

		if (!emulatorReady) {
			alert('Emulator not ready yet!');
			return;
		}

		if (window.startRLTraining) {
			console.log('🔵 [JS] Calling window.startRLTraining()');
			window.startRLTraining();
		} else {
			console.error('🔴 [JS] window.startRLTraining not found! Python may not be ready.');
			status = 'error';
			statusMessage = 'Python is not ready yet. Please wait a moment and try again.';
		}
	}

	function pauseTraining() {
		if (window.pauseRLTraining) {
			window.pauseRLTraining();
		}
	}

	function resetTraining() {
		if (window.resetRLTraining) {
			window.resetRLTraining();
		}
	}

	function playDemo() {
		if (window.playRLDemo) {
			window.playRLDemo();
		}
	}

	function playManual() {
		console.log('🔵 [JS] playManual() called');

		if (!emulatorReady) {
			alert('Emulator not ready yet!');
			return;
		}

		// Stop any training
		if (status === 'training') {
			pauseTraining();
		}

		// Enable keyboard controls
		const emulator = window.nesEmulator;
		if (emulator) {
			emulator.enableKeyboard();

			// Start emulator
			if (!emulator.isRunning()) {
				console.log('▶️ Starting emulator for manual play');
				emulator.start();
			}

			status = 'playing';
			statusMessage = 'Manual play mode active! Use keyboard to control Mario.';
		}
	}

	function stopManual() {
		console.log('🔵 [JS] stopManual() called');

		const emulator = window.nesEmulator;
		if (emulator) {
			emulator.disableKeyboard();
			emulator.stop();

			status = 'ready';
			statusMessage = 'Manual play stopped. Ready for next action.';
		}
	}

	function saveState() {
		console.log('💾 [JS] saveState() called');

		const emulator = window.nesEmulator;
		if (emulator && emulator.controller) {
			const state = emulator.controller.saveState();
			if (state) {
				// Convert to JSON string
				const stateJson = JSON.stringify(state, null, 2);

				// Save to memory
				savedState = stateJson;
				hasState = true;

				// Print JSON to console for copying to data/state.json
				console.log('📋 Copy this JSON and save it to static/data/state.json:');
				console.log(stateJson);

				// Try to download as file
				try {
					const blob = new Blob([stateJson], { type: 'application/json' });
					const url = URL.createObjectURL(blob);
					const a = document.createElement('a');
					a.href = url;
					a.download = 'state.json';
					a.click();
					URL.revokeObjectURL(url);
					statusMessage = 'State saved! Check your downloads for state.json';
				} catch (error) {
					console.error('Could not download file:', error);
					statusMessage = 'State JSON printed to console - copy it to static/data/state.json';
				}
			}
		}
	}

	function loadState() {
		console.log('📂 [JS] loadState() called - opening file picker');

		// Create file input for picking JSON file
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.json,application/json';

		input.onchange = async (e) => {
			const file = e.target.files[0];
			if (!file) {
				console.log('No file selected');
				return;
			}

			try {
				// Read file contents
				const text = await file.text();
				const stateJson = JSON.parse(text); // Validate JSON

				// Save to memory
				savedState = text;
				hasState = true;

				console.log('✅ State file loaded into memory');
				statusMessage = `State loaded from ${file.name}! Click Play or Start Training to use it.`;

				// Immediately apply the state to the emulator if it's ready
				const emulator = window.nesEmulator;
				if (emulator && emulator.controller) {
					const loaded = emulator.controller.loadState(text);
					if (loaded) {
						console.log('✅ State applied to emulator');
						statusMessage = `State from ${file.name} applied! Game is now at saved position.`;
					}
				}
			} catch (error) {
				console.error('❌ Failed to load state file:', error);
				statusMessage = 'Error loading state file. Make sure it\'s a valid state.json file.';
			}
		};

		// Trigger file picker
		input.click();
	}

	// Computed status display
	$effect(() => {
		console.log('Status changed:', status, statusMessage);
	});
</script>

<ExperimentCard props={{ previousPage: '/examples/sentiment', nextPage: '/' }}>
	<div slot="py_slot" class="flex h-full flex-col p-5 space-y-4">
		<!-- Emulator Display -->
		<div class="flex justify-center">
			<NesEmulator
				romPath={getLink('data/mario.nes')}
				scale={2}
				onReady={handleEmulatorReady}
				onError={handleEmulatorError}
			/>
		</div>

		<!-- Control Buttons -->
		<div class="space-y-3">
			<!-- Row 1: Play Game and Pause -->
			<div class="grid grid-cols-2 gap-3">
				<button
					onclick={status === 'playing' ? stopManual : playManual}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-purple-500 px-6 py-3 font-bold text-white hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'playing' ? '⏹️ Stop Playing' : '🎮 Play Game'}
				</button>
				<button
					onclick={pauseTraining}
					disabled={status !== 'training'}
					class="rounded bg-yellow-500 px-6 py-3 font-bold text-white hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					⏸️ Pause
				</button>
			</div>

			<!-- Row 2: Start Training and Reset -->
			<div class="grid grid-cols-2 gap-3">
				<button
					onclick={startTraining}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-green-500 px-6 py-3 font-bold text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					{status === 'training' ? '🏃 Training...' : '▶️ Start Training'}
				</button>
				<button
					onclick={resetTraining}
					disabled={status === 'training'}
					class="rounded bg-red-500 px-6 py-3 font-bold text-white hover:bg-red-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					🔄 Reset
				</button>
			</div>

			<!-- Row 3: Save and Load State -->
			<div class="grid grid-cols-2 gap-3">
				<button
					onclick={saveState}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-blue-500 px-6 py-3 font-bold text-white hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					💾 Save State
				</button>
				<button
					onclick={loadState}
					disabled={status === 'training' || status === 'initializing'}
					class="rounded bg-cyan-500 px-6 py-3 font-bold text-white hover:bg-cyan-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
				>
					📂 Load State {hasState ? '✓' : ''}
				</button>
			</div>
		</div>

		<!-- Metrics Display -->
		<div class="grid grid-cols-3 gap-3">
			<div class="rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">Episode</div>
				<div class="text-3xl font-bold">{episode}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-green-500 to-green-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">Total Reward</div>
				<div class="text-3xl font-bold">{totalReward.toFixed(1)}</div>
			</div>
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 p-4 text-white shadow-lg">
				<div class="text-sm font-semibold opacity-90">High Score</div>
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
							: status === 'ready'
								? 'text-blue-700'
								: 'text-gray-600'}"
			>
				{statusMessage}
			</p>
		</div>

		<!-- Keyboard Controls (only show when playing) -->
		{#if status === 'playing'}
			<div class="rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 p-4 text-white shadow-lg">
				<h3 class="mb-3 text-lg font-bold">⌨️ Keyboard Controls</h3>
				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<div class="font-semibold">Arrow Keys</div>
						<div class="opacity-90">Move Mario</div>
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

		<!-- Hidden Python script containers -->
		<div id="neural-script" style="display: none;"></div>
		<div id="mario-script" style="display: none;"></div>
	</div>

	<article slot="content_slot" class="mb-10">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none space-y-4">
			<p class="text-sm">
				Watch an AI agent learn to play Super Mario Bros using Reinforcement Learning! This
				demonstration shows how machines can learn from trial and error, just like humans do.
			</p>

			<div class="rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-blue-900">🤖 What is Reinforcement Learning?</h3>
				<p class="text-sm text-blue-800">
					Reinforcement Learning (RL) is a type of machine learning where an agent learns to make
					decisions by interacting with an environment. The agent receives rewards for good actions
					and penalties for bad ones, gradually learning the optimal strategy through trial and
					error. It's how AlphaGo mastered chess, how robots learn to walk, and how self-driving
					cars learn to navigate.
				</p>
			</div>

			<div class="rounded-lg bg-purple-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-purple-900">🎮 The Environment: Super Mario Bros</h3>
				<p class="text-sm text-purple-800">
					We're using the classic NES game Super Mario Bros as our training environment. The agent
					receives the game screen as input (visual observations) and must learn to control Mario's
					movements (jump, run, duck) to maximize its score. The game provides natural rewards:
					collecting coins, defeating enemies, and progressing through the level.
				</p>
			</div>

			<div class="rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-green-900">🧠 The Agent & Algorithm</h3>
				<p class="text-sm text-green-800 mb-3">
					This demo uses a Q-Learning approach with a neural network (Deep Q-Network or DQN). The
					agent observes the game state, predicts which action will yield the highest future
					reward, takes that action, and learns from the outcome. Over many episodes, it discovers
					patterns like "jumping over enemies is good" and "falling into pits is bad."
				</p>
				<ul class="list-disc space-y-1 pl-5 text-sm text-green-800">
					<li><strong>State:</strong> Current game screen (pixel data)</li>
					<li><strong>Actions:</strong> Controller inputs (A, B, directional buttons)</li>
					<li><strong>Rewards:</strong> Score changes, level progress, survival time</li>
					<li><strong>Goal:</strong> Maximize cumulative reward over time</li>
				</ul>
			</div>

			<div class="rounded-lg bg-amber-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-amber-900">📊 Training Metrics</h3>
				<ul class="list-disc space-y-1 pl-5 text-sm text-amber-800">
					<li>
						<strong>Episode:</strong> One complete playthrough of the level (ends on death or completion)
					</li>
					<li><strong>Total Reward:</strong> Cumulative score earned in current episode</li>
					<li><strong>High Score:</strong> Best reward achieved across all episodes</li>
				</ul>
			</div>

			<div class="rounded-lg bg-red-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-red-900">⚡ Real-Time Learning in the Browser</h3>
				<p class="text-sm text-red-800">
					This entire demo runs in your browser using PyScript (Python) and JSNes (JavaScript NES
					emulator). The RL agent is implemented in Python, controlling the emulator through a clean
					event-driven architecture. No servers, no cloud compute - just pure client-side machine
					learning!
				</p>
			</div>

			<div class="rounded-lg bg-cyan-50 p-4">
				<h3 class="mb-2 text-lg font-bold text-cyan-900">🎯 How to Use</h3>
				<ol class="list-decimal space-y-2 pl-5 text-sm text-cyan-800">
					<li><strong>Play Game:</strong> Try playing Mario yourself! Get a feel for the controls and difficulty</li>
					<li><strong>Start Training:</strong> Begin the RL training loop and watch the AI learn</li>
					<li><strong>Observe:</strong> Watch as the agent explores different strategies</li>
					<li><strong>Pause/Resume:</strong> Pause training to inspect the agent's current behavior</li>
					<li><strong>Reset:</strong> Clear training progress and start learning from scratch</li>
				</ol>
				<p class="mt-3 text-xs text-cyan-700">
					💡 <strong>Tip:</strong> Play the game manually first during class intermission! It helps students appreciate how hard the task is and makes the AI's learning more impressive.
				</p>
			</div>
		</div>

		<p class="mt-6">
			<a
				class="text-sky-500"
				href="https://github.com/guinetik/pyscript-lab/blob/master/static/python/rl_agent.py"
				target="_blank">View source</a
			>
		</p>
	</article>
</ExperimentCard>
