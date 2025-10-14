/**
 * BokehController
 *
 * Manages Bokeh visualization examples using PyScriptManager.
 * Replaces polling-based initialization with event-driven lifecycle.
 *
 * @author Guinetik
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class BokehController {
	/**
	 * Creates a new BokehController instance.
	 */
	constructor() {
		/** @type {PyScriptManager|null} */
		this.pyManager = null;

		/** @type {boolean} */
		this.isReady = false;

		/** @type {Function|null} */
		this.onReadyCallback = null;

		/** @type {Function|null} */
		this.onErrorCallback = null;

		this.logger = createLogger({
			prefix: 'BokehController',
			level: 'debug'
		});
	}

	/**
	 * Initialize the controller and load Python Bokeh script.
	 *
	 * @param {string} scriptName - Name of the Python script (e.g., 'bokeh_index')
	 * @returns {Promise<void>}
	 */
	async initialize(scriptName = 'bokeh_index') {
		this.logger.log(`Initializing with script: ${scriptName}`);

		try {
			// Create PyScriptManager instance
			this.pyManager = new PyScriptManager();

			// Setup event listeners
			this.pyManager.addEventListener('script:ready', this._handleReady.bind(this));
			this.pyManager.addEventListener('script:error', this._handleError.bind(this));

			// Load Python script
			const scriptUrl = getLink(`python/bokeh/${scriptName}.py`);
			this.logger.log(`Loading script: ${scriptUrl}`);

			// Start loading (events will handle completion)
			this.pyManager.runScript(scriptUrl, 'body');

		} catch (error) {
			this.logger.error('Initialization failed:', error);
			if (this.onErrorCallback) {
				this.onErrorCallback(error.message);
			}
			throw error;
		}
	}

	/**
	 * Handle script ready event.
	 * @private
	 * @param {CustomEvent} event - Ready event with exports
	 */
	_handleReady(event) {
		this.logger.log('Python module ready!', event.detail);

		this.isReady = true;

		// Call ready callback if set
		if (this.onReadyCallback) {
			this.onReadyCallback();
		}

		this.logger.log('✅ Controller ready');
	}

	/**
	 * Handle script error event.
	 * @private
	 * @param {CustomEvent} event - Error event with details
	 */
	_handleError(event) {
		this.logger.error('Python module error:', event.detail.error);

		// Call error callback if set
		if (this.onErrorCallback) {
			this.onErrorCallback(event.detail.error);
		}
	}

	/**
	 * Set callback for when Python is ready.
	 * @param {Function} callback - Function to call when ready
	 */
	onReady(callback) {
		this.onReadyCallback = callback;
		// If already ready, call immediately
		if (this.isReady) {
			callback();
		}
	}

	/**
	 * Set callback for errors.
	 * @param {Function} callback - Function to call on error
	 */
	onError(callback) {
		this.onErrorCallback = callback;
	}

	/**
	 * Clean up resources.
	 */
	destroy() {
		if (this.pyManager) {
			this.pyManager.destroy();
			this.pyManager = null;
		}

		this.isReady = false;
		this.onReadyCallback = null;
		this.onErrorCallback = null;

		this.logger.log('🧹 Destroyed');
	}
}
