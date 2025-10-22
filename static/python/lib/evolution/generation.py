"""
Generation Manager - Handles generation lifecycle for neuroevolution

Manages:
- Generation timeouts (adaptive)
- Death detection (stuck, timeout, killed)
- Progress tracking
- Generation reset

Separate from evolution strategy (single responsibility).

Author: Guinetik
"""

from js import console


class GenerationManager:
    """
    Manages the lifecycle of a single generation.

    Responsibilities:
    - Decide when generation ends (timeout, death, stuck)
    - Track generation statistics
    - Calculate adaptive timeouts
    - No evolution logic (handled by EvolutionStrategy)
    """

    def __init__(
        self,
        base_timeout_frames: int = 1800,  # 30 seconds
        timeout_increase_per_gen: int = 600,  # 10 seconds
        max_timeout_frames: int = 12000,  # 200 seconds
        base_stuck_threshold: int = 150,  # 2.5 seconds
        min_stuck_threshold: int = 90,  # 1.5 seconds (minimum)
        progressive_timeout: bool = True,
        progressive_stuck_threshold: bool = True
    ):
        """
        Initialize generation manager.

        Args:
            base_timeout_frames: Initial timeout (at gen 0)
            timeout_increase_per_gen: Frames added per generation
            max_timeout_frames: Maximum timeout cap
            base_stuck_threshold: Initial stuck detection threshold
            min_stuck_threshold: Minimum stuck threshold
            progressive_timeout: Enable progressive timeout increase
            progressive_stuck_threshold: Enable progressive stuck threshold decrease
        """
        self.base_timeout = base_timeout_frames
        self.timeout_increase = timeout_increase_per_gen
        self.max_timeout = max_timeout_frames
        self.base_stuck_threshold = base_stuck_threshold
        self.min_stuck_threshold = min_stuck_threshold
        self.progressive_timeout = progressive_timeout
        self.progressive_stuck_threshold = progressive_stuck_threshold

        # Current generation state
        self.current_generation = 0
        self.max_frames = base_timeout_frames
        self.stuck_threshold = base_stuck_threshold

        print(f"⏱️ Initialized GenerationManager:")
        print(f"   Base timeout: {base_timeout_frames} frames ({base_timeout_frames/60:.1f}s)")
        print(f"   Progressive timeout: {progressive_timeout}")
        print(f"   Stuck threshold: {base_stuck_threshold} frames ({base_stuck_threshold/60:.1f}s)")

    def start_generation(self, generation_number: int):
        """
        Start a new generation.
        Calculates adaptive timeouts.

        Args:
            generation_number: Current generation number
        """
        self.current_generation = generation_number

        # Calculate adaptive timeout
        if self.progressive_timeout:
            timeout = min(
                self.base_timeout + (generation_number * self.timeout_increase),
                self.max_timeout
            )
        else:
            timeout = self.base_timeout

        self.max_frames = timeout

        # Calculate adaptive stuck threshold (DECREASES over time to force efficiency)
        if self.progressive_stuck_threshold:
            # Gradually decrease from base to min over 200 generations
            generation_factor = max(0.6, 1.0 - (generation_number / 200))
            stuck = int(self.base_stuck_threshold * generation_factor)
            stuck = max(stuck, self.min_stuck_threshold)
        else:
            stuck = self.base_stuck_threshold

        self.stuck_threshold = stuck

        timeout_seconds = timeout / 60
        stuck_seconds = stuck / 60
        print(f"🔄 Starting generation {generation_number + 1}")
        print(f"⏱️ Timeout: {timeout_seconds:.1f}s ({timeout} frames)")
        print(f"🚫 Stuck threshold: {stuck_seconds:.1f}s ({stuck} frames)")

    def check_generation_end(self, step_info: dict) -> tuple:
        """
        Check if generation should end.

        Args:
            step_info: Dict from agent.step() with:
                - frames: Current frame count
                - alive: Is agent alive?
                - stuck_frames: Frames without progress

        Returns:
            tuple: (should_end: bool, death_cause: str or None)
                death_cause: 'timeout', 'enemy', 'stuck', or None
        """
        frames = step_info['frames']
        alive = step_info['alive']
        stuck_frames = step_info['stuck_frames']

        # Check timeout
        if frames >= self.max_frames:
            return (True, 'timeout')

        # Check death
        if not alive:
            return (True, 'enemy')

        # Check stuck
        if stuck_frames > self.stuck_threshold:
            return (True, 'stuck')

        # Generation continues
        return (False, None)

    def get_generation_summary(self, step_info: dict, death_cause: str) -> dict:
        """
        Create summary of completed generation.

        Args:
            step_info: Final step info
            death_cause: How generation ended

        Returns:
            dict: Generation summary
        """
        return {
            'generation': self.current_generation,
            'distance': step_info['max_position'],
            'frames': step_info['frames'],
            'death_cause': death_cause,
            'timeout_used': self.max_frames,
            'stuck_threshold': self.stuck_threshold
        }


class GenerationLogger:
    """
    Logs generation events to console.
    Separates logging concerns from generation management.
    """

    @staticmethod
    def log_generation_start(generation: int, best_distance: int):
        """Log generation start."""
        print(f"\n{'='*60}")
        print(f"🎮 GENERATION {generation + 1} | Best: {best_distance}px")
        print(f"{'='*60}")

    @staticmethod
    def log_generation_end(summary: dict, fitness: float, best_distance: int, best_fitness: float):
        """
        Log generation end with summary.

        Args:
            summary: Generation summary dict
            fitness: Fitness achieved this generation
            best_distance: All-time best distance
            best_fitness: All-time best fitness
        """
        generation = summary['generation']
        distance = summary['distance']
        frames = summary['frames']
        cause = summary['death_cause']

        death_messages = {
            'enemy': '💀 Hit an enemy',
            'stuck': '🚫 Got stuck',
            'timeout': '⏰ Time ran out'
        }
        death_msg = death_messages.get(cause, '❌ Unknown')

        print(f"\n📊 Generation {generation + 1} complete:")
        print(f"   Distance: {distance}px, Fitness: {fitness:.1f}")
        print(f"   Frames: {frames}, Cause: {death_msg}")
        print(f"   Best Distance: {best_distance}px, Best Fitness: {best_fitness:.1f}")

    @staticmethod
    def log_new_champion(distance: int, fitness: float):
        """Log new champion found."""
        print(f"\n🏆 NEW CHAMPION! Distance: {distance}px, Fitness: {fitness:.1f}")
        print(f"💾 Saved champion weights")

    @staticmethod
    def log_restore_champion(best_distance: int):
        """Log champion restoration."""
        print(f"🔄 Restoring champion (best: {best_distance}px)")

    @staticmethod
    def log_progress(frames: int, current_x: int, max_x: int, max_frames: int):
        """Log periodic progress."""
        print(f"🎮 Frame {frames}/{max_frames}, X: {current_x}, Max: {max_x}")

    @staticmethod
    def log_stuck_vision(vision_string: str, context_features=None):
        """Log vision when stuck (for debugging)."""
        print(f"\n👁️ Vision at stuck position:")
        print(vision_string)
        if context_features:
            print(f"🎯 Context features: {context_features}")
