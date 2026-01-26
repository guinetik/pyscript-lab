/**
 * Screen - Handles canvas rendering for NES emulator
 * Based on jsnes-react implementation
 */

import { createLogger } from "@guinetik/logger";

const SCREEN_WIDTH = 256;
const SCREEN_HEIGHT = 240;

export class Screen {
	/**
	 * Creates a Screen instance
	 * @param {HTMLCanvasElement} canvas - Canvas element to render to
	 */
	constructor(canvas) {
		this.logger = createLogger(
			{prefix: 'Screen',
			level: 'debug'});
		this.canvas = canvas;
		this.context = null;
		this.imageData = null;
		
		// Frame buffer
		this.buffer = null;
		this.buffer8 = null;
		this.buffer32 = null;
		
		this.initCanvas();
		this.logger.log('🖥️ Screen created');
	}

	/**
	 * Initialize canvas and buffers
	 */
	initCanvas() {
		this.context = this.canvas.getContext('2d');
		this.imageData = this.context.createImageData(SCREEN_WIDTH, SCREEN_HEIGHT);
		
		// Fill with black initially
		this.context.fillStyle = 'black';
		this.context.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
		
		// Create frame buffer with 8-bit and 32-bit views
		this.buffer = new ArrayBuffer(this.imageData.data.length);
		this.buffer8 = new Uint8ClampedArray(this.buffer);
		this.buffer32 = new Uint32Array(this.buffer);
		
		// Set alpha channel to opaque
		for (let i = 0; i < this.buffer32.length; i++) {
			this.buffer32[i] = 0xff000000;
		}
		
		this.logger.log('✅ Screen initialized');
	}

	/**
	 * Set buffer from NES frame data
	 * This is called by the NES onFrame callback
	 * @param {Array} nesBuffer - Frame buffer from NES (BGR format)
	 */
	setBuffer(nesBuffer) {
		// Convert NES BGR format to canvas ABGR format
		for (let i = 0; i < nesBuffer.length; i++) {
			this.buffer32[i] = 0xff000000 | nesBuffer[i];
		}
	}

	/**
	 * Write the buffer to the canvas
	 * This is called on each animation frame
	 */
	writeBuffer() {
		this.imageData.data.set(this.buffer8);
		this.context.putImageData(this.imageData, 0, 0);
	}

	/**
	 * Get the frame buffer (for external access)
	 * @returns {Uint8ClampedArray} Frame buffer
	 */
	getBuffer() {
		return this.buffer8;
	}

	/**
	 * Take a screenshot
	 * @returns {HTMLImageElement} Screenshot image
	 */
	screenshot() {
		const img = new Image();
		img.src = this.canvas.toDataURL('image/png');
		return img;
	}
}

