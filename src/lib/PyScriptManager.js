/**
 * PyScriptManager - Event-driven PyScript lifecycle management
 *
 * Manages the lifecycle of PyScript modules with event-based communication.
 * Replaces polling patterns with direct callbacks from Python code.
 *
 * Features:
 * - Event-driven: Scripts signal readiness via callbacks
 * - Dual API: Support both async/await and event listeners
 * - Error handling: Captures and propagates Python errors
 * - Cleanup: Proper resource management
 *
 * @example
 * // Async/await style
 * const manager = new PyScriptManager();
 * const exports = await manager.runScript('/python/my_module.py');
 * exports.myFunction();
 *
 * @example
 * // Event-driven style
 * const manager = new PyScriptManager();
 * manager.addEventListener('script:ready', (e) => {
 *   console.log('Script ready:', e.detail.scriptId);
 * });
 * manager.runScript('/python/my_module.py');
 *
 * @author Guinetik
 */

export class PyScriptManager extends EventTarget {
	/**
	 * Creates a new PyScriptManager instance.
	 */
	constructor() {
		super();

		/**
		 * Map of script ID to script metadata
		 * @type {Map<string, {script: HTMLScriptElement, status: 'loading'|'ready'|'error'}>}
		 */
		this.scripts = new Map();

		// Setup global callbacks for Python to call
		this._setupGlobalCallbacks();
	}

	/**
	 * Setup global callback functions that Python scripts will invoke.
	 * @private
	 */
	_setupGlobalCallbacks() {
		/**
		 * Called by Python when a script is ready.
		 * @param {string} scriptId - Identifier of the ready script
		 * @param {Object} exports - Exported functions/data from Python
		 */
		window.__pyScriptReady = (scriptId, exports = {}) => {
			console.log(`✅ [PyScriptManager] Script ready: ${scriptId}`);

			// Update script status
			const scriptInfo = this.scripts.get(scriptId);
			if (scriptInfo) {
				scriptInfo.status = 'ready';
			}

			// Dispatch event for listeners
			this.dispatchEvent(
				new CustomEvent('script:ready', {
					detail: { scriptId, exports }
				})
			);
		};

		/**
		 * Called by Python when a script encounters an error.
		 * @param {string} scriptId - Identifier of the failed script
		 * @param {string} error - Error message from Python
		 */
		window.__pyScriptError = (scriptId, error) => {
			console.error(`❌ [PyScriptManager] Script error: ${scriptId}`, error);

			// Update script status
			const scriptInfo = this.scripts.get(scriptId);
			if (scriptInfo) {
				scriptInfo.status = 'error';
			}

			// Dispatch event for listeners
			this.dispatchEvent(
				new CustomEvent('script:error', {
					detail: { scriptId, error }
				})
			);
		};
	}

	/**
	 * Generate a unique script ID from source URL.
	 * @private
	 * @param {string} srcUrl - Source URL of the Python script
	 * @returns {string} Unique script identifier
	 */
	_generateScriptId(srcUrl) {
		const name = srcUrl.split('/').pop().replace('.py', '');
		return `py-${name}-${Date.now()}`;
	}

	/**
	 * Load and execute a Python script.
	 *
	 * Returns a Promise that resolves when the Python script signals readiness.
	 * Events are also dispatched for event-driven consumers.
	 *
	 * @param {string} srcUrl - URL to the Python script file
	 * @param {string} [targetId='body'] - DOM element ID to append script to
	 * @returns {Promise<Object>} Promise resolving to exported functions/data
	 *
	 * @example
	 * const exports = await manager.runScript('/python/my_module.py');
	 * exports.myFunction();
	 */
	runScript(srcUrl, targetId = 'body') {
		const scriptId = this._generateScriptId(srcUrl);

		// Create script element
		const script = document.createElement('script');
		script.type = 'py';
		script.src = srcUrl;
		script.id = scriptId;
		script.dataset.scriptId = scriptId;

		// Find target element
		const target = targetId === 'body' ? document.body : document.getElementById(targetId);

		if (!target) {
			console.error(`❌ [PyScriptManager] Target element not found: ${targetId}`);
			return Promise.reject(new Error(`Target element not found: ${targetId}`));
		}

		// Append to DOM
		target.appendChild(script);

		// Track script
		this.scripts.set(scriptId, { script, status: 'loading' });

		console.log(`🔄 [PyScriptManager] Loading script: ${scriptId}`);

		// Return Promise for await syntax
		return new Promise((resolve, reject) => {
			const readyHandler = (e) => {
				if (e.detail.scriptId === scriptId) {
					this.removeEventListener('script:ready', readyHandler);
					this.removeEventListener('script:error', errorHandler);
					resolve(e.detail.exports);
				}
			};

			const errorHandler = (e) => {
				if (e.detail.scriptId === scriptId) {
					this.removeEventListener('script:ready', readyHandler);
					this.removeEventListener('script:error', errorHandler);
					reject(new Error(e.detail.error));
				}
			};

			this.addEventListener('script:ready', readyHandler);
			this.addEventListener('script:error', errorHandler);
		});
	}

	/**
	 * Execute inline Python code.
	 *
	 * Note: Inline code cannot use the PyScriptManager ready signaling.
	 * Use runScript() for code that needs lifecycle management.
	 *
	 * @param {string} code - Python code to execute
	 * @param {string} [targetId='body'] - DOM element ID to append script to
	 * @returns {string} Script ID
	 */
	runCode(code, targetId = 'body') {
		const scriptId = `py-inline-${Date.now()}`;

		// Create script element
		const script = document.createElement('script');
		script.type = 'py';
		script.textContent = code;
		script.id = scriptId;

		// Find target element
		const target = targetId === 'body' ? document.body : document.getElementById(targetId);

		if (!target) {
			console.error(`❌ [PyScriptManager] Target element not found: ${targetId}`);
			return scriptId;
		}

		// Append to DOM
		target.appendChild(script);

		// Track script
		this.scripts.set(scriptId, { script, status: 'loading' });

		console.log(`🔄 [PyScriptManager] Running inline code: ${scriptId}`);

		return scriptId;
	}

	/**
	 * Get the status of a script.
	 * @param {string} scriptId - Script identifier
	 * @returns {'loading'|'ready'|'error'|'unknown'} Script status
	 */
	getScriptStatus(scriptId) {
		const scriptInfo = this.scripts.get(scriptId);
		return scriptInfo ? scriptInfo.status : 'unknown';
	}

	/**
	 * Clean up all managed scripts and remove global callbacks.
	 * @param {boolean} [removeElements=true] - Whether to remove script elements from DOM
	 */
	destroy(removeElements = true) {
		if (removeElements) {
			this.scripts.forEach(({ script }) => {
				if (script.parentNode) {
					script.parentNode.removeChild(script);
				}
			});
		}

		this.scripts.clear();

		// Clean up global callbacks
		delete window.__pyScriptReady;
		delete window.__pyScriptError;

		console.log('🧹 [PyScriptManager] Destroyed');
	}
}
