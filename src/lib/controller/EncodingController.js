/**
 * EncodingController
 *
 * Manages the text encoding/hashing example using PyScriptManager.
 * Demonstrates event-driven PyScript initialization without polling.
 *
 * Features:
 * - Multiple encoding functions (MD5, SHA-256, SHA-1, Base64, ROT13)
 * - Event-driven initialization
 * - Error handling
 * - Clean resource management
 *
 * @author Guinetik
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

export class EncodingController {
	/**
	 * Creates a new EncodingController instance.
	 */
	constructor() {
		/** @type {PyScriptManager|null} */
		this.pyManager = null;

		/** @type {Object|null} */
		this.encoders = null;

		/** @type {boolean} */
		this.isReady = false;

		/** @type {Function|null} */
		this.onReadyCallback = null;

		/** @type {Function|null} */
		this.onErrorCallback = null;

		this.logger = createLogger({
			prefix: 'EncodingController',
			level: 'debug'
		});
	}

	/**
	 * Initialize the controller and load Python encoding module.
	 *
	 * @returns {Promise<void>}
	 */
	async initialize() {
		this.logger.log('Initializing...');

		try {
			// Create PyScriptManager instance
			this.pyManager = new PyScriptManager();

			// Setup event listeners
			this.pyManager.addEventListener('script:ready', this._handleReady.bind(this));
			this.pyManager.addEventListener('script:error', this._handleError.bind(this));

			// Load Python script
			const scriptUrl = getLink('python/basic/encoder.py');
			this.logger.log(`Loading script: ${scriptUrl}`);

			// Start loading (can use await or rely on events)
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

		// Store exported functions
		this.encoders = {
			md5: window.encodeMD5,
			sha256: window.encodeSHA256,
			sha1: window.encodeSHA1,
			base64Encode: window.encodeBase64,
			base64Decode: window.decodeBase64,
			rot13: window.encodeROT13
		};

		this.isReady = true;

		// Call ready callback if set
		if (this.onReadyCallback) {
			this.onReadyCallback();
		}

		this.logger.log('✅ Controller ready with encoding functions');
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
	 * Encode text using specified format.
	 *
	 * @param {string} text - Text to encode
	 * @param {string} format - Encoding format (md5, sha256, sha1, base64, rot13, base64-decode)
	 * @returns {string} Encoded result or error message
	 */
	encode(text, format) {
		if (!this.isReady || !this.encoders) {
			this.logger.warn('Encode called before ready');
			return 'Error: Python module not ready yet';
		}

		if (!text) {
			return '';
		}

		try {
			switch (format) {
				case 'md5':
					return this.encoders.md5(text);
				case 'sha256':
					return this.encoders.sha256(text);
				case 'sha1':
					return this.encoders.sha1(text);
				case 'base64':
					return this.encoders.base64Encode(text);
				case 'base64-decode':
					return this.encoders.base64Decode(text);
				case 'rot13':
					return this.encoders.rot13(text);
				default:
					return `Error: Unknown format '${format}'`;
			}
		} catch (error) {
			this.logger.error('Encoding error:', error);
			return `Error: ${error.message}`;
		}
	}

	/**
	 * Get list of available encoding formats.
	 * @returns {Array<{value: string, label: string}>}
	 */
	getFormats() {
		return [
			{ value: 'md5', label: 'MD5 Hash' },
			{ value: 'sha1', label: 'SHA-1 Hash' },
			{ value: 'sha256', label: 'SHA-256 Hash' },
			{ value: 'base64', label: 'Base64 Encode' },
			{ value: 'base64-decode', label: 'Base64 Decode' },
			{ value: 'rot13', label: 'ROT13 Cipher' }
		];
	}

	/**
	 * Clean up resources.
	 */
	destroy() {
		if (this.pyManager) {
			this.pyManager.destroy();
			this.pyManager = null;
		}

		this.encoders = null;
		this.isReady = false;
		this.onReadyCallback = null;
		this.onErrorCallback = null;

		this.logger.log('🧹 Destroyed');
	}
}
