/**
 * NES - Proper NES emulator wrapper based on jsnes-web
 * Key insight: Audio drives timing, not video
 */

const SCREEN_WIDTH = 256;
const SCREEN_HEIGHT = 240;
const JSNES_URL = 'https://unpkg.com/jsnes@1.2.1/dist/jsnes.min.js';
const FPS = 60.098; // Actual NES FPS

export class NES {
	/**
	 * @param {HTMLCanvasElement} canvas
	 */
	constructor(canvas) {
		this.canvas = canvas;
		this.ctx = canvas.getContext('2d');
		this.nes = null;
		this.running = false;
		
		// Frame timing
		this.frameTimer = null;
		this.frameInterval = 1000 / FPS;
		this.lastFrameTime = 0;
		this.rafId = null;
		
		// Screen buffer
		this.imageData = this.ctx.createImageData(SCREEN_WIDTH, SCREEN_HEIGHT);
		this.buf = new ArrayBuffer(this.imageData.data.length);
		this.buf8 = new Uint8ClampedArray(this.buf);
		this.buf32 = new Uint32Array(this.buf);
		
		// Set alpha to opaque
		for (let i = 0; i < this.buf32.length; i++) {
			this.buf32[i] = 0xff000000;
		}
		
		// Audio - Ring buffer
		this.audioCtx = null;
		this.scriptNode = null;
		this.audioBufferSize = 8192;
		this.audioBuffer = new RingBuffer(this.audioBufferSize * 2);
		this.muted = false;
		
		// ROM data
		this.romData = null;
		
		// Init canvas black
		this.ctx.fillStyle = 'black';
		this.ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
		
		console.log('[NES] Created');
	}
	
	/**
	 * Get audio sample rate
	 */
	getSampleRate() {
		if (!window.AudioContext) return 44100;
		const ctx = new AudioContext();
		const rate = ctx.sampleRate;
		ctx.close();
		return rate;
	}
	
	/**
	 * Initialize emulator
	 */
	async init() {
		if (!window.jsnes) {
			await this._loadScript(JSNES_URL);
		}
		
		if (!window.jsnes) {
			throw new Error('Failed to load JSNes');
		}
		
		// Create NES with proper sample rate
		this.nes = new window.jsnes.NES({
			onFrame: (buffer) => this._setBuffer(buffer),
			onAudioSample: (left, right) => this._writeSample(left, right),
			sampleRate: this.getSampleRate()
		});
		
		console.log('[NES] Initialized with sample rate:', this.getSampleRate());
		return this;
	}
	
