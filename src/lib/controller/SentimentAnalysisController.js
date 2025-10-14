/**
 * SentimentAnalysisController
 *
 * Business logic layer for sentiment analysis.
 * Handles Python script loading, window callbacks, and Custom Events.
 *
 * @author Guinetik
 */

import RunPython from '$lib/RunPython.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class SentimentAnalysisController {
	constructor() {
		this.logger = createLogger(
			{
				prefix: 'SentimentAnalysisController',
				level: 'debug'
			});
		this.pyScriptRunner = null;
		this.isInitialized = false;
	}

	/**
	 * Initialize controller - setup callbacks and load Python
	 */
	async initialize() {
		this.logger.log('🔵 [Controller] initialize() called');

		if (this.isInitialized) {
			this.logger.warn('⚠️ Controller already initialized');
			return;
		}

		this.logger.log('🔵 [Controller] Setting up callbacks...');
		// Setup window callbacks FIRST
		this._setupCallbacks();

		this.logger.log('🔵 [Controller] Creating RunPython instance...');
		// Then load Python script
		this.pyScriptRunner = RunPython();

		this.logger.log('🔵 [Controller] Getting script URL...');
		const pyScriptUrl = getLink('python/ml/sentiment_analysis.py');
		this.logger.log('🔵 [Controller] Script URL:', pyScriptUrl);

		this.logger.log('🔵 [Controller] Loading Python script...');
		this.pyScriptRunner.runScript(pyScriptUrl, 'sentiment-analysis-script', false);

		this.isInitialized = true;
		this.logger.log('✅ [Controller] SentimentAnalysisController initialized');
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

		if (!this.isInitialized) {
			console.error('❌ [Controller] Controller not initialized');
			return;
		}

		this.logger.log('🔵 [Controller] Checking for window.predictSentiment...');
		this.logger.log('🔵 [Controller] window.predictSentiment:', typeof window.predictSentiment);

		if (window.predictSentiment) {
			this.logger.log('🔵 [Controller] Calling window.predictSentiment()...');
			window.predictSentiment(text);
			this.logger.log('🔵 [Controller] Call completed');
		} else {
			console.error('🔴 [Controller] window.predictSentiment not found');
			window.dispatchEvent(
				new CustomEvent('sentimentError', {
					detail: { message: 'Python not ready yet' }
				})
			);
		}
	}

	/**
	 * Confirm prediction was correct
	 */
	confirmPrediction() {
		if (window.handleCorrectPrediction) {
			window.handleCorrectPrediction();
		}
	}

	/**
	 * Correct prediction with new label
	 */
	correctPrediction(label) {
		if (window.retrainWithCorrection) {
			window.retrainWithCorrection(label);
		}
	}

	/**
	 * Reset model
	 */
	resetModel() {
		if (window.resetTraining) {
			window.resetTraining();
		}
	}

	/**
	 * Cleanup
	 */
	destroy() {
		if (this.pyScriptRunner) {
			this.pyScriptRunner.destroy();
			this.pyScriptRunner = null;
		}

		delete window.onModelReady;
		delete window.onSentimentPrediction;
		delete window.onModelUpdated;
		delete window.onSentimentError;

		this.isInitialized = false;
		this.logger.log('✅ Controller destroyed');
	}
}
