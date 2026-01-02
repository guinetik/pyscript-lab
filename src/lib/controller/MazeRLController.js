/**
 * MazeRLController
 *
 * Orchestrates Q-Learning reinforcement learning for maze solving.
 * Follows the data-only communication pattern with Python.
 *
 * Architecture:
 * - MazeEnvironment: Generates mazes in JavaScript
 * - QLearningAgent: Python Q-learning implementation
 * - AgentActor: Visualizes agent movement
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';

// Action encoding for Python communication
export const Actions = {
	UP: 'UP',
	DOWN: 'DOWN',
	LEFT: 'LEFT',
	RIGHT: 'RIGHT'
};

// Mock Maze Generator (will be replaced by Python)
class MazeEnvironment {
	constructor(rows, cols, cellSize) {
		this.rows = rows;
		this.cols = cols;
		this.cellSize = cellSize;
		this.grid = [];
		this.startPos = { row: 0, col: 0 };
		this.endPos = { row: rows - 1, col: cols - 1 };
	}

	generate() {
		// Initialize grid with all walls
		this.grid = [];
		for (let r = 0; r < this.rows; r++) {
			this.grid[r] = [];
			for (let c = 0; c < this.cols; c++) {
				this.grid[r][c] = {
					visited: false,
					walls: { top: true, right: true, bottom: true, left: true }
				};
			}
		}

		// Recursive backtracker algorithm
		const stack = [];
		let current = { row: 0, col: 0 };
		this.grid[0][0].visited = true;

		while (true) {
			const neighbors = this.getUnvisitedNeighbors(current.row, current.col);

			if (neighbors.length > 0) {
				const next = neighbors[Math.floor(Math.random() * neighbors.length)];
				this.removeWalls(current, next);
				this.grid[next.row][next.col].visited = true;
				stack.push(current);
				current = next;
			} else if (stack.length > 0) {
				current = stack.pop();
			} else {
				break;
			}
		}

		return this.toSerializable();
	}

	getUnvisitedNeighbors(row, col) {
		const neighbors = [];

		if (row > 0 && !this.grid[row - 1][col].visited) {
			neighbors.push({ row: row - 1, col, dir: 'top' });
		}
		if (col < this.cols - 1 && !this.grid[row][col + 1].visited) {
			neighbors.push({ row, col: col + 1, dir: 'right' });
		}
		if (row < this.rows - 1 && !this.grid[row + 1][col].visited) {
			neighbors.push({ row: row + 1, col, dir: 'bottom' });
		}
		if (col > 0 && !this.grid[row][col - 1].visited) {
			neighbors.push({ row, col: col - 1, dir: 'left' });
		}

		return neighbors;
	}

	removeWalls(current, next) {
		const rowDiff = current.row - next.row;
		const colDiff = current.col - next.col;

		if (rowDiff === 1) {
			this.grid[current.row][current.col].walls.top = false;
			this.grid[next.row][next.col].walls.bottom = false;
		} else if (rowDiff === -1) {
			this.grid[current.row][current.col].walls.bottom = false;
			this.grid[next.row][next.col].walls.top = false;
		} else if (colDiff === 1) {
			this.grid[current.row][current.col].walls.left = false;
			this.grid[next.row][next.col].walls.right = false;
		} else if (colDiff === -1) {
			this.grid[current.row][current.col].walls.right = false;
			this.grid[next.row][next.col].walls.left = false;
		}
	}

	canMove(row, col, action) {
		if (row < 0 || row >= this.rows || col < 0 || col >= this.cols) {
			return false;
		}

		const directionMap = {
			[Actions.UP]: 'top',
			[Actions.DOWN]: 'bottom',
			[Actions.LEFT]: 'left',
			[Actions.RIGHT]: 'right'
		};

		return !this.grid[row][col].walls[directionMap[action]];
	}

	getNextPosition(row, col, action) {
		if (!this.canMove(row, col, action)) {
			return { row, col };
		}

		switch (action) {
			case Actions.UP:
				return { row: row - 1, col };
			case Actions.DOWN:
				return { row: row + 1, col };
			case Actions.LEFT:
				return { row, col: col - 1 };
			case Actions.RIGHT:
				return { row, col: col + 1 };
			default:
				return { row, col };
		}
	}

	toSerializable() {
		return {
			grid: this.grid,
			rows: this.rows,
			cols: this.cols,
			startPos: this.startPos,
			endPos: this.endPos
		};
	}
}

// Q-Learning Agent is implemented in Python
// Python script handles training loop and Q-table management

// Agent Actor for visualization
export class AgentActor {
	constructor(position) {
		this.position = { ...position };
		this.targetPosition = { ...position };
		this.isMoving = false;
		this.moveProgress = 0;
		this.moveSpeed = 0.08; // 0 to 1 per frame (smoother tweening across 250ms moves)
	}

	setTarget(newPosition) {
		this.targetPosition = { ...newPosition };
		this.isMoving = true;
		this.moveProgress = 0;
	}

	update() {
		if (!this.isMoving) return;

		this.moveProgress += this.moveSpeed;
		if (this.moveProgress >= 1) {
			this.position = { ...this.targetPosition };
			this.isMoving = false;
			this.moveProgress = 0;
		}
	}

	getCurrentPosition() {
		if (!this.isMoving) {
			return this.position;
		}

		// Interpolate between current and target
		return {
			row: this.position.row + (this.targetPosition.row - this.position.row) * this.moveProgress,
			col: this.position.col + (this.targetPosition.col - this.position.col) * this.moveProgress
		};
	}
}

// Main Controller
export class MazeRLController {
	constructor() {
		this.environment = null;
		this.actor = null;
		this.isTraining = false;

		// Python integration
		this.pyScriptManager = new PyScriptManager();
		this.pythonExports = null;

		// Callbacks for UI updates
		this.callbacks = {
			onMazeGenerated: null,
			onAgentMove: null,
			onMetricsUpdate: null,
			onTrainingComplete: null,
			onEpisodeEnd: null,
			onDemoComplete: null
		};
	}

	// Initialize Python Q-learning module
	async initialize() {
		console.log('[MazeRLController] Initializing Python Q-learning...');

		// Set up window callbacks for Python to call
		window.mazeRLCallbacks = {
			onAgentMove: (data) => {
				if (this.callbacks.onAgentMove) {
					this.callbacks.onAgentMove(data);
				}
			},
			onMetricsUpdate: (metrics) => {
				if (this.callbacks.onMetricsUpdate) {
					this.callbacks.onMetricsUpdate(metrics);
				}
			},
			onEpisodeEnd: (episodeData) => {
				// Reset agent to start for next episode
				if (this.environment && this.callbacks.onEpisodeEnd) {
					this.callbacks.onEpisodeEnd(episodeData);
				}
			},
			onDemoComplete: (results) => {
				if (this.callbacks.onDemoComplete) {
					this.callbacks.onDemoComplete(results);
				}
			}
		};

		// Load Python Q-learning module
		this.pythonExports = await this.pyScriptManager.runScript(
			'/python/ml/rl/q_learning.py',
			'body'
		);

		console.log('[MazeRLController] Python Q-learning initialized ✅');
	}

	// Generate new maze
	generateMaze(difficulty = 'medium') {
		const difficultySettings = {
			easy: { rows: 10, cols: 10, cellSize: 40 },
			medium: { rows: 15, cols: 15, cellSize: 30 },
			hard: { rows: 20, cols: 20, cellSize: 25 },
			insane: { rows: 30, cols: 30, cellSize: 20 }
		};

		const settings = difficultySettings[difficulty] || difficultySettings.medium;
		this.environment = new MazeEnvironment(settings.rows, settings.cols, settings.cellSize);

		const mazeData = this.environment.generate();
		this.actor = new AgentActor(mazeData.startPos);

		// Send maze to Python with difficulty level
		if (this.pythonExports && this.pythonExports.setMaze) {
			this.pythonExports.setMaze(mazeData, difficulty);
			console.log('[MazeRLController] Maze sent to Python with difficulty:', difficulty);
		}

		// Callback to UI
		if (this.callbacks.onMazeGenerated) {
			this.callbacks.onMazeGenerated(mazeData);
		}

		console.log(`[MazeRLController] Generated ${difficulty} maze (${settings.rows}x${settings.cols})`);
		return mazeData;
	}

	// Start training (calls Python)
	startTraining() {
		if (this.isTraining) return;

		if (!this.pythonExports || !this.pythonExports.startTraining) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = true;
		console.log('[MazeRLController] Starting Python training...');
		this.pythonExports.startTraining();
	}

	// Pause training (calls Python)
	pauseTraining() {
		if (!this.pythonExports || !this.pythonExports.pauseTraining) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = false;
		console.log('[MazeRLController] Pausing Python training...');
		this.pythonExports.pauseTraining();
	}

	// Resume training (calls Python)
	resumeTraining() {
		if (!this.pythonExports || !this.pythonExports.resumeTraining) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = true;
		console.log('[MazeRLController] Resuming Python training...');
		this.pythonExports.resumeTraining();
	}

	// Stop training (calls Python)
	stopTraining() {
		if (!this.pythonExports || !this.pythonExports.stopTraining) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = false;
		console.log('[MazeRLController] Stopping Python training...');
		this.pythonExports.stopTraining();
	}

	// Reset training (calls Python)
	resetTraining() {
		if (!this.pythonExports || !this.pythonExports.resetTraining) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = false;

		// Reset actor to start position
		if (this.environment) {
			this.actor = new AgentActor(this.environment.startPos);
		}

		console.log('[MazeRLController] Resetting Python training...');
		this.pythonExports.resetTraining();
	}

	// Run demo with learned policy (calls Python)
	runDemo() {
		if (!this.pythonExports || !this.pythonExports.runDemo) {
			console.error('[MazeRLController] Python not loaded!');
			return;
		}

		this.isTraining = false;
		console.log('[MazeRLController] Running demo with learned policy...');
		this.pythonExports.runDemo();
	}

	// Cleanup
	destroy() {
		console.log('[MazeRLController] Starting cleanup...');

		// Stop Python training
		if (this.pythonExports && this.pythonExports.stopTraining) {
			this.pythonExports.stopTraining();
		}

		// Stop Python demo
		if (this.pythonExports && this.pythonExports.stopDemo) {
			this.pythonExports.stopDemo();
		}

		// Clean up window callbacks
		if (window.mazeRLCallbacks) {
			delete window.mazeRLCallbacks;
		}

		// Clean up PyScriptManager (synchronous, doesn't remove DOM elements)
		if (this.pyScriptManager) {
			this.pyScriptManager.destroy();
		}

		console.log('[MazeRLController] Destroyed');
	}
}
