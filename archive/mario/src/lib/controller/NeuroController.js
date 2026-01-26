/**
 * NeuroController - Reinforcement Learning Demo Controller
 *
 * Manages the lifecycle of the RL training system:
 * - PyScriptManager for event-driven Python module loading
 * - Neural network module initialization
 * - Mario agent initialization
 * - Communication between Python, emulator, and UI
 *
 * @author Guinetik
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class NeuroController {
	constructor() {
		this.logger = createLogger({
			prefix: 'NeuroController',
			level: 'debug'
		});

		/** @type {PyScriptManager|null} */
		this.pyScriptManager = null;

		/** @type {Object|null} - Python exported functions from agent */
		this.pythonExports = null;

		/** @type {boolean} */
		this.isInitialized = false;

		/** @type {boolean} */
		this.neuralModuleLoaded = false;
	}

	/**
	 * Initialize controller - load neural network then agent
	 */
	async initialize() {
		this.logger.log('🔵 Initializing NeuroController...');

		if (this.isInitialized) {
			this.logger.warn('⚠️ NeuroController already initialized');
			return;
		}

		try {
			// Setup window callbacks FIRST
			this._setupCallbacks();

			// Create PyScriptManager instance
			this.pyScriptManager = new PyScriptManager();

			// Load neural network module first (exports to builtins, no ready signal)
			this.logger.log('🔵 Loading neural network module...');
			const neuralUrl = getLink('python/ml/neural/neural.py');

			// Create script element for neural module (doesn't use PyScriptManager ready signal)
			const neuralScript = document.createElement('script');
			neuralScript.type = 'py';
			neuralScript.src = neuralUrl;
			neuralScript.id = 'neural-script';

			const neuralContainer = document.getElementById('neural-script') || document.body;
			neuralContainer.appendChild(neuralScript);

			// Wait for neural module to load (it exports to builtins)
			await new Promise(resolve => setTimeout(resolve, 1000));
			this.neuralModuleLoaded = true;
			this.logger.log('✅ Neural network module loaded');

			// Load Mario agent with PyScriptManager
			this.logger.log('🔵 Loading Mario agent module...');
			const agentUrl = getLink('python/ml/neural/agent.py');

			try {
				// PyScriptManager generates script ID automatically, 'body' means append to document.body
			this.pythonExports = await this.pyScriptManager.runScript(agentUrl, 'body');

				this.logger.log('✅ Mario agent ready! Exports:', Object.keys(this.pythonExports));
				this.isInitialized = true;

				// Notify UI that Python is ready
				if (window.rlUIHandler && window.rlUIHandler.onPythonReady) {
					window.rlUIHandler.onPythonReady();
				}
			} catch (error) {
				this.logger.error('❌ Failed to load Mario agent:', error);
				if (window.rlUIHandler && window.rlUIHandler.onError) {
					window.rlUIHandler.onError(`Failed to load agent: ${error.message}`);
				}
				throw error;
			}
		} catch (error) {
			this.logger.error('❌ Failed to initialize NeuroController:', error);
			throw error;
		}
	}

	/**
	 * Setup window callbacks that Python will call
	 */
	_setupCallbacks() {
		this.logger.log('🔵 Setting up window callbacks...');

		// Create Mario-specific logger for Python to use
		const marioLogger = createLogger({
			prefix: 'MarioAgent',
			level: 'debug'
		});

		// Expose logger methods to Python via window
		window.marioLogger = {
			log: (...args) => marioLogger.log(...args),
			debug: (...args) => marioLogger.debug(...args),
			info: (...args) => marioLogger.info(...args),
			warn: (...args) => marioLogger.warn(...args),
			error: (...args) => marioLogger.error(...args),
			group: (label) => console.group(`[MarioAgent] ${label}`),
			groupEnd: () => console.groupEnd(),
			// Convenience methods - use console.log directly for group content
			gen: (genNum, msg) => console.log(`[Gen ${genNum}] ${msg}`),
			fitness: (msg) => console.log(`[Fitness] ${msg}`),
			evolution: (msg) => console.log(`[Evolution] ${msg}`),
			champion: (msg) => console.log(`[Champion] ${msg}`),
			vision: (msg) => console.log(`[Vision] ${msg}`),
			network: (msg) => console.log(`[Network] ${msg}`),
			frame: (msg) => console.log(`[Frame] ${msg}`)
		};

		window.updateRLStatus = (status, message) => {
			this.logger.log('🟢 updateRLStatus called:', status, message);
			if (window.rlUIHandler && window.rlUIHandler.onStatusUpdate) {
				window.rlUIHandler.onStatusUpdate(status, message);
			}
		};

		window.updateRLMetrics = (episode, reward, highScore, currentDistance) => {
			this.logger.log('🟢 updateRLMetrics called:', { episode, reward, highScore, currentDistance });
			if (window.rlUIHandler && window.rlUIHandler.onMetricsUpdate) {
				window.rlUIHandler.onMetricsUpdate(episode, reward, highScore, currentDistance);
			}
		};

		this.logger.log('✅ Window callbacks registered');
		this.logger.log('✅ marioLogger exposed to Python');
	}

	/**
	 * Start training
	 * @param {string} networkType - Type of neural network to use
	 */
	startTraining(networkType = 'simple-feedforward') {
		this.logger.log('🔵 startTraining() called with network:', networkType);

		if (!this.isInitialized || !this.pythonExports) {
			this.logger.error('❌ Controller not initialized or Python not ready');
			if (window.rlUIHandler && window.rlUIHandler.onError) {
				window.rlUIHandler.onError('Python not ready yet. Please wait a moment.');
			}
			return;
		}

		if (this.pythonExports.startRLTraining) {
			this.logger.log('🔵 Calling pythonExports.startRLTraining() with network:', networkType);
			this.pythonExports.startRLTraining(networkType);
		} else {
			this.logger.error('🔴 startRLTraining not found in exports');
		}
	}

	/**
	 * Pause training
	 */
	pauseTraining() {
		this.logger.log('🔵 pauseTraining() called');

		if (this.pythonExports?.pauseRLTraining) {
			this.pythonExports.pauseRLTraining();
		} else {
			this.logger.error('🔴 pauseRLTraining not found in exports');
		}
	}

	/**
	 * Reset training
	 */
	resetTraining() {
		this.logger.log('🔵 resetTraining() called');

		if (this.pythonExports?.resetRLTraining) {
			this.pythonExports.resetRLTraining();
		} else {
			this.logger.error('🔴 resetRLTraining not found in exports');
		}
	}

	/**
	 * Stop training
	 */
	stopTraining() {
		this.logger.log('🔵 stopTraining() called');

		if (this.pythonExports?.stopRLTraining) {
			this.pythonExports.stopRLTraining();
		} else {
			this.logger.error('🔴 stopRLTraining not found in exports');
		}
	}

	/**
	 * Clean up resources
	 */
	destroy() {
		if (this.pyScriptManager) {
			this.pyScriptManager.destroy();
			this.pyScriptManager = null;
		}

		delete window.updateRLStatus;
		delete window.updateRLMetrics;
		delete window.rlUIHandler;

		this.pythonExports = null;
		this.isInitialized = false;
		this.neuralModuleLoaded = false;
		this.logger.log('✅ NeuroController destroyed');
	}
}
