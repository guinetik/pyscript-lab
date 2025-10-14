/**
 * SentimentAnalysisController
 *
 * Business logic layer for sentiment analysis with event-driven initialization.
 * Handles PyScriptManager lifecycle, window callbacks, and exported functions.
 *
 * @author Guinetik
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class SentimentAnalysisController {
	constructor() {
		this.logger = createLogger({
			prefix: 'SentimentAnalysisController',
			level: 'debug'
		});

		/** @type {PyScriptManager|null} */
		this.pyScriptManager = null;

		/** @type {Object|null} - Python exported functions */
		this.pythonExports = null;

		/** @type {boolean} */
		this.isInitialized = false;
	}

	/**
	 * Initialize controller - setup callbacks and load Python with event-driven approach
	 */
	async initialize() {
		this.logger.log('🔵 [Controller] initialize() called');

		if (this.isInitialized) {
			this.logger.warn('⚠️ Controller already initialized');
			return;
		}

		try {
			this.logger.log('🔵 [Controller] Setting up callbacks...');
			// Setup window callbacks FIRST
			this._setupCallbacks();

			// Create PyScriptManager and load script with Promise-based approach
			this.pyScriptManager = new PyScriptManager();
			const pyScriptUrl = getLink('python/ml/sentiment_analysis.py');

			this.logger.log('🔵 [Controller] Loading Python script...');

			// Await the Promise returned by runScript
			try {
				this.pythonExports = await this.pyScriptManager.runScript(
					pyScriptUrl,
					'sentiment-analysis-script'
				);

				this.logger.log(
					'✅ [Controller] Python script ready! Exports:',
					Object.keys(this.pythonExports)
				);
				this.isInitialized = true;

				// Notify UI that Python is ready
				if (window.sentimentUIHandler && window.sentimentUIHandler.onPythonReady) {
					window.sentimentUIHandler.onPythonReady();
				}
			} catch (error) {
				this.logger.error('❌ [Controller] Python script failed to load:', error);
				if (window.sentimentUIHandler && window.sentimentUIHandler.onError) {
					window.sentimentUIHandler.onError(`Failed to load Python: ${error.message}`);
				}
				throw error;
			}
		} catch (error) {
			this.logger.error('❌ [Controller] Failed to initialize:', error);
			throw error;
		}
	}

	/**
	 * Setup window callbacks that Python will call
	 * These delegate to the UIHandler exposed by Svelte
	 */
	_setupCallbacks() {
		this.logger.log('🔵 [Controller] _setupCallbacks() called');

		window.onModelReady = (stats) => {
			this.logger.log('🔵 [Controller] onModelReady called, delegating to UIHandler');
			if (window.sentimentUIHandler) {
				// Python now converts to plain JS object using to_js(), so just pass through
				window.sentimentUIHandler.onModelReady(stats);
			} else {
				console.error('🔴 [Controller] window.sentimentUIHandler not found!');
			}
		};

		window.onSentimentPrediction = (result) => {
			this.logger.log('🔵 [Controller] onSentimentPrediction called, delegating to UIHandler');
			if (window.sentimentUIHandler) {
				// Python now converts to plain JS object using to_js(), so just pass through
				window.sentimentUIHandler.onPrediction(result);
			} else {
				console.error('🔴 [Controller] window.sentimentUIHandler not found!');
			}
		};

		window.onModelUpdated = (update) => {
			this.logger.log('🔵 [Controller] onModelUpdated called, delegating to UIHandler');
			if (window.sentimentUIHandler) {
				// Python now converts to plain JS object using to_js(), so just pass through
				window.sentimentUIHandler.onModelUpdate(update);
			} else {
				console.error('🔴 [Controller] window.sentimentUIHandler not found!');
			}
		};

		window.onSentimentError = (message) => {
			console.error('🔴 [Controller] onSentimentError called, delegating to UIHandler');
			if (window.sentimentUIHandler) {
				window.sentimentUIHandler.onError(message);
			} else {
				console.error('🔴 [Controller] window.sentimentUIHandler not found!');
			}
		};

		this.logger.log('✅ [Controller] Window callbacks registered');
		this.logger.log('🔵 [Controller] Checking for UIHandler:', typeof window.sentimentUIHandler);
	}

	/**
	 * Analyze sentiment - call Python
	 */
	analyzeSentiment(text) {
		this.logger.log('🔵 [Controller] analyzeSentiment() called with:', text.substring(0, 50));

		if (!this.isInitialized || !this.pythonExports) {
			console.error('❌ [Controller] Controller not initialized or Python not ready');
			if (window.sentimentUIHandler && window.sentimentUIHandler.onError) {
				window.sentimentUIHandler.onError('Python not ready yet. Please wait a moment.');
			}
			return;
		}

		if (this.pythonExports.predictSentiment) {
			this.logger.log('🔵 [Controller] Calling pythonExports.predictSentiment()...');
			this.pythonExports.predictSentiment(text);
			this.logger.log('🔵 [Controller] Call completed');
		} else {
			console.error('🔴 [Controller] predictSentiment not found in exports');
		}
	}

	/**
	 * Confirm prediction was correct
	 */
	confirmPrediction() {
		if (this.pythonExports?.handleCorrectPrediction) {
			this.pythonExports.handleCorrectPrediction();
		} else {
			this.logger.error('🔴 [Controller] handleCorrectPrediction not found in exports');
		}
	}

	/**
	 * Correct prediction with new label
	 */
	correctPrediction(label) {
		if (this.pythonExports?.retrainWithCorrection) {
			this.pythonExports.retrainWithCorrection(label);
		} else {
			this.logger.error('🔴 [Controller] retrainWithCorrection not found in exports');
		}
	}

	/**
	 * Reset model
	 */
	resetModel() {
		if (this.pythonExports?.resetTraining) {
			this.pythonExports.resetTraining();
		} else {
			this.logger.error('🔴 [Controller] resetTraining not found in exports');
		}
	}

	/**
	 * Cleanup
	 */
	destroy() {
		if (this.pyScriptManager) {
			this.pyScriptManager.destroy();
			this.pyScriptManager = null;
		}

		delete window.onModelReady;
		delete window.onSentimentPrediction;
		delete window.onModelUpdated;
		delete window.onSentimentError;
		delete window.sentimentUIHandler;

		this.pythonExports = null;
		this.isInitialized = false;
		this.logger.log('✅ Controller destroyed');
	}
}
