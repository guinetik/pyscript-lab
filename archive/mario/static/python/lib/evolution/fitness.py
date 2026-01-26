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
    MATCHING REFERENCE IMPLEMENTATION from SuperMarioBros-AI.

    Reference formula:
        max(distance^1.8 - frames^1.5 + min(max(distance-50, 0), 1) * 2500 + did_win * 1e6, 0.00001)

    Key insight: Frame penalty is CRITICAL! It forces Mario to move efficiently
    rather than standing still. Without it, Mario learns to not move (safe but no progress).
    """

    def __init__(
        self,
        distance_exponent: float = 1.8,
        distance_weight: float = 1.0,
        frame_penalty_exponent: float = 1.5,
        frame_penalty_weight: float = 1.0,
        enable_milestones: bool = True,
        milestone_values: dict = None,
        score_multiplier: float = 0.0,  # Reference doesn't use game score
        min_fitness: float = 0.00001,
        win_bonus: float = 1_000_000
    ):
        """
        Initialize Mario fitness calculator (matching reference).

        Args:
            distance_exponent: Exponent for distance reward (reference: 1.8)
            distance_weight: Multiplier for distance component (reference: 1.0)
            frame_penalty_exponent: Exponent for frame penalty (reference: 1.5)
            frame_penalty_weight: Multiplier for frame penalty (reference: 1.0)
            enable_milestones: Enable milestone bonuses (reference: single 50px milestone)
            milestone_values: Dict of {distance_threshold: bonus_value}
            score_multiplier: Multiplier for game score bonus (reference: 0)
            min_fitness: Minimum fitness (reference: 0.00001)
            win_bonus: Bonus for beating the level (reference: 1,000,000)
        """
        self.distance_exponent = distance_exponent
        self.distance_weight = distance_weight
        self.frame_penalty_exponent = frame_penalty_exponent
        self.frame_penalty_weight = frame_penalty_weight
        self.enable_milestones = enable_milestones
        self.score_multiplier = score_multiplier
        self.min_fitness = min_fitness
        self.win_bonus = win_bonus

        # Reference milestone: single bonus at 50px
        # min(max(distance-50, 0), 1) * 2500 = 2500 if distance > 50, else 0
        self.milestone_values = milestone_values or {
            50: 2500  # Matching reference: single milestone at 50px
        }

        print(f"📊 Initialized MarioFitnessCalculator (REFERENCE MATCHING):")
        print(f"   Formula: distance^{distance_exponent} - frames^{frame_penalty_exponent} + milestones + win_bonus")
        print(f"   Milestones: {self.milestone_values}")
        print(f"   Win bonus: {win_bonus:,}")

    def calculate(self, generation_info: dict) -> float:
        """
        Calculate Mario fitness using REFERENCE FORMULA.

        Reference formula:
            max(distance^1.8 - frames^1.5 + milestone_bonus + did_win * 1e6, 0.00001)

        The frame penalty (frames^1.5) is CRITICAL:
        - 100 frames → penalty of 1,000
        - 500 frames → penalty of 11,180
        - 1000 frames → penalty of 31,623

        This forces Mario to move forward efficiently. Standing still = low fitness!

        Args:
            generation_info: Dict with:
                - 'distance': Max X position reached
                - 'frames': Number of frames taken
                - 'did_win': Whether Mario beat the level (optional)
                - 'generation': Current generation number (optional, for logging)

        Returns:
            float: Fitness score
        """
        distance = generation_info.get('distance', 0)
        frames = generation_info.get('frames', 1)  # Avoid division by zero
        did_win = generation_info.get('did_win', False)
        generation = generation_info.get('generation', 0)

        # Component 1: Distance reward (distance^1.8)
        distance_reward = (distance ** self.distance_exponent) * self.distance_weight

        # Component 2: Frame penalty (frames^1.5) - CRITICAL FOR LEARNING!
        # This penalizes slow/standing still behavior
        frame_penalty = (frames ** self.frame_penalty_exponent) * self.frame_penalty_weight

        # Component 3: Milestone bonus (reference: +2500 if distance > 50)
        milestone_bonus = 0
        if self.enable_milestones:
            for threshold, bonus in sorted(self.milestone_values.items()):
                if distance > threshold:
                    milestone_bonus += bonus

        # Component 4: Win bonus (reference: +1,000,000)
        win_bonus = self.win_bonus if did_win else 0

        # Total fitness (matching reference formula)
        fitness = distance_reward - frame_penalty + milestone_bonus + win_bonus

        # Ensure minimum fitness (never zero or negative)
        fitness = max(fitness, self.min_fitness)

        # Debug: Print breakdown occasionally
        if generation > 0 and generation % 5 == 0:
            print(f"📊 Fitness breakdown (Gen {generation}):")
            print(f"   Distance^{self.distance_exponent}: +{distance_reward:.1f}")
            print(f"   Frames^{self.frame_penalty_exponent} penalty: -{frame_penalty:.1f}")
            print(f"   Milestones: +{milestone_bonus:.1f}")
            if win_bonus > 0:
                print(f"   Win bonus: +{win_bonus:,.0f}")
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
