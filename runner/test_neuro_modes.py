"""
Regression tests for Mario neuroevolution training modes.

These tests validate the intended behavior for:
1. `simple` mode matching the reference project's random initialization.
2. `optimize` mode using reference weights when available.
3. `optimize` mode falling back cleanly to `simple` when unavailable.
4. `sbx` and `uniform` breeding every generation for non-champion slots.
"""

import sys
import unittest
from pathlib import Path

import numpy as np


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).parent.parent
STATIC_PYTHON = PROJECT_ROOT / "static" / "python"
sys.path.insert(0, str(STATIC_PYTHON))

import mocks  # noqa: F401  # Installs browser/PyScript mocks on import.
from js import window

from ml.neuro.agent import Population
from ml.neuro.trainer import Trainer


class ReferenceWeights:
    """Container that mimics the JS object shape used by PyScript."""

    def __init__(self, W1, b1, W2, b2):
        self.W1 = W1
        self.b1 = b1
        self.W2 = W2
        self.b2 = b2


class DummyNES:
    """Minimal stand-in for the JS headless NES wrapper."""

    @staticmethod
    def getMarioX():
        """Return a stable starting X value for trainer initialization."""
        return 0


class DummyPool:
    """Minimal pool that satisfies the trainer initialization contract."""

    def initialize(self, rom_data, initial_state):
        """Accept ROM/state input without doing any browser work."""
        self.rom_data = rom_data
        self.initial_state = initial_state

    @staticmethod
    def getInstance(index):
        """Return a dummy emulator instance for initialization checks."""
        del index
        return DummyNES()


class NeuroModeTests(unittest.TestCase):
    """Regression tests for `simple` and `optimize` mode behavior."""

    def setUp(self):
        """Reset the mocked browser state before each test."""
        np.random.seed(1234)
        window._referenceWeights = None
        window._trainingRomData = "rom"
        window._trainingInitialState = {"state": "ok"}
        window.createHeadlessNESPool = lambda size: DummyPool()

    def test_simple_mode_uses_fully_random_biases(self):
        """`simple` mode should not reuse fixed reference biases."""
        population = Population(size=2, mode=Population.MODE_SIMPLE)
        population.initialize()

        self.assertFalse(
            np.allclose(population.agents[0].b1, population.agents[1].b1),
            "simple mode should randomize hidden biases per agent",
        )
        self.assertFalse(
            np.allclose(population.agents[0].b2, population.agents[1].b2),
            "simple mode should randomize output biases per agent",
        )

    def test_optimize_mode_loads_reference_weights(self):
        """`optimize` mode should seed the first agent with exact reference weights."""
        reference = ReferenceWeights(
            W1=[[0.1] * 80 for _ in range(9)],
            b1=[0.2] * 9,
            W2=[[0.3] * 9 for _ in range(6)],
            b2=[0.4] * 6,
        )
        window._referenceWeights = reference

        population = Population(size=2, mode=Population.MODE_OPTIMIZE)
        population.initialize()

        self.assertTrue(np.allclose(population.agents[0].W1, np.array(reference.W1)))
        self.assertTrue(np.allclose(population.agents[0].b1, np.array(reference.b1)))
        self.assertTrue(np.allclose(population.agents[0].W2, np.array(reference.W2)))
        self.assertTrue(np.allclose(population.agents[0].b2, np.array(reference.b2)))

    def test_optimize_fallback_updates_trainer_mode(self):
        """Trainer state should match population state after optimize fallback."""
        trainer = Trainer()
        initialized = trainer.initialize("rom", {"state": "ok"}, mode=Population.MODE_OPTIMIZE)

        self.assertTrue(initialized)
        self.assertEqual(
            trainer.population.mode,
            Population.MODE_SIMPLE,
            "population should fall back to simple mode when references are unavailable",
        )
        self.assertEqual(
            trainer.mode,
            Population.MODE_SIMPLE,
            "trainer mode should stay in sync with the population fallback mode",
        )

    def test_sbx_preserves_only_champion_and_breeds_other_slots(self):
        """SBX mode should preserve only slot 0 and breed every other slot."""
        population = Population(size=6, mode=Population.MODE_SBX)
        population.initialize()

        champion_weights = population.agents[0].get_weights()
        for idx, agent in enumerate(population.agents):
            agent.fitness = 100 - idx

        population.evolve()

        self.assertEqual(population.last_generation_events[0]["operator"], "preserve")
        self.assertTrue(population.last_generation_events[0]["preserved"])
        for event in population.last_generation_events[1:]:
            self.assertEqual(event["operator"], Population.MODE_SBX)
            self.assertEqual(len(event["parent_slots"]), 2)
            self.assertTrue(event["mutated"])

        self.assertTrue(np.allclose(population.agents[0].W1, np.array(champion_weights["W1"])))
        self.assertTrue(np.allclose(population.agents[0].b1, np.array(champion_weights["b1"])))
        self.assertTrue(np.allclose(population.agents[0].W2, np.array(champion_weights["W2"])))
        self.assertTrue(np.allclose(population.agents[0].b2, np.array(champion_weights["b2"])))

    def test_uniform_preserves_only_champion_and_breeds_other_slots(self):
        """Uniform mode should preserve only slot 0 and breed every other slot."""
        population = Population(size=6, mode=Population.MODE_UNIFORM)
        population.initialize()

        champion_weights = population.agents[0].get_weights()
        for idx, agent in enumerate(population.agents):
            agent.fitness = 100 - idx

        population.evolve()

        self.assertEqual(population.last_generation_events[0]["operator"], "preserve")
        self.assertTrue(population.last_generation_events[0]["preserved"])
        for event in population.last_generation_events[1:]:
            self.assertEqual(event["operator"], Population.MODE_UNIFORM)
            self.assertEqual(len(event["parent_slots"]), 2)
            self.assertTrue(event["mutated"])

        self.assertTrue(np.allclose(population.agents[0].W1, np.array(champion_weights["W1"])))
        self.assertTrue(np.allclose(population.agents[0].b1, np.array(champion_weights["b1"])))
        self.assertTrue(np.allclose(population.agents[0].W2, np.array(champion_weights["W2"])))
        self.assertTrue(np.allclose(population.agents[0].b2, np.array(champion_weights["b2"])))


if __name__ == "__main__":
    unittest.main()
