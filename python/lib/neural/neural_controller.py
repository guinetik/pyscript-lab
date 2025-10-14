"""
Neural Controller - Abstract interface for neural network controllers

Provides a clean abstraction for different neural network implementations.
Agents can swap out different NN architectures without changing game logic.

Author: Guinetik
"""

from abc import ABC, abstractmethod
import numpy as np
from js import console


class NeuralController(ABC):
    """
    Abstract base class for neural network controllers.
    Defines the interface all neural controllers must implement.
    """

    @abstractmethod
    def forward(self, state: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network.

        Args:
            state: Input state vector

        Returns:
            np.ndarray: Output vector (typically button activations)
        """
        pass

    @abstractmethod
    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.5):
        """
        Mutate the network weights for evolutionary learning.

        Args:
            mutation_rate: Probability of mutating each weight
            mutation_scale: Scale of random mutations
        """
        pass

    @abstractmethod
    def get_weights(self) -> dict:
        """
        Get network weights for saving.

        Returns:
            dict: Dictionary containing weights and biases
        """
        pass

    @abstractmethod
    def set_weights(self, weights: list, biases: list):
        """
        Set network weights from saved data.

        Args:
            weights: List of weight matrices
            biases: List of bias vectors
        """
        pass

    @abstractmethod
    def randomize(self):
        """Randomize all network weights."""
        pass


class SimpleNeuralController(NeuralController):
    """
    Simple feedforward neural network controller.
    Uses the NeuralNetwork class from neural.py.
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int, seed=None):
        """
        Initialize simple neural controller.

        Args:
            input_size: Number of input neurons
            hidden_size: Number of hidden neurons
            output_size: Number of output neurons
            seed: Random seed (None for random initialization)
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Get NeuralNetwork class from builtins (loaded by neural.py)
        import builtins
        NeuralNetwork = builtins.NeuralNetwork
        
        self.network = NeuralNetwork(
            [input_size, hidden_size, output_size], 
            seed=seed
        )

        console.log(f"🧠 SimpleNeuralController initialized")
        console.log(f"   Architecture: {input_size} → {hidden_size} → {output_size}")

    def forward(self, state: np.ndarray) -> np.ndarray:
        """
        Forward pass through network.

        Args:
            state: Input state vector

        Returns:
            np.ndarray: Network output activations
        """
        return self.network.forward(state)

    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.5):
        """
        Mutate network weights.

        Args:
            mutation_rate: Probability of mutating each weight
            mutation_scale: Scale of mutations
        """
        self.network.mutate(
            mutation_rate=mutation_rate,
            mutation_scale=mutation_scale
        )

    def get_weights(self) -> dict:
        """
        Get network weights.

        Returns:
            dict: {'weights': [...], 'biases': [...]}
        """
        return {
            'weights': self.network.weights,
            'biases': self.network.biases
        }

    def set_weights(self, weights: list, biases: list):
        """
        Set network weights.

        Args:
            weights: List of weight matrices
            biases: List of bias vectors
        """
        self.network.set_weights(weights, biases)

    def randomize(self):
        """Randomize all network weights."""
        for i in range(len(self.network.weights)):
            self.network.weights[i] = np.random.randn(*self.network.weights[i].shape) * 0.5
            self.network.biases[i] = np.random.randn(*self.network.biases[i].shape) * 0.5


class ActionDecoder:
    """
    Converts neural network outputs into button actions.
    Handles thresholding and action interpretation.
    """

    def __init__(self, use_variable_threshold: bool = True):
        """
        Initialize action decoder.

        Args:
            use_variable_threshold: Use random thresholds for more variety
        """
        self.use_variable_threshold = use_variable_threshold

    def decode(self, output: np.ndarray) -> np.ndarray:
        """
        Convert network output to button presses.

        Args:
            output: Neural network output (typically sigmoid activations)

        Returns:
            np.ndarray: Binary button states [0 or 1 for each button]
        """
        if self.use_variable_threshold:
            # Variable threshold adds exploration variety
            thresholds = np.random.uniform(0.4, 0.6, size=output.shape)
            buttons = (output > thresholds).astype(int).flatten()
        else:
            # Fixed threshold (more deterministic)
            buttons = (output > 0.5).astype(int).flatten()

        return buttons

    def decode_deterministic(self, output: np.ndarray) -> np.ndarray:
        """
        Deterministic decoding (always use 0.5 threshold).

        Args:
            output: Neural network output

        Returns:
            np.ndarray: Binary button states
        """
        return (output > 0.5).astype(int).flatten()

