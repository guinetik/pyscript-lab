"""
Neural Controller - Abstract interface for neural network controllers

Provides a clean abstraction for different neural network implementations.
Agents can swap out different NN architectures without changing game logic.

Includes:
- SimpleNeuralController: Fixed 3-layer feedforward network
- NEATController: Topology-evolving network (NEAT algorithm)

Author: Guinetik
"""

from abc import ABC, abstractmethod
import numpy as np
from js import console
import random
from copy import deepcopy


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

    def apply_priors(self, prior_values: list):
        """
        Apply behavioral priors to network (optional, not all networks support this).

        Args:
            prior_values: List of bias values to apply (e.g., for output layer)

        Note:
            This is an optional method. Networks that don't support priors can ignore this.
            Default implementation does nothing.
        """
        pass  # Optional method - networks can override if they support priors


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

    def forward(self, state: np.ndarray, capture_activations: bool = False) -> np.ndarray:
        """
        Forward pass through network.

        Args:
            state: Input state vector
            capture_activations: If True, capture layer activations for visualization

        Returns:
            np.ndarray: Network output activations (1D array)
        """
        # Debug network architecture (log once)
        if not hasattr(self, '_logged_arch'):
            console.log(f"🔍 Network layer shapes:")
            for i, (w, b) in enumerate(zip(self.network.weights, self.network.biases)):
                console.log(f"   Layer {i}: weights={w.shape}, biases={b.shape}")
            self._logged_arch = True

        output = self.network.forward(state, capture_activations=capture_activations)

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

    def get_visualization_data(self) -> dict:
        """
        Get visualization data from the underlying network.
        Returns layer sizes, activations, and weight statistics.
        """
        if hasattr(self.network, 'get_visualization_data'):
            return self.network.get_visualization_data()
        else:
            # Fallback for networks that don't support visualization
            return {
                'layer_sizes': [self.input_size, self.hidden_size, self.output_size],
                'num_params': 0,
                'error': 'Visualization not supported for this network type'
            }

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

    def apply_priors(self, prior_values: list):
        """
        Apply behavioral priors to the output layer biases.

        Args:
            prior_values: List of 6 bias values in button order [UP, DOWN, LEFT, RIGHT, A, B]
        """
        if len(prior_values) != 6:
            console.error(f"❌ Expected 6 prior values, got {len(prior_values)}")
            return

        # Bias the OUTPUT layer (last layer)
        output_layer_idx = len(self.network.biases) - 1
        output_size = self.network.biases[output_layer_idx].shape[0]

        if output_size != 6:
            console.error(f"❌ Expected 6 outputs, got {output_size}")
            return

        # Set the output layer biases
        self.network.biases[output_layer_idx] = np.array(prior_values, dtype=np.float32)

        console.log(f"✅ Behavioral priors applied to output layer: {prior_values}")


class NEATNode:
    """Represents a node (neuron) in a NEAT genome."""

    def __init__(self, node_id: int, node_type: str):
        """
        Args:
            node_id: Unique identifier for this node
            node_type: 'input', 'hidden', or 'output'
        """
        self.id = node_id
        self.type = node_type
        self.value = 0.0  # Current activation value


class NEATConnection:
    """Represents a weighted connection between two nodes."""

    def __init__(self, in_node: int, out_node: int, weight: float, innovation: int, enabled: bool = True):
        """
        Args:
            in_node: ID of input node
            out_node: ID of output node
            weight: Connection weight
            innovation: Innovation number (tracks historical mutations)
            enabled: Whether this connection is active
        """
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.innovation = innovation
        self.enabled = enabled


