"""
Evolution Strategies - Pluggable evolution algorithms for neuroevolution

Provides clean abstraction for different evolution strategies:
- (1+1)-ES: One parent, one offspring, elitism
- (1+λ)-ES: One parent, multiple offspring, best selection
- Adaptive mutation for escaping local optima

Author: Guinetik
"""

from abc import ABC, abstractmethod
from js import console


class EvolutionStrategy(ABC):
    """
    Abstract base class for evolution strategies.
    Handles selection, mutation, and elitism logic.
    """

    @abstractmethod
    def should_keep_offspring(self, offspring_fitness: float, champion_fitness: float) -> bool:
        """
        Decide whether to keep offspring or restore champion.

        Args:
            offspring_fitness: Fitness of current generation
            champion_fitness: Fitness of best solution so far

        Returns:
            bool: True to keep offspring, False to restore champion
        """
        pass

    @abstractmethod
    def get_mutation_params(self, generation_info: dict) -> tuple:
        """
        Calculate mutation parameters for next generation.

        Args:
            generation_info: Dict with distance, fitness, history, etc.

        Returns:
            tuple: (mutation_rate, mutation_scale)
        """
        pass

    @abstractmethod
    def on_generation_end(self, generation_info: dict):
        """
        Hook called at end of each generation.
        Used to update internal state.

        Args:
            generation_info: Dict with generation results
        """
        pass


class OnePlusOneES(EvolutionStrategy):
    """
    (1+1)-ES: One parent + one offspring with elitism.

    Features:
    - Elite preservation (champion always kept)
    - Adaptive mutation (escapes local optima)
    - Simple and effective for small networks
    """

    def __init__(
        self,
        mutation_rate: float = 0.05,
        mutation_scale: float = 0.2,
        adaptive_mutation: bool = True,
        local_optimum_threshold: int = 5
    ):
        """
        Initialize (1+1)-ES strategy.

        Args:
            mutation_rate: Base probability of mutating each weight (0-1)
            mutation_scale: Base standard deviation of mutations
            adaptive_mutation: Enable adaptive mutation for local optima
            local_optimum_threshold: Generations stuck before boosting mutation
        """
        self.base_mutation_rate = mutation_rate
        self.base_mutation_scale = mutation_scale
        self.adaptive_mutation = adaptive_mutation
        self.local_optimum_threshold = local_optimum_threshold

        # Track stuck locations for adaptive mutation
        self.stuck_location_history = []
        self.max_history_size = 10

        print(f"🧬 Initialized (1+1)-ES:")
        print(f"   Mutation rate: {mutation_rate}")
        print(f"   Mutation scale: {mutation_scale}")
        print(f"   Adaptive mutation: {adaptive_mutation}")

    def should_keep_offspring(self, offspring_fitness: float, champion_fitness: float) -> bool:
        """
        Keep offspring only if it beats the champion.
        This is the core of elitism.

        Args:
            offspring_fitness: Fitness of current generation
            champion_fitness: Fitness of champion (best so far)

        Returns:
            bool: True if offspring is better
        """
        return offspring_fitness > champion_fitness

    def get_mutation_params(self, generation_info: dict) -> tuple:
        """
        Calculate adaptive mutation parameters.

        Two-way adaptation:
        1. INCREASE mutation when stuck at same location (escape local optima)
        2. DECREASE mutation when champion is good (preserve successful behaviors)

        Args:
            generation_info: Dict with 'distance', 'fitness', 'best_distance', etc.

        Returns:
            tuple: (mutation_rate, mutation_scale)
        """
        if not self.adaptive_mutation:
            return (self.base_mutation_rate, self.base_mutation_scale)

        distance = generation_info.get('distance', 0)
        best_distance = generation_info.get('best_distance', 0)

        # === PRESERVATION MODE: Reduce mutation when champion is good ===
        # IMPORTANT: Start preservation early to avoid destroying forward movement behavior!
        # Even networks that reach the first pipe (400px+) have learned valuable behaviors
        preservation_factor = 1.0
        if best_distance >= 800:
            # Excellent champion (past 3+ pipes) - be VERY conservative
            preservation_factor = 0.25
            print(f"🛡️ PRESERVATION MODE: Champion at {best_distance}px - using 25% mutation")
        elif best_distance >= 600:
            # Good champion (past 2 pipes) - be conservative  
            preservation_factor = 0.4
            print(f"🛡️ PRESERVATION MODE: Champion at {best_distance}px - using 40% mutation")
        elif best_distance >= 400:
            # Decent progress (approaching first pipe) - start being careful
            # This prevents destroying the "run forward" behavior
            preservation_factor = 0.6
            print(f"🛡️ PRESERVATION MODE: Champion at {best_distance}px - using 60% mutation")

        # Track stuck location (rounded to nearest 100px)
        stuck_location = int(distance / 100) * 100
        self.stuck_location_history.append(stuck_location)
        if len(self.stuck_location_history) > self.max_history_size:
            self.stuck_location_history.pop(0)

        # === ESCAPE MODE: Increase mutation when stuck ===
        # Check for local optimum
        if len(self.stuck_location_history) >= self.local_optimum_threshold:
            recent_locations = self.stuck_location_history[-self.local_optimum_threshold:]
            unique_locations = len(set(recent_locations))

            # Check for extended stuckness (10+ generations at same spot)
            extended_stuck = len(self.stuck_location_history) >= 10
            if extended_stuck:
                extended_locations = self.stuck_location_history[-10:]
                extended_unique = len(set(extended_locations))
            else:
                extended_unique = 999  # Not enough history

            if extended_unique == 1:
                # Severely stuck for 10+ generations → AGGRESSIVE mutation to escape
                # Override preservation mode when severely stuck
                print(f"🔥 SEVERELY STUCK: Same location for 10+ generations!")
                print(f"   AGGRESSIVE mutation boost (5x rate, 3x scale) - overrides preservation")
                return (min(self.base_mutation_rate * 5.0, 0.25), self.base_mutation_scale * 3.0)

            elif unique_locations == 1:
                # Stuck at exact same location for 5 gens → strong boost
                print(f"🚨 LOCAL OPTIMUM: Stuck at {stuck_location}px for {self.local_optimum_threshold}+ gens")
                print(f"   Strong mutation boost to escape (4x rate, 2.5x scale)")
                return (min(self.base_mutation_rate * 4.0, 0.20), self.base_mutation_scale * 2.5)

            elif unique_locations <= 2:
                # Oscillating between 2 locations → moderate boost
                print(f"⚠️ Oscillating between 2 locations (last {self.local_optimum_threshold} gens)")
                return (min(self.base_mutation_rate * 3.0, 0.15), self.base_mutation_scale * 2.0)

        # Normal mutation with preservation factor applied
        final_rate = self.base_mutation_rate * preservation_factor
        final_scale = self.base_mutation_scale * preservation_factor
        return (final_rate, final_scale)

    def on_generation_end(self, generation_info: dict):
        """
        Update internal state at end of generation.

        Args:
            generation_info: Generation results
        """
        # Nothing to do for (1+1)-ES
        # State is managed by get_mutation_params
        pass


