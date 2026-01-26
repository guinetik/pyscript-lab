"""
Crossover methods for neuroevolution breeding.
Ported from archive implementation.
"""

import numpy as np


def simulated_binary_crossover(parent1: np.ndarray, parent2: np.ndarray,
                                eta: float = 100.0) -> tuple:
    """
    Simulated Binary Crossover (SBX).
    
    Creates offspring that are probabilistically distributed around parents.
    Higher eta values create offspring closer to parents.
    
    Args:
        parent1: First parent array (weights or biases)
        parent2: Second parent array (weights or biases)
        eta: Distribution index. Higher eta = offspring closer to parents
        
    Returns:
        Tuple of two offspring arrays
    """
    # Initialize offspring as copies
    offspring1 = parent1.copy()
    offspring2 = parent2.copy()
    
    # Random values for crossover calculation
    rand = np.random.random(parent1.shape)
    
    # Calculate spread factor gamma
    gamma = np.empty(parent1.shape)
    gamma[rand <= 0.5] = (2 * rand[rand <= 0.5]) ** (1.0 / (eta + 1))
    gamma[rand > 0.5] = (1.0 / (2 * (1 - rand[rand > 0.5]))) ** (1.0 / (eta + 1))
    
    # Create offspring as weighted combination of parents
    offspring1 = 0.5 * ((1 + gamma) * parent1 + (1 - gamma) * parent2)
    offspring2 = 0.5 * ((1 - gamma) * parent1 + (1 + gamma) * parent2)
    
    return offspring1, offspring2


def uniform_crossover(parent1: np.ndarray, parent2: np.ndarray,
                      mix_prob: float = 0.5) -> tuple:
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
    
    # Create mask for gene selection
    mask = np.random.uniform(0, 1, size=offspring1.shape)
    
    # Swap genes based on mask
    offspring1[mask > mix_prob] = parent2[mask > mix_prob]
    offspring2[mask > mix_prob] = parent1[mask > mix_prob]
    
    return offspring1, offspring2


def crossover_networks(parent1_weights: dict, parent2_weights: dict,
                       method: str = 'sbx', eta: float = 100.0) -> dict:
    """
    Apply crossover to complete neural networks.
    
    Args:
        parent1_weights: First parent's weights dict {'W1': ..., 'b1': ..., 'W2': ..., 'b2': ...}
        parent2_weights: Second parent's weights dict
        method: 'sbx' or 'uniform'
        eta: SBX distribution index (higher = closer to parents)
        
    Returns:
        Offspring weights dict
    """
    # Select crossover function
    if method == 'sbx':
        crossover_fn = lambda p1, p2: simulated_binary_crossover(p1, p2, eta=eta)
    else:
        crossover_fn = lambda p1, p2: uniform_crossover(p1, p2)
    
    offspring = {}
    
    # Crossover each weight/bias matrix
    for key in ['W1', 'b1', 'W2', 'b2']:
        p1 = np.array(parent1_weights[key])
        p2 = np.array(parent2_weights[key])
        
        # Get two offspring, randomly pick one
        o1, o2 = crossover_fn(p1, p2)
        offspring[key] = o1 if np.random.random() > 0.5 else o2
        
        # Clip to [-1, 1] like SuperMarioBros-AI
        offspring[key] = np.clip(offspring[key], -1.0, 1.0)
    
    return offspring
