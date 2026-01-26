/**
 * GrokController - Manages the Grokking Neural Network training
 * 
 * Uses the main thread with asyncio yields for UI responsiveness,
 * matching the pattern used by the existing neuro example.
 * 
 * @module GrokController
 */

import { PyScriptManager } from '$lib/PyScriptManager.js';

/**
 * @typedef {Object} TrainingProgress
 * @property {number} epoch - Current epoch number
 * @property {number} train_acc - Training accuracy (0-1)
 * @property {number} test_acc - Test accuracy (0-1)
 * @property {boolean} grok_detected - Whether grokking has been detected
 * @property {number} grok_epoch - Epoch when grokking was detected (-1 if not)
 * @property {Object} activations - Network activations for visualization
 * @property {number[]} layer_sizes - Sizes of each layer
 */

/**
 * @typedef {Object} GrokCallbacks
 * @property {function(TrainingProgress): void} onProgress - Called after each training batch
 * @property {function(number): void} onGrokDetected - Called when grokking is detected
 * @property {function(string): void} onStatus - Called with status messages
 * @property {function(): void} onComplete - Called when training completes
 * @property {function(Object): void} onError - Called on error
 */

/**
 * Controller for the Grokking Neural Network.
 */
export class GrokController {
    constructor() {
        /** @type {PyScriptManager} */
        this.pyScriptManager = new PyScriptManager();
        
        /** @type {boolean} */
        this.initialized = false;
        
        /** @type {boolean} */
        this.training = false;
        
        /** @type {boolean} */
        this.grokDetected = false;
        
        /** @type {GrokCallbacks} */
        this.callbacks = {
            onProgress: null,
            onGrokDetected: null,
            onStatus: null,
            onComplete: null,
            onError: null
        };
        
        /** @type {Object} */
        // Original parameters that produce grokking
        this.config = {
            n_tokens: 67,       // Original value
            embed_size: 500,    // Original value  
            hidden_size: 64,    // Original value
            learning_rate: 0.01,
            weight_decay: 1.0,  // HIGH - key to grokking!
            train_fraction: 0.4
        };
        
        // Bind window callbacks
        this._setupWindowCallbacks();
    }
    
    /**
     * Set up window callbacks for Python to call.
     * @private
     */
    _setupWindowCallbacks() {
        // Progress callback - called by Python during training
        window.onGrokProgress = (data) => {
            // Convert Pyodide proxy to plain object
            const result = this._toPlainObject(data);
            
            if (this.callbacks.onProgress) {
                this.callbacks.onProgress(result);
            }
            
            // Check for grokking
            if (result.grok_detected && !this.grokDetected) {
                this.grokDetected = true;
                if (this.callbacks.onGrokDetected) {
                    this.callbacks.onGrokDetected(result.grok_epoch);
                }
            }
            
            // Update status
            const statusMsg = result.grok_detected 
                ? `GROKKED at epoch ${result.grok_epoch}! Epoch ${result.epoch}: Train ${(result.train_acc * 100).toFixed(1)}%, Test ${(result.test_acc * 100).toFixed(1)}%`
                : `Epoch ${result.epoch}: Train ${(result.train_acc * 100).toFixed(1)}%, Test ${(result.test_acc * 100).toFixed(1)}%`;
            this._status(statusMsg);
        };
        
        // Completion callback
        window.onGrokComplete = () => {
            this.training = false;
            if (this.callbacks.onComplete) {
                this.callbacks.onComplete();
            }
        };
        
        // Ready callback - called when Python module loads
        window.onGrokReady = () => {
            console.log('[GrokController] Python module ready');
            this.initialized = true;
        };
    }
    
    /**
     * Convert Pyodide proxy to plain JavaScript object.
     * @private
     */
    _toPlainObject(proxy) {
        if (!proxy) return proxy;
        
        try {
            // If it's a Pyodide proxy, convert it
            if (proxy.toJs) {
                const jsObj = proxy.toJs({ dict_converter: Object.fromEntries });
                proxy.destroy?.();
                return jsObj;
            }
            
            // Already a plain object - deep convert
            if (typeof proxy === 'object') {
                const result = {};
                for (const key of Object.keys(proxy)) {
                    const value = proxy[key];
                    if (value && value.toJs) {
                        result[key] = value.toJs();
                        value.destroy?.();
                    } else if (Array.isArray(value)) {
                        result[key] = [...value];
                    } else {
                        result[key] = value;
                    }
                }
                return result;
            }
            
            return proxy;
        } catch (e) {
            console.warn('[GrokController] Proxy conversion error:', e);
            return proxy;
        }
    }
    
