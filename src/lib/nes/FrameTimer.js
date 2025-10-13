/**
 * FrameTimer - Handles frame timing and RAF loop
 * Based on jsnes-react implementation
 */

const FPS = 60;

export class FrameTimer {
	/**
	 * Creates a FrameTimer
	 * @param {Object} options - Configuration options
	 * @param {Function} options.onGenerateFrame - Called to generate a frame (calls nes.frame())
	 * @param {Function} options.onWriteFrame - Called to write frame to screen
	 */
	constructor({ onGenerateFrame, onWriteFrame }) {
		this.onGenerateFrame = onGenerateFrame;
		this.onWriteFrame = onWriteFrame;
		this.running = false;
		this.requestId = null;
		this.interval = 1000 / FPS;
		this.lastFrameTime = 0;
		
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
		
		console.log('▶️ FrameTimer started');
		this.running = true;
		this.lastFrameTime = 0;
		this.requestAnimationFrame();
	}

	/**
	 * Stop the frame timer
	 */
	stop() {
		console.log('⏹️ FrameTimer stopped');
		this.running = false;
		
		if (this.requestId) {
			window.cancelAnimationFrame(this.requestId);
			this.requestId = null;
		}
		
		this.lastFrameTime = 0;
	}

	/**
	 * Request next animation frame
	 */
	requestAnimationFrame() {
		this.requestId = window.requestAnimationFrame(this.onAnimationFrame);
	}

	/**
	 * Generate one frame
	 */
	generateFrame() {
		this.onGenerateFrame();
		this.lastFrameTime += this.interval;
	}

	/**
	 * Animation frame handler
	 * @param {number} time - Current time from RAF
	 */
	onAnimationFrame(time) {
		if (!this.running) {
			return;
		}

		// Schedule next frame
		this.requestAnimationFrame();

		// How many ms after 60fps frame time
		const excess = time % this.interval;

		// newFrameTime is the current time aligned to 60fps intervals
		// i.e. 16.6, 33.3, etc
		const newFrameTime = time - excess;

		// First frame, do nothing
		if (!this.lastFrameTime) {
			this.lastFrameTime = newFrameTime;
			return;
		}

		const numFrames = Math.round(
			(newFrameTime - this.lastFrameTime) / this.interval
		);

		// This can happen on high refresh rate displays
		if (numFrames === 0) {
			return;
		}

		// Generate and display first frame
		this.generateFrame();
		this.onWriteFrame();

		// Generate additional frames if needed (for timing correction)
		// but don't display them until next RAF call
		if (numFrames > 1) {
			console.log('⏩ Skipping', numFrames - 1, 'frame(s)');
			const timeToNextFrame = this.interval - excess;
			for (let i = 1; i < numFrames; i++) {
				setTimeout(
					() => {
						if (this.running) {
							this.generateFrame();
						}
					},
					(i * timeToNextFrame) / numFrames
				);
			}
		}
	}
}

