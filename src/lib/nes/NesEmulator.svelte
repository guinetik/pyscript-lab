<script>
	import { onMount, onDestroy } from 'svelte';
	import { NesEmulatorController } from './index.js';

	let {
		romPath = '',
		width = 256,
		height = 240,
		scale = 2,
		onReady = () => {},
		onError = (error) => console.error(error)
	} = $props();

	let canvasElement;
	let controller;
	let keyboardEnabled = false;

	onMount(async () => {
		// Create controller
		controller = new NesEmulatorController(canvasElement);

		// Initialize with ROM
		await controller.initialize(romPath, (ctrl) => {
			console.log('✅ Controller ready');

			// Expose to window for Python/external access
			window.nesEmulator = {
				controller: ctrl,
				nes: ctrl.nes,
				start: () => ctrl.start(),
				stop: () => ctrl.stop(),
				reset: () => ctrl.reset(),
				buttonDown: (c, b) => ctrl.buttonDown(c, b),
				buttonUp: (c, b) => ctrl.buttonUp(c, b),
				frame: () => ctrl.nes && ctrl.isLoaded ? ctrl.nes.frame() : null,
				isLoaded: () => ctrl.isLoaded,
				isRunning: () => ctrl.isRunning,
				enableKeyboard: enableKeyboardControls,
				disableKeyboard: disableKeyboardControls,
				loadROM: (path) => ctrl.loadROM(path),
				getFrameBuffer: () => ctrl.framebuffer_u8,
				// Gamepad info
				isGamepadConnected: () => ctrl.gamepadController?.isGamepadConnected() || false,
				gamepadController: ctrl.gamepadController
			};

			onReady(window.nesEmulator);
		}, onError);
	});

	onDestroy(() => {
		disableKeyboardControls();
		if (controller) {
			controller.destroy();
		}
	});

	function enableKeyboardControls() {
		if (keyboardEnabled) return;
		keyboardEnabled = true;
		console.log('⌨️ Keyboard enabled');
		document.addEventListener('keydown', handleKeyDown);
		document.addEventListener('keyup', handleKeyUp);
	}

	function disableKeyboardControls() {
		if (!keyboardEnabled) return;
		keyboardEnabled = false;
		console.log('⌨️ Keyboard disabled');
		document.removeEventListener('keydown', handleKeyDown);
		document.removeEventListener('keyup', handleKeyUp);
	}

	function handleKeyDown(event) {
		if (!controller || !controller.isLoaded || !controller.isRunning) return;

		const BUTTON_A = 0;
		const BUTTON_B = 1;
		const BUTTON_START = 3;
		const BUTTON_UP = 4;
		const BUTTON_DOWN = 5;
		const BUTTON_LEFT = 6;
		const BUTTON_RIGHT = 7;

		switch (event.key) {
			case 'ArrowUp':
				controller.buttonDown(1, BUTTON_UP);
				event.preventDefault();
				break;
			case 'ArrowDown':
				controller.buttonDown(1, BUTTON_DOWN);
				event.preventDefault();
				break;
			case 'ArrowLeft':
				controller.buttonDown(1, BUTTON_LEFT);
				event.preventDefault();
				break;
			case 'ArrowRight':
				controller.buttonDown(1, BUTTON_RIGHT);
				event.preventDefault();
				break;
			case 'z':
			case 'Z':
				controller.buttonDown(1, BUTTON_A);
				event.preventDefault();
				break;
			case 'x':
			case 'X':
				controller.buttonDown(1, BUTTON_B);
				event.preventDefault();
				break;
			case 'Enter':
				controller.buttonDown(1, BUTTON_START);
				event.preventDefault();
				break;
		}
	}

	function handleKeyUp(event) {
		if (!controller || !controller.isLoaded) return;

		const BUTTON_A = 0;
		const BUTTON_B = 1;
		const BUTTON_START = 3;
		const BUTTON_UP = 4;
		const BUTTON_DOWN = 5;
		const BUTTON_LEFT = 6;
		const BUTTON_RIGHT = 7;

		switch (event.key) {
			case 'ArrowUp':
				controller.buttonUp(1, BUTTON_UP);
				break;
			case 'ArrowDown':
				controller.buttonUp(1, BUTTON_DOWN);
				break;
			case 'ArrowLeft':
				controller.buttonUp(1, BUTTON_LEFT);
				break;
			case 'ArrowRight':
				controller.buttonUp(1, BUTTON_RIGHT);
				break;
			case 'z':
			case 'Z':
				controller.buttonUp(1, BUTTON_A);
				break;
			case 'x':
			case 'X':
				controller.buttonUp(1, BUTTON_B);
				break;
			case 'Enter':
				controller.buttonUp(1, BUTTON_START);
				break;
		}
	}
</script>

<div class="nes-emulator-container">
	<canvas
		bind:this={canvasElement}
		width={width}
		height={height}
		style="width: {width * scale}px; height: {height * scale}px; image-rendering: pixelated; image-rendering: crisp-edges;"
		class="border-4 border-gray-800 rounded bg-black"
	></canvas>
</div>

<style>
	.nes-emulator-container {
		display: flex;
		justify-content: center;
		align-items: center;
	}

	canvas {
		image-rendering: -moz-crisp-edges;
		image-rendering: -webkit-crisp-edges;
	}
</style>
