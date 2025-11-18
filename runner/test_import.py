"""
Test runner to verify neuroevolution code can load headless.

This script tests that we can import and instantiate the Mario agent
classes without PyScript/browser dependencies.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_PYTHON = PROJECT_ROOT / "static" / "python"
sys.path.insert(0, str(STATIC_PYTHON))

# Install browser API mocks BEFORE importing agent code
print("=" * 60)
print("🔧 Installing browser API mocks...")
print("=" * 60)
import mocks  # This auto-installs the mocks

# Now try importing the agent modules
print("\n" + "=" * 60)
print("📦 Importing neuroevolution modules...")
print("=" * 60)

try:
    # Import core modules
    from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder
    print("✅ Imported SimpleNeuralController and ActionDecoder")

    from lib.evolution.strategy import OnePlusOneES
    print("✅ Imported OnePlusOneES evolution strategy")

    from lib.evolution.fitness import MarioFitnessCalculator
    print("✅ Imported MarioFitnessCalculator")

    from lib.evolution.generation import GenerationManager, GenerationLogger
    print("✅ Imported GenerationManager and GenerationLogger")

    # Test instantiation
    print("\n" + "=" * 60)
    print("🧪 Testing class instantiation...")
    print("=" * 60)

    # Create a simple neural controller
    input_size = 16 * 7 + 3  # Vision grid + context features
    hidden_size = 32
    output_size = 6  # 6 buttons

    neural_controller = SimpleNeuralController(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size
    )
    print(f"✅ Created SimpleNeuralController (input={input_size}, hidden={hidden_size}, output={output_size})")

    # Create action decoder
    action_decoder = ActionDecoder()
    print("✅ Created ActionDecoder")

    # Create evolution strategy
    evolution_strategy = OnePlusOneES(
        mutation_rate=0.15,
        mutation_scale=0.3
    )
    print("✅ Created OnePlusOneES evolution strategy")

    # Create fitness calculator
    fitness_calculator = MarioFitnessCalculator()
    print("✅ Created MarioFitnessCalculator")

    # Test a forward pass
    print("\n" + "=" * 60)
    print("🧠 Testing neural network forward pass...")
    print("=" * 60)

    import numpy as np
    test_input = np.random.randn(input_size)
    output = neural_controller.forward(test_input)
    print(f"✅ Forward pass successful: input shape {test_input.shape} -> output shape {output.shape}")
    print(f"   Output values: {output}")

    # Test action decoding
    buttons = action_decoder.decode(output)
    print(f"✅ Action decoder: {output} -> Buttons: {buttons}")

    # Test fitness calculation
    test_fitness = fitness_calculator.calculate({
        'distance': 500,
        'frames': 300,
        'score_gained': 100,
        'generation': 0
    })
    print(f"✅ Fitness calculation: {test_fitness:.2f}")

    # Test weight mutation
    print("\n" + "=" * 60)
    print("🧬 Testing weight mutation...")
    print("=" * 60)

    # Get original weights (returns dict with 'weights' and 'biases' keys)
    original_weights_dict = neural_controller.get_weights()
    original_weights = [w.copy() for w in original_weights_dict['weights']]
    original_biases = [b.copy() for b in original_weights_dict['biases']]

    # Apply mutation
    neural_controller.mutate(mutation_rate=0.1, mutation_scale=0.3)

    # Get new weights
    new_weights_dict = neural_controller.get_weights()
    new_weights = new_weights_dict['weights']
    new_biases = new_weights_dict['biases']

    # Calculate average weight change across all layers
    weight_changes = []
    for orig, new in zip(original_weights, new_weights):
        weight_changes.append(np.abs(new - orig).mean())
    avg_weight_change = np.mean(weight_changes)

    # Calculate average bias change
    bias_changes = []
    for orig, new in zip(original_biases, new_biases):
        bias_changes.append(np.abs(new - orig).mean())
    avg_bias_change = np.mean(bias_changes)

    print(f"✅ Mutation applied:")
    print(f"   Avg weight change: {avg_weight_change:.6f}")
    print(f"   Avg bias change: {avg_bias_change:.6f}")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✨ The neuroevolution code can run headless!")
    print("   Next step: Create a full training loop without the NES emulator dependency")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
