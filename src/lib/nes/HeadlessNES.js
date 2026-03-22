/**
 * HeadlessNES - Fast NES emulator for background training
 *
 * No rendering, no audio - just raw emulation speed.
 * Used for evaluating neural network populations during training.
 */

import telemetry from '../Telemetry.js';

// ── Shared constants for input building (matches Agent.js) ──
const INPUT_CFG = {
	startRow: 4,
	vizWidth: 7,
	vizHeight: 10
};
const RAM = {
	Player_X_Position_In_Level: 0x06D,
	Player_X_Position_On_Screen: 0x086,
	Player_X_Position_Screen_Offset: 0x3AD,
	Player_Y_Position_Screen_Offset: 0x3B8,
	Player_Y_Pos_On_Screen: 0xCE,
	Player_Vertical_Screen_Position: 0xB5,
	Player_State: 0x0E,
	Player_Float_State: 0x001D,
	Enemy_Drawn: 0x0F,
	Enemy_Type: 0x16,
	Enemy_X_Position_In_Level: 0x6E,
	Enemy_X_Position_On_Screen: 0x87,
	Enemy_Y_Position_On_Screen: 0xCF,
	Tile_Base: 0x500,
	Tile_Page_Size: 208
};

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
	 * Set initial state for quick resets.
	 * Runs settle frames ONCE and caches the result so reset() is just a fromJSON().
	 * @param {object} state - NES state object
	 */
	setInitialState(state) {
		// Deep copy to ensure we have a clean state
		this.initialState = JSON.parse(JSON.stringify(state));

		// Pre-compute settled state: load, run 100 settle frames, snapshot
		if (this.nes) {
			this.nes.fromJSON(this.initialState);
			const SETTLE_FRAMES = 100;
			for (let i = 0; i < SETTLE_FRAMES; i++) {
				this.nes.frame();
			}
			for (let i = 0; i < 8; i++) {
				this.nes.buttonUp(1, i);
			}
			// Cache the settled state — reset() will just fromJSON this
			this.settledState = this.nes.toJSON();

			const mem = this.nes.cpu.mem;
			telemetry.log('headless', 'Settled state cached', {
				x: mem[0x06D] * 256 + mem[0x086],
				yOff: mem[0x3B8],
				settleFrames: SETTLE_FRAMES
			});
		}
	}

	/**
	 * Reset to settled state (fast — just fromJSON, no settle frames)
	 */
	reset() {
		if (this.nes && this.settledState) {
			this.nes.fromJSON(this.settledState);
			// Clear any button presses
			for (let i = 0; i < 8; i++) {
				this.nes.buttonUp(1, i);
			}
		} else if (this.nes && this.initialState) {
			// Fallback if settledState not cached yet
			this.nes.fromJSON(this.initialState);
			const SETTLE_FRAMES = 100;
			for (let i = 0; i < SETTLE_FRAMES; i++) {
				this.nes.frame();
			}
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
	 * Get lightweight state for position/death/win checks — no tiles or enemies.
	 * Much cheaper than getGameState() for the post-frame position check.
	 * @returns {Object} { x, playerState, playerFloatState }
	 */
	getQuickState() {
		if (!this.nes?.cpu?.mem) return null;
		const mem = this.nes.cpu.mem;
		return {
			x: mem[RAM.Player_X_Position_In_Level] * 256 + mem[RAM.Player_X_Position_On_Screen],
			playerState: mem[RAM.Player_State],
			playerFloatState: mem[RAM.Player_Float_State]
		};
	}

	/**
	 * Build the 80-element neural network input array entirely in JS.
	 * Eliminates JsProxy overhead — Python receives a plain JS array of numbers.
	 * @returns {number[]} 80-element array: 70 vision tiles + 10 row encoding
	 */
	getInputs() {
		if (!this.nes?.cpu?.mem) return [];
		const mem = this.nes.cpu.mem;

		// Mario position
		const marioLevelX = mem[RAM.Player_X_Position_In_Level] * 256 + mem[RAM.Player_X_Position_On_Screen];
		const marioScreenX = mem[RAM.Player_X_Position_Screen_Offset];
		const marioScreenY = mem[RAM.Player_Y_Pos_On_Screen] * mem[RAM.Player_Vertical_Screen_Position] + 16; // SPRITE_HEIGHT
		const xStart = marioLevelX - marioScreenX;

		// Mario row/col
		const marioRow = Math.floor((mem[RAM.Player_Y_Position_Screen_Offset] + 16) / 16);
		const marioCol = Math.floor((mem[RAM.Player_X_Position_Screen_Offset] + 12) / 16);

		// Enemies
		const enemies = [];
		for (let i = 0; i < 5; i++) {
			if (mem[RAM.Enemy_Drawn + i]) {
				enemies.push({
					x: mem[RAM.Enemy_X_Position_In_Level + i] * 256 + mem[RAM.Enemy_X_Position_On_Screen + i],
					y: mem[RAM.Enemy_Y_Position_On_Screen + i]
				});
			}
		}

		// Build tile map (only the rows/cols we need for vision)
		// Full tile dict covers 15 rows × 16 cols, but we only need a subset
		const inputs = [];
		for (let row = INPUT_CFG.startRow; row < INPUT_CFG.startRow + INPUT_CFG.vizHeight; row++) {
			for (let col = marioCol; col < marioCol + INPUT_CFG.vizWidth; col++) {
				const yPos = row * 16;
				const xPos = xStart + col * 16;
				let val = 0;

				if (row >= 2) {
					// Tile lookup
					const page = Math.floor(xPos / 256) % 2;
					const subX = Math.floor((xPos % 256) / 16);
					const subY = Math.floor((yPos - 32) / 16);

					if (subY >= 0 && subY < 13) {
						const addr = RAM.Tile_Base + page * RAM.Tile_Page_Size + subY * 16 + subX;
						if (mem[addr] !== 0) val = 1;
					}
				}

				// Enemy check
				for (const e of enemies) {
					const ey = e.y + 8;
					if (Math.abs(xPos - e.x) <= 8 && Math.abs(yPos - ey) <= 8) {
						val = -1;
						break;
					}
				}

				inputs.push(val);
			}
		}

		// Row encoding: one-hot for mario's row relative to vision start
		const relativeRow = marioRow - INPUT_CFG.startRow;
		for (let i = 0; i < INPUT_CFG.vizHeight; i++) {
			inputs.push(i === relativeRow && relativeRow >= 0 && relativeRow < INPUT_CFG.vizHeight ? 1 : 0);
		}

		return inputs;
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
		this.settledState = null;
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
