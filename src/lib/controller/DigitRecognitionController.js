/**
 * DigitRecognitionController
 *
 * Manages the machine learning digit recognition feature with proper separation of concerns.
 * Handles:
 * - PyScriptManager setup and lifecycle (event-driven)
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

import { PyScriptManager } from '$lib/PyScriptManager.js';
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

		/** @type {PyScriptManager|null} */
		this.pyScriptManager = null;

		/** @type {boolean} */
		this.isInitialized = false;

		/** @type {HTMLCanvasElement|null} */
		this.canvas = null;

		/** @type {Object|null} - Python exported functions */
		this.pythonExports = null;
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

			// Create PyScriptManager and load script with Promise-based approach
			this.pyScriptManager = new PyScriptManager();
			const pyScriptUrl = getLink('python/ml/digit_recognition.py');

			this.logger.log('🔵 Loading Python script...');

			// Await the Promise returned by runScript
			try {
				this.pythonExports = await this.pyScriptManager.runScript(pyScriptUrl, 'script_gutter');

				this.logger.log('✅ Python script ready! Exports:', Object.keys(this.pythonExports));
				this.isInitialized = true;

				// Notify UI that Python is ready
				if (window.digitRecognitionUIHandler) {
					window.digitRecognitionUIHandler.onPythonReady();
				}
			} catch (error) {
				this.logger.error('❌ Python script failed to load:', error);
				if (window.digitRecognitionUIHandler) {
					window.digitRecognitionUIHandler.onUIState(
						'error',
						`Failed to load Python: ${error.message}`
					);
				}
				throw error;
			}
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

		if (!this.isInitialized || !this.pythonExports) {
			this.logger.error('❌ Controller not initialized or Python not ready');
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

			// Call Python function from exports
			if (this.pythonExports.predict_digit) {
				this.logger.log('🔵 Calling pythonExports.predict_digit()');
				this.pythonExports.predict_digit(imageData);
				this.logger.log('🔵 Python call completed');
			} else {
				this.logger.error('🔴 predict_digit not found in exports!');
				if (window.digitRecognitionUIHandler) {
					window.digitRecognitionUIHandler.onUIState(
						'error',
						'Python function not available.'
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
		if (this.pythonExports?.handleCorrectPrediction) {
			this.pythonExports.handleCorrectPrediction();
		} else {
			this.logger.error('🔴 handleCorrectPrediction not found in exports!');
		}
	}

	/**
	 * Retrain the model with a corrected digit.
	 *
	 * @param {number} correctDigit - The correct digit (0-9)
	 */
	retrainWithCorrection(correctDigit) {
		this.logger.log('🔵 retrainWithCorrection() called with:', correctDigit);
		if (this.pythonExports?.retrainWithCorrection) {
			this.pythonExports.retrainWithCorrection(correctDigit);
		} else {
			this.logger.error('🔴 retrainWithCorrection not found in exports!');
		}
	}

	/**
	 * Reset the model to original training data.
	 */
	resetTraining() {
		this.logger.log('🔵 resetTraining() called');
		if (this.pythonExports?.resetTraining) {
			this.pythonExports.resetTraining();
		} else {
			this.logger.error('🔴 resetTraining not found in exports!');
		}
	}

	/**
	 * Request training examples from Python.
	 */
	showTrainingExamples() {
		this.logger.log('🔵 showTrainingExamples() called');
		if (this.pythonExports?.showTrainingExamples) {
			this.pythonExports.showTrainingExamples();
		} else {
			this.logger.error('🔴 showTrainingExamples not found in exports!');
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
		if (this.pyScriptManager) {
			this.pyScriptManager.destroy();
			this.pyScriptManager = null;
		}

		// Clean up window references
		delete window.updatePredictionResult;
		delete window.updateModelState;
		delete window.updateUIState;
		delete window.updateTrainingExamples;
		delete window.digitRecognitionUIHandler;

		this.canvas = null;
		this.pythonExports = null;
		this.isInitialized = false;
		this.logger.log('✅ DigitRecognitionController destroyed');
	}
}
