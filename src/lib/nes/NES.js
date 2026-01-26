/**
 * NES - Minimal NES emulator wrapper
 * Loads JSNes, renders to canvas, supports save states
 */

const SCREEN_WIDTH = 256;
const SCREEN_HEIGHT = 240;
const JSNES_URL = 'https://unpkg.com/jsnes@1.2.1/dist/jsnes.min.js';

export class NES {
	/**
	 * @param {HTMLCanvasElement} canvas - Canvas element to render to
	 */
	constructor(canvas) {
		this.canvas = canvas;
		this.ctx = canvas.getContext('2d');
		this.nes = null;
		this.running = false;
		this.rafId = null;
		
		// Frame timing
		this.lastTime = 0;
		this.frameInterval = 1000 / 60;
		
		// Frame buffer
		this.imageData = this.ctx.createImageData(SCREEN_WIDTH, SCREEN_HEIGHT);
		this.buffer = new ArrayBuffer(this.imageData.data.length);
		this.buffer8 = new Uint8ClampedArray(this.buffer);
		this.buffer32 = new Uint32Array(this.buffer);
		
		// Set alpha to opaque
		for (let i = 0; i < this.buffer32.length; i++) {
			this.buffer32[i] = 0xff000000;
		}
		
		// Audio
		this.audioCtx = null;
		this.audioNode = null;
		this.audioBuffer = [];
		this.audioBufferSize = 8192;
		this.audioWriteIndex = 0;
		this.audioReadIndex = 0;
		this.muted = false;
		
		// ROM data (for state restore)
		this.romData = null;
		
		// Init canvas to black
		this.ctx.fillStyle = 'black';
		this.ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
		
		console.log('[NES] Created');
	}
	
	/**
	 * Load JSNes library and initialize emulator
	 */
	async init() {
		// Load JSNes if not already loaded
		if (!window.jsnes) {
			await this._loadScript(JSNES_URL);
		}
		
		if (!window.jsnes) {
			throw new Error('Failed to load JSNes');
		}
		
		// Create NES instance
		this.nes = new window.jsnes.NES({
			onFrame: (framebuffer) => this._onFrame(framebuffer),
			onAudioSample: (left, right) => this._onAudio(left, right)
		});
		
		console.log('[NES] Initialized');
		return this;
	}
	
	/**
	 * Load ROM from URL
	 * @param {string} url - ROM file URL
	 */
	async loadROM(url) {
		const response = await fetch(url);
		if (!response.ok) throw new Error(`Failed to load ROM: ${response.statusText}`);
		
		const buffer = await response.arrayBuffer();
		const data = new Uint8Array(buffer);
		
		// Convert to binary string (JSNes format)
		let romString = '';
		for (let i = 0; i < data.length; i++) {
			romString += String.fromCharCode(data[i]);
		}
		
		this.romData = romString;
		this.nes.loadROM(romString);
		
		console.log(`[NES] ROM loaded: ${data.length} bytes`);
		return this;
	}
	
	/**
	 * Load saved state from URL
	 * @param {string} url - State JSON file URL
	 */
	async loadState(url) {
		const response = await fetch(url);
		if (!response.ok) throw new Error(`Failed to load state: ${response.statusText}`);
		
		const state = await response.json();
		this.nes.fromJSON(state);
		
		console.log('[NES] State loaded');
		return this;
	}
	
	/**
	 * Load saved state from object
	 * @param {object} state - State object
	 */
	loadStateFromObject(state) {
		this.nes.fromJSON(state);
		console.log('[NES] State loaded from object');
		return this;
	}
	
	/**
	 * Save current state
	 * @returns {object} State object
	 */
	saveState() {
		return this.nes.toJSON();
	}
	
	/**
	 * Start emulation
	 */
	start() {
		if (this.running) return this;
		
		this.running = true;
		this.lastTime = 0;
		this._initAudio();
		this._loop();
		
		console.log('[NES] Started');
		return this;
	}
	
	/**
	 * Stop emulation
	 */
	stop() {
		this.running = false;
		if (this.rafId) {
			cancelAnimationFrame(this.rafId);
			this.rafId = null;
		}
		this._stopAudio();
		
		console.log('[NES] Stopped');
		return this;
	}
	
	/**
	 * Reset emulator
	 */
	reset() {
		this.nes.reset();
		console.log('[NES] Reset');
		return this;
	}
	
	/**
	 * Set mute state
	 * @param {boolean} muted
	 */
	setMuted(muted) {
		this.muted = muted;
		if (this.audioCtx) {
			if (muted) {
				this.audioCtx.suspend();
			} else {
				this.audioCtx.resume();
			}
		}
		return this;
	}
	
