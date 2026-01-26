"""
Crossover Operations - Genetic recombination for neural networks

Implements various crossover methods for combining parent networks.
Based on techniques from SuperMarioBros-AI project.
"""

import numpy as np
from typing import Tuple, List, Dict
from js import console


def simulated_binary_crossover(parent1: np.ndarray, parent2: np.ndarray,
                               eta: float = 100.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulated Binary Crossover (SBX).

    Creates offspring that are probabilistically distributed around parents.
    Higher eta values create offspring closer to parents.

    Args:
        parent1: First parent array (weights or biases)
        parent2: Second parent array (weights or biases)
        eta: Distribution index (default: 100.0, range typically 2-100)
             Higher eta = offspring closer to parents
             Lower eta = more exploration

    Returns:
        Tuple of two offspring arrays
    """
    # Initialize offspring as copies
    offspring1 = parent1.copy()
    offspring2 = parent2.copy()

    # Generate random values for each gene
    rand = np.random.random(parent1.shape)

    # Calculate spread factor (gamma)
    gamma = np.empty(parent1.shape)

    # For each gene, calculate crossover spread
    # This creates a probability distribution around parents
    gamma[rand <= 0.5] = (2 * rand[rand <= 0.5]) ** (1.0 / (eta + 1))
    gamma[rand > 0.5] = (1.0 / (2.0 * (1.0 - rand[rand > 0.5]))) ** (1.0 / (eta + 1))

    # Create offspring as weighted combination of parents
    offspring1 = 0.5 * ((1 + gamma) * parent1 + (1 - gamma) * parent2)
    offspring2 = 0.5 * ((1 - gamma) * parent1 + (1 + gamma) * parent2)

    return offspring1, offspring2


def uniform_crossover(parent1: np.ndarray, parent2: np.ndarray,
                     mix_prob: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Uniform crossover - each gene independently selected from parents.

    Args:
        parent1: First parent array
        parent2: Second parent array
        mix_prob: Probability of selecting from parent1 (default: 0.5)

    Returns:
        Tuple of two offspring arrays
    """
    offspring1 = parent1.copy()
    offspring2 = parent2.copy()

    # Create random mask
    mask = np.random.uniform(0, 1, size=offspring1.shape)

    # Swap genes based on mask
    offspring1[mask > mix_prob] = parent2[mask > mix_prob]
    offspring2[mask > mix_prob] = parent1[mask > mix_prob]

    return offspring1, offspring2


def arithmetic_crossover(parent1: np.ndarray, parent2: np.ndarray,
                        alpha: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Arithmetic crossover - weighted average of parents.

    Args:
        parent1: First parent array
        parent2: Second parent array
        alpha: Blending factor (0.5 = equal blend)

    Returns:
        Tuple of two offspring arrays
    """
    offspring1 = alpha * parent1 + (1 - alpha) * parent2
    offspring2 = (1 - alpha) * parent1 + alpha * parent2

    return offspring1, offspring2


def crossover_neural_networks(parent1_weights: Dict, parent2_weights: Dict,
                             method: str = 'sbx', **kwargs) -> Dict:
    """
    Apply crossover to complete neural networks.

    Args:
        parent1_weights: First parent's weights dict {'weights': [...], 'biases': [...]}
        parent2_weights: Second parent's weights dict
        method: Crossover method ('sbx', 'uniform', 'arithmetic')
        **kwargs: Additional parameters for crossover method

    Returns:
        Offspring weights dictionary
    """
    # Select crossover function
    if method == 'sbx':
        crossover_fn = lambda p1, p2: simulated_binary_crossover(
            p1, p2, eta=kwargs.get('eta', 100.0)
        )
    elif method == 'uniform':
        crossover_fn = lambda p1, p2: uniform_crossover(
            p1, p2, mix_prob=kwargs.get('mix_prob', 0.5)
        )
    elif method == 'arithmetic':
        crossover_fn = lambda p1, p2: arithmetic_crossover(
            p1, p2, alpha=kwargs.get('alpha', 0.5)
        )
    else:
        # Default to SBX
        crossover_fn = lambda p1, p2: simulated_binary_crossover(p1, p2, eta=100.0)

    # Initialize offspring
    offspring_weights = []
    offspring_biases = []

    # Get parent networks
    p1_weights = parent1_weights['weights']
    p1_biases = parent1_weights['biases']
    p2_weights = parent2_weights['weights']
    p2_biases = parent2_weights['biases']

    # Apply crossover layer by layer
    num_layers = len(p1_weights)

    for layer in range(num_layers):
        # Crossover weights
        w1, w2 = crossover_fn(p1_weights[layer], p2_weights[layer])

        # Crossover biases
        b1, b2 = crossover_fn(p1_biases[layer], p2_biases[layer])

        # Randomly choose one of the two offspring for each layer
        # This increases diversity
        if np.random.random() > 0.5:
            offspring_weights.append(w1)
            offspring_biases.append(b1)
        else:
            offspring_weights.append(w2)
            offspring_biases.append(b2)

    # Clip weights to reasonable bounds
    for i in range(len(offspring_weights)):
        offspring_weights[i] = np.clip(offspring_weights[i], -5.0, 5.0)
        offspring_biases[i] = np.clip(offspring_biases[i], -5.0, 5.0)

    return {
        'weights': offspring_weights,
        'biases': offspring_biases
    }


def breed_networks(parent1_weights: Dict, parent2_weights: Dict,
                  mutation_rate: float = 0.01, mutation_scale: float = 0.1,
                  crossover_method: str = 'sbx', **kwargs) -> Dict:
    """
    Complete breeding pipeline: crossover + mutation.

    Args:
        parent1_weights: First parent network
        parent2_weights: Second parent network
        mutation_rate: Probability of mutating each weight
        mutation_scale: Scale of mutations
        crossover_method: Method for crossover
        **kwargs: Additional crossover parameters

    Returns:
        Offspring network weights
    """
    # Step 1: Crossover
    offspring = crossover_neural_networks(
        parent1_weights, parent2_weights,
        method=crossover_method,
        **kwargs
    )

    # Step 2: Mutation
    for layer_weights in offspring['weights']:
        # Mutate weights
        mutation_mask = np.random.random(layer_weights.shape) < mutation_rate
        mutations = np.random.normal(0, mutation_scale, layer_weights.shape)
        layer_weights[mutation_mask] += mutations[mutation_mask]

    for layer_biases in offspring['biases']:
        # Mutate biases
        mutation_mask = np.random.random(layer_biases.shape) < mutation_rate
        mutations = np.random.normal(0, mutation_scale, layer_biases.shape)
        layer_biases[mutation_mask] += mutations[mutation_mask]

    # Step 3: Clip to bounds
    for i in range(len(offspring['weights'])):
        offspring['weights'][i] = np.clip(offspring['weights'][i], -5.0, 5.0)
        offspring['biases'][i] = np.clip(offspring['biases'][i], -5.0, 5.0)

    return offspring