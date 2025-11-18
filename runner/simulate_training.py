"""
Multi-Run Simulator - Test network behavior consistency

Run the same scenario multiple times to understand:
1. How random initialization affects behavior
2. Variance in mutation effects
3. Probability of certain actions for given inputs

This helps debug why the network is so inconsistent (312px vs 1528px).
"""

import sys
from pathlib import Path
import numpy as np
from datetime import datetime
from collections import Counter

# Setup Python path
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_PYTHON = PROJECT_ROOT / "static" / "python"
sys.path.insert(0, str(STATIC_PYTHON))

# Install mocks
import mocks

# Import neuroevolution components
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder
from lib.evolution.strategy import OnePlusOneES
from lib.evolution.fitness import MarioFitnessCalculator


class SimulationResults:
    """Track simulation results across runs"""

    def __init__(self):
        self.runs = []
        self.button_counts = Counter()
        self.action_sequences = []

    def add_run(self, seed, scenario_name, buttons, output):
        """Record a single run"""
        button_names = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]
        pressed = tuple(name for name, p in zip(button_names, buttons) if p)

        self.runs.append({
            'seed': seed,
            'scenario': scenario_name,
            'buttons': pressed,
            'output': output.copy()
        })

        self.button_counts[pressed] += 1
        self.action_sequences.append(pressed)

    def summary(self):
        """Generate summary statistics"""
        total_runs = len(self.runs)

        print(f"\n{'='*60}")
        print(f"SIMULATION SUMMARY ({total_runs} runs)")
        print(f"{'='*60}")

        # Action distribution
        print("\nAction distribution:")
        for action, count in self.button_counts.most_common():
            pct = (count / total_runs) * 100
            action_str = ' + '.join(action) if action else '(no buttons)'
            bar = "█" * int(pct / 5)
            print(f"  {action_str:20s}: {count:3d} ({pct:5.1f}%) {bar}")

        # Consistency metrics
        most_common_action = self.button_counts.most_common(1)[0]
        consistency = (most_common_action[1] / total_runs) * 100

        print(f"\nConsistency:")
        print(f"  Most common action: {' + '.join(most_common_action[0]) if most_common_action[0] else '(none)'}")
        print(f"  Appears in: {most_common_action[1]}/{total_runs} runs ({consistency:.1f}%)")

        if consistency < 50:
            print(f"  ⚠️  LOW CONSISTENCY - Network is very random!")
        elif consistency < 80:
            print(f"  ⚙️  MODERATE CONSISTENCY")
        else:
            print(f"  ✅ HIGH CONSISTENCY")

        # Output variance
        outputs = np.array([r['output'] for r in self.runs])
        mean_output = outputs.mean(axis=0)
        std_output = outputs.std(axis=0)

        print(f"\nOutput statistics (across {total_runs} runs):")
        button_names = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]
        for i, name in enumerate(button_names):
            print(f"  {name:>5}: mean={mean_output[i]:.3f}, std={std_output[i]:.3f}")

        return {
            'total_runs': total_runs,
            'consistency': consistency,
            'action_distribution': dict(self.button_counts),
            'mean_output': mean_output,
            'std_output': std_output
        }


def run_scenario_multiple_times(scenario_name, vision, context, num_runs=100, apply_priors=False):
    """
    Run the same scenario multiple times with different random initializations.

    Args:
        scenario_name: Name of the scenario
        vision: Vision grid
        context: Context features
        num_runs: Number of times to run
        apply_priors: Whether to apply behavioral priors

    Returns:
        SimulationResults object
    """
    print(f"\n{'='*60}")
    print(f"RUNNING SIMULATION: {scenario_name}")
    print(f"{'='*60}")
    print(f"Num runs: {num_runs}")
    print(f"Behavioral priors: {'YES' if apply_priors else 'NO'}")
    print()

    results = SimulationResults()
    decoder = ActionDecoder()

    # Combine vision + context
    full_input = np.concatenate([vision, context])

    input_size = 16 * 7 + 3
    hidden_size = 32
    output_size = 6

    for run_idx in range(num_runs):
        # Create fresh network with different seed
        seed = 1000 + run_idx
        controller = SimpleNeuralController(
            input_size=input_size,
            hidden_size=hidden_size,
            output_size=output_size,
            seed=seed
        )

        # Apply priors if requested (matching agent.py config)
        if apply_priors:
            priors = [0, 0, 0, 5.0, 5.0, 0]  # [UP, DOWN, LEFT, RIGHT, A, B]
            controller.apply_priors(priors)

        # Forward pass
        output = controller.forward(full_input, capture_activations=False)
        buttons = decoder.decode(output)

        # Record result
        results.add_run(seed, scenario_name, buttons, output)

        # Progress indicator
        if (run_idx + 1) % 20 == 0:
            print(f"  Progress: {run_idx + 1}/{num_runs} runs...")

    # Print summary
    stats = results.summary()

    return results, stats