    /**
     * Set callback functions.
     * @param {Partial<GrokCallbacks>} callbacks - Callback functions
     */
    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }
    
    /**
     * Initialize the neural network and data.
     * @returns {Promise<boolean>} True if initialization succeeded
     */
    async initialize() {
        try {
            this._status('Loading Python trainer...');
            
            // Load the trainer module if not already loaded
            if (!window.grok_initialize) {
                // Use runCode to import and setup the trainer
                this.pyScriptManager.runCode(`
from ml.grokking.trainer import (
    grok_initialize, 
    grok_train, 
    grok_stop, 
    grok_reset, 
    grok_predict
)
from js import window

# Expose to JavaScript
window.grok_initialize = grok_initialize
window.grok_train = grok_train
window.grok_stop = grok_stop
window.grok_reset = grok_reset
window.grok_predict = grok_predict

print("[GrokController] Functions exposed to JS")
window.onGrokReady()
`, 'body');
                
                // Wait for ready signal
                let attempts = 0;
                while (!this.initialized && attempts < 100) {
                    await this._sleep(100);
                    attempts++;
                }
                
                if (!this.initialized) {
                    throw new Error('Timeout waiting for Python trainer to load');
                }
            }
            
            this._status('Initializing neural network...');
            
            // Call Python initialization
            if (window.grok_initialize) {
                window.grok_initialize(this.config);
            }
            
            this._status('Ready to train');
            return true;
            
        } catch (error) {
            console.error('[GrokController] Initialization failed:', error);
            this._error(error);
            return false;
        }
    }
    
    /**
     * Start training.
     * @param {number} [maxEpochs=50000] - Maximum epochs to train
     */
    async startTraining(maxEpochs = 50000) {
        if (this.training) {
            this._status('Already training');
            return;
        }
        
        try {
            this.training = true;
            this.grokDetected = false;
            this._status('Training started...');
            
            // Call Python training function (async)
            if (window.grok_train) {
                await window.grok_train(maxEpochs);
            }
            
        } catch (error) {
            console.error('[GrokController] Training error:', error);
            this._error(error);
        }
        
        this.training = false;
    }
    
    /**
     * Stop training.
     */
    stop() {
        try {
            if (window.grok_stop) {
                window.grok_stop();
            }
            this.training = false;
            this._status('Training stopped');
        } catch (error) {
            console.error('[GrokController] Stop error:', error);
        }
    }
    
    /**
     * Reset the network.
     */
    reset() {
        try {
            if (window.grok_reset) {
                window.grok_reset();
            }
            this.grokDetected = false;
            this._status('Network reset');
        } catch (error) {
            console.error('[GrokController] Reset error:', error);
        }
    }
    
    /**
     * Get a prediction.
     * @param {number} a - First operand
     * @param {number} b - Second operand
     * @returns {Object|null} Prediction result
     */
    getPrediction(a, b) {
        try {
            if (window.grok_predict) {
                const result = window.grok_predict(a, b);
                return this._toPlainObject(result);
            }
            return null;
        } catch (error) {
            console.error('[GrokController] Prediction error:', error);
            return { error: error.message };
        }
    }
    
    /**
     * Cleanup resources.
     */
    destroy() {
        this.stop();
        this.pyScriptManager.destroy();
        window.onGrokProgress = null;
        window.onGrokComplete = null;
        window.onGrokReady = null;
        window.grok_initialize = null;
        window.grok_train = null;
        window.grok_stop = null;
        window.grok_reset = null;
        window.grok_predict = null;
    }
    
    // --- Private helpers ---
    
    _status(message) {
        if (this.callbacks.onStatus) {
            this.callbacks.onStatus(message);
        }
    }
    
    _error(error) {
        if (this.callbacks.onError) {
            this.callbacks.onError(error);
        }
    }
    
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
