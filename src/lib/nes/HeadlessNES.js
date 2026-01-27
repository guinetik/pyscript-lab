/**
 * HeadlessNES - Fast NES emulator for background training
 *
 * No rendering, no audio - just raw emulation speed.
 * Used for evaluating neural network populations during training.
 */

import telemetry from '../Telemetry.js';

export class HeadlessNES {
	constructor() {
		this.nes = null;
		this.isLoaded = false;
		this.romData = null;
		this.initialState = null;

		telemetry.log('headless', 'Created');
	}

	/**
	 * Initialize with ROM binary string
	 * @param {string} romBinaryString - ROM as binary string
	 */
	initialize(romBinaryString) {
		if (!window.jsnes) {
			throw new Error('JSNes not loaded');
		}

		this.romData = romBinaryString;

		// Get proper sample rate (matches visual NES)
		// JSNes uses sampleRate for internal timing calculations
		let sampleRate = 44100;
		if (window.AudioContext) {
			try {
				const ctx = new AudioContext();
				sampleRate = ctx.sampleRate;
				ctx.close();
			} catch (e) {
				// Use default
			}
		}

		// Create NES with no-op callbacks but proper sample rate
		// CRITICAL: sampleRate must match visual NES for consistent physics timing
		this.nes = new window.jsnes.NES({
			onFrame: () => {},
			onAudioSample: () => {},
			onStatusUpdate: () => {},
			sampleRate: sampleRate
		});

		this.nes.loadROM(romBinaryString);
		this.isLoaded = true;

		telemetry.log('headless', 'Initialized', { sampleRate });
	}

	/**
	 * Set initial state for quick resets
	 * @param {object} state - NES state object
	 */
	setInitialState(state) {
		// Deep copy to ensure we have a clean state
		this.initialState = JSON.parse(JSON.stringify(state));
	}

	/**
	 * Reset to initial state (fast)
	 */
	reset() {
		if (this.nes && this.initialState) {
			// Load the saved state
			this.nes.fromJSON(this.initialState);

			// Capture state after fromJSON
			const mem = this.nes.cpu.mem;
			const afterFromJSON = {
				x: mem[0x06D] * 256 + mem[0x086],
				yOff: mem[0x3B8],
				xOff: mem[0x3AD]
			};

			// Run settle frames for game to properly start and Mario to spawn
			// Need ~100 frames for Mario to fall to ground from spawn
			const SETTLE_FRAMES = 100;
			for (let i = 0; i < SETTLE_FRAMES; i++) {
				this.nes.frame();
			}

			// Capture state after settle frames
			const afterSettle = {
				x: mem[0x06D] * 256 + mem[0x086],
				yOff: mem[0x3B8],
				xOff: mem[0x3AD],
				settleFrames: SETTLE_FRAMES
			};

			// Log reset with both states for comparison
			telemetry.logReset('headless', afterFromJSON, afterSettle);

			// Clear any button presses from state
			for (let i = 0; i < 8; i++) {
				this.nes.buttonUp(1, i);
			}
		} else if (this.nes) {
			telemetry.log('headless', 'No initialState, doing hard reset');
			this.nes.reset();
		}
	}

	/**
	 * Advance one frame
	 */
	frame() {
		if (this.nes && this.isLoaded) {
			this.nes.frame();
		}
	}

	/**
	 * Run multiple frames (batch processing)
	 * @param {number} count - Number of frames to run
	 */
	runFrames(count) {
		for (let i = 0; i < count; i++) {
			this.frame();
		}
	}

	/**
	 * Press button
	 */
	buttonDown(controller, button) {
		if (this.nes && this.isLoaded) {
			this.nes.buttonDown(controller, button);
		}
	}

	/**
	 * Release button
	 */
	buttonUp(controller, button) {
		if (this.nes && this.isLoaded) {
			this.nes.buttonUp(controller, button);
		}
	}

	/**
	 * Set button state directly
	 * @param {number[]} buttons - Array of button indices to press
	 */
	setButtons(buttons) {
		if (!this.nes || !this.isLoaded) return;

		// Release all buttons first
		for (let i = 0; i < 8; i++) {
			this.nes.buttonUp(1, i);
		}

		// Press specified buttons
		for (const btn of buttons) {
			this.nes.buttonDown(1, btn);
		}
	}

	/**
	 * Read RAM byte
	 */
	readRAM(address) {
		if (this.nes && this.isLoaded) {
			return this.nes.cpu.mem[address];
		}
		return 0;
	}

	/**
	 * Read multiple RAM bytes
	 * @param {number[]} addresses - Array of addresses
	 * @returns {number[]} Array of values
	 */
	readRAMBatch(addresses) {
		if (!this.nes || !this.isLoaded) return addresses.map(() => 0);
		return addresses.map(addr => this.nes.cpu.mem[addr]);
	}