def test_goomba_consistency():
    """Test: Does the network consistently respond to the first Goomba?"""

    print("\n" + "="*60)
    print("TEST: Goomba Response Consistency")
    print("="*60)
    print("\nQuestion: Does the network react to a Goomba 3 tiles ahead?")
    print("Expected: RIGHT + A (run right and jump)")
    print()

    # Build scenario
    vision = np.zeros(16 * 7)
    # Add ground
    for col in range(16):
        vision[6 * 16 + col] = 1.0
    # Add Goomba 3 tiles ahead (Mario at col 4, Goomba at col 7)
    mario_row = 3
    goomba_col = 4 + 3
    vision[mario_row * 16 + goomba_col] = -1.0

    context = np.array([0.3, 0.0, 1.0])  # Enemy close, on ground, no pit

    # Test WITHOUT priors
    print("\n" + "-"*60)
    print("WITHOUT BEHAVIORAL PRIORS")
    print("-"*60)
    results_no_priors, stats_no_priors = run_scenario_multiple_times(
        "Goomba 3 tiles ahead (no priors)",
        vision,
        context,
        num_runs=100,
        apply_priors=False
    )

    # Test WITH priors
    print("\n" + "-"*60)
    print("WITH BEHAVIORAL PRIORS (RIGHT=3.0, A=2.0)")
    print("-"*60)
    results_with_priors, stats_with_priors = run_scenario_multiple_times(
        "Goomba 3 tiles ahead (with priors)",
        vision,
        context,
        num_runs=100,
        apply_priors=True
    )

    # Compare
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    print(f"\nWithout priors:")
    print(f"  Consistency: {stats_no_priors['consistency']:.1f}%")
    print(f"\nWith priors:")
    print(f"  Consistency: {stats_with_priors['consistency']:.1f}%")

    improvement = stats_with_priors['consistency'] - stats_no_priors['consistency']
    print(f"\nPriors improve consistency by: {improvement:+.1f}%")

    return results_no_priors, results_with_priors


def test_mutation_effects():
    """Test: How does mutation change behavior?"""

    print("\n" + "="*60)
    print("TEST: Mutation Effect on Behavior")
    print("="*60)
    print("\nQuestion: Does mutation change actions significantly?")
    print()

    # Create baseline network
    input_size = 16 * 7 + 3
    hidden_size = 32
    output_size = 6

    controller = SimpleNeuralController(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        seed=42
    )

    decoder = ActionDecoder()

    # Test scenario: Goomba ahead
    vision = np.zeros(16 * 7)
    for col in range(16):
        vision[6 * 16 + col] = 1.0
    vision[3 * 16 + 7] = -1.0  # Goomba

    context = np.array([0.3, 0.0, 1.0])
    full_input = np.concatenate([vision, context])

    # Test multiple mutation strengths
    mutation_configs = [
        (0.05, 0.1, "Low"),
        (0.15, 0.3, "Medium"),
        (0.30, 0.5, "High"),
        (0.50, 0.8, "Very High"),
    ]

    results = []

    for mut_rate, mut_scale, label in mutation_configs:
        print(f"\n{'-'*60}")
        print(f"Mutation: {label} (rate={mut_rate}, scale={mut_scale})")
        print(f"{'-'*60}")

        # Save original weights
        original_weights = controller.get_weights()

        # Test before mutation
        output_before = controller.forward(full_input, capture_activations=False)
        buttons_before = decoder.decode(output_before)

        # Count behavior changes
        behavior_changes = 0
        for trial in range(50):
            # Restore original
            controller.set_weights(
                original_weights['weights'],
                original_weights['biases']
            )

            # Mutate
            controller.mutate(mutation_rate=mut_rate, mutation_scale=mut_scale)

            # Test after mutation
            output_after = controller.forward(full_input, capture_activations=False)
            buttons_after = decoder.decode(output_after)

            # Check if behavior changed
            if not np.array_equal(buttons_before, buttons_after):
                behavior_changes += 1

        change_rate = (behavior_changes / 50) * 100
        print(f"  Behavior changed in: {behavior_changes}/50 trials ({change_rate:.1f}%)")

        results.append({
            'label': label,
            'mutation_rate': mut_rate,
            'mutation_scale': mut_scale,
            'change_rate': change_rate
        })

    # Summary
    print(f"\n{'='*60}")
    print("MUTATION SUMMARY")
    print(f"{'='*60}")
    for r in results:
        print(f"  {r['label']:10s}: {r['change_rate']:5.1f}% behavior change")

    return results


def main():
    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(__file__).parent / f"simulation_{timestamp}.log"

    print(f"\n{'='*60}")
    print("MULTI-RUN SIMULATOR")
    print(f"{'='*60}")
    print(f"Logging to: {log_path}")

    # Redirect print to file
    import sys
    original_stdout = sys.stdout
    log_file = open(log_path, 'w')

    class DualOutput:
        def __init__(self, *files):
            self.files = files

        def write(self, text):
            for f in self.files:
                f.write(text)
                f.flush()

        def flush(self):
            for f in self.files:
                f.flush()

    sys.stdout = DualOutput(original_stdout, log_file)

    try:
        # Run tests
        test_goomba_consistency()
        test_mutation_effects()

        print(f"\n{'='*60}")
        print("✅ SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"\n📄 Full log saved to: {log_path}")

    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == "__main__":
    main()
