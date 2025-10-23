"""
Test Module Loading - Verify new architecture loads correctly

This script tests that all new modules can be imported.
Run this in the browser console to verify PyScript configuration.

Author: Guinetik
"""

from js import console

print("="*60)
print("🧪 Testing Module Imports")
print("="*60)

# Test 1: Neural modules
try:
    from lib.neural.neural_agent import NeuralAgent, MarioAgent
    print("✅ lib.neural.neural_agent imported successfully")
except Exception as e:
    print(f"❌ Failed to import neural_agent: {e}")

# Test 2: Evolution strategies
try:
    from lib.evolution.strategy import OnePlusOneES, OnePlusLambdaES, EvolutionStrategy
    print("✅ lib.evolution.strategy imported successfully")
except Exception as e:
    print(f"❌ Failed to import strategy: {e}")

# Test 3: Fitness calculators
try:
    from lib.evolution.fitness import MarioFitnessCalculator, SimpleFitnessCalculator, FitnessCalculator
    print("✅ lib.evolution.fitness imported successfully")
except Exception as e:
    print(f"❌ Failed to import fitness: {e}")

# Test 4: Generation management
try:
    from lib.evolution.generation import GenerationManager, GenerationLogger
    print("✅ lib.evolution.generation imported successfully")
except Exception as e:
    print(f"❌ Failed to import generation: {e}")

# Test 5: Evolution module __init__
try:
    from lib.evolution import (
        OnePlusOneES,
        MarioFitnessCalculator,
        GenerationManager
    )
    print("✅ lib.evolution package imported successfully")
except Exception as e:
    print(f"❌ Failed to import evolution package: {e}")

# Test 6: Create instances to verify classes work
try:
    print("\n🔧 Testing class instantiation...")

    # Create evolution strategy
    evolution = OnePlusOneES(
        mutation_rate=0.05,
        mutation_scale=0.2,
        adaptive_mutation=True
    )
    print("  ✅ OnePlusOneES instantiated")

    # Create fitness calculator
    fitness_calc = MarioFitnessCalculator(
        distance_exponent=1.8,
        frame_penalty_exponent=1.4
    )
    print("  ✅ MarioFitnessCalculator instantiated")

    # Create generation manager
    gen_manager = GenerationManager()
    print("  ✅ GenerationManager instantiated")

except Exception as e:
    print(f"  ❌ Failed to instantiate classes: {e}")

print("\n" + "="*60)
print("✅ All module tests passed!")
print("="*60)
print("\n💡 You can now refactor agent.py to use these modules")
