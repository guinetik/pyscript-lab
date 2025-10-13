/**
 * Svelte store for digit recognition state
 *
 * Manages the state of the digit recognition ML demo, providing reactive
 * updates when Python makes predictions or the model is retrained.
 *
 * @module digitRecognitionStore
 */

import { writable } from 'svelte/store';

/**
 * @typedef {Object} PredictionData
 * @property {number} prediction - Predicted digit (0-9)
 * @property {number} confidence - Confidence percentage (0-100)
 * @property {number[]} probabilities - Probability for each digit 0-9
 * @property {number[]} imageData - Flattened 8x8 array of pixel values
 * @property {number[][]} imageData2D - 8x8 array for visualization
 */

/**
 * @typedef {Object} ModelState
 * @property {number} accuracy - Model accuracy percentage (0-100)
 * @property {number} trainingExamples - Number of training examples
 */

/**
 * @typedef {Object} UIState
 * @property {'ready' | 'processing' | 'result' | 'error'} status
 * @property {string} message - Status or error message
 */

/**
 * Store for prediction results
 * @type {import('svelte/store').Writable<PredictionData | null>}
 */
export const predictionResult = writable(null);

/**
 * Store for model state (accuracy, training size)
 * @type {import('svelte/store').Writable<ModelState>}
 */
export const modelState = writable({
	accuracy: 0,
	trainingExamples: 0
});

/**
 * Store for UI state (ready, processing, error, etc.)
 * @type {import('svelte/store').Writable<UIState>}
 */
export const uiState = writable({
	status: 'ready',
	message: 'Draw a digit and click Predict'
});

/**
 * Store for training examples visualization
 * @type {import('svelte/store').Writable<any | null>}
 */
export const trainingExamples = writable(null);

/**
 * Reset all stores to initial state
 */
export function resetStores() {
	predictionResult.set(null);
	uiState.set({
		status: 'ready',
		message: 'Draw a digit and click Predict'
	});
}
