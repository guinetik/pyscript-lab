/**
 * NesEmulatorController - Clean wrapper around JSNes
 * Uses separate FrameTimer, Speakers, and Screen classes
 * Based on jsnes-react architecture
 */

import { FrameTimer } from './FrameTimer.js';
import { Speakers } from './Speakers.js';
import { Screen } from './Screen.js';
import { GamepadController } from './GamepadController.js';
import { initializeFrameSync } from './FrameSync.js';
import { createLogger } from '@guinetik/logger';

export class NesEmulatorController {
	/**
	 * Creates a NesEmulatorController
	 * @param {HTMLCanvasElement} canvasElement - Canvas element for rendering
	 */
	constructor(canvasElement) {
		this.logger = createLogger(
			{prefix: 'NesEmulatorController',
			level: 'debug'});
		// Core components
		this.canvas = canvasElement;
		this.screen = null;
		this.speakers = null;
		this.frameTimer = null;
		this.gamepadController = null;
		this.gamepadPolling = null;
		this.frameSync = null;  // Frame synchronization for Python agent

		// NES instance
		this.nes = null;
		this.isLoaded = false;
		this.isRunning = false;

		// Callbacks
		this.onReadyCallback = null;
		this.onErrorCallback = null;

		// Initialize frame sync (makes it available to Python)
		this.frameSync = initializeFrameSync();

		this.logger.log('🎮 NesEmulatorController created');
	}

	/**
	 * Initialize the emulator
	 * @param {string} romPath - Path to ROM file
	 * @param {Function} onReady - Called when emulator is ready
	 * @param {Function} onError - Called on error
	 */
	async initialize(romPath, onReady, onError) {
		this.onReadyCallback = onReady;
		this.onErrorCallback = onError;

		try {
			// Load JSNes library
			await this.loadScript('https://unpkg.com/jsnes@1.2.1/dist/jsnes.min.js');

			// @ts-ignore - jsnes is loaded dynamically
			if (!window.jsnes) {
				throw new Error('JSNes failed to load');
			}

			this.logger.log('✅ JSNes loaded');

			// Create screen
			this.screen = new Screen(this.canvas);

			// Create speakers with buffer underrun handling
			this.speakers = new Speakers({
				onBufferUnderrun: (/** @type {number} */ actualSize, /** @type {number} */ desiredSize) => {
					// Generate extra frame to catch up on audio
					if (this.frameTimer && this.isRunning) {
						this.logger.log('🔊 Audio buffer underrun, generating extra frame');
						this.frameTimer.generateFrame();
						
						// Check if we need a second frame
						// @ts-ignore - speakers exists here
						if (this.speakers.getBufferSize() / 2 < desiredSize) {
							this.logger.log('🔊 Still underrun, generating second frame');
							this.frameTimer.generateFrame();
						}
					}
				}
			});

			// Create NES instance
			this.setupNES();

			// Create frame timer (30 FPS for training mode)
			this.frameTimer = new FrameTimer({
				fps: 30,  // Run emulator at 30 FPS to sync with agent
				onGenerateFrame: (time) => {
					if (this.nes && this.isLoaded) {
						this.nes.frame();

						// Notify Python agent that a new frame is ready
						// This ensures 1:1 correspondence between emulator frames and agent observations
						if (this.frameSync) {
							this.frameSync.onFrameGenerated(time);
						}
					}
				},
				onWriteFrame: () => {
					if (this.screen) {
						this.screen.writeBuffer();
					}
				}
			});

			// Create gamepad controller
			this.gamepadController = new GamepadController({
				onButtonDown: (/** @type {number} */ player, /** @type {number} */ button) => {
					if (this.nes && this.isLoaded) {
						this.nes.buttonDown(player, button);
					}
				},
				onButtonUp: (/** @type {number} */ player, /** @type {number} */ button) => {
					if (this.nes && this.isLoaded) {
						this.nes.buttonUp(player, button);
					}
				}
			});

			// Start gamepad polling
			this.gamepadPolling = this.gamepadController.startPolling();

			// Load ROM if provided
			if (romPath) {
				const loaded = await this.loadROM(romPath);
				if (!loaded) {
					throw new Error('Failed to load ROM');
				}
			}

			this.logger.log('✅ NesEmulatorController initialized');

			if (this.onReadyCallback) {
				this.onReadyCallback(this);
			}
		} catch (error) {
			console.error('❌ Initialization failed:', error);
			if (this.onErrorCallback) {
				this.onErrorCallback(error);
			}
		}
	}

	/**
	 * Setup NES instance with callbacks
	 */
	setupNES() {
		// @ts-ignore - jsnes is loaded dynamically
		this.nes = new window.jsnes.NES({
			onFrame: (/** @type {any} */ framebuffer) => {
				// Pass frame to screen
				// @ts-ignore - screen exists here
				this.screen.setBuffer(framebuffer);
			},
			onAudioSample: (/** @type {number} */ left, /** @type {number} */ right) => {
				// Pass audio samples to speakers
				// @ts-ignore - speakers exists here
				this.speakers.writeSample(left, right);
			},
			onStatusUpdate: (/** @type {string} */ status) => {
				this.logger.log('🎮 JSNes status:', status);
			}
		});

		// JSNes internally calls stop() on errors but doesn't provide the method
		// Add stub that logs but doesn't actually stop (let it keep running)
		let stopCallCount = 0;
		this.nes.stop = () => {
			stopCallCount++;
			if (stopCallCount === 1) {
				console.warn('⚠️ JSNes called stop() - ignoring to keep emulation running');
				console.warn('   Stack trace:', new Error().stack);
			}
			// DON'T call this.stop() - let the emulator keep running
		};

		this.nes.start = () => {
			this.logger.log('▶️ JSNes called start()');
		};

		this.logger.log('✅ NES instance created');
	}

