"""
Evolution Module - Neuroevolution components

Provides clean separation of concerns for evolutionary algorithms:
- EvolutionStrategy: Selection and mutation logic
- FitnessCalculator: Fitness function logic
- GenerationManager: Generation lifecycle management
- GenerationLogger: Logging utilities

Author: Guinetik
"""

from .strategy import (
    EvolutionStrategy,
    OnePlusOneES,
    OnePlusLambdaES,
    NoElitismStrategy
)

from .fitness import (
    FitnessCalculator,
    MarioFitnessCalculator,
    SimpleFitnessCalculator,
    VelocityFitnessCalculator
)

from .generation import (
    GenerationManager,
    GenerationLogger
)

from .population import (
    Individual,
    PopulationManager
)

from .crossover import (
    simulated_binary_crossover,
    uniform_crossover,
    arithmetic_crossover,
    crossover_neural_networks,
    breed_networks
)

__all__ = [
    # Strategies
    'EvolutionStrategy',
    'OnePlusOneES',
    'OnePlusLambdaES',
    'NoElitismStrategy',
    # Fitness
    'FitnessCalculator',
    'MarioFitnessCalculator',
    'SimpleFitnessCalculator',
    'VelocityFitnessCalculator',
    # Generation
    'GenerationManager',
    'GenerationLogger',
    # Population
    'Individual',
    'PopulationManager',
    # Crossover
    'simulated_binary_crossover',
    'uniform_crossover',
    'arithmetic_crossover',
    'crossover_neural_networks',
    'breed_networks'
]
