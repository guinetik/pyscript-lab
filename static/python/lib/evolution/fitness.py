"""
Fitness Calculators - Pluggable fitness functions for neuroevolution

Provides clean abstraction for fitness calculation with declarative configuration.
Makes it easy to experiment with different fitness formulas.

Author: Guinetik
"""

from abc import ABC, abstractmethod


class FitnessCalculator(ABC):
    """
    Abstract base class for fitness calculators.
    Encapsulates fitness function logic.
    """

    @abstractmethod
    def calculate(self, generation_info: dict) -> float:
        """
        Calculate fitness score for a generation.

        Args:
            generation_info: Dict with distance, frames, score, etc.

        Returns:
            float: Fitness score (higher is better)
        """
        pass


class MarioFitnessCalculator(FitnessCalculator):
    """
    Fitness calculator for Super Mario Bros.

    Features:
    - Exponential distance reward (encourages progress)
    - Frame penalty (encourages speed)
    - Milestone bonuses (stepping stones)
    - Score bonus (coins, enemies, blocks)

    All components are configurable via constructor.
    """

    def __init__(
        self,
        distance_exponent: float = 1.8,
        distance_weight: float = 1.0,
        frame_penalty_exponent: float = 1.4,
        frame_penalty_weight: float = 1.0,
        enable_milestones: bool = True,
        milestone_values: dict = None,
        score_multiplier: float = 10.0,
        min_fitness: float = 0.1
    ):
        """
        Initialize Mario fitness calculator.

        Args:
            distance_exponent: Exponent for distance reward (>1 = exponential)
            distance_weight: Multiplier for distance component
            frame_penalty_exponent: Exponent for frame penalty (>1 = harsh)
            frame_penalty_weight: Multiplier for frame penalty
            enable_milestones: Enable milestone bonuses
            milestone_values: Dict of {distance_threshold: bonus_value}
            score_multiplier: Multiplier for game score bonus
            min_fitness: Minimum fitness (prevents zero/negative)
        """
        self.distance_exponent = distance_exponent
        self.distance_weight = distance_weight
        self.frame_penalty_exponent = frame_penalty_exponent
        self.frame_penalty_weight = frame_penalty_weight
        self.enable_milestones = enable_milestones
        self.score_multiplier = score_multiplier
        self.min_fitness = min_fitness

        # Default milestones (can be overridden)
        # IMPORTANT: 700-800px is the "third pipe" obstacle where agents often get stuck
        self.milestone_values = milestone_values or {
            50: 2500,      # Past spawn
            300: 5000,     # Past first Goomba
            500: 10000,    # Past first pipe
            700: 15000,    # Approaching the difficult third pipe
            750: 25000,    # CRITICAL: Cleared third pipe! Big reward to encourage this
            800: 30000,    # Past the third pipe zone
            1000: 40000,   # Significant progress
            1500: 60000,   # Mid-level
            2000: 80000,   # Advanced
            3000: 150000   # Near end of 1-1
        }

        print(f"📊 Initialized MarioFitnessCalculator:")
        print(f"   Distance: ^{distance_exponent} × {distance_weight}")
        print(f"   Frame penalty: ^{frame_penalty_exponent} × {frame_penalty_weight}")
        print(f"   Milestones: {enable_milestones}")
        print(f"   Score multiplier: {score_multiplier}x")

    def calculate(self, generation_info: dict) -> float:
        """
        Calculate Mario fitness.

        Formula:
            fitness = (distance^exp × weight)
                    - (frames^exp × weight)
                    + milestones
                    + (score × multiplier)

        Args:
            generation_info: Dict with:
                - 'distance': Max X position reached
                - 'frames': Number of frames taken
                - 'score_gained': Points earned (optional)
                - 'generation': Current generation number (optional, for logging)

        Returns:
            float: Fitness score
        """
        distance = generation_info.get('distance', 0)
        frames = generation_info.get('frames', 1)  # Avoid division by zero
        score_gained = generation_info.get('score_gained', 0)
        generation = generation_info.get('generation', 0)

        # Component 1: Exponential distance reward
        # Getting from 1000px to 1100px worth MORE than 100px to 200px
        distance_reward = (distance ** self.distance_exponent) * self.distance_weight

        # Component 2: Frame penalty (optional - set exponent to 0 to disable)
        # With (1+1)-ES, frame penalty can prevent exploration
        if self.frame_penalty_exponent > 0:
            frame_penalty = (frames ** self.frame_penalty_exponent) * self.frame_penalty_weight
        else:
            frame_penalty = 0  # No penalty - pure distance-based fitness

        # Component 3: Milestone bonuses (stepping stones in fitness landscape)
        milestone_bonus = 0
        if self.enable_milestones:
            for threshold, bonus in sorted(self.milestone_values.items()):
                if distance > threshold:
                    milestone_bonus += bonus
                else:
                    break  # Thresholds are sorted, stop checking

        # Component 4: Game score bonus
        score_bonus = score_gained * self.score_multiplier

        # Total fitness
        fitness = distance_reward - frame_penalty + milestone_bonus + score_bonus

        # Ensure minimum fitness (never zero or negative)
        fitness = max(fitness, self.min_fitness)

        # Debug: Print breakdown occasionally
        if generation % 10 == 0:
            print(f"📊 Fitness breakdown (Gen {generation}):")
            print(f"   Distance^{self.distance_exponent}: {distance_reward:.1f}")
            print(f"   Frames^{self.frame_penalty_exponent} penalty: -{frame_penalty:.1f}")
            print(f"   Milestones: {milestone_bonus:.1f}")
            print(f"   Score: {score_bonus:.1f}")
            print(f"   TOTAL: {fitness:.1f}")

        return fitness


class SimpleFitnessCalculator(FitnessCalculator):
    """
    Simple linear fitness calculator.
    Just returns distance traveled (no penalties or bonuses).

    Useful for debugging and baseline comparisons.
    """

    def __init__(self):
        """Initialize simple fitness calculator."""
        print(f"📊 Initialized SimpleFitnessCalculator (distance only)")

    def calculate(self, generation_info: dict) -> float:
        """
        Return distance as fitness.

        Args:
            generation_info: Dict with 'distance'

        Returns:
            float: Distance traveled
        """
        return float(generation_info.get('distance', 0))


class VelocityFitnessCalculator(FitnessCalculator):
    """
    Velocity-based fitness calculator.
    Rewards distance per frame (speed).

    Formula: fitness = distance / frames

    Good for encouraging fast, efficient solutions.
    """

    def __init__(self, min_frames: int = 1):
        """
        Initialize velocity fitness calculator.

        Args:
            min_frames: Minimum frames (prevents division by zero)
        """
        self.min_frames = min_frames
        print(f"📊 Initialized VelocityFitnessCalculator (distance/frames)")

    def calculate(self, generation_info: dict) -> float:
        """
        Calculate velocity-based fitness.

        Args:
            generation_info: Dict with 'distance' and 'frames'

        Returns:
            float: Distance per frame
        """
        distance = generation_info.get('distance', 0)
        frames = max(generation_info.get('frames', 1), self.min_frames)

        return distance / frames
