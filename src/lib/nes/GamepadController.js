/**
 * GamepadController - Handles gamepad input for NES emulator
 * Based on jsnes-react implementation
 */

import { createLogger } from "@guinetik/logger";

// NES button constants
export const NES_BUTTON = {
	A: 0,
	B: 1,
	SELECT: 2,
	START: 3,
	UP: 4,
	DOWN: 5,
	LEFT: 6,
	RIGHT: 7
};

export class GamepadController {
	/**
	 * Creates a GamepadController
	 * @param {Object} options - Configuration
	 * @param {Function} options.onButtonDown - Called when button pressed
	 * @param {Function} options.onButtonUp - Called when button released
	 */
	constructor({ onButtonDown, onButtonUp }) {
		this.logger = createLogger(
			{prefix: 'GamepadController',
			level: 'debug'});
		this.onButtonDown = onButtonDown;
		this.onButtonUp = onButtonUp;
		
		// Track button states to detect changes
		this.buttonStates = {};
		
		// Polling interval
		this.pollingInterval = null;
		this.isPolling = false;
		
		// Gamepad enabled flag
		this.enabled = true;
		
		this.logger.log('🎮 GamepadController created');
	}

	/**
	 * Default button mapping (Xbox/PlayStation style)
	 * Can be customized by user
	 */
	getDefaultMapping() {
		return {
			// Standard gamepad buttons (indices 0-15)
			0: NES_BUTTON.B,      // A button (Xbox) / Cross (PS)
			1: NES_BUTTON.A,      // B button (Xbox) / Circle (PS)
			2: NES_BUTTON.SELECT, // X button (Xbox) / Square (PS)
			3: NES_BUTTON.START,  // Y button (Xbox) / Triangle (PS)
			8: NES_BUTTON.SELECT, // Select/Back
			9: NES_BUTTON.START,  // Start
			12: NES_BUTTON.UP,    // D-pad up
			13: NES_BUTTON.DOWN,  // D-pad down
			14: NES_BUTTON.LEFT,  // D-pad left
			15: NES_BUTTON.RIGHT  // D-pad right
		};
	}

	/**
	 * Start polling for gamepad input
	 * @param {number} [interval=16] - Polling interval in ms (default ~60fps)
	 */
	startPolling(interval = 16) {
		if (this.isPolling) {
			console.warn('⚠️ GamepadController already polling');
			return;
		}

		this.logger.log('▶️ GamepadController polling started');
		this.isPolling = true;
		this.buttonStates = {};

		this.pollingInterval = setInterval(() => {
			this.pollGamepads();
		}, interval);

		return {
			stop: () => this.stopPolling()
		};
	}

	/**
	 * Stop polling for gamepad input
	 */
	stopPolling() {
		if (!this.isPolling) {
			return;
		}

		this.logger.log('⏹️ GamepadController polling stopped');
		this.isPolling = false;

		if (this.pollingInterval) {
			clearInterval(this.pollingInterval);
			this.pollingInterval = null;
		}
	}

	/**
	 * Poll all connected gamepads
	 */
	pollGamepads() {
		if (!this.enabled) {
			return;
		}

		const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
		
		for (let i = 0; i < gamepads.length; i++) {
			const gamepad = gamepads[i];
			if (gamepad && gamepad.connected) {
				// Use player 1 for first gamepad, player 2 for second
				const player = i === 0 ? 1 : 2;
				this.processGamepad(gamepad, player);
			}
		}
	}