class NEATGenome:
    """
    NEAT genome representing network topology and weights.
    Simplified implementation for browser-based evolution.
    """

    # Global innovation counter (shared across all genomes)
    global_innovation = 0
    innovation_history = {}  # Maps (in, out) -> innovation number

    def __init__(self, input_size: int, output_size: int):
        """
        Initialize minimal genome with direct input→output connections.

        Args:
            input_size: Number of input nodes
            output_size: Number of output nodes
        """
        self.input_size = input_size
        self.output_size = output_size

        # Create nodes
        self.nodes = {}
        next_id = 0

        # Input nodes
        for i in range(input_size):
            self.nodes[next_id] = NEATNode(next_id, 'input')
            next_id += 1

        # Output nodes
        for i in range(output_size):
            self.nodes[next_id] = NEATNode(next_id, 'output')
            next_id += 1

        self.next_node_id = next_id

        # Create minimal connections (input → output)
        self.connections = []
        for in_id in range(input_size):
            for out_id in range(input_size, input_size + output_size):
                weight = np.random.randn() * 0.5
                innov = self._get_innovation(in_id, out_id)
                self.connections.append(NEATConnection(in_id, out_id, weight, innov))

    @classmethod
    def _get_innovation(cls, in_node: int, out_node: int) -> int:
        """Get or create innovation number for a connection."""
        key = (in_node, out_node)
        if key not in cls.innovation_history:
            cls.innovation_history[key] = cls.global_innovation
            cls.global_innovation += 1
        return cls.innovation_history[key]

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network using topological sorting.

        Args:
            inputs: Input vector

        Returns:
            Output vector
        """
        # Reset all node values
        for node in self.nodes.values():
            node.value = 0.0

        # Set input values
        for i, val in enumerate(inputs):
            if i < self.input_size:
                self.nodes[i].value = val

        # Get evaluation order (topological sort)
        eval_order = self._topological_sort()

        # Propagate activations
        for node_id in eval_order:
            if self.nodes[node_id].type == 'input':
                continue  # Inputs already set

            # Sum weighted inputs
            activation = 0.0
            for conn in self.connections:
                if conn.enabled and conn.out_node == node_id:
                    activation += self.nodes[conn.in_node].value * conn.weight

            # Apply activation function (sigmoid)
            self.nodes[node_id].value = 1.0 / (1.0 + np.exp(-activation))

        # Collect outputs
        outputs = []
        for i in range(self.input_size, self.input_size + self.output_size):
            outputs.append(self.nodes[i].value)

        return np.array(outputs, dtype=np.float32)

    def _topological_sort(self) -> list:
        """
        Topological sort to determine evaluation order.
        Returns list of node IDs in evaluation order.
        """
        # Build adjacency list
        adj = {node_id: [] for node_id in self.nodes.keys()}
        in_degree = {node_id: 0 for node_id in self.nodes.keys()}

        for conn in self.connections:
            if conn.enabled:
                adj[conn.in_node].append(conn.out_node)
                in_degree[conn.out_node] += 1

        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in adj[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def mutate_weights(self, mutation_rate: float = 0.1, mutation_scale: float = 0.5):
        """Mutate connection weights."""
        for conn in self.connections:
            if random.random() < mutation_rate:
                # Perturb weight
                conn.weight += np.random.randn() * mutation_scale

    def mutate_add_connection(self, max_attempts: int = 20):
        """Add a new connection between two nodes."""
        for _ in range(max_attempts):
            # Pick random nodes (not both inputs, not output→input)
            node_ids = list(self.nodes.keys())
            in_node = random.choice(node_ids)
            out_node = random.choice(node_ids)

            # Validate connection
            if in_node == out_node:
                continue
            if self.nodes[in_node].type == 'output':
                continue
            if self.nodes[out_node].type == 'input':
                continue

            # Check if connection already exists
            exists = any(c.in_node == in_node and c.out_node == out_node for c in self.connections)
            if exists:
                continue

            # Create connection
            weight = np.random.randn() * 0.5
            innov = self._get_innovation(in_node, out_node)
            self.connections.append(NEATConnection(in_node, out_node, weight, innov))
            console.log(f"🔗 Added connection: {in_node} → {out_node}")
            return True

        return False

    def mutate_add_node(self):
        """Split an existing connection by adding a new node."""
        if not self.connections:
            return False

        # Pick random enabled connection
        enabled_conns = [c for c in self.connections if c.enabled]
        if not enabled_conns:
            return False

        conn = random.choice(enabled_conns)

        # Disable old connection
        conn.enabled = False

        # Create new node
        new_node_id = self.next_node_id
        self.nodes[new_node_id] = NEATNode(new_node_id, 'hidden')
        self.next_node_id += 1

        # Create two new connections (in→new, new→out)
        innov1 = self._get_innovation(conn.in_node, new_node_id)
        innov2 = self._get_innovation(new_node_id, conn.out_node)

        self.connections.append(NEATConnection(conn.in_node, new_node_id, 1.0, innov1))
        self.connections.append(NEATConnection(new_node_id, conn.out_node, conn.weight, innov2))

        console.log(f"➕ Added node {new_node_id}: {conn.in_node} → [{new_node_id}] → {conn.out_node}")
        return True

    def get_complexity(self) -> dict:
        """Return complexity metrics."""
        return {
            'nodes': len(self.nodes),
            'connections': len([c for c in self.connections if c.enabled]),
            'hidden_nodes': len([n for n in self.nodes.values() if n.type == 'hidden'])
        }


class NEATController(NeuralController):
    """
    NEAT (NeuroEvolution of Augmenting Topologies) controller.
    Evolves both network topology and weights.
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int, seed=None):
        """
        Initialize NEAT controller with minimal topology.

        Args:
            input_size: Number of inputs
            hidden_size: Ignored (NEAT evolves its own topology)
            output_size: Number of outputs
            seed: Random seed
        """
        self.input_size = input_size
        self.output_size = output_size

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        # Create genome
        self.genome = NEATGenome(input_size, output_size)

        # Activation storage
        self.layer_activations = []

        console.log(f"🧬 NEATController initialized")
        console.log(f"   Architecture: {input_size} inputs → {output_size} outputs")
        console.log(f"   Starting topology: {self.genome.get_complexity()}")

    def forward(self, state: np.ndarray, capture_activations: bool = False) -> np.ndarray:
        """
        Forward pass through evolved topology.

        Args:
            state: Input state vector
            capture_activations: If True, capture layer activations for visualization
        """
        # Clear previous activations
        if capture_activations:
            self.layer_activations = []

        # Forward pass through genome
        output = self.genome.forward(state)

        # Capture activations if requested
        if capture_activations:
            # Layer 0: Input nodes
            input_values = [self.genome.nodes[i].value for i in range(self.input_size)]
            self.layer_activations.append(np.array(input_values, dtype=np.float32))

            # Layer 1: Hidden nodes (if any)
            hidden_ids = [node_id for node_id, node in self.genome.nodes.items() if node.type == 'hidden']
            if hidden_ids:
                hidden_values = [self.genome.nodes[node_id].value for node_id in hidden_ids]
                self.layer_activations.append(np.array(hidden_values, dtype=np.float32))
            else:
                # No hidden layer, add empty layer
                self.layer_activations.append(np.array([], dtype=np.float32))

            # Layer 2: Output nodes
            output_values = [self.genome.nodes[i].value for i in range(self.input_size, self.input_size + self.output_size)]
            self.layer_activations.append(np.array(output_values, dtype=np.float32))

        return output

    def get_visualization_data(self) -> dict:
        """
        Get visualization data for NEAT network.
        Returns topology complexity information.
        """
        complexity = self.genome.get_complexity()

        # Compute weight statistics from connections
        weights = np.array([c.weight for c in self.genome.connections if c.enabled])

        weight_stats = []
        if len(weights) > 0:
            weight_stats = [{
                'layer': 0,
                'weights': {
                    'min': float(weights.min()),
                    'max': float(weights.max()),
                    'mean': float(weights.mean()),
                    'std': float(weights.std())
                },
                'biases': {
                    'min': 0.0,
                    'max': 0.0,
                    'mean': 0.0,
                    'std': 0.0
                }
            }]

        # Serialize captured activations
        activations = []
        if self.layer_activations:
            for i, layer_output in enumerate(self.layer_activations):
                if len(layer_output) == 0:
                    # Empty hidden layer
                    activations.append({
                        'layer': i,
                        'values': [],
                        'min': 0.0,
                        'max': 0.0,
                        'mean': 0.0,
                        'active_count': 0
                    })
                else:
                    flat_output = layer_output.flatten()
                    # Send all values so visualization can sample correctly
                    activations.append({
                        'layer': i,
                        'values': flat_output.tolist(),
                        'min': float(flat_output.min()),
                        'max': float(flat_output.max()),
                        'mean': float(flat_output.mean()),
                        'active_count': int(np.sum(flat_output > 0.1))
                    })

        return {
            'layer_sizes': [int(self.input_size), int(complexity['hidden_nodes']), int(self.output_size)],
            'num_params': int(complexity['connections']),
            'architecture': 'NEAT (Evolved Topology)',
            'nodes': complexity['nodes'],
            'connections': complexity['connections'],
            'hidden_nodes': complexity['hidden_nodes'],
            'weight_stats': weight_stats,
            'activations': activations
        }

    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.5):
        """
        Mutate the genome (weights + structure).

        NEAT mutations:
        - 80% weight mutation
        - 10% add connection
        - 5% add node
        - 5% toggle connection
        """
        rand = random.random()

        if rand < 0.80:
            # Weight mutation (most common)
            self.genome.mutate_weights(mutation_rate, mutation_scale)
        elif rand < 0.90:
            # Structural: add connection
            self.genome.mutate_add_connection()
        elif rand < 0.95:
            # Structural: add node
            self.genome.mutate_add_node()
        else:
            # Toggle random connection
            if self.genome.connections:
                conn = random.choice(self.genome.connections)
                conn.enabled = not conn.enabled

    def get_weights(self) -> dict:
        """Get genome for saving."""
        return {
            'genome': deepcopy(self.genome),
            'complexity': self.genome.get_complexity()
        }

    def set_weights(self, weights: list, biases: list):
        """
        Set genome from saved data.

        Note: NEAT stores entire genome, not just weight matrices.
        For compatibility, we accept dict with 'genome' key.
        """
        if isinstance(weights, dict) and 'genome' in weights:
            self.genome = deepcopy(weights['genome'])
        else:
            console.warn("⚠️ NEAT requires full genome, not just weights")

    def randomize(self):
        """Reset to minimal topology."""
        self.genome = NEATGenome(self.input_size, self.output_size)
        console.log("🔄 NEAT genome reset to minimal topology")