	/**
	 * Load ROM from URL
	 */
	async loadROM(url) {
		const response = await fetch(url);
		if (!response.ok) throw new Error(`Failed to load ROM: ${response.statusText}`);
		
		const buffer = await response.arrayBuffer();
		const data = new Uint8Array(buffer);
		
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
	 * Load state from URL
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
	 * Load state from object
	 */
	loadStateFromObject(state) {
		this.nes.fromJSON(state);
		return this;
	}
	
	/**
	 * Save state
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
		this.lastFrameTime = 0;
		
		// Start audio
		this._startAudio();
		
		// Start frame loop
		this._requestFrame();
		
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
		this.lastFrameTime = 0;
		
		console.log('[NES] Stopped');
		return this;
	}
	
	/**
	 * Reset
	 */
	reset() {
		this.nes.reset();
		return this;
	}
	
	/**
	 * Set muted
	 */
	setMuted(muted) {
		this.muted = muted;
		return this;
	}
	
	/**
	 * Button down
	 */
	buttonDown(button, player = 1) {
		this.nes.buttonDown(player, button);
		return this;
	}
	
	/**
	 * Button up
	 */
	buttonUp(button, player = 1) {
		this.nes.buttonUp(player, button);
		return this;
	}
	
	/**
	 * Get frame buffer
	 */
	getFrameBuffer() {
		return this.buf8;
	}
	
	/**
	 * Destroy
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
	
	// === Private ===
	
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
	
	_setBuffer(buffer) {
		for (let i = 0; i < buffer.length; i++) {
			this.buf32[i] = 0xff000000 | buffer[i];
		}
	}
	
	_writeBuffer() {
		this.imageData.data.set(this.buf8);
		this.ctx.putImageData(this.imageData, 0, 0);
	}
	
	_writeSample(left, right) {
		if (this.muted) return;
		
		// Handle buffer overrun
		if (this.audioBuffer.size() / 2 >= this.audioBufferSize) {
			console.log('Buffer overrun');
			this.audioBuffer.deqN(this.audioBufferSize / 2);
		}
		
		this.audioBuffer.enq(left);
		this.audioBuffer.enq(right);
	}
	
	_generateFrame() {
		this.nes.frame();
		this.lastFrameTime += this.frameInterval;
	}
	
	_requestFrame() {
		this.rafId = requestAnimationFrame((time) => this._onAnimationFrame(time));
	}
	
	_onAnimationFrame(time) {
		if (!this.running) return;
		
		this._requestFrame();
		
		// Align to 60fps intervals
		const excess = time % this.frameInterval;
		const newFrameTime = time - excess;
		
		// First frame
		if (!this.lastFrameTime) {
			this.lastFrameTime = newFrameTime;
			return;
		}
		
		// How many frames should have been generated
		const numFrames = Math.round((newFrameTime - this.lastFrameTime) / this.frameInterval);
		
		// No frames needed (can happen on 144Hz displays)
		if (numFrames === 0) return;
		
		// Generate first frame and display it
		this._generateFrame();
		this._writeBuffer();
		
		// Generate additional frames (not displayed) spread over time until next RAF
		const timeToNextFrame = this.frameInterval - excess;
		for (let i = 1; i < numFrames; i++) {
			setTimeout(() => {
				if (this.running) this._generateFrame();
			}, (i * timeToNextFrame) / numFrames);
		}
		
		if (numFrames > 1) {
			console.log('Frame skip:', numFrames - 1);
		}
	}
	
	_startAudio() {
		if (!window.AudioContext) return;
		
		this.audioCtx = new AudioContext();
		this.scriptNode = this.audioCtx.createScriptProcessor(1024, 0, 2);
		this.scriptNode.onaudioprocess = (e) => this._onAudioProcess(e);
		this.scriptNode.connect(this.audioCtx.destination);
	}
	
	_stopAudio() {
		if (this.scriptNode) {
			this.scriptNode.disconnect();
			this.scriptNode.onaudioprocess = null;
			this.scriptNode = null;
		}
		if (this.audioCtx) {
			this.audioCtx.close().catch(() => {});
			this.audioCtx = null;
		}
	}
	
	_onAudioProcess(e) {
		const left = e.outputBuffer.getChannelData(0);
		const right = e.outputBuffer.getChannelData(1);
		const size = left.length;
		
		// Buffer underrun - generate extra frames to catch up
		if (this.audioBuffer.size() < size * 2) {
			if (this.running && !this.muted) {
				console.log('Buffer underrun, generating frame');
				this._generateFrame();
				
				if (this.audioBuffer.size() < size * 2) {
					console.log('Still underrun, generating second frame');
					this._generateFrame();
				}
			}
		}
		
		// Try to get samples
		try {
			const samples = this.audioBuffer.deqN(size * 2);
			for (let i = 0; i < size; i++) {
				left[i] = samples[i * 2];
				right[i] = samples[i * 2 + 1];
			}
		} catch (e) {
			// Real underrun - output silence
			for (let i = 0; i < size; i++) {
				left[i] = 0;
				right[i] = 0;
			}
		}
	}
}

/**
 * Simple Ring Buffer implementation
 */
class RingBuffer {
	constructor(capacity) {
		this.capacity = capacity;
		this.buffer = new Array(capacity);
		this.head = 0;
		this.tail = 0;
		this.length = 0;
	}
	
	size() {
		return this.length;
	}
	
	enq(item) {
		if (this.length >= this.capacity) {
			throw new Error('Buffer full');
		}
		this.buffer[this.tail] = item;
		this.tail = (this.tail + 1) % this.capacity;
		this.length++;
	}
	
	deq() {
		if (this.length === 0) {
			throw new Error('Buffer empty');
		}
		const item = this.buffer[this.head];
		this.head = (this.head + 1) % this.capacity;
		this.length--;
		return item;
	}
	
	deqN(count) {
		if (this.length < count) {
			throw new Error('Not enough items');
		}
		const items = new Array(count);
		for (let i = 0; i < count; i++) {
			items[i] = this.buffer[this.head];
			this.head = (this.head + 1) % this.capacity;
		}
		this.length -= count;
		return items;
	}
}

// Button constants
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
