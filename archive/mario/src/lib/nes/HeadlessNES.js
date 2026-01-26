/**
 * HeadlessNES - Sandboxed NES emulator for background training
 *
 * Completely isolated from the foreground emulator:
 * - Own NES instance (not window.nesEmulator)
 * - No canvas rendering
 * - No audio output
 * - Only shares ROM data and state format
 */

import { createLogger } from '@guinetik/logger';

const logger = createLogger({
	prefix: 'HeadlessNES',
	level: 'debug'
});

export class HeadlessNES {
	constructor() {
		this.nes = null;
		this.isLoaded = false;
		this.romData = null;  // Store ROM for reloading

		logger.log('🔇 HeadlessNES created (no rendering, no audio)');
	}

	/**
	 * Initialize with ROM data (not path - avoids re-fetching)
	 * @param {string} romBinaryString - ROM as binary string (same format jsnes uses)
	 */
	initialize(romBinaryString) {
		if (!window.jsnes) {
			throw new Error('JSNes not loaded');
		}

		this.romData = romBinaryString;

		// Create isolated NES instance with no-op callbacks
		this.nes = new window.jsnes.NES({
			onFrame: () => {},  // No rendering
			onAudioSample: () => {},  // No audio
			onStatusUpdate: () => {}  // No status
		});

		// Load ROM
		this.nes.loadROM(romBinaryString);
		this.isLoaded = true;

		logger.log('✅ HeadlessNES initialized with ROM');
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
	 * Press a button
	 * @param {number} controller - Controller number (1 or 2)
	 * @param {number} button - Button code
	 */
	buttonDown(controller, button) {
		if (this.nes && this.isLoaded) {
			this.nes.buttonDown(controller, button);
		}
	}

	/**
	 * Release a button
	 * @param {number} controller - Controller number (1 or 2)
	 * @param {number} button - Button code
	 */
	buttonUp(controller, button) {
		if (this.nes && this.isLoaded) {
			this.nes.buttonUp(controller, button);
		}
	}

	/**
	 * Read RAM byte
	 * @param {number} address - RAM address
	 * @returns {number} Byte value
	 */
	readRAM(address) {
		if (this.nes && this.isLoaded) {
			return this.nes.cpu.mem[address];
		}
		return 0;
	}

	/**
	 * Save state
	 * @returns {object} State object
	 */
	saveState() {
		if (this.nes && this.isLoaded) {
			return this.nes.toJSON();
		}
		return null;
	}

	/**
	 * Load state
	 * @param {object} state - State object
	 */
	loadState(state) {
		if (this.nes && this.isLoaded && state) {
			this.nes.fromJSON(state);
		}
	}

	/**
	 * Reset emulator
	 */
	reset() {
		if (this.nes && this.isLoaded) {
			this.nes.reset();
		}
	}

	/**
	 * Clean up
	 */
	destroy() {
		this.nes = null;
		this.isLoaded = false;
		this.romData = null;
		logger.log('🗑️ HeadlessNES destroyed');
	}
}

/**
 * Create and expose headless NES factory to window
 * Python can call window.createHeadlessNES() to get isolated instances
 */
export function initializeHeadlessNESFactory() {
	window.createHeadlessNES = () => new HeadlessNES();
	window.HeadlessNES = HeadlessNES;
	logger.log('🏭 HeadlessNES factory available on window.createHeadlessNES()');
}