class ConvNeuralController(NeuralController):
    """
    Convolutional neural controller for Mario.
    Preserves 2D spatial structure of the 7x16 vision grid before flattening.
    Perfect for agents that rely on visual pattern recognition (gaps, enemies, blocks).
    """

    def __init__(
        self,
        vision_shape=(7, 16),
        context_size=8,
        num_filters=4,
        hidden_size=32,
        output_size=6,
        seed=None
    ):
        import numpy as np
        from js import console

        if seed is not None:
            np.random.seed(seed)

        self.vision_shape = vision_shape
        self.context_size = context_size
        self.num_filters = num_filters
        self.hidden_size = hidden_size
        self.output_size = output_size

        # 3x3 conv kernels + biases
        self.kernels = np.random.randn(num_filters, 3, 3) * 0.3
        self.biases_conv = np.zeros(num_filters)

        # Output size after valid conv: (H-2)*(W-2)*num_filters
        conv_out_size = (vision_shape[0] - 2) * (vision_shape[1] - 2) * num_filters
        fc_input_size = conv_out_size + context_size

        # Fully connected weights
        self.W1 = np.random.randn(hidden_size, fc_input_size) * 0.3
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(output_size, hidden_size) * 0.3
        self.b2 = np.zeros(output_size)

        # Activation storage
        self.layer_activations = []

        console.log(f"👁️ ConvNeuralController initialized")
        console.log(f"   Vision shape: {vision_shape}, Filters: {num_filters}, Hidden: {hidden_size}, Output: {output_size}")
        console.log(f"   Conv output size: {conv_out_size}, FC input: {fc_input_size}")

    def _conv_forward(self, x: np.ndarray) -> np.ndarray:
        """Apply simple valid convolution with ReLU activation."""
        h, w = self.vision_shape
        out_h, out_w = h - 2, w - 2
        out = np.zeros((self.num_filters, out_h, out_w))

        for f in range(self.num_filters):
            kernel = self.kernels[f]
            for i in range(out_h):
                for j in range(out_w):
                    region = x[i:i + 3, j:j + 3]
                    out[f, i, j] = np.sum(region * kernel) + self.biases_conv[f]

        # ReLU
        return np.maximum(0, out).flatten()

    def forward(self, state: np.ndarray, capture_activations: bool = False) -> np.ndarray:
        """
        Forward pass:
        1. Convolution on 7x16 vision grid
        2. Concatenate with context
        3. Fully connected layers with ReLU + sigmoid

        Args:
            state: Input state vector
            capture_activations: If True, capture layer activations for visualization
        """
        # Clear previous activations
        if capture_activations:
            self.layer_activations = []

        # Separate vision and context
        vision = state[:112].reshape(self.vision_shape)
        context = state[112:] if len(state) > 112 else np.zeros(self.context_size)

        # Layer 0: Input (vision + context flattened)
        input_layer = state.flatten()
        if capture_activations:
            self.layer_activations.append(input_layer)

        # Conv features
        conv_features = self._conv_forward(vision)
        x = np.concatenate([conv_features, context])

        # Layer 1: Conv features (after concatenation with context)
        if capture_activations:
            self.layer_activations.append(x)

        # FC layers
        h = np.maximum(0, self.W1 @ x + self.b1)  # ReLU

        # Layer 2: Hidden layer
        if capture_activations:
            self.layer_activations.append(h)

        out = 1 / (1 + np.exp(-(self.W2 @ h + self.b2)))  # Sigmoid

        # Layer 3: Output layer
        if capture_activations:
            self.layer_activations.append(out)

        if not hasattr(self, "_logged_arch"):
            console.log(f"🔍 Conv forward shapes:")
            console.log(f"   Conv features: {conv_features.shape}")
            console.log(f"   Hidden: {h.shape}, Output: {out.shape}")
            self._logged_arch = True

        return out.flatten()

    def get_visualization_data(self) -> dict:
        """
        Get visualization data for the convolutional network.
        Returns layer information and parameter counts.
        """
        conv_params = self.kernels.size + self.biases_conv.size
        fc_params = self.W1.size + self.b1.size + self.W2.size + self.b2.size
        total_params = conv_params + fc_params

        conv_out_size = (self.vision_shape[0] - 2) * (self.vision_shape[1] - 2) * self.num_filters

        # Weight statistics for visualization
        weight_stats = [
            {
                'layer': 0,
                'weights': {
                    'min': float(self.kernels.min()),
                    'max': float(self.kernels.max()),
                    'mean': float(self.kernels.mean()),
                    'std': float(self.kernels.std())
                },
                'biases': {
                    'min': float(self.biases_conv.min()),
                    'max': float(self.biases_conv.max()),
                    'mean': float(self.biases_conv.mean()),
                    'std': float(self.biases_conv.std())
                }
            },
            {
                'layer': 1,
                'weights': {
                    'min': float(self.W1.min()),
                    'max': float(self.W1.max()),
                    'mean': float(self.W1.mean()),
                    'std': float(self.W1.std())
                },
                'biases': {
                    'min': float(self.b1.min()),
                    'max': float(self.b1.max()),
                    'mean': float(self.b1.mean()),
                    'std': float(self.b1.std())
                }
            },
            {
                'layer': 2,
                'weights': {
                    'min': float(self.W2.min()),
                    'max': float(self.W2.max()),
                    'mean': float(self.W2.mean()),
                    'std': float(self.W2.std())
                },
                'biases': {
                    'min': float(self.b2.min()),
                    'max': float(self.b2.max()),
                    'mean': float(self.b2.mean()),
                    'std': float(self.b2.std())
                }
            }
        ]

        # Serialize captured activations
        activations = []
        if self.layer_activations:
            for i, layer_output in enumerate(self.layer_activations):
                flat_output = layer_output.flatten()
                # Send all values so visualization can sample correctly
                activations.append({
                    'layer': i,
                    'values': flat_output.tolist(),
                    'min': float(flat_output.min()),
                    'max': float(flat_output.max()),
                    'mean': float(flat_output.mean()),
                    'active_count': int(np.sum(flat_output > 0.1))
                })

        return {
            'layer_sizes': [int(112 + self.context_size), int(conv_out_size), int(self.hidden_size), int(self.output_size)],
            'num_params': int(total_params),
            'architecture': 'Convolutional',
            'conv_filters': self.num_filters,
            'vision_shape': self.vision_shape,
            'weight_stats': weight_stats,
            'activations': activations
        }

    def mutate(self, mutation_rate: float = 0.1, mutation_scale: float = 0.3):
        """Mutate kernels and dense weights randomly."""
        def mutate_param(param):
            mask = np.random.random(param.shape) < mutation_rate
            param += mask * np.random.randn(*param.shape) * mutation_scale

        for param in [
            self.kernels, self.biases_conv,
            self.W1, self.b1,
            self.W2, self.b2
        ]:
            mutate_param(param)

    def get_weights(self) -> dict:
        """Get network weights for saving."""
        return {
            "kernels": self.kernels,
            "biases_conv": self.biases_conv,
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2
        }

    def set_weights(self, weights: dict, biases=None):
        """Restore network weights from dict."""
        if isinstance(weights, dict):
            for name, value in weights.items():
                if hasattr(self, name):
                    setattr(self, name, value)

    def randomize(self):
        """Reinitialize all weights randomly."""
        self.kernels = np.random.randn(*self.kernels.shape) * 0.3
        self.biases_conv = np.zeros_like(self.biases_conv)
        self.W1 = np.random.randn(*self.W1.shape) * 0.3
        self.b1 = np.zeros_like(self.b1)
        self.W2 = np.random.randn(*self.W2.shape) * 0.3
        self.b2 = np.zeros_like(self.b2)

    def apply_priors(self, prior_values: list):
        """
        Apply behavioral priors to output biases (A, B, RIGHT, etc.)
        Same interface as SimpleNeuralController.
        """
        if len(prior_values) != self.output_size:
            console.error(f"❌ Expected {self.output_size} prior values, got {len(prior_values)}")
            return

        self.b2 = np.array(prior_values, dtype=np.float32)
        console.log(f"✅ Applied behavioral priors to ConvNeuralController: {prior_values}")


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

