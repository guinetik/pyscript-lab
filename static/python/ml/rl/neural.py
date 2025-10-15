"""
Simple Neural Network for Mario
Simplified feedforward network with no training (just forward pass)
"""
import numpy as np
from typing import List, Callable


class NeuralNetwork:
    """
    Simple feedforward neural network.
    Takes game state as input, outputs button presses.
    """

    def __init__(self, layer_sizes: List[int], seed: int = None):
        """
        Initialize neural network.

        Args:
            layer_sizes: List of layer sizes [input, hidden1, hidden2, ..., output]
            seed: Random seed for reproducibility
        """
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes)

        # Set random seed
        if seed is not None:
            np.random.seed(seed)

        # Initialize weights and biases with random values
        self.weights = []
        self.biases = []

        for i in range(len(layer_sizes) - 1):
            # Xavier initialization for better starting weights
            w = np.random.randn(layer_sizes[i+1], layer_sizes[i]) * np.sqrt(2.0 / layer_sizes[i])
            # Bias should be 1D array, not 2D column vector
            b = np.zeros(layer_sizes[i+1])

            self.weights.append(w)
            self.biases.append(b)

    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def forward(self, x: np.ndarray, capture_activations: bool = False) -> np.ndarray:
        """
        Forward pass through the network.

        Args:
            x: Input array (flattened game state)
            capture_activations: If True, store layer activations for visualization

        Returns:
            Output array (button probabilities) - 1D array
        """
        # Ensure input is 1D
        x = x.flatten()

        activation = x

        # Optional: capture activations for visualization
        if capture_activations:
            self.layer_activations = [activation.copy()]  # Store input layer

        # Feed through hidden layers with ReLU
        for i in range(len(self.weights) - 1):
            z = np.dot(self.weights[i], activation) + self.biases[i]
            activation = self.relu(z)

            if capture_activations:
                self.layer_activations.append(activation.copy())

        # Output layer with sigmoid (for button probabilities)
        z = np.dot(self.weights[-1], activation) + self.biases[-1]
        output = self.sigmoid(z)

        if capture_activations:
            self.layer_activations.append(output.copy())

        # Return 1D array
        return output.flatten()

    def set_weights(self, weights: List[np.ndarray], biases: List[np.ndarray]):
        """
        Set network weights and biases.
        Useful for loading pre-trained weights.
        """
        self.weights = weights
        self.biases = biases

    def get_weights(self) -> tuple:
        """Get current weights and biases."""
        return self.weights, self.biases

    def get_visualization_data(self) -> dict:
        """
        Get network visualization data.
        Returns layer sizes, activations (if captured), and weight statistics.

        Returns:
            dict: {
                'layer_sizes': [120, 32, 6],
                'activations': [[...], [...], [...]],  # If captured
                'weight_stats': [{min, max, mean}, ...],
                'num_params': total parameter count
            }
        """
        import json

        # Calculate total parameters
        num_params = sum(w.size + b.size for w, b in zip(self.weights, self.biases))

        # Weight statistics for each layer
        weight_stats = []
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            stats = {
                'layer': int(i),
                'weights': {
                    'min': float(w.min()),
                    'max': float(w.max()),
                    'mean': float(w.mean()),
                    'std': float(w.std())
                },
                'biases': {
                    'min': float(b.min()),
                    'max': float(b.max()),
                    'mean': float(b.mean()),
                    'std': float(b.std())
                }
            }
            weight_stats.append(stats)

        # Build data structure with pure Python types (no numpy)
        data = {
            'layer_sizes': [int(s) for s in self.layer_sizes],  # Convert to plain Python ints
            'num_params': int(num_params),
            'weight_stats': weight_stats
        }

        # Include activations if they were captured
        if hasattr(self, 'layer_activations'):
            # Convert numpy arrays to lists for JS
            activations_list = []
            for act in self.layer_activations:
                activations_list.append({
                    'values': [float(v) for v in act],  # Explicit conversion to Python floats
                    'min': float(act.min()),
                    'max': float(act.max()),
                    'mean': float(act.mean()),
                    'active_count': int(np.sum(act > 0.1))  # Neurons with significant activation
                })
            data['activations'] = activations_list

        # Convert to JSON and back to ensure pure Python types
        # This removes any Pyodide proxy objects
        json_str = json.dumps(data)
        return json.loads(json_str)

    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.5):
        """
        Mutate weights randomly (for evolution/exploration).

        Args:
            mutation_rate: Probability of mutating each weight
            mutation_scale: Scale of random mutations
        """
        for i in range(len(self.weights)):
            # Mutate weights
            mask = np.random.random(self.weights[i].shape) < mutation_rate
            self.weights[i] += mask * np.random.randn(*self.weights[i].shape) * mutation_scale

            # Mutate biases - but reduce mutation on OUTPUT layer to preserve behavioral priors
            is_output_layer = (i == len(self.weights) - 1)

            if is_output_layer:
                # Output layer biases (behavioral priors) - mutate less aggressively
                bias_mutation_scale = mutation_scale * 0.3  # Only 30% of normal mutation
                bias_mutation_rate = mutation_rate * 0.5    # Half the mutation rate
            else:
                # Hidden layer biases - mutate normally
                bias_mutation_scale = mutation_scale
                bias_mutation_rate = mutation_rate

            mask = np.random.random(self.biases[i].shape) < bias_mutation_rate
            self.biases[i] += mask * np.random.randn(*self.biases[i].shape) * bias_mutation_scale


# Export to global scope for other scripts to use
import builtins
builtins.NeuralNetwork = NeuralNetwork
