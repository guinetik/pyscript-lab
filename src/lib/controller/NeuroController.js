import { PyScriptManager } from '$lib/PyScriptManager.js';
import { NES, Button } from '$lib/nes/NES.js';
import { Agent } from '$lib/nes/Agent.js';
import { initHeadlessNESFactory } from '$lib/nes/HeadlessNES.js';
import telemetry from '$lib/Telemetry.js';

export class NeuroController {
    constructor() {
        this.nes = null;
        this.agent = null;
        this.canvas = null;
        this.pyScriptManager = new PyScriptManager();

        // State
        this.romBinaryString = null;
        this.initialStateJSON = null;
        this.originalNesFrame = null;
        this.pressedButtons = new Set();
        this.trainedWeights = null;

        // Callbacks
        this.callbacks = {
            onProgress: null, // (gen, fit, dist)
            onBreeding: null, // (breedingData)
            onState: null,    // (state)
            onStats: null,    // (stats)
            onViz: null,      // (vizData)
            onComplete: null, // (success)
            onStatus: null    // (msg)
        };

        this.keyMap = {
            'ArrowUp': Button.UP,
            'ArrowDown': Button.DOWN,
            'ArrowLeft': Button.LEFT,
            'ArrowRight': Button.RIGHT,
            'KeyZ': Button.A,      // Jump
            'KeyX': Button.B,      // Run
            'Enter': Button.START,
            'ShiftRight': Button.SELECT
        };

        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
    }

    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }

    async initialize(canvas) {
        this.canvas = canvas;

        // Initialize HeadlessNES factory for Python to use
        initHeadlessNESFactory();

        // Initialize NES
        this.nes = new NES(canvas);
        await this.nes.init();

        // Load ROM
        const romResponse = await fetch('/data/package.nes');
        const romBuffer = await romResponse.arrayBuffer();
        this.romBinaryString = String.fromCharCode.apply(null, new Uint8Array(romBuffer));
        this.nes.nes.loadROM(this.romBinaryString);

        // Load state
        const stateResponse = await fetch('/data/nes_state.json');
        const stateObj = await stateResponse.json();
        this.initialStateJSON = JSON.stringify(stateObj);

        // Load initial state
        this.nes.nes.fromJSON(JSON.parse(this.initialStateJSON));

        // Store original frame function
        this.originalNesFrame = this.nes.nes.frame.bind(this.nes.nes);

        // Load Python trainer script
        if (!window.initTrainer) {
             // We need to load the python files.
             // trainer.py imports agent.py, utils.py.
             // PyScriptManager can load a script.
             // We'll load a script that imports trainer and calls setup_js_bridge()
             // Use runCode for inline code, not runScript
             this.pyScriptManager.runCode(
                `
from ml.neuro.trainer import setup_js_bridge
setup_js_bridge()
                `,
                'body'
             );

             // Wait for it to be ready
             let attempts = 0;
             while (!window.initTrainer && attempts < 20) {
                 await new Promise(r => setTimeout(r, 100));
                 attempts++;
             }
        }

        telemetry.log('visual', 'NeuroController initialized');
    }

    resetNES() {
        if (!this.nes || !this.initialStateJSON) return;

        this.nes.stop();

        // Clear buttons
        for (let i = 0; i < 8; i++) {
            this.nes.nes.buttonUp(1, i);
        }
        this.pressedButtons.clear();

        // Restore original frame
        if (this.originalNesFrame) {
            this.nes.nes.frame = this.originalNesFrame;
        }

        // Restore state
        this.nes.nes.fromJSON(JSON.parse(this.initialStateJSON));

        // Capture state after fromJSON
        const mem = this.nes.nes.cpu.mem;
        const afterFromJSON = {
            x: mem[0x06D] * 256 + mem[0x086],
            yOff: mem[0x3B8],
            xOff: mem[0x3AD]
        };

        // Run settle frames for game to properly start and Mario to spawn
        // Must match HeadlessNES (100 frames) for consistent behavior
        const SETTLE_FRAMES = 100;
        for (let i = 0; i < SETTLE_FRAMES; i++) {
            this.nes.nes.frame();
        }

        // Capture state after settle frames
        const afterSettle = {
            x: mem[0x06D] * 256 + mem[0x086],
            yOff: mem[0x3B8],
            xOff: mem[0x3AD],
            settleFrames: SETTLE_FRAMES
        };

        // Log reset with both states for comparison
        telemetry.logReset('visual', afterFromJSON, afterSettle);

        // Clear buttons again
        for (let i = 0; i < 8; i++) {
            this.nes.nes.buttonUp(1, i);
        }
    }

    async startPlay() {
        this.resetNES();
        this.enableKeyboard();
        this.nes.start();
        if (this.callbacks.onStatus) this.callbacks.onStatus('Manual Play - Use Arrow Keys + Z (Jump) + X (Run)');
    }

    stop() {
        if (window.stopTraining) {
            window.stopTraining();
        }
        this.resetNES();
        this.disableKeyboard();
        if (this.callbacks.onState) this.callbacks.onState('IDLE');
        if (this.callbacks.onStatus) this.callbacks.onStatus('Stopped');
    }

    toggleMute(muted) {
        if (this.nes) {
            this.nes.setMuted(muted);
        }
    }

    // === AI / Training Logic ===

    /**
     * Start training with specified evolution mode.
     * @param {string} mode - Evolution mode: 'simple', 'sbx', 'uniform', or 'optimize'
     */
    async startTraining(mode = 'simple') {
        this.resetNES();

        // Store ROM and state on window for Python
        window._trainingRomData = this.romBinaryString;
        window._trainingInitialState = JSON.parse(this.initialStateJSON);

        // For 'optimize' mode, load reference weights for Python to use
        if (mode === 'optimize') {
            if (this.callbacks.onStatus) this.callbacks.onStatus('Loading reference weights...');
            const [W1, b1, W2, b2] = await Promise.all([
                fetch('/data/reference_weights/W1.json').then(r => r.json()),
                fetch('/data/reference_weights/b1.json').then(r => r.json()),
                fetch('/data/reference_weights/W2.json').then(r => r.json()),
                fetch('/data/reference_weights/b2.json').then(r => r.json())
            ]);
            window._referenceWeights = { W1, b1, W2, b2 };
            telemetry.log('trainer', 'Reference weights loaded for optimize mode');
        } else {
            window._referenceWeights = null;
        }

        if (!window.initTrainer) {
            if (this.callbacks.onStatus) this.callbacks.onStatus('Error: Python trainer not loaded');
            return;
        }

        const success = window.initTrainer(
            (gen, fit, dist) => {
                if (this.callbacks.onProgress) this.callbacks.onProgress(gen, fit, dist);
                telemetry.log('trainer', 'Progress', { generation: gen, bestFitness: fit, bestDistance: dist });
            },
            (weightsJson) => this.onTrainerForeground(weightsJson),
            (newState) => {
                if (this.callbacks.onState) this.callbacks.onState(newState);
                telemetry.setPhase(newState.toLowerCase());

                if (newState === 'IDLE') {
                    this.nes.stop();
                } else if (newState === 'BACKGROUND') {
                    this.nes.stop();
                }
            },
            (success) => {
                if (this.callbacks.onComplete) this.callbacks.onComplete(success);
                this.resetNES();
                telemetry.log('trainer', 'Training complete', { success });
            },
            mode,  // Pass evolution mode to Python
            (breedingJson) => this.onTrainerBreeding(breedingJson)
        );

        if (success) {
            window.startTraining();
            if (this.callbacks.onStatus) {
                const modeLabels = {
                    simple: 'Simple (Elite + Mutation)',
                    sbx: 'SBX Breeding',
                    uniform: 'Uniform Breeding',
                    optimize: 'Optimize (Reference Seed)'
                };
                this.callbacks.onStatus(`Training started [${modeLabels[mode] || mode}]`);
            }
            telemetry.log('trainer', 'Training started', { mode });
        } else {
            if (this.callbacks.onStatus) this.callbacks.onStatus('Error: Failed to initialize trainer');
        }
    }

    async onTrainerForeground(weightsJson) {
        this.trainedWeights = JSON.parse(weightsJson);
        if (this.callbacks.onState) this.callbacks.onState('FOREGROUND');
        if (this.callbacks.onStatus) this.callbacks.onStatus('Showing best agent...');

        telemetry.setPhase('foreground');

        const didWin = await this.runForegroundDisplay();

        // Dump telemetry at end of foreground session
        telemetry.dump('Foreground Session');

        // Wait a frame
        await new Promise(resolve => requestAnimationFrame(resolve));

        // Pass win status to trainer so it can skip remaining foreground sessions
        window.foregroundComplete?.(didWin);
    }

    /**
     * Forward breeding lineage payloads from Python to the UI.
     * @param {string} breedingJson - JSON string containing the latest breeding events.
     */
    onTrainerBreeding(breedingJson) {
        const breedingData = JSON.parse(breedingJson);
        if (this.callbacks.onBreeding) {
            this.callbacks.onBreeding(breedingData);
        }
        telemetry.log('trainer', 'Breeding', breedingData);
    }

    runForegroundDisplay() {
        return new Promise((resolve) => {
            if (!this.trainedWeights) {
                resolve(false);  // No win
                return;
            }

            this.resetNES();

            this.agent = new Agent();
            this.agent.W1 = this.trainedWeights.W1;
            this.agent.b1 = this.trainedWeights.b1;
            this.agent.W2 = this.trainedWeights.W2;
            this.agent.b2 = this.trainedWeights.b2;
            this.agent.loaded = true;
            this.agent.reset();

            let frameCount = 0;
            let farthestX = 0;
            let stuckFrames = 0;
            let isDone = false;
            let winDetected = false;  // Separate flag to keep playing after win
            const STUCK_THRESHOLD = 120;

            if (this.callbacks.onStatus) this.callbacks.onStatus('Best agent playing...');

            this.nes.nes.frame = () => {
                if (isDone) return;

                // If win detected, keep running frames but don't check for end conditions
                if (winDetected) {
                    this.originalNesFrame();
                    return;
                }

                // CRITICAL: Get buttons BEFORE running frame (matches Python trainer)
                // This ensures agent reacts to current state, not previous state
                const buttons = this.agent.update(this.nes.nes);

                // Match HeadlessNES button handling exactly: clear all, then set active
                for (let i = 0; i < 8; i++) {
                    this.nes.nes.buttonUp(1, i);
                }
                for (const btn of buttons) {
                    this.nes.nes.buttonDown(1, btn);
                }

                // NOW run the frame with buttons already set
                this.originalNesFrame();
                frameCount++;

                // Log key frames for telemetry comparison
                if ([0, 1, 2, 3, 4, 60, 120, 180].includes(frameCount)) {
                    const ram = this.nes.nes.cpu.mem;
                    const x = ram[0x06D] * 256 + ram[0x086];
                    const yOff = ram[0x3B8];
                    const xOff = ram[0x3AD];
                    const row = Math.floor((yOff + 16) / 16);
                    const col = Math.floor((xOff + 12) / 16);
                    const vision = this.agent.lastInputs ? this.agent.lastInputs.slice(0, 70) : [];
                    const solids = vision.filter(v => v === 1).length;

                    telemetry.logFrame('visual', frameCount, {
                        x, yOff, xOff, row, col, solids,
                        buttons: buttons.slice()
                    });
                }

                // Stats
                const stats = this.agent.getStats(this.nes.nes);
                if (this.callbacks.onStats) this.callbacks.onStats(stats);

                // Viz
                if (frameCount % 10 === 0 && this.agent.lastInputs && this.agent.lastOutputs) {
                    if (this.callbacks.onViz) {
                        this.callbacks.onViz({
                            layer_sizes: [80, 9, 6],
                            activations: [
                                { values: this.agent.lastInputs, active_count: this.agent.lastInputs.filter(v => v !== 0).length },
                                { values: Array(9).fill(0.5), active_count: 5 },
                                { values: this.agent.lastOutputs, active_count: this.agent.lastOutputs.filter(v => v > 0.5).length }
                            ],
                            num_params: 80 * 9 + 9 + 9 * 6 + 6
                        });
                    }
                }

                // Progress check
                const ram = this.nes.nes.cpu.mem;
                const x = ram[0x06D] * 256 + ram[0x086];

                if (x > farthestX) {
                    farthestX = x;
                    stuckFrames = 0;
                } else {
                    stuckFrames++;
                }

                const playerState = ram[0x000E];
                const isDead = playerState === 0x06 || playerState === 0x0B;
                const isStuck = stuckFrames > STUCK_THRESHOLD;
                // Win requires flag state AND being past finish line (prevents stale state bugs)
                const didWin = ram[0x001D] === 3 && x > 3000;

                if (this.callbacks.onStatus) {
                    if (didWin) {
                        this.callbacks.onStatus(`🎉 LEVEL COMPLETE! X=${x} | Frames=${frameCount}`);
                    } else {
                        this.callbacks.onStatus(`Playing: X=${x} | Frames=${frameCount}` + (isDead ? ' DIED!' : isStuck ? ' STUCK!' : ''));
                    }
                }

                if (didWin && !winDetected) {
                    // Win! Keep playing for 10 seconds to celebrate, then continue
                    winDetected = true;
                    telemetry.log('visual', 'Level complete!', { x, frames: frameCount });
                    setTimeout(() => {
                        isDone = true;
                        this.resetNES();
                        resolve(true);  // Won!
                    }, 10000);
                } else if (isDead || isStuck) {
                    isDone = true;
                    telemetry.log('visual', isDead ? 'Mario died' : 'Mario stuck', { x, frames: frameCount, farthestX });
                    setTimeout(() => {
                        this.resetNES();
                        resolve(false);  // Did not win
                    }, 1000);
                }
            };

            this.nes.start();
        });
    }

    async startAI() {
        this.resetNES();

        this.agent = new Agent();
        await this.agent.loadWeights('/data/reference_weights');

        let aiFrameCount = 0;
        let aiWinDetected = false;

        telemetry.setPhase('ai-play');
        telemetry.log('visual', 'AI playback started (reference weights)');

        this.nes.nes.frame = () => {
            // Get buttons BEFORE running frame (matches Python trainer timing)
            const buttons = this.agent.update(this.nes.nes);

            // Match HeadlessNES button handling exactly: clear all, then set active
            for (let i = 0; i < 8; i++) {
                this.nes.nes.buttonUp(1, i);
            }
            for (const btn of buttons) {
                this.nes.nes.buttonDown(1, btn);
            }

            // NOW run the frame
            this.originalNesFrame();
            aiFrameCount++;

            // Log key frames
            if ([0, 1, 2, 3, 4, 60, 120, 180].includes(aiFrameCount)) {
                const ram = this.nes.nes.cpu.mem;
                const x = ram[0x06D] * 256 + ram[0x086];
                const yOff = ram[0x3B8];
                const xOff = ram[0x3AD];
                const row = Math.floor((yOff + 16) / 16);
                const col = Math.floor((xOff + 12) / 16);

                telemetry.logFrame('visual', aiFrameCount, {
                    x, yOff, xOff, row, col,
                    buttons: buttons.slice()
                });
            }

            const stats = this.agent.getStats(this.nes.nes);
            if (this.callbacks.onStats) this.callbacks.onStats(stats);

            if (aiFrameCount % 10 === 0 && this.agent.lastInputs && this.agent.lastOutputs) {
                if (this.callbacks.onViz) {
                    this.callbacks.onViz({
                        layer_sizes: [80, 9, 6],
                        activations: [
                            { values: this.agent.lastInputs, active_count: this.agent.lastInputs.filter(v => v !== 0).length },
                            { values: Array(9).fill(0.5), active_count: 5 },
                            { values: this.agent.lastOutputs, active_count: this.agent.lastOutputs.filter(v => v > 0.5).length }
                        ],
                        button_labels: ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A', 'B']
                    });
                }
            }

            if (!aiWinDetected && this.agent.didWin(this.nes.nes.cpu.mem)) {
                aiWinDetected = true;
                telemetry.log('visual', 'AI won!', { frames: aiFrameCount });
                if (this.callbacks.onStatus) this.callbacks.onStatus('Level Complete! Restarting in 5...');
                setTimeout(() => {
                    telemetry.dump('AI Playback');
                    this.startAI();
                }, 5000);
            }
        };

        this.nes.start();
        if (this.callbacks.onStatus) this.callbacks.onStatus('AI Playing (Reference Weights)');
    }

    // Keyboard handling
    handleKeyDown(e) {
        const btn = this.keyMap[e.code];
        if (btn !== undefined && this.nes) {
            this.nes.nes.buttonDown(1, btn);
            e.preventDefault();
        }
    }

    handleKeyUp(e) {
        const btn = this.keyMap[e.code];
        if (btn !== undefined && this.nes) {
            this.nes.nes.buttonUp(1, btn);
            e.preventDefault();
        }
    }

    enableKeyboard() {
        window.addEventListener('keydown', this.handleKeyDown);
        window.addEventListener('keyup', this.handleKeyUp);
    }

    disableKeyboard() {
        window.removeEventListener('keydown', this.handleKeyDown);
        window.removeEventListener('keyup', this.handleKeyUp);
    }

    destroy() {
        this.stop();
        if (this.nes) {
            this.nes.destroy();
            this.nes = null;
        }
        if (this.pyScriptManager) {
            this.pyScriptManager.destroy();
        }
    }
}
