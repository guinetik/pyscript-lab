/**
 * Mario AI Agent
 */

import telemetry from '../Telemetry.js';

// Network config (world 1-1)
const CONFIG = {
	startRow: 4,
	vizWidth: 7,
	vizHeight: 10,
	hiddenSize: 9,
	outputSize: 6
};

// RAM addresses from reference utils.py
const RAM = {
	// Player position
	Player_X_Position_In_Level: 0x06D,
	Player_X_Position_On_Screen: 0x086,
	Player_X_Position_Screen_Offset: 0x3AD,
	Player_Y_Position_Screen_Offset: 0x3B8,
	Player_Y_Pos_On_Screen: 0xCE,
	Player_Vertical_Screen_Position: 0xB5,

	// Enemies (5 max)
	Enemy_Drawn: 0x0F,
	Enemy_Type: 0x16,
	Enemy_X_Position_In_Level: 0x6E,
	Enemy_X_Position_On_Screen: 0x87,
	Enemy_Y_Position_On_Screen: 0xCF,

	// Game state
	Player_State: 0x0E,
	Player_Dying: 0x001D,

	// Tiles
	Tile_Base: 0x500,
	Tile_Page_Size: 208
};

// Sprite size
const SPRITE_WIDTH = 16;
const SPRITE_HEIGHT = 16;

// JSNes button indices: A=0, B=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7
const OUTPUT_TO_BUTTON = [4, 5, 6, 7, 0, 1]; // UP, DOWN, LEFT, RIGHT, A, B

export class Agent {
	constructor() {
		this.W1 = null;
		this.b1 = null;
		this.W2 = null;
		this.b2 = null;
		this.loaded = false;

		this.framesAlive = 0;
		this.farthestX = 0;
		this.framesSinceProgress = 0;
		this.maxFramesStuck = 60 * 3;

		// For debugging
		this.lastInputs = [];
		this.lastOutputs = [];

		telemetry.log('agent', 'Agent created');
	}

	async loadWeights(basePath = '/data/reference_weights') {
		const [W1, b1, W2, b2] = await Promise.all([
			fetch(`${basePath}/W1.json`).then(r => r.json()),
			fetch(`${basePath}/b1.json`).then(r => r.json()),
			fetch(`${basePath}/W2.json`).then(r => r.json()),
			fetch(`${basePath}/b2.json`).then(r => r.json())
		]);

		this.W1 = W1;
		this.b1 = b1;
		this.W2 = W2;
		this.b2 = b2;
		this.loaded = true;

		telemetry.log('agent', 'Weights loaded', {
			W1: `${W1.length}x${W1[0].length}`,
			b1: b1.length,
			W2: `${W2.length}x${W2[0].length}`,
			b2: b2.length
		});

		return this;
	}

	reset() {
		this.framesAlive = 0;
		this.farthestX = 0;
		this.framesSinceProgress = 0;
	}

	// Reference: SMB.get_mario_location_in_level
	getMarioLocationInLevel(ram) {
		const x = ram[RAM.Player_X_Position_In_Level] * 256 + ram[RAM.Player_X_Position_On_Screen];
		const y = ram[RAM.Player_Y_Position_Screen_Offset];
		return { x, y };
	}

	// Reference: SMB.get_mario_location_on_screen
	getMarioLocationOnScreen(ram) {
		const x = ram[RAM.Player_X_Position_Screen_Offset];
		const y = ram[RAM.Player_Y_Pos_On_Screen] * ram[RAM.Player_Vertical_Screen_Position] + SPRITE_HEIGHT;
		return { x, y };
	}

	// Reference: SMB.get_mario_row_col
	getMarioRowCol(ram) {
		const y = ram[RAM.Player_Y_Position_Screen_Offset] + 16;
		const x = ram[RAM.Player_X_Position_Screen_Offset] + 12;
		const col = Math.floor(x / 16);
		const row = Math.floor(y / 16);
		return { row, col };
	}

	// Reference: SMB.get_tile with group_non_zero_tiles=true
	getTile(ram, x, y) {
		const page = Math.floor(x / 256) % 2;
		const subX = Math.floor((x % 256) / 16);
		const subY = Math.floor((y - 32) / 16);

		if (subY < 0 || subY >= 13) {
			return 0; // Empty (StaticTileType.Empty)
		}

		const addr = RAM.Tile_Base + page * RAM.Tile_Page_Size + subY * 16 + subX;
		const tile = ram[addr];

		// group_non_zero_tiles: if non-zero, return 1 (Fake/solid)
		return tile !== 0 ? 1 : 0;
	}

	// Reference: SMB.get_enemy_locations
	getEnemies(ram) {
		const enemies = [];

		for (let i = 0; i < 5; i++) {
			const drawn = ram[RAM.Enemy_Drawn + i];
			if (drawn) {
				const xLevel = ram[RAM.Enemy_X_Position_In_Level + i];
				const xScreen = ram[RAM.Enemy_X_Position_On_Screen + i];
				const x = xLevel * 256 + xScreen;
				const y = ram[RAM.Enemy_Y_Position_On_Screen + i];
				enemies.push({ x, y });
			}
		}

		return enemies;
	}

