/**
 * InteropController
 *
 * Demonstrates JavaScript-Python interoperability with proper separation of concerns.
 * Handles:
 * - PyScript runner setup and lifecycle
 * - Window callback registration for Python to call
 * - Business logic layer between Python and Svelte UI
 *
 * This controller follows the architectural principle:
 * - Python sends only data (no HTML)
 * - JavaScript/Svelte handles all rendering
 * - Controller manages the communication layer
 *
 * @author Guinetik
 */

import RunPython from '$lib/RunPython.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class InteropController {
	/**
	 * Creates a new InteropController instance.
	 */
	constructor() {
		this.logger = createLogger({
			prefix: 'InteropController',
			level: 'debug'
		});

		/** @type {RunPython|null} */
		this.pyScriptRunner = null;

		/** @type {boolean} */
		this.isInitialized = false;
	}

	/**
	 * Initialize the controller by setting up PyScript and callbacks.
	 *
	 * @returns {Promise<void>}
	 */
	async initialize() {
		if (this.isInitialized) {
			this.logger.warn('⚠️ InteropController already initialized');
			return;
		}

		try {
			this.logger.log('🔵 Initializing InteropController...');

			// Setup callbacks FIRST (before Python loads)
			this._setupCallbacks();

			// Load Python script
			this.pyScriptRunner = RunPython();
			const pyScriptUrl = getLink('python/interop.py');
			this.pyScriptRunner.runScript(pyScriptUrl, 'script_gutter', false);

			this.isInitialized = true;
			this.logger.log('✅ InteropController initialized');
		} catch (error) {
			this.logger.error('❌ Failed to initialize InteropController:', error);
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

		// Callback for greeting initialization status
		window.onInteropReady = (data) => {
			this.logger.log('🟢 onInteropReady called:', data);
			if (window.interopUIHandler) {
				window.interopUIHandler.onReady(data);
			} else {
				this.logger.error('🔴 window.interopUIHandler not found!');
			}
		};

		// Callback for greeting results
		window.onGreetingResult = (data) => {
			this.logger.log('🟢 onGreetingResult called:', data);
			if (window.interopUIHandler) {
				window.interopUIHandler.onGreeting(data);
			} else {
				this.logger.error('🔴 window.interopUIHandler not found!');
			}
		};

		// Callback for validation errors
		window.onValidationError = (data) => {
			this.logger.log('🟠 onValidationError called:', data);
			if (window.interopUIHandler) {
				window.interopUIHandler.onError(data);
			} else {
				this.logger.error('🔴 window.interopUIHandler not found!');
			}
		};

		this.logger.log('✅ Window callbacks registered');
	}

	/**
	 * Call Python greeting function with user input.
	 *
	 * @param {string} name - User's name
	 * @param {number|string} age - User's age
	 */
	greetUser(name, age) {
		this.logger.log('🔵 greetUser() called:', { name, age });

		if (!this.isInitialized) {
			this.logger.error('❌ Controller not initialized');
			if (window.interopUIHandler) {
				window.interopUIHandler.onError({
					message: 'Python not initialized yet. Please wait a moment.'
				});
			}
			return;
		}

		// Call Python function through window
		if (window.runGreeting) {
			this.logger.log('🔵 Calling window.runGreeting()...');
			window.runGreeting(name, age);
		} else {
			this.logger.error('🔴 window.runGreeting not found! Python may not be ready.');
			if (window.interopUIHandler) {
				window.interopUIHandler.onError({
					message: 'Python is not ready yet. Please wait a moment and try again.'
				});
			}
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
		delete window.onInteropReady;
		delete window.onGreetingResult;
		delete window.onValidationError;
		delete window.interopUIHandler;

		this.isInitialized = false;
		this.logger.log('✅ InteropController destroyed');
	}
}