	/**
	 * Load ROM from URL
	 * @param {string} path - Path to ROM file
	 * @returns {Promise<boolean>} True if loaded successfully
	 */
	async loadROM(path) {
		try {
			this.logger.log(`🎮 Loading ROM: ${path}`);

			if (!this.nes) {
				throw new Error('NES instance not created yet');
			}

			const response = await fetch(path);
			if (!response.ok) {
				throw new Error(`Failed to fetch ROM: ${response.statusText}`);
			}

			const arrayBuffer = await response.arrayBuffer();
			const romData = new Uint8Array(arrayBuffer);

			this.logger.log(`📦 ROM data received: ${romData.length} bytes`);

			// Convert to binary string (JSNes expects this format)
			let binaryString = '';
			for (let i = 0; i < romData.length; i++) {
				binaryString += String.fromCharCode(romData[i]);
			}

			// Load into NES
			this.nes.loadROM(binaryString);
			
			// Verify NES is in good state
			// @ts-ignore - cpu and ppu are internal JSNes properties
			if (!this.nes || !this.nes.cpu || !this.nes.ppu) {
				throw new Error('NES not properly initialized after ROM load');
			}

			this.isLoaded = true;
			this.logger.log('✅ ROM loaded successfully');
			return true;
		} catch (error) {
			console.error('❌ ROM loading failed:', error);
			this.isLoaded = false;
			if (this.onErrorCallback) {
				this.onErrorCallback(error);
			}
			return false;
		}
	}

	/**
	 * Start emulation
	 */
	start() {
		if (!this.isLoaded || !this.nes) {
			console.error('❌ Cannot start - not ready');
			return;
		}

		if (this.isRunning) {
			console.warn('⚠️ Already running');
			return;
		}

		this.logger.log('▶️ Starting emulation');
		
		this.isRunning = true;
		
		if (this.frameTimer) {
			this.frameTimer.start();
		}
		if (this.speakers) {
			this.speakers.start();
		}
		
		this.logger.log('✅ Emulation started');
	}

	/**
	 * Stop emulation
	 */
	stop() {
		if (!this.isRunning) {
			return;
		}

		this.logger.log('⏹️ Stopping emulation');
		
		this.isRunning = false;
		
		if (this.frameTimer) {
			this.frameTimer.stop();
		}
		
		if (this.speakers) {
			this.speakers.stop();
		}
		
		this.logger.log('✅ Emulation stopped');
	}

	/**
	 * Reset the emulator
	 */
	reset() {
		if (this.nes && this.isLoaded) {
			this.nes.reset();
			this.logger.log('🔄 Emulator reset');
		}
	}

	/**
	 * Save current emulator state
	 * @returns {object|null} State object (to be stringified by caller)
	 */
	saveState() {
		if (this.nes && this.isLoaded) {
			try {
				const state = this.nes.toJSON(); // Returns an object, not a string
				this.logger.log('💾 State saved (object)');
				return state;
			} catch (error) {
				console.error('❌ Failed to save state:', error);
				return null;
			}
		}
		return null;
	}

	/**
	 * Load emulator state from object
	 * @param {object} stateObj - State object (parsed from JSON)
	 * @returns {boolean} True if loaded successfully
	 */
	loadState(stateObj) {
		if (this.nes && this.isLoaded && stateObj) {
			try {
				this.nes.fromJSON(stateObj);
				this.logger.log('📂 State loaded successfully');
				return true;
			} catch (error) {
				console.error('❌ Failed to load state:', error);
				console.error('Error details:', error.message);
				return false;
			}
		}
		console.warn('⚠️ Cannot load state: emulator not ready or invalid state');
		return false;
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
	 * Get the frame buffer (for external access like RL agents)
	 * @returns {Uint8ClampedArray | null} Frame buffer
	 */
	get framebuffer_u8() {
		return this.screen ? this.screen.getBuffer() : null;
	}

	/**
	 * Destroy the emulator and clean up resources
	 */
	destroy() {
		this.stop();

		if (this.speakers) {
			this.speakers.destroy(); // Use destroy() not stop()
		}

		if (this.gamepadPolling) {
			this.gamepadPolling.stop();
		}

		if (this.gamepadController) {
			this.gamepadController.destroy();
		}

		this.nes = null;
		this.screen = null;
		this.speakers = null;
		this.frameTimer = null;
		this.gamepadController = null;
		this.gamepadPolling = null;

		this.logger.log('🗑️ NesEmulatorController destroyed');
	}

	/**
	 * Load external script
	 * @param {string} src - Script URL
	 * @returns {Promise<void>}
	 */
	loadScript(src) {
		return new Promise((resolve, reject) => {
			if (document.querySelector(`script[src="${src}"]`)) {
				resolve();
				return;
			}

			const script = document.createElement('script');
			script.src = src;
			script.onload = () => resolve();
			script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
			document.head.appendChild(script);
		});
	}
}