	/**
	 * Get full CPU memory reference (for agent)
	 */
	get mem() {
		return this.nes?.cpu?.mem || null;
	}

	/**
	 * Get Mario's current X position (for debugging)
	 */
	getMarioX() {
		if (!this.nes?.cpu?.mem) return 0;
		return this.nes.cpu.mem[0x06D] * 256 + this.nes.cpu.mem[0x086];
	}

	/**
	 * Get memory as plain array (for Python interop)
	 * Converts Uint8Array to regular Array for better PyScript compatibility
	 * WARNING: This is slow (copies 65KB) - prefer getGameState() for training
	 */
	getMemArray() {
		if (!this.nes?.cpu?.mem) return [];
		return Array.from(this.nes.cpu.mem);
	}

	/**
	 * Get only the RAM addresses needed for Mario AI - MUCH faster than getMemArray()
	 * Returns a plain object with all values needed for build_inputs, is_dead, did_win, etc.
	 * @returns {Object} Game state with specific RAM values
	 */
	getGameState() {
		if (!this.nes?.cpu?.mem) return null;
		const mem = this.nes.cpu.mem;

		// Player position
		const playerXLevel = mem[0x06D];
		const playerXScreen = mem[0x086];
		const playerXScreenOffset = mem[0x3AD];
		const playerYScreenOffset = mem[0x3B8];
		const playerYScreen = mem[0xCE];
		const playerVerticalScreen = mem[0xB5];
		const playerState = mem[0x000E];
		const playerFloatState = mem[0x001D];

		// Enemies (5 slots)
		const enemies = [];
		for (let i = 0; i < 5; i++) {
			enemies.push({
				drawn: mem[0x0F + i],
				type: mem[0x16 + i],
				xLevel: mem[0x6E + i],
				xScreen: mem[0x87 + i],
				yScreen: mem[0xCF + i]
			});
		}

		// Tiles: 2 pages × 208 bytes = 416 bytes (much smaller than 65KB!)
		const tiles = [];
		for (let i = 0; i < 416; i++) {
			tiles.push(mem[0x500 + i]);
		}

		return {
			playerXLevel,
			playerXScreen,
			playerXScreenOffset,
			playerYScreenOffset,
			playerYScreen,
			playerVerticalScreen,
			playerState,
			playerFloatState,
			enemies,
			tiles
		};
	}

	/**
	 * Save state
	 */
	saveState() {
		if (this.nes && this.isLoaded) {
			return this.nes.toJSON();
		}
		return null;
	}

	/**
	 * Load state
	 */
	loadState(state) {
		if (this.nes && this.isLoaded && state) {
			this.nes.fromJSON(state);
		}
	}

	/**
	 * Clean up
	 */
	destroy() {
		this.nes = null;
		this.isLoaded = false;
		this.romData = null;
		this.initialState = null;
	}
}

/**
 * HeadlessNES Pool - Manages multiple instances for parallel evaluation
 */
export class HeadlessNESPool {
	constructor(size = 4) {
		this.pool = [];
		this.size = size;
		this.romData = null;
		this.initialState = null;
	}

	/**
	 * Initialize pool with ROM data
	 */
	initialize(romBinaryString, initialState = null) {
		this.romData = romBinaryString;
		this.initialState = initialState;

		telemetry.log('headless', 'Pool initializing', { size: this.size });

		// Create pool of headless instances
		for (let i = 0; i < this.size; i++) {
			const instance = new HeadlessNES();
			instance.initialize(romBinaryString);
			if (initialState) {
				// Deep copy state to avoid mutation issues
				const stateCopy = JSON.parse(JSON.stringify(initialState));
				instance.setInitialState(stateCopy);
				instance.reset();
			}
			this.pool.push(instance);
		}

		// Verify first instance position
		if (this.pool.length > 0 && this.pool[0].nes) {
			const mem = this.pool[0].nes.cpu.mem;
			const x = mem[0x06D] * 256 + mem[0x086];
			const yOff = mem[0x3B8];
			telemetry.log('headless', 'Pool ready', { initialX: x, initialYOff: yOff });
		}
	}

	/**
	 * Get an instance from pool
	 */
	getInstance(index) {
		return this.pool[index % this.size];
	}

	/**
	 * Reset all instances to initial state
	 */
	resetAll() {
		for (const instance of this.pool) {
			instance.reset();
		}
	}

	/**
	 * Destroy all instances
	 */
	destroy() {
		for (const instance of this.pool) {
			instance.destroy();
		}
		this.pool = [];
	}
}

// Export factory for window access
export function initHeadlessNESFactory() {
	window.createHeadlessNES = () => new HeadlessNES();
	window.createHeadlessNESPool = (size) => new HeadlessNESPool(size);
	window.HeadlessNES = HeadlessNES;
	window.HeadlessNESPool = HeadlessNESPool;
	telemetry.log('headless', 'Factory functions available on window');
}