class OnePlusLambdaES(EvolutionStrategy):
    """
    (1+λ)-ES: One parent + λ offspring, select best.

    Features:
    - Multiple offspring per generation (faster exploration)
    - Elite preservation (parent always competes)
    - Better at escaping local optima than (1+1)

    TODO: Not yet implemented (requires running multiple evaluations per generation)
    """

    def __init__(
        self,
        lambda_value: int = 4,
        mutation_rate: float = 0.05,
        mutation_scale: float = 0.2
    ):
        """
        Initialize (1+λ)-ES strategy.

        Args:
            lambda_value: Number of offspring per generation
            mutation_rate: Probability of mutating each weight
            mutation_scale: Standard deviation of mutations
        """
        self.lambda_value = lambda_value
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale

        print(f"🧬 Initialized (1+{lambda_value})-ES:")
        print(f"   Lambda (offspring): {lambda_value}")
        print(f"   Mutation rate: {mutation_rate}")
        print(f"   Mutation scale: {mutation_scale}")

    def should_keep_offspring(self, offspring_fitness: float, champion_fitness: float) -> bool:
        """Keep if better (same as (1+1) for single evaluation)."""
        return offspring_fitness > champion_fitness

    def get_mutation_params(self, generation_info: dict) -> tuple:
        """Return fixed mutation params (no adaptive for now)."""
        return (self.mutation_rate, self.mutation_scale)

    def on_generation_end(self, generation_info: dict):
        """No state to update."""
        pass


class NoElitismStrategy(EvolutionStrategy):
    """
    Baseline strategy with NO elitism (for comparison).
    Always keeps offspring regardless of fitness.

    WARNING: This will perform poorly! Only use for experiments.
    """

    def __init__(self, mutation_rate: float = 0.05, mutation_scale: float = 0.2):
        """
        Initialize no-elitism strategy.

        Args:
            mutation_rate: Probability of mutating each weight
            mutation_scale: Standard deviation of mutations
        """
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale

        print(f"⚠️ Initialized NO ELITISM strategy (for experiments only):")
        print(f"   Mutation rate: {mutation_rate}")
        print(f"   Mutation scale: {mutation_scale}")

    def should_keep_offspring(self, offspring_fitness: float, champion_fitness: float) -> bool:
        """Always keep offspring (no elitism)."""
        return True

    def get_mutation_params(self, generation_info: dict) -> tuple:
        """Return fixed mutation params."""
        return (self.mutation_rate, self.mutation_scale)

    def on_generation_end(self, generation_info: dict):
        """No state to update."""
        pass
