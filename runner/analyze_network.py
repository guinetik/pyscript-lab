"""
Neural Network Debugger - Analyze what the network sees and does

This tool lets you:
1. Feed specific vision patterns to see what the network outputs
2. Visualize neuron activations for different scenarios
3. Test behavioral priors and mutations
4. Debug why Mario keeps dying at the first Goomba

Input structure (115 dimensions):
- Vision grid: 16×7 = 112 values
  - 0.0 = empty/air
  - 1.0 = solid block/ground
  - -1.0 = enemy (Goomba, Koopa, etc.)
  - Layout: 4 tiles behind Mario, 11 tiles ahead
  - Vertical: 3 above, 1 current row, 3 below

- Context features: 3 values (reduced from 9)
  - [enemy_dist, ground_dist, pit_dist] normalized 0-1

Output (6 buttons):
- [UP, DOWN, LEFT, RIGHT, A, B]
- Values are sigmoid activations (0-1)
- Decoded to binary: > 0.5 = pressed
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime

# Setup Python path
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_PYTHON = PROJECT_ROOT / "static" / "python"
sys.path.insert(0, str(STATIC_PYTHON))

# Install mocks
import mocks

# Import neuroevolution components
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder


# Global log file
LOG_FILE = None


def log_print(*args, **kwargs):
    """Print to both console and log file"""
    print(*args, **kwargs)
    if LOG_FILE:
        print(*args, **kwargs, file=LOG_FILE)
        LOG_FILE.flush()


class VisionBuilder:
    """Helper to build vision grids for testing"""

    WIDTH = 16
    HEIGHT = 7

    @staticmethod
    def empty():
        """Empty vision - just air"""
        return np.zeros(VisionBuilder.WIDTH * VisionBuilder.HEIGHT)

    @staticmethod
    def flat_ground():
        """Flat ground below Mario"""
        vision = np.zeros(VisionBuilder.WIDTH * VisionBuilder.HEIGHT)
        # Bottom row is ground
        bottom_row_start = (VisionBuilder.HEIGHT - 1) * VisionBuilder.WIDTH
        vision[bottom_row_start:] = 1.0
        return vision

    @staticmethod
    def goomba_ahead(distance_tiles=3):
        """Enemy ahead at specified distance"""
        vision = VisionBuilder.flat_ground()

        # Mario is at column 4 (0-indexed), row 3 (middle)
        mario_col = 4
        mario_row = 3

        # Place enemy ahead
        enemy_col = mario_col + distance_tiles
        if 0 <= enemy_col < VisionBuilder.WIDTH:
            idx = mario_row * VisionBuilder.WIDTH + enemy_col
            vision[idx] = -1.0

        return vision

    @staticmethod
    def pit_ahead(distance_tiles=5, width_tiles=2):
        """Pit ahead at specified distance"""
        vision = VisionBuilder.flat_ground()

        mario_col = 4

        # Remove ground for pit
        for offset in range(width_tiles):
            col = mario_col + distance_tiles + offset
            if 0 <= col < VisionBuilder.WIDTH:
                # Remove bottom rows for pit
                for row in range(VisionBuilder.HEIGHT - 3, VisionBuilder.HEIGHT):
                    idx = row * VisionBuilder.WIDTH + col
                    vision[idx] = 0.0

        return vision

    @staticmethod
    def obstacle_ahead(distance_tiles=4, height_tiles=2):
        """Obstacle/block ahead"""
        vision = VisionBuilder.flat_ground()

        mario_col = 4
        mario_row = 3

        # Place blocks
        for h in range(height_tiles):
            col = mario_col + distance_tiles
            row = mario_row - h
            if 0 <= col < VisionBuilder.WIDTH and 0 <= row < VisionBuilder.HEIGHT:
                idx = row * VisionBuilder.WIDTH + col
                vision[idx] = 1.0

        return vision

    @staticmethod
    def goomba_very_close(distance_tiles=1):
        """Enemy VERY close - immediate danger"""
        return VisionBuilder.goomba_ahead(distance_tiles)

    @staticmethod
    def two_goombas_ahead():
        """Two enemies in a row"""
        vision = VisionBuilder.flat_ground()
        mario_col = 4
        mario_row = 3

        # First Goomba at distance 3
        idx1 = mario_row * VisionBuilder.WIDTH + (mario_col + 3)
        vision[idx1] = -1.0

        # Second Goomba at distance 6
        idx2 = mario_row * VisionBuilder.WIDTH + (mario_col + 6)
        vision[idx2] = -1.0

        return vision

    @staticmethod
    def goomba_on_platform():
        """Goomba walking on a platform above"""
        vision = VisionBuilder.flat_ground()
        mario_col = 4
        mario_row = 3

        # Platform 2 tiles above Mario
        platform_row = mario_row - 2
        for col_offset in range(3, 8):
            col = mario_col + col_offset
            if 0 <= col < VisionBuilder.WIDTH:
                idx = platform_row * VisionBuilder.WIDTH + col
                vision[idx] = 1.0

        # Goomba on platform
        enemy_col = mario_col + 5
        enemy_row = platform_row
        idx = enemy_row * VisionBuilder.WIDTH + enemy_col
        vision[idx] = -1.0

        return vision

    @staticmethod
    def staircase_ahead():
        """Ascending blocks"""
        vision = VisionBuilder.flat_ground()
        mario_col = 4
        mario_row = 3

        # Create stairs going up
        for step in range(1, 5):
            col = mario_col + 2 + step
            # Build column of blocks
            for h in range(step):
                row = mario_row + 2 - h
                if 0 <= col < VisionBuilder.WIDTH and 0 <= row < VisionBuilder.HEIGHT:
                    idx = row * VisionBuilder.WIDTH + col
                    vision[idx] = 1.0

        return vision

    @staticmethod
    def falling_no_ground():
        """Mario is falling - no ground below"""
        vision = np.zeros(VisionBuilder.WIDTH * VisionBuilder.HEIGHT)
        # No ground at all
        return vision

    @staticmethod
    def visualize(vision):
        """Print ASCII visualization of vision grid"""
        log_print("\n" + "="*50)
        log_print("VISION GRID (Mario's view)")
        log_print("="*50)
        log_print("Legend: . = empty, # = solid, E = enemy, M = Mario")
        log_print()

        for row in range(VisionBuilder.HEIGHT):
            line = ""
            for col in range(VisionBuilder.WIDTH):
                idx = row * VisionBuilder.WIDTH + col
                value = vision[idx]

                # Mario is at col 4, row 3
                if col == 4 and row == 3:
                    line += "M "
                elif value == -1.0:
                    line += "E "
                elif value == 1.0:
                    line += "# "
                else:
                    line += ". "

            # Row labels
            if row == 0:
                line += "  (3 above)"
            elif row == 3:
                line += "  (Mario row)"
            elif row == 6:
                line += "  (3 below)"

            log_print(line)

        log_print()
        log_print("Horizontal: 4 tiles behind ← M → 11 tiles ahead")
        log_print("="*50)


def test_scenario(controller, decoder, scenario_name, vision, context, expected_action=None):
    """Test a specific scenario and show results"""
    log_print(f"\n{'='*60}")
    log_print(f"SCENARIO: {scenario_name}")
    log_print(f"{'='*60}")

    # Visualize input
    VisionBuilder.visualize(vision)

    # Show context features
    log_print(f"Context features:")
    log_print(f"  Enemy distance: {context[0]:.2f}")
    log_print(f"  Ground distance: {context[1]:.2f}")
    log_print(f"  Pit distance: {context[2]:.2f}")
    log_print()

    # Combine vision + context
    full_input = np.concatenate([vision, context])

    # Forward pass
    output = controller.forward(full_input, capture_activations=True)

    # Decode buttons
    buttons = decoder.decode(output)
    button_names = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]

    log_print(f"Network output (raw activations):")
    for name, val in zip(button_names, output):
        bar = "█" * int(val * 20)
        log_print(f"  {name:>5}: {val:.3f} {bar}")
    log_print()

    log_print(f"Button presses (decoded):")
    pressed = [name for name, pressed in zip(button_names, buttons) if pressed]
    if pressed:
        action_str = ' + '.join(pressed)
        log_print(f"  {action_str}")

        # Check if matches expected
        if expected_action:
            if action_str == expected_action:
                log_print(f"  ✅ CORRECT (expected: {expected_action})")
            else:
                log_print(f"  ❌ WRONG (expected: {expected_action})")
    else:
        log_print(f"  (no buttons pressed)")
        if expected_action:
            log_print(f"  ❌ WRONG (expected: {expected_action})")
    log_print()

    # Show hidden layer activations
    if hasattr(controller.network, 'layer_activations'):
        activations = controller.network.layer_activations
        log_print(f"Hidden layer activations (32 neurons):")
        hidden = activations[1]  # Layer 1 is hidden layer
        active_count = np.sum(hidden > 0.1)
        log_print(f"  Active neurons: {active_count}/32")
        log_print(f"  Mean activation: {hidden.mean():.3f}")
        log_print(f"  Max activation: {hidden.max():.3f}")
        log_print()


def analyze_behavioral_priors(controller, decoder):
    """Test what behavioral priors do"""
    log_print("\n" + "="*60)
    log_print("BEHAVIORAL PRIORS ANALYSIS")
    log_print("="*60)

    # Apply strong priors toward RIGHT+JUMP
    priors = [0, 0, 0, 3.0, 2.0, 0]  # [UP, DOWN, LEFT, RIGHT, A, B]
    controller.apply_priors(priors)

    log_print("Applied priors: RIGHT=3.0, A=2.0 (bias toward running right and jumping)")
    log_print()

    # Test with empty input
    vision = VisionBuilder.empty()
    context = np.array([1.0, 0.0, 1.0])  # No enemy, on ground, no pit

    test_scenario(
        controller,
        decoder,
        "EMPTY SPACE (testing priors)",
        vision,
        context,
        expected_action="RIGHT + A"
    )


def test_mutation_effects(controller, decoder):
    """Test how mutation changes behavior"""
    log_print("\n" + "="*60)
    log_print("MUTATION EFFECT ANALYSIS")
    log_print("="*60)

    # Test scenario: Goomba ahead
    vision = VisionBuilder.goomba_ahead(distance_tiles=3)
    context = np.array([0.3, 0.0, 1.0])

    log_print("Testing same scenario before and after mutation...\n")

    # Before mutation
    log_print("BEFORE MUTATION:")
    full_input = np.concatenate([vision, context])
    output_before = controller.forward(full_input, capture_activations=False)
    buttons_before = decoder.decode(output_before)
    button_names = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]
    pressed_before = [name for name, pressed in zip(button_names, buttons_before) if pressed]
    log_print(f"  Buttons: {' + '.join(pressed_before) if pressed_before else '(none)'}")
    log_print(f"  Raw: {output_before}")

    # Apply mutation
    log_print("\nApplying mutation (rate=0.2, scale=0.5)...")
    controller.mutate(mutation_rate=0.2, mutation_scale=0.5)

    # After mutation
    log_print("\nAFTER MUTATION:")
    output_after = controller.forward(full_input, capture_activations=False)
    buttons_after = decoder.decode(output_after)
    pressed_after = [name for name, pressed in zip(button_names, buttons_after) if pressed]
    log_print(f"  Buttons: {' + '.join(pressed_after) if pressed_after else '(none)'}")
    log_print(f"  Raw: {output_after}")

    # Compare
    log_print("\nCHANGE:")
    output_diff = np.abs(output_after - output_before)
    log_print(f"  Avg output change: {output_diff.mean():.4f}")
    log_print(f"  Max output change: {output_diff.max():.4f}")
    if pressed_before != pressed_after:
        log_print(f"  ✨ BEHAVIOR CHANGED!")
    else:
        log_print(f"  ⚠️  Behavior unchanged (same buttons)")
    log_print()


def main():
    global LOG_FILE

    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(__file__).parent / f"analysis_{timestamp}.log"
    LOG_FILE = open(log_path, 'w')

    log_print("\n" + "="*60)
    log_print("MARIO NEURAL NETWORK DEBUGGER")
    log_print("="*60)
    log_print(f"Logging to: {log_path}")

    # Create network
    input_size = 16 * 7 + 3  # Vision grid + context features
    hidden_size = 32
    output_size = 6

    controller = SimpleNeuralController(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        seed=42  # Fixed seed for reproducible results
    )

    decoder = ActionDecoder()

    # Test scenarios
    log_print("\n🎮 Testing different scenarios...")

    # Scenario 1: Flat ground, nothing ahead
    test_scenario(
        controller,
        decoder,
        "FLAT GROUND - Clear path",
        VisionBuilder.flat_ground(),
        np.array([1.0, 0.0, 1.0]),
        expected_action="RIGHT"
    )

    # Scenario 2: Goomba close ahead (THE CRITICAL 315px DEATH!)
    test_scenario(
        controller,
        decoder,
        "GOOMBA 3 TILES AHEAD - Should jump!",
        VisionBuilder.goomba_ahead(distance_tiles=3),
        np.array([0.3, 0.0, 1.0]),
        expected_action="RIGHT + A"
    )

    # Scenario 3: Goomba VERY close - immediate danger
    test_scenario(
        controller,
        decoder,
        "GOOMBA 1 TILE AHEAD - EMERGENCY JUMP!",
        VisionBuilder.goomba_very_close(distance_tiles=1),
        np.array([0.1, 0.0, 1.0]),
        expected_action="RIGHT + A"
    )

    # Scenario 4: Two Goombas in a row
    test_scenario(
        controller,
        decoder,
        "TWO GOOMBAS - Multiple threats",
        VisionBuilder.two_goombas_ahead(),
        np.array([0.3, 0.0, 1.0]),
        expected_action="RIGHT + A"
    )

    # Scenario 5: Pit ahead
    test_scenario(
        controller,
        decoder,
        "PIT 5 TILES AHEAD - Should jump over",
        VisionBuilder.pit_ahead(distance_tiles=5, width_tiles=2),
        np.array([1.0, 0.8, 0.2]),
        expected_action="RIGHT + A"
    )

    # Scenario 6: Obstacle ahead
    test_scenario(
        controller,
        decoder,
        "OBSTACLE 4 TILES AHEAD - Should jump",
        VisionBuilder.obstacle_ahead(distance_tiles=4, height_tiles=2),
        np.array([1.0, 0.0, 1.0]),
        expected_action="RIGHT + A"
    )

    # Scenario 7: Goomba on platform above
    test_scenario(
        controller,
        decoder,
        "GOOMBA ON PLATFORM ABOVE - Can ignore or jump on",
        VisionBuilder.goomba_on_platform(),
        np.array([0.5, 0.0, 1.0]),
        expected_action="RIGHT"
    )

    # Scenario 8: Staircase
    test_scenario(
        controller,
        decoder,
        "STAIRCASE AHEAD - Should climb",
        VisionBuilder.staircase_ahead(),
        np.array([1.0, 0.0, 1.0]),
        expected_action="RIGHT + A"
    )

    # Scenario 9: Falling (no ground)
    test_scenario(
        controller,
        decoder,
        "FALLING - No ground below",
        VisionBuilder.falling_no_ground(),
        np.array([1.0, 1.0, 0.0]),
        expected_action="RIGHT"
    )

    # Test behavioral priors
    analyze_behavioral_priors(controller, decoder)

    # Test mutation effects
    # Create fresh network for mutation test
    controller_fresh = SimpleNeuralController(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        seed=42
    )
    test_mutation_effects(controller_fresh, decoder)

    log_print("\n" + "="*60)
    log_print("✅ ANALYSIS COMPLETE")
    log_print("="*60)
    log_print(f"\n📄 Full log saved to: {log_path}")
    log_print("\nKey findings:")
    log_print("1. Check if network goes LEFT instead of RIGHT (wrong direction)")
    log_print("2. Check if behavioral priors (RIGHT=3.0, A=2.0) fix the issue")
    log_print("3. Verify mutation changes behavior enough to escape local optima")
    log_print("\nNext steps:")
    log_print("1. Load trained weights from browser and analyze")
    log_print("2. Compare untrained vs trained network behavior")
    log_print("3. Identify which neurons respond to enemies")

    LOG_FILE.close()


if __name__ == "__main__":
    main()
