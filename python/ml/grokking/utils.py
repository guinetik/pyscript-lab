"""
Utility functions for the Grokking Neural Network.

Provides data generation, shuffling, and accuracy calculation.
"""

import random


def shuffle(array):
    """
    Fisher-Yates shuffle - in-place array randomization.
    
    Args:
        array: List to shuffle (mutated in place)
        
    Returns:
        list: The same array, shuffled
    """
    for i in range(len(array) - 1, 0, -1):
        j = random.randint(0, i)
        array[i], array[j] = array[j], array[i]
    return array


def generate_all_pairs(mod, symmetric=True):
    """
    Generate all pairs dataset for modular addition.
    
    Creates examples of the form: (a, b) -> (a + b) mod p
    
    Args:
        mod: Modulus value (number of possible outputs)
        symmetric: If True, only use pairs where a <= b (reduces dataset size)
        
    Returns:
        list: Dataset of dictionaries with 'a', 'b', 'target' keys
    """
    data = []
    
    for a in range(mod):
        for b in range(mod):
            if symmetric and a > b:
                continue  # Skip if using symmetric pairs
            
            c = (a + b) % mod
            data.append({
                'a': a,
                'b': b,
                'target': c
            })
    
    return data


def split_data(dataset, train_fraction=0.4):
    """
    Split dataset into train/test sets.
    
    Args:
        dataset: List of examples
        train_fraction: Fraction for training (0-1)
        
    Returns:
        tuple: (train_data, test_data)
    """
    # Shuffle a copy
    shuffled = dataset.copy()
    shuffle(shuffled)
    
    split_idx = int(len(shuffled) * train_fraction)
    
    return shuffled[:split_idx], shuffled[split_idx:]


def calc_accuracy(network, dataset):
    """
    Calculate prediction accuracy on a dataset.
    
    Args:
        network: FactoredNetwork instance
        dataset: List of examples with 'a', 'b', 'target' keys
        
    Returns:
        float: Accuracy (0-1)
    """
    if not dataset:
        return 0.0
    
    correct = 0
    
    for example in dataset:
        prediction = network.predict(example['a'], example['b'])
        if prediction == example['target']:
            correct += 1
    
    return correct / len(dataset)


def get_sample_predictions(network, dataset, num_samples=5):
    """
    Get sample predictions for visualization.
    
    Args:
        network: FactoredNetwork instance
        dataset: List of examples
        num_samples: Number of samples to return
        
    Returns:
        list: Sample predictions with input, target, prediction, correct
    """
    samples = []
    indices = list(range(len(dataset)))
    shuffle(indices)
    
    for i in indices[:num_samples]:
        example = dataset[i]
        a, b = example['a'], example['b']
        target = example['target']
        prediction = network.predict(a, b)
        
        samples.append({
            'a': a,
            'b': b,
            'target': target,
            'prediction': prediction,
            'correct': prediction == target,
            'expression': f"{a} + {b} mod {network.n_tokens} = {target}"
        })
    
    return samples