	/**
	 * Process a single gamepad's input
	 * @param {Gamepad} gamepad - The gamepad to process
	 * @param {number} player - Player number (1 or 2)
	 */
	processGamepad(gamepad, player) {
		const mapping = this.getDefaultMapping();
		const stateKey = `${gamepad.index}`;

		// Initialize state for this gamepad if needed
		if (!this.buttonStates[stateKey]) {
			this.buttonStates[stateKey] = {};
		}

		// Check standard buttons
		gamepad.buttons.forEach((button, index) => {
			const nesButton = mapping[index];
			if (nesButton === undefined) {
				return;
			}

			const buttonKey = `btn_${index}`;
			const isPressed = button.pressed || button.value > 0.5;
			const wasPressed = this.buttonStates[stateKey][buttonKey];

			if (isPressed && !wasPressed) {
				// Button just pressed
				this.onButtonDown(player, nesButton);
				this.buttonStates[stateKey][buttonKey] = true;
			} else if (!isPressed && wasPressed) {
				// Button just released
				this.onButtonUp(player, nesButton);
				this.buttonStates[stateKey][buttonKey] = false;
			}
		});

		// Check analog sticks for directional input
		this.processAnalogStick(gamepad, player, stateKey);
	}

	/**
	 * Process analog stick input as directional buttons
	 * @param {Gamepad} gamepad - The gamepad
	 * @param {number} player - Player number
	 * @param {string} stateKey - State key for this gamepad
	 */
	processAnalogStick(gamepad, player, stateKey) {
		// Left stick (axes 0 and 1) - standard Xbox/PlayStation
		const deadzone = 0.3;
		const xAxis = gamepad.axes[0] || 0;
		const yAxis = gamepad.axes[1] || 0;

		// Horizontal
		const pressingLeft = xAxis < -deadzone;
		const pressingRight = xAxis > deadzone;
		const wasPressingLeft = this.buttonStates[stateKey].axis_left;
		const wasPressingRight = this.buttonStates[stateKey].axis_right;

		if (pressingLeft && !wasPressingLeft) {
			this.onButtonDown(player, NES_BUTTON.LEFT);
			this.buttonStates[stateKey].axis_left = true;
		} else if (!pressingLeft && wasPressingLeft) {
			this.onButtonUp(player, NES_BUTTON.LEFT);
			this.buttonStates[stateKey].axis_left = false;
		}

		if (pressingRight && !wasPressingRight) {
			this.onButtonDown(player, NES_BUTTON.RIGHT);
			this.buttonStates[stateKey].axis_right = true;
		} else if (!pressingRight && wasPressingRight) {
			this.onButtonUp(player, NES_BUTTON.RIGHT);
			this.buttonStates[stateKey].axis_right = false;
		}

		// Vertical
		const pressingUp = yAxis < -deadzone;
		const pressingDown = yAxis > deadzone;
		const wasPressingUp = this.buttonStates[stateKey].axis_up;
		const wasPressingDown = this.buttonStates[stateKey].axis_down;

		if (pressingUp && !wasPressingUp) {
			this.onButtonDown(player, NES_BUTTON.UP);
			this.buttonStates[stateKey].axis_up = true;
		} else if (!pressingUp && wasPressingUp) {
			this.onButtonUp(player, NES_BUTTON.UP);
			this.buttonStates[stateKey].axis_up = false;
		}

		if (pressingDown && !wasPressingDown) {
			this.onButtonDown(player, NES_BUTTON.DOWN);
			this.buttonStates[stateKey].axis_down = true;
		} else if (!pressingDown && wasPressingDown) {
			this.onButtonUp(player, NES_BUTTON.DOWN);
			this.buttonStates[stateKey].axis_down = false;
		}
	}

	/**
	 * Disable gamepad input (e.g., when keyboard is being used)
	 * @returns {Function} Function that wraps another function, disabling it if gamepad is enabled
	 */
	disableIfGamepadEnabled(fn) {
		return (...args) => {
			if (!this.enabled) {
				return fn(...args);
			}
			// If gamepad is enabled, don't call the function (blocks keyboard)
		};
	}

	/**
	 * Check if any gamepad is connected
	 * @returns {boolean} True if at least one gamepad is connected
	 */
	isGamepadConnected() {
		const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
		return gamepads.some(gp => gp && gp.connected);
	}

	/**
	 * Cleanup
	 */
	destroy() {
		this.stopPolling();
		this.logger.log('🗑️ GamepadController destroyed');
	}
}

