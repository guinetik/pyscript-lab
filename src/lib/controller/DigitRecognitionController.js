/**
 * DigitRecognitionController
 *
 * Manages the machine learning digit recognition feature with proper separation of concerns.
 * Handles:
 * - PyScript runner setup and lifecycle
 * - Window callback registration for Python to call
 * - Business logic layer between Python ML engine and Svelte UI
 * - Canvas image data extraction and transmission to Python
 *
 * This controller follows the architectural principle:
 * - Python performs ML computations and sends only data
 * - JavaScript/Svelte handles all rendering and DOM manipulation
 * - Controller manages the communication layer
 *
 * @author Guinetik
 */

import RunPython from '$lib/RunPython.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class DigitRecognitionController {
	/**
	 * Creates a new DigitRecognitionController instance.
	 */
	constructor() {
		this.logger = createLogger({
			prefix: 'DigitRecognitionController',
			level: 'debug'
		});

		/** @type {RunPython|null} */
		this.pyScriptRunner = null;

		/** @type {boolean} */
		this.isInitialized = false;

		/** @type {HTMLCanvasElement|null} */
		this.canvas = null;
	}

	/**
	 * Initialize the controller by setting up PyScript and callbacks.
	 *
	 * @returns {Promise<void>}
	 */
	async initialize() {
		if (this.isInitialized) {
			this.logger.warn('⚠️ DigitRecognitionController already initialized');
			return;
		}

		try {
			this.logger.log('🔵 Initializing DigitRecognitionController...');

			// Setup callbacks FIRST (before Python loads)
			this._setupCallbacks();

			// Load Python script
			this.pyScriptRunner = RunPython();
			const pyScriptUrl = getLink('python/ml/digit_recognition.py');
			this.pyScriptRunner.runScript(pyScriptUrl, 'script_gutter', false);

			this.isInitialized = true;
			this.logger.log('✅ DigitRecognitionController initialized');
		} catch (error) {
			this.logger.error('❌ Failed to initialize DigitRecognitionController:', error);
			throw error;
		}
	}

	/**
	 * Setup window callbacks that Python will call.
	 *
	 * These callbacks receive data from Python and delegate to the UIHandler
	 * exposed by the Svelte component.
	 *
	 * @private
	 */
	_setupCallbacks() {
		this.logger.log('🔵 Setting up window callbacks...');

		// Callback for prediction results
		window.updatePredictionResult = (data) => {
			this.logger.log('🟢 updatePredictionResult called:', data);
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onPredictionResult(data);
			} else {
				this.logger.error('🔴 window.digitRecognitionUIHandler not found!');
			}
		};

		// Callback for model state updates
		window.updateModelState = (data) => {
			this.logger.log('🟢 updateModelState called:', data);
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onModelState(data);
			} else {
				this.logger.error('🔴 window.digitRecognitionUIHandler not found!');
			}
		};

		// Callback for UI state updates (status messages)
		window.updateUIState = (status, message) => {
			this.logger.log('🟢 updateUIState called:', status, message);
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onUIState(status, message);
			} else {
				this.logger.error('🔴 window.digitRecognitionUIHandler not found!');
			}
		};

		// Callback for training examples data
		window.updateTrainingExamples = (data) => {
			this.logger.log('🟢 updateTrainingExamples called with', data?.examples?.length || 0, 'examples');
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onTrainingExamples(data);
			} else {
				this.logger.error('🔴 window.digitRecognitionUIHandler not found!');
			}
		};

		this.logger.log('✅ Window callbacks registered');
	}

	/**
	 * Set the canvas reference for image extraction.
	 *
	 * @param {HTMLCanvasElement} canvas - The drawing canvas element
	 */
	setCanvas(canvas) {
		this.canvas = canvas;
		this.logger.log('✅ Canvas reference set');
	}

	/**
	 * Predict the drawn digit by sending canvas data to Python.
	 */
	predictDigit() {
		this.logger.log('🔵 predictDigit() called');

		if (!this.isInitialized) {
			this.logger.error('❌ Controller not initialized');
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onUIState(
					'error',
					'Python not initialized yet. Please wait a moment.'
				);
			}
			return;
		}

		if (!this.canvas) {
			this.logger.error('❌ Canvas not set');
			return;
		}

		try {
			// Get canvas data as base64
			const imageData = this.canvas.toDataURL('image/png');
			this.logger.log('🔵 Got canvas data, length:', imageData.length);

			// Call Python function through window
			if (window.predict_digit) {
				this.logger.log('🔵 Calling window.predict_digit()');
				window.predict_digit(imageData);
				this.logger.log('🔵 Python call completed');
			} else {
				this.logger.error('🔴 window.predict_digit not found! Python may not be ready.');
				if (window.digitRecognitionUIHandler) {
					window.digitRecognitionUIHandler.onUIState(
						'error',
						'Python is not ready yet. Please wait a moment and try again.'
					);
				}
			}
		} catch (e) {
			this.logger.error('🔴 Error in predictDigit:', e);
			if (window.digitRecognitionUIHandler) {
				window.digitRecognitionUIHandler.onUIState('error', e.message);
			}
		}
	}

	/**
	 * Confirm that the prediction was correct (positive feedback).
	 */
	confirmCorrectPrediction() {
		this.logger.log('🔵 confirmCorrectPrediction() called');
		if (window.handleCorrectPrediction) {
			window.handleCorrectPrediction();
		} else {
			this.logger.error('🔴 window.handleCorrectPrediction not found!');
		}
	}

	/**
	 * Retrain the model with a corrected digit.
	 *
	 * @param {number} correctDigit - The correct digit (0-9)
	 */
	retrainWithCorrection(correctDigit) {
		this.logger.log('🔵 retrainWithCorrection() called with:', correctDigit);
		if (window.retrainWithCorrection) {
			window.retrainWithCorrection(correctDigit);
		} else {
			this.logger.error('🔴 window.retrainWithCorrection not found!');
		}
	}

	/**
	 * Reset the model to original training data.
	 */
	resetTraining() {
		this.logger.log('🔵 resetTraining() called');
		if (window.resetTraining) {
			window.resetTraining();
		} else {
			this.logger.error('🔴 window.resetTraining not found!');
		}
	}

	/**
	 * Request training examples from Python.
	 */
	showTrainingExamples() {
		this.logger.log('🔵 showTrainingExamples() called');
		if (window.showTrainingExamples) {
			window.showTrainingExamples();
		} else {
			this.logger.error('🔴 window.showTrainingExamples not found!');
		}
	}

	/**
	 * Hide training examples.
	 */
	hideTrainingExamples() {
		this.logger.log('🔵 hideTrainingExamples() called');
		if (window.digitRecognitionUIHandler) {
			window.digitRecognitionUIHandler.onTrainingExamples(null);
		}
	}

	/**
	 * Clear canvas and reset state.
	 */
	clearAndReset() {
		this.logger.log('🔵 clearAndReset() called');
		if (window.digitRecognitionUIHandler) {
			window.digitRecognitionUIHandler.onClearAndReset();
		}
	}

	/**
	 * Clean up resources.
	 */
	destroy() {
		if (this.pyScriptRunner) {
			this.pyScriptRunner.destroy();
			this.pyScriptRunner = null;
		}

		// Clean up window references
		delete window.updatePredictionResult;
		delete window.updateModelState;
		delete window.updateUIState;
		delete window.updateTrainingExamples;
		delete window.digitRecognitionUIHandler;

		this.canvas = null;
		this.isInitialized = false;
		this.logger.log('✅ DigitRecognitionController destroyed');
	}
}