	/**
	 * Press button
	 * @param {number} button - Button code (0=A, 1=B, 2=Select, 3=Start, 4=Up, 5=Down, 6=Left, 7=Right)
	 * @param {number} player - Player (1 or 2)
	 */
	buttonDown(button, player = 1) {
		this.nes.buttonDown(player, button);
		return this;
	}
	
	/**
	 * Release button
	 * @param {number} button - Button code
	 * @param {number} player - Player (1 or 2)
	 */
	buttonUp(button, player = 1) {
		this.nes.buttonUp(player, button);
		return this;
	}
	
	/**
	 * Get frame buffer for external use
	 * @returns {Uint8ClampedArray}
	 */
	getFrameBuffer() {
		return this.buffer8;
	}
	
	/**
	 * Destroy and cleanup
	 */
	destroy() {
		this.stop();
		if (this.audioCtx) {
			this.audioCtx.close();
			this.audioCtx = null;
		}
		this.nes = null;
		console.log('[NES] Destroyed');
	}
	
	// === Private methods ===
	
	_loadScript(src) {
		return new Promise((resolve, reject) => {
			if (document.querySelector(`script[src="${src}"]`)) {
				resolve();
				return;
			}
			const script = document.createElement('script');
			script.src = src;
			script.onload = resolve;
			script.onerror = () => reject(new Error(`Failed to load: ${src}`));
			document.head.appendChild(script);
		});
	}
	
	_onFrame(framebuffer) {
		// Convert NES BGR to canvas ABGR
		for (let i = 0; i < framebuffer.length; i++) {
			this.buffer32[i] = 0xff000000 | framebuffer[i];
		}
	}
	
	_onAudio(left, right) {
		if (this.muted) return;
		
		const size = this._getAudioBufferSize();
		if (size >= this.audioBufferSize * 2) {
			// Overflow - drop samples
			this.audioReadIndex = (this.audioReadIndex + this.audioBufferSize) % (this.audioBufferSize * 2);
		}
		
		this.audioBuffer[this.audioWriteIndex] = left;
		this.audioBuffer[this.audioWriteIndex + 1] = right;
		this.audioWriteIndex = (this.audioWriteIndex + 2) % (this.audioBufferSize * 2);
	}
	
	_render() {
		this.imageData.data.set(this.buffer8);
		this.ctx.putImageData(this.imageData, 0, 0);
	}
	
	_loop(time = 0) {
		if (!this.running) return;
		
		this.rafId = requestAnimationFrame((t) => this._loop(t));
		
		if (!this.lastTime) {
			this.lastTime = time;
			return;
		}
		
		// Generate frame at 60fps
		if (time - this.lastTime >= this.frameInterval) {
			this.nes.frame();
			this._render();
			this.lastTime = time;
		}
	}
	
	_initAudio() {
		if (!window.AudioContext || this.audioCtx) return;
		
		try {
			this.audioCtx = new AudioContext();
			this.audioNode = this.audioCtx.createScriptProcessor(1024, 0, 2);
			this.audioNode.onaudioprocess = (e) => this._processAudio(e);
			this.audioNode.connect(this.audioCtx.destination);
			
			if (this.muted) {
				this.audioCtx.suspend();
			}
		} catch (err) {
			console.warn('[NES] Audio init failed:', err);
		}
	}
	
	_stopAudio() {
		if (this.audioCtx && this.audioCtx.state === 'running') {
			this.audioCtx.suspend();
		}
		this.audioBuffer = [];
		this.audioWriteIndex = 0;
		this.audioReadIndex = 0;
	}
	
	_getAudioBufferSize() {
		if (this.audioWriteIndex >= this.audioReadIndex) {
			return this.audioWriteIndex - this.audioReadIndex;
		}
		return (this.audioBufferSize * 2) - this.audioReadIndex + this.audioWriteIndex;
	}
	
	_processAudio(event) {
		const left = event.outputBuffer.getChannelData(0);
		const right = event.outputBuffer.getChannelData(1);
		
		for (let i = 0; i < left.length; i++) {
			if (this._getAudioBufferSize() >= 2) {
				left[i] = this.audioBuffer[this.audioReadIndex];
				right[i] = this.audioBuffer[this.audioReadIndex + 1];
				this.audioReadIndex = (this.audioReadIndex + 2) % (this.audioBufferSize * 2);
			} else {
				left[i] = 0;
				right[i] = 0;
			}
		}
	}
}

// Button constants for convenience
export const Button = {
	A: 0,
	B: 1,
	SELECT: 2,
	START: 3,
	UP: 4,
	DOWN: 5,
	LEFT: 6,
	RIGHT: 7
};
