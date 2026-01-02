"""
Population Manager - Tracks elite individuals for breeding

Manages a small pool of elite performers for periodic breeding cycles.
Based on genetic algorithm concepts from SuperMarioBros-AI project.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from js import console


class Individual:
    """Represents a single neural network agent with fitness."""

    def __init__(self, weights: dict, fitness: float, distance: int, generation: int):
        """
        Initialize an individual.

        Args:
            weights: Neural network weights and biases
            fitness: Fitness score achieved
            distance: Maximum distance reached
            generation: Generation when this individual was created
        """
        self.weights = weights  # {'weights': [...], 'biases': [...]}
        self.fitness = fitness
        self.distance = distance
        self.generation = generation
        self.age = 0  # Generations survived

    def __repr__(self):
        return f"Individual(gen={self.generation}, fitness={self.fitness:.1f}, dist={self.distance}px)"


class PopulationManager:
    """
    Manages elite individuals for breeding.

    Maintains a small pool of the best performers and handles
    breeding operations to create offspring through crossover.
    """

    def __init__(self, elite_size: int = 5, breeding_interval: int = 4):
        """
        Initialize population manager.

        Args:
            elite_size: Maximum number of elite individuals to track
            breeding_interval: Breed every N generations (default: 4)
        """
        self.elite_size = elite_size
        self.breeding_interval = breeding_interval
        self.elites: List[Individual] = []
        self.breeding_history: List[Dict] = []

    def update_elites(self, individual: Individual) -> bool:
        """
        Add or update elite pool with new individual.

        Args:
            individual: New individual to potentially add

        Returns:
            True if individual was added to elites
        """
        # Check if this individual should be in elite pool
        if len(self.elites) < self.elite_size:
            # Pool not full, add individual
            self.elites.append(individual)
            self.elites.sort(key=lambda x: x.fitness, reverse=True)
            console.log(f"🏆 Added to elite pool: {individual}")
            return True

        elif individual.fitness > self.elites[-1].fitness:
            # Better than worst elite, replace it
            self.elites[-1] = individual
            self.elites.sort(key=lambda x: x.fitness, reverse=True)
            console.log(f"🏆 Replaced worst elite with: {individual}")
            return True

        return False

    def age_elites(self):
        """Increment age of all elites (called each generation)."""
        for elite in self.elites:
            elite.age += 1

    def should_breed(self, generation: int) -> bool:
        """
        Check if current generation should perform breeding.

        Args:
            generation: Current generation number

        Returns:
            True if breeding should occur
        """
        # Need at least 2 elites to breed
        if len(self.elites) < 2:
            return False

        # Breed every N generations (but not on gen 0)
        return generation > 0 and generation % self.breeding_interval == 0

    def select_parents(self, method: str = 'tournament') -> Tuple[Individual, Individual]:
        """
        Select two parents for breeding.

        Args:
            method: Selection method ('tournament', 'roulette', 'best')

        Returns:
            Tuple of two parent individuals
        """
        if len(self.elites) < 2:
            raise ValueError("Need at least 2 elites for breeding")

        if method == 'best':
            # Always breed the top 2
            return self.elites[0], self.elites[1]

        elif method == 'tournament':
            # Tournament selection (size=2)
            tournament_size = min(2, len(self.elites))

            # Select parent 1
            tournament1 = np.random.choice(self.elites, tournament_size, replace=False)
            parent1 = max(tournament1, key=lambda x: x.fitness)

            # Select parent 2 (ensure different from parent1)
            remaining = [e for e in self.elites if e != parent1]
            if remaining:
                tournament2 = np.random.choice(remaining,
                                              min(tournament_size, len(remaining)),
                                              replace=False)
                parent2 = max(tournament2, key=lambda x: x.fitness)
            else:
                parent2 = parent1  # Self-breeding if only one elite

            return parent1, parent2

        elif method == 'roulette':
            # Roulette wheel selection (fitness-proportional)
            total_fitness = sum(e.fitness for e in self.elites)

            # Select parent 1
            pick1 = np.random.uniform(0, total_fitness)
            current = 0
            parent1 = None
            for elite in self.elites:
                current += elite.fitness
                if current > pick1:
                    parent1 = elite
                    break

            # Select parent 2
            pick2 = np.random.uniform(0, total_fitness)
            current = 0
            parent2 = None
            for elite in self.elites:
                current += elite.fitness
                if current > pick2:
                    parent2 = elite
                    break

            return parent1 or self.elites[0], parent2 or self.elites[1]

        else:
            # Default to best
            return self.elites[0], self.elites[1]

    def log_breeding_event(self, parent1: Individual, parent2: Individual,
                           offspring_weights: dict, generation: int):
        """
        Record breeding event for history.

        Args:
            parent1: First parent
            parent2: Second parent
            offspring_weights: Created offspring weights
            generation: Current generation number
        """
        event = {
            'generation': generation,
            'parent1': {
                'fitness': parent1.fitness,
                'distance': parent1.distance,
                'generation': parent1.generation,
                'age': parent1.age
            },
            'parent2': {
                'fitness': parent2.fitness,
                'distance': parent2.distance,
                'generation': parent2.generation,
                'age': parent2.age
            },
            'elite_pool_size': len(self.elites),
            'avg_elite_fitness': np.mean([e.fitness for e in self.elites])
        }
        self.breeding_history.append(event)

        console.log("=" * 60)
        console.log(f"🧬 BREEDING EVENT - Generation {generation}")
        console.log(f"   Parent 1: Gen {parent1.generation}, Fitness {parent1.fitness:.1f}, {parent1.distance}px")
        console.log(f"   Parent 2: Gen {parent2.generation}, Fitness {parent2.fitness:.1f}, {parent2.distance}px")
        console.log(f"   Elite Pool: {len(self.elites)} individuals")
        console.log(f"   Avg Elite Fitness: {event['avg_elite_fitness']:.1f}")
        console.log("=" * 60)

    def get_statistics(self) -> Dict:
        """
        Get current population statistics.

        Returns:
            Dictionary with population stats
        """
        if not self.elites:
            return {
                'elite_count': 0,
                'best_fitness': 0,
                'avg_fitness': 0,
                'best_distance': 0,
                'oldest_age': 0
            }

        return {
            'elite_count': len(self.elites),
            'best_fitness': self.elites[0].fitness,
            'avg_fitness': np.mean([e.fitness for e in self.elites]),
            'best_distance': self.elites[0].distance,
            'oldest_age': max(e.age for e in self.elites),
            'diversity': self._calculate_diversity()
        }

    def _calculate_diversity(self) -> float:
        """
        Calculate genetic diversity in elite pool.

        Returns:
            Diversity score (0-1, higher = more diverse)
        """
        if len(self.elites) < 2:
            return 0.0

        # Simple diversity: standard deviation of fitness scores
        fitness_values = [e.fitness for e in self.elites]
        std_dev = np.std(fitness_values)
        mean_fitness = np.mean(fitness_values)

        # Normalize by mean (coefficient of variation)
        if mean_fitness > 0:
            diversity = min(1.0, std_dev / mean_fitness)
        else:
            diversity = 0.0

        return diversity