	// Reference: SMB.get_tiles - builds tile dictionary for screen
	getTiles(ram) {
		const tiles = {};

		const marioLevel = this.getMarioLocationInLevel(ram);
		const marioScreen = this.getMarioLocationOnScreen(ram);
		const xStart = marioLevel.x - marioScreen.x;

		const enemies = this.getEnemies(ram);

		let row = 0;
		for (let yPos = 0; yPos < 240; yPos += 16) {
			let col = 0;
			for (let xPos = xStart; xPos < xStart + 256; xPos += 16) {
				const key = `${row},${col}`;

				// PPU/status bar (first 2 rows)
				if (row < 2) {
					tiles[key] = 0;
				} else {
					tiles[key] = this.getTile(ram, xPos, yPos);
				}

				// Check for enemies at this position
				for (const enemy of enemies) {
					const ex = enemy.x;
					const ey = enemy.y + 8; // Reference uses +8 offset

					// Reference: if abs(x_pos - ex) <= 8 and abs(y_pos - ey) <= 8
					if (Math.abs(xPos - ex) <= 8 && Math.abs(yPos - ey) <= 8) {
						tiles[key] = -1; // Enemy
					}
				}

				col++;
			}
			row++;
		}

		return tiles;
	}

	// Reference: Mario.set_input_as_array
	buildInputs(ram) {
		const { row: marioRow, col: marioCol } = this.getMarioRowCol(ram);
		const tiles = this.getTiles(ram);
		const inputs = [];

		// Vision grid: 10 rows starting at row 4, 7 cols starting at mario_col
		for (let row = CONFIG.startRow; row < CONFIG.startRow + CONFIG.vizHeight; row++) {
			for (let col = marioCol; col < marioCol + CONFIG.vizWidth; col++) {
				const key = `${row},${col}`;
				const tile = tiles[key];

				if (tile === undefined) {
					inputs.push(0);
				} else if (tile === -1) {
					inputs.push(-1); // Enemy
				} else if (tile === 1 || tile > 0) {
					inputs.push(1); // Solid
				} else {
					inputs.push(0); // Empty
				}
			}
		}

		// Row encoding: one-hot for mario's row relative to vision start
		const relativeRow = marioRow - CONFIG.startRow;
		for (let i = 0; i < CONFIG.vizHeight; i++) {
			inputs.push(i === relativeRow && relativeRow >= 0 && relativeRow < CONFIG.vizHeight ? 1 : 0);
		}

		this.lastInputs = inputs;
		return inputs;
	}

	relu(x) {
		return Math.max(0, x);
	}

	sigmoid(x) {
		return 1.0 / (1.0 + Math.exp(-x));
	}

	forward(inputs) {
		// Hidden layer
		const hidden = [];
		for (let i = 0; i < CONFIG.hiddenSize; i++) {
			let sum = this.b1[i];
			for (let j = 0; j < inputs.length; j++) {
				sum += this.W1[i][j] * inputs[j];
			}
			hidden.push(this.relu(sum));
		}

		// Output layer
		const outputs = [];
		for (let i = 0; i < CONFIG.outputSize; i++) {
			let sum = this.b2[i];
			for (let j = 0; j < hidden.length; j++) {
				sum += this.W2[i][j] * hidden[j];
			}
			outputs.push(this.sigmoid(sum));
		}

		this.lastOutputs = outputs;
		return outputs;
	}

	isDead(ram) {
		const state = ram[RAM.Player_State];
		return state === 0x0B || state === 0x06 || ram[0xB5] === 2;
	}

	didWin(ram) {
		return ram[0x001D] === 3;
	}

	update(nes) {
		if (!this.loaded) return [];

		const ram = nes.cpu.mem;
		this.framesAlive++;

		if (this.isDead(ram)) {
			return [];
		}

		if (this.didWin(ram)) {
			return [];
		}

		const pos = this.getMarioLocationInLevel(ram);
		if (pos.x > this.farthestX) {
			this.farthestX = pos.x;
			this.framesSinceProgress = 0;
		} else {
			this.framesSinceProgress++;
		}

		if (this.framesSinceProgress > this.maxFramesStuck) {
			return [];
		}

		const inputs = this.buildInputs(ram);
		const outputs = this.forward(inputs);

		// Convert to button presses
		// Network outputs: [UP, DOWN, LEFT, RIGHT, A, B]
		// OUTPUT_TO_BUTTON: [4, 5, 6, 7, 0, 1]
		//
		// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		// DO NOT REMOVE THE UP/DOWN FILTERING BELOW!
		// The reference weights were trained with this filtering.
		// Removing it will break the "Start AI" mode with reference weights.
		// The Python trainer (agent.py) must use the same filtering for
		// trained weights to be compatible with this JS playback.
		// !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		const buttons = [];
		for (let i = 0; i < outputs.length; i++) {
			if (outputs[i] > 0.5) {
				const btn = OUTPUT_TO_BUTTON[i];
				// CRITICAL: Skip UP (4) and DOWN (5) - DO NOT CHANGE
				if (btn !== 4 && btn !== 5) {
					buttons.push(btn);
				}
			}
		}

		return buttons;
	}

	getStats(nes) {
		const ram = nes.cpu.mem;
		const pos = this.getMarioLocationInLevel(ram);
		return {
			x: pos.x,
			y: pos.y,
			frames: this.framesAlive,
			farthestX: this.farthestX,
			framesSinceProgress: this.framesSinceProgress
		};
	}
}
