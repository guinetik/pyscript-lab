import { PyScriptManager } from '$lib/PyScriptManager.js';
import { NES, Button } from '$lib/nes/NES.js';
import { Agent } from '$lib/nes/Agent.js';
import { initHeadlessNESFactory } from '$lib/nes/HeadlessNES.js';

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
        
        // Settle memory
        for (let i = 0; i < 10; i++) {
            this.nes.nes.frame();
        }
        
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

    async startTraining() {
        this.resetNES();
        
        // Store ROM and state on window for Python
        window._trainingRomData = this.romBinaryString;
        window._trainingInitialState = JSON.parse(this.initialStateJSON);
        
        if (!window.initTrainer) {
            if (this.callbacks.onStatus) this.callbacks.onStatus('Error: Python trainer not loaded');
            return;
        }
        
        const success = window.initTrainer(
            (gen, fit, dist) => {
                if (this.callbacks.onProgress) this.callbacks.onProgress(gen, fit, dist);
            },
            (weightsJson) => this.onTrainerForeground(weightsJson),
            (newState) => {
                if (this.callbacks.onState) this.callbacks.onState(newState);
                
                if (newState === 'IDLE') {
                    this.nes.stop();
                } else if (newState === 'BACKGROUND') {
                    this.nes.stop();
                }
            },
            (success) => {
                if (this.callbacks.onComplete) this.callbacks.onComplete(success);
                this.resetNES();
            }
        );
        
        if (success) {
            window.startTraining();
        } else {
            if (this.callbacks.onStatus) this.callbacks.onStatus('Error: Failed to initialize trainer');
        }
    }

    async onTrainerForeground(weightsJson) {
        this.trainedWeights = JSON.parse(weightsJson);
        if (this.callbacks.onState) this.callbacks.onState('FOREGROUND');
        if (this.callbacks.onStatus) this.callbacks.onStatus('Showing best agent...');
        
        await this.runForegroundDisplay();
        
        // Wait a frame
        await new Promise(resolve => requestAnimationFrame(resolve));
        
        window.foregroundComplete?.();
    }

    runForegroundDisplay() {
        return new Promise((resolve) => {
            if (!this.trainedWeights) {
                resolve();
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
            const STUCK_THRESHOLD = 120;
            
            if (this.callbacks.onStatus) this.callbacks.onStatus('Best agent playing...');
            
            this.nes.nes.frame = () => {
                if (isDone) return;
                
                this.originalNesFrame();
                frameCount++;
                
                const buttons = this.agent.update(this.nes.nes);
                const newPressed = new Set(buttons);
                
                for (const btn of this.pressedButtons) {
                    if (!newPressed.has(btn)) this.nes.nes.buttonUp(1, btn);
                }
                for (const btn of newPressed) {
                    if (!this.pressedButtons.has(btn)) this.nes.nes.buttonDown(1, btn);
                }
                this.pressedButtons = newPressed;
                
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
                
                if (this.callbacks.onStatus) {
                     this.callbacks.onStatus(`Playing: X=${x} | Frames=${frameCount}` + (isDead ? ' DIED!' : isStuck ? ' STUCK!' : ''));
                }
                
                if (isDead || isStuck) {
                    isDone = true;
                    setTimeout(() => {
                        this.resetNES();
                        resolve();
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
        
        this.nes.nes.frame = () => {
            this.originalNesFrame();
            aiFrameCount++;
            
            const buttons = this.agent.update(this.nes.nes);
            const newPressed = new Set(buttons);
            
            for (const btn of this.pressedButtons) {
                if (!newPressed.has(btn)) this.nes.nes.buttonUp(1, btn);
            }
            for (const btn of newPressed) {
                if (!this.pressedButtons.has(btn)) this.nes.nes.buttonDown(1, btn);
            }
            this.pressedButtons = newPressed;
            
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
                if (this.callbacks.onStatus) this.callbacks.onStatus('Level Complete! Restarting in 5...');
                setTimeout(() => {
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
