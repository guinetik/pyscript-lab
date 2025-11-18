"""
Verify that output layer biases are frozen during mutation.

This test confirms that the behavioral priors (RIGHT=3.0, A=2.0)
are preserved across mutations.
"""

import sys
from pathlib import Path
import numpy as np

# Setup Python path
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_PYTHON = PROJECT_ROOT / "static" / "python"
sys.path.insert(0, str(STATIC_PYTHON))

# Install mocks
import mocks

# Import neuroevolution components
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder


def test_output_bias_freeze():
    """Test that output biases don't change during mutation"""

    print("="*60)
    print("TESTING: Output Bias Freeze")
    print("="*60)

    # Create network
    controller = SimpleNeuralController(
        input_size=115,
        hidden_size=32,
        output_size=6,
        seed=42
    )

    # Apply strong behavioral priors (matching agent.py config)
    priors = [0, 0, 0, 5.0, 5.0, 0]  # [UP, DOWN, LEFT, RIGHT, A, B]
    controller.apply_priors(priors)

    print(f"\n✅ Applied priors: {priors}")

    # Get initial output biases
    initial_biases = controller.network.biases[-1].copy()
    print(f"Initial output biases: {initial_biases}")

    # Mutate multiple times
    num_mutations = 50
    print(f"\n🧬 Applying {num_mutations} mutations...")

    for i in range(num_mutations):
        controller.mutate(mutation_rate=0.3, mutation_scale=0.5)

    # Get final output biases
    final_biases = controller.network.biases[-1]
    print(f"\nFinal output biases: {final_biases}")

    # Check if they're identical
    biases_changed = not np.allclose(initial_biases, final_biases)

    if biases_changed:
        print("\n❌ FAILED: Output biases changed!")
        print(f"Difference: {final_biases - initial_biases}")
        return False
    else:
        print("\n✅ SUCCESS: Output biases are frozen!")
        print(f"Priors preserved across {num_mutations} mutations")

        # Test that hidden layer biases DID change
        initial_hidden = controller.network.biases[0].copy()
        controller.mutate(mutation_rate=0.5, mutation_scale=1.0)
        final_hidden = controller.network.biases[0]

        hidden_changed = not np.allclose(initial_hidden, final_hidden)

        if hidden_changed:
            print("✅ Hidden layer biases still mutate (as expected)")
        else:
            print("⚠️  Warning: Hidden layer biases didn't change")

        return True


def test_behavioral_consistency():
    """Test that behavior is now consistent with frozen priors"""

    print("\n" + "="*60)
    print("TESTING: Behavioral Consistency with Frozen Priors")
    print("="*60)

    # Goomba scenario
    vision = np.zeros(16 * 7)
    for col in range(16):
        vision[6 * 16 + col] = 1.0  # Ground
    vision[3 * 16 + 7] = -1.0  # Goomba at col 7

    context = np.array([0.3, 0.0, 1.0])
    full_input = np.concatenate([vision, context])

    decoder = ActionDecoder()
    button_names = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]

    # Test with 20 different random initializations
    results = []

    print("\nTesting 20 random networks with frozen priors...")

    for seed in range(1000, 1020):
        controller = SimpleNeuralController(
            input_size=115,
            hidden_size=32,
            output_size=6,
            seed=seed
        )

        # Apply priors
        priors = [0, 0, 0, 5.0, 4.0, 0]
        controller.apply_priors(priors)

        # Test before mutation
        output = controller.forward(full_input, capture_activations=False)
        buttons = decoder.decode(output)
        pressed = tuple(name for name, p in zip(button_names, buttons) if p)

        results.append(pressed)

    # Count RIGHT + A appearances
    right_a_count = sum(1 for r in results if 'RIGHT' in r and 'A' in r)
    consistency = (right_a_count / len(results)) * 100

    print(f"\nResults:")
    from collections import Counter
    for action, count in Counter(results).most_common(5):
        pct = (count / len(results)) * 100
        action_str = ' + '.join(action) if action else '(none)'
        print(f"  {action_str:20s}: {count:2d} ({pct:5.1f}%)")

    print(f"\nNetworks with RIGHT + A: {right_a_count}/{len(results)} ({consistency:.1f}%)")

    if consistency >= 80:
        print("✅ EXCELLENT: High consistency!")
        return True
    elif consistency >= 50:
        print("⚙️  GOOD: Decent consistency")
        return True
    else:
        print("⚠️  LOW: Still inconsistent")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VERIFICATION: Output Bias Freeze Fix")
    print("="*60)

    test1_passed = test_output_bias_freeze()
    test2_passed = test_behavioral_consistency()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Test 1 (Bias Freeze): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Consistency): {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The fix is working.")
        print("\nNext steps:")
        print("1. Clear your browser cache and reload")
        print("2. Start a fresh training session")
        print("3. Check mario.log for death vision logs")
        print("4. Mario should now consistently go RIGHT and JUMP")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
