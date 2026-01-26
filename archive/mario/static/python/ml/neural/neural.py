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
        # MATCHING REFERENCE: uniform distribution in [-1, 1]
        self.weights = []
        self.biases = []

        for i in range(len(layer_sizes) - 1):
            # Reference uses uniform(-1, 1) initialization
            w = np.random.uniform(-1, 1, size=(layer_sizes[i+1], layer_sizes[i]))
            w = w.astype(np.float32)
            # Bias also uniform(-1, 1) like reference
            b = np.random.uniform(-1, 1, size=layer_sizes[i+1])
            b = b.astype(np.float32)

            # Output layer bias: favor RIGHT, JUMP, RUN for forward progress
            # For 6-button [UP, DOWN, LEFT, RIGHT, A, B] - matching reference
            is_output_layer = (i == len(layer_sizes) - 2)
            if is_output_layer and len(b) == 6:
                b[0] = -1.0  # UP - discourage
                b[1] = -1.0  # DOWN - discourage
                b[2] = -2.0  # LEFT - very strongly discourage
                b[3] = 2.0   # RIGHT - very strongly encourage
                b[4] = 1.5   # A (JUMP) - strongly encourage
                b[5] = 1.0   # B (RUN) - encourage
                print(f"🎮 Output biases (6-btn): UP={b[0]:.1f}, DOWN={b[1]:.1f}, LEFT={b[2]:.1f}, RIGHT={b[3]:.1f}, JUMP={b[4]:.1f}, RUN={b[5]:.1f}")

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
        Set network weights and biases (makes deep copies to avoid reference issues).
        Useful for loading pre-trained weights.
        """
        self.weights = [w.copy() for w in weights]
        self.biases = [b.copy() for b in biases]

    def get_weights(self) -> tuple:
        """Get current weights and biases (deep copies for safe saving)."""
        return [w.copy() for w in self.weights], [b.copy() for b in self.biases]

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

    def mutate(self, mutation_rate: float = 0.05, mutation_scale: float = 0.2):
        """
        Mutate weights randomly (for evolution/exploration).
        MATCHING REFERENCE: Gaussian mutation with clipping to [-1, 1].

        Reference code:
            mutation_array = np.random.random(chromosome.shape) < prob_mutation
            gaussian_mutation = np.random.normal(size=chromosome.shape)
            if scale: gaussian_mutation[mutation_array] *= scale
            chromosome[mutation_array] += gaussian_mutation[mutation_array]
            np.clip(chromosome, -1, 1, out=chromosome)

        Args:
            mutation_rate: Probability of mutating each weight (default: 0.05)
            mutation_scale: Scale of random mutations (default: 0.2)
        """
        for i in range(len(self.weights)):
            # Mutate weights - matching reference exactly
            mutation_mask = np.random.random(self.weights[i].shape) < mutation_rate
            gaussian_noise = np.random.randn(*self.weights[i].shape) * mutation_scale
            self.weights[i][mutation_mask] += gaussian_noise[mutation_mask]
            
            # CRITICAL: Clip weights to [-1, 1] like reference
            np.clip(self.weights[i], -1, 1, out=self.weights[i])

            # Mutate biases - same process as weights (matching reference)
            mutation_mask = np.random.random(self.biases[i].shape) < mutation_rate
            gaussian_noise = np.random.randn(*self.biases[i].shape) * mutation_scale
            self.biases[i][mutation_mask] += gaussian_noise[mutation_mask]
            
            # CRITICAL: Clip biases to [-1, 1] like reference
            np.clip(self.biases[i], -1, 1, out=self.biases[i])


# Export to global scope for other scripts to use
import builtins
builtins.NeuralNetwork = NeuralNetwork
