/**
 * FrameTimer - Handles frame timing and RAF loop
 * Based on jsnes-react implementation
 */

import { createLogger } from "@guinetik/logger";

const DEFAULT_FPS = 60;

export class FrameTimer {
	/**
	 * Creates a FrameTimer
	 * @param {Object} options - Configuration options
	 * @param {Function} options.onGenerateFrame - Called to generate a frame (calls nes.frame())
	 * @param {Function} options.onWriteFrame - Called to write frame to screen
	 * @param {number} options.fps - Target FPS (default: 60)
	 */
	constructor({ onGenerateFrame, onWriteFrame, fps = DEFAULT_FPS }) {
		this.logger = createLogger(
			{prefix: 'FrameTimer',
			level: 'debug'});
		this.onGenerateFrame = onGenerateFrame;
		this.onWriteFrame = onWriteFrame;
		this.running = false;
		this.requestId = null;
		this.fps = fps;
		this.interval = 1000 / fps;

		// Timing state
		this.lastTime = 0;
		this.nextFrameTime = 0;

		this.logger.log(`⚙️ FrameTimer configured for ${fps} FPS (${this.interval.toFixed(2)}ms per frame)`);

		// Bind the animation frame handler
		this.onAnimationFrame = this.onAnimationFrame.bind(this);
	}

	/**
	 * Start the frame timer
	 */
	start() {
		if (this.running) {
			console.warn('⚠️ FrameTimer already running');
			return;
		}

		this.logger.log('▶️ FrameTimer started');
		this.running = true;
		this.lastTime = 0;
		this.nextFrameTime = 0;
		this.requestAnimationFrame();
	}

	/**
	 * Stop the frame timer
	 */
	stop() {
		this.logger.log('⏹️ FrameTimer stopped');
		this.running = false;

		if (this.requestId) {
			window.cancelAnimationFrame(this.requestId);
			this.requestId = null;
		}

		this.lastTime = 0;
		this.nextFrameTime = 0;
	}

	/**
	 * Request next animation frame
	 */
	requestAnimationFrame() {
		this.requestId = window.requestAnimationFrame(this.onAnimationFrame);
	}

	/**
	 * Generate one frame
	 * @param {number} time - Current time
	 */
	generateFrame(time) {
		this.onGenerateFrame(time);
	}

	/**
	 * Animation frame handler - precise timing without catchup
	 * @param {number} time - Current time from RAF
	 */
	onAnimationFrame(time) {
		if (!this.running) {
			return;
		}

		// Schedule next frame immediately
		this.requestAnimationFrame();

		// First frame - record when next frame should be generated
		if (!this.lastTime) {
			this.lastTime = time;
			this.nextFrameTime = time + this.interval;
			return;
		}

		// Check if it's time for next frame
		if (time >= this.nextFrameTime) {
			// Generate exactly ONE frame
			this.generateFrame(time);
			this.onWriteFrame();

			// Schedule next frame at precise interval
			// Use nextFrameTime (not current time) to maintain steady rhythm
			this.nextFrameTime += this.interval;

			// But if we've fallen too far behind (>2 frames), reset to prevent catchup
			if (time - this.nextFrameTime > this.interval * 2) {
				this.nextFrameTime = time + this.interval;
			}
		}
	}
}
