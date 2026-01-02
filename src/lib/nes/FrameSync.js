/**
 * FrameSync - JavaScript bridge for Python frame synchronization
 *
 * Provides a callback interface that Python can register with to receive
 * frame notifications at exactly 60 FPS, synchronized with NES emulation.
 */

import { createLogger } from "@guinetik/logger";

const logger = createLogger({
	prefix: 'FrameSync',
	level: 'debug'
});

export class FrameSync {
	constructor() {
		this.pythonCallback = null;
		this.frameCount = 0;
		this.enabled = false;
	}

	/**
	 * Register a Python callback to be called each frame
	 * @param {Function} callback - Python function to call (via Pyodide proxy)
	 */
	registerCallback(callback) {
		this.pythonCallback = callback;
		this.frameCount = 0;
		this.enabled = true;
		logger.log('✅ Python callback registered');
	}

	/**
	 * Unregister the Python callback
	 */
	unregisterCallback() {
		this.pythonCallback = null;
		this.enabled = false;
		logger.log('🔌 Python callback unregistered');
	}

	/**
	 * Called by FrameTimer after each NES frame is generated
	 * This ensures 1:1 correspondence between emulator frames and agent observations
	 *
	 * @param {number} time - Current time from requestAnimationFrame
	 */
	onFrameGenerated(time) {
		if (!this.enabled || !this.pythonCallback) {
			return;
		}

		try {
			this.frameCount++;

			// Call Python with current frame time
			this.pythonCallback(time);

		} catch (error) {
			logger.error('❌ Error calling Python callback:', error);
			// Don't disable on error - Python will handle it
		}
	}

	/**
	 * Get current frame count
	 */
	getFrameCount() {
		return this.frameCount;
	}

	/**
	 * Reset frame count
	 */
	reset() {
		this.frameCount = 0;
		logger.log('🔄 Frame count reset');
	}
}

/**
 * Create global instance and expose to window
 * This allows Python to access it via js.window.nesFrameSync
 */
export function initializeFrameSync() {
	const frameSync = new FrameSync();

	// Expose to window for Python access
	window.nesFrameSync = frameSync;

	logger.log('🌐 FrameSync available on window.nesFrameSync');

	return frameSync;
}