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
            b = np.zeros((layer_sizes[i+1], 1))

            self.weights.append(w)
            self.biases.append(b)

    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)

    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network.

        Args:
            x: Input array (flattened game state)

        Returns:
            Output array (button probabilities)
        """
        # Ensure input is column vector
        if x.ndim == 1:
            x = x.reshape(-1, 1)

        activation = x

        # Feed through hidden layers with ReLU
        for i in range(len(self.weights) - 1):
            z = np.dot(self.weights[i], activation) + self.biases[i]
            activation = self.relu(z)

        # Output layer with sigmoid (for button probabilities)
        z = np.dot(self.weights[-1], activation) + self.biases[-1]
        output = self.sigmoid(z)

        return output

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

            # Mutate biases
            mask = np.random.random(self.biases[i].shape) < mutation_rate
            self.biases[i] += mask * np.random.randn(*self.biases[i].shape) * mutation_scale


# Export to global scope for other scripts to use
import builtins
builtins.NeuralNetwork = NeuralNetwork
