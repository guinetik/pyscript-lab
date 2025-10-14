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

        # Debug: Check actual network layer sizes
        console.log(f"   Weight shapes: {[w.shape for w in self.network.weights]}")
        console.log(f"   Bias shapes: {[b.shape for b in self.network.biases]}")

    def forward(self, state: np.ndarray) -> np.ndarray:
        """
        Forward pass through network.

        Args:
            state: Input state vector

        Returns:
            np.ndarray: Network output activations (1D array)
        """
        # Debug network architecture (log once)
        if not hasattr(self, '_logged_arch'):
            console.log(f"🔍 Network layer shapes:")
            for i, (w, b) in enumerate(zip(self.network.weights, self.network.biases)):
                console.log(f"   Layer {i}: weights={w.shape}, biases={b.shape}")
            self._logged_arch = True

        output = self.network.forward(state)

        # Debug raw output shape
        if not hasattr(self, '_logged_output'):
            console.log(f"🔍 Raw network output shape: {output.shape}, expected: ({self.output_size},)")
            self._logged_output = True

        # Ensure output is 1D with shape (output_size,)
        flattened = output.flatten()

        # If wrong size, slice to correct size
        if len(flattened) != self.output_size:
            console.error(f"⚠️ Output size mismatch! Got {len(flattened)}, expected {self.output_size}. Taking first {self.output_size} values.")
            return flattened[:self.output_size]

        return flattened

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

    def randomize_with_bias(self):
        """
        Randomize weights with behavioral priors for Mario.

        Biases the output layer to encourage:
        - RIGHT button (index 3) = move right (good!)
        - A button (index 4) = jump (good!)
        - Discourage LEFT button (index 2) = move left (bad!)

        Output button order: [UP, DOWN, LEFT, RIGHT, A, B]
        """
        console.log("🎯 Initializing with behavioral priors (RIGHT + JUMP bias)")

        # Randomize all layers normally first
        for i in range(len(self.network.weights)):
            self.network.weights[i] = np.random.randn(*self.network.weights[i].shape) * 0.5
            self.network.biases[i] = np.random.randn(*self.network.biases[i].shape) * 0.5

        # Bias the OUTPUT layer (last layer)
        output_layer_idx = len(self.network.biases) - 1
        output_size = self.network.biases[output_layer_idx].shape[0]

        console.log(f"   Output layer size: {output_size}")

        # Ensure we have 6 outputs
        if output_size != 6:
            console.error(f"❌ Expected 6 outputs, got {output_size}")
            return

        # Bias output neurons to prefer certain buttons
        # Output order: [UP, DOWN, LEFT, RIGHT, A, B]
        # Using VERY strong biases to override random input weights
        button_biases = np.array([
            -3.0,  # UP - strongly discourage
            -3.0,  # DOWN - strongly discourage (crouching is rarely useful)
            -5.0,  # LEFT - VERY strongly discourage (moving backward is bad)
            5.0,   # RIGHT - VERY strongly encourage (this is the goal!)
            2.5,   # A (jump) - strongly encourage (needed to clear obstacles)
            1.5    # B (run) - encourage (running is good)
        ], dtype=np.float32)

        # Set the output layer biases
        self.network.biases[output_layer_idx] = button_biases

        console.log("✅ Behavioral priors applied: RIGHT=+5.0, A(jump)=+2.5, B(run)=+1.5, LEFT=-5.0")


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

