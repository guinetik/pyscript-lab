"""
Neural Network Agent for Mario AI
Handles network architecture, forward pass, and weight management.
"""

import numpy as np
from js import window, console

# Network architecture (matches reference)
INPUT_SIZE = 80   # 7x10 vision + 10 row encoding
HIDDEN_SIZE = 9
OUTPUT_SIZE = 6   # UP, DOWN, LEFT, RIGHT, A, B

# Button mapping to JSNes indices
# JSNes: A=0, B=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7
OUTPUT_TO_BUTTON = [4, 5, 6, 7, 0, 1]  # UP, DOWN, LEFT, RIGHT, A, B


class NeuralAgent:
    """Simple feedforward neural network agent."""

    def __init__(self):
        self.W1 = None  # (HIDDEN_SIZE, INPUT_SIZE)
        self.b1 = None  # (HIDDEN_SIZE,)
        self.W2 = None  # (OUTPUT_SIZE, HIDDEN_SIZE)
        self.b2 = None  # (OUTPUT_SIZE,)

        self.fitness = 0
        self.frames_alive = 0
        self.farthest_x = 0
        self.won = False  # Did agent complete the level?
        self.frames = 0   # Frames taken (for win time tracking)
        
    def init_random(self):
        """Initialize weights and biases like the reference project."""
        self.W1 = np.random.uniform(-1, 1, size=(HIDDEN_SIZE, INPUT_SIZE))
        self.W2 = np.random.uniform(-1, 1, size=(OUTPUT_SIZE, HIDDEN_SIZE))
        self.b1 = np.random.uniform(-1, 1, size=(HIDDEN_SIZE,))
        self.b2 = np.random.uniform(-1, 1, size=(OUTPUT_SIZE,))
        
    def copy_from(self, other):
        """Copy weights from another agent."""
        self.W1 = other.W1.copy()
        self.b1 = other.b1.copy()
        self.W2 = other.W2.copy()
        self.b2 = other.b2.copy()
        
    def mutate(self, rate=0.1, strength=0.5):
        """Mutate weights with given rate and strength.
        
        Uses gaussian mutation matching SuperMarioBros-AI.
        Clips values to [-1, 1] to keep weights bounded.
        """
        for param in [self.W1, self.b1, self.W2, self.b2]:
            mask = np.random.random(param.shape) < rate
            param[mask] += np.random.randn(*param.shape)[mask] * strength
            # Clip to [-1, 1] like SuperMarioBros-AI does
            np.clip(param, -1, 1, out=param)
            
    def get_weights(self):
        """Get weights as flat arrays for serialization."""
        return {
            'W1': self.W1.tolist(),
            'b1': self.b1.tolist(),
            'W2': self.W2.tolist(),
            'b2': self.b2.tolist()
        }
        
    def set_weights(self, weights):
        """Set weights from dict."""
        self.W1 = np.array(weights['W1'])
        self.b1 = np.array(weights['b1'])
        self.W2 = np.array(weights['W2'])
        self.b2 = np.array(weights['b2'])
        
    def forward(self, inputs):
        """Forward pass through network."""
        # Hidden layer with ReLU
        h = np.dot(self.W1, inputs) + self.b1
        h = np.maximum(0, h)  # ReLU
        
        # Output layer with sigmoid
        out = np.dot(self.W2, h) + self.b2
        out = 1.0 / (1.0 + np.exp(-np.clip(out, -500, 500)))  # Sigmoid
        
        return out
        
    def get_buttons(self, outputs, threshold=0.5):
        """Convert network outputs to button indices.
        
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        DO NOT REMOVE THE UP/DOWN FILTERING BELOW!
        This MUST match the filtering in src/lib/nes/Agent.js
        The reference weights and trained weights both depend on this.
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """
        buttons = []
        for i, val in enumerate(outputs):
            if val > threshold:
                btn = OUTPUT_TO_BUTTON[i]
                # CRITICAL: Skip UP (4) and DOWN (5) - DO NOT CHANGE
                if btn not in [4, 5]:
                    buttons.append(btn)
        return buttons
        
    def reset(self):
        """Reset runtime state for new episode."""
        self.fitness = 0
        self.frames_alive = 0
        self.farthest_x = 0
        self.won = False
        self.frames = 0
        
    def get_activations(self, inputs):
        """Get layer activations for visualization."""
        # Hidden layer
        h = np.dot(self.W1, inputs) + self.b1
        h_relu = np.maximum(0, h)
        
        # Output layer
        out = np.dot(self.W2, h_relu) + self.b2
        out_sigmoid = 1.0 / (1.0 + np.exp(-np.clip(out, -500, 500)))
        
        return {
            'layer_sizes': [INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE],
            'activations': [
                {'values': inputs.tolist(), 'active_count': int(np.sum(inputs != 0))},
                {'values': h_relu.tolist(), 'active_count': int(np.sum(h_relu > 0.1))},
                {'values': out_sigmoid.tolist(), 'active_count': int(np.sum(out_sigmoid > 0.5))}
            ],
            'num_params': INPUT_SIZE * HIDDEN_SIZE + HIDDEN_SIZE + HIDDEN_SIZE * OUTPUT_SIZE + OUTPUT_SIZE
        }


class Population:
    """Population of agents for evolutionary training.

    Supports multiple evolution modes:
    - 'simple': Preserve elites, mutate copies of strong performers
    - 'sbx': Preserve champion, breed every other slot with SBX + mutation
    - 'uniform': Preserve champion, breed every other slot with uniform crossover + mutation
    - 'optimize': Start from reference weights, then continue with mutation only
    """

    # Evolution mode constants
    MODE_SIMPLE = 'simple'
    MODE_SBX = 'sbx'
    MODE_UNIFORM = 'uniform'
    MODE_OPTIMIZE = 'optimize'
    
    def __init__(self, size=20, mode='simple'):
        """
        Initialize population.
        
        Args:
            size: Population size
            mode: Evolution mode ('simple', 'sbx', 'uniform', 'optimize')
        """
        self.size = size
        self.mode = mode
        self.agents = []
        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        self.last_generation_events = []
        
        # Elite pool for crossover modes (tracks best across generations)
        self.elite_pool = []
        self.elite_pool_size = 5
        
    def initialize(self):
        """Create initial population.

        For simple, sbx, and uniform modes: uses full random initialization.
        For optimize mode: loads reference weights and creates variations.
        """
        self.agents = []

        if self.mode == self.MODE_OPTIMIZE:
            # Load reference weights from window (set by JS)
            ref_weights = self._load_reference_weights()
            if ref_weights:
                for i in range(self.size):
                    agent = NeuralAgent()
                    agent.set_weights(ref_weights)
                    # First agent keeps exact reference weights (elite)
                    # Others get slight mutations for diversity
                    if i > 0:
                        agent.mutate(rate=0.1, strength=0.2)
                    self.agents.append(agent)
                console.log(f"[Population] Initialized {self.size} agents from reference weights (optimize mode)")
            else:
                # Fallback to simple mode if no reference weights
                console.log("[Population] No reference weights found, falling back to simple mode")
                self.mode = self.MODE_SIMPLE
                self._init_random_population()
        else:
            self._init_random_population()

        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        self.elite_pool = []
        self.last_generation_events = []

    def _init_random_population(self):
        """Initialize population with reference-faithful random weights."""
        for _ in range(self.size):
            agent = NeuralAgent()
            agent.init_random()
            self.agents.append(agent)
        console.log(f"[Population] Initialized {self.size} agents (mode: {self.mode}) (full random)")

    def _load_reference_weights(self):
        """Load reference weights from window._referenceWeights (set by JS)."""
        try:
            if hasattr(window, '_referenceWeights') and window._referenceWeights:
                ref = window._referenceWeights
                # Convert JsProxy to Python types
                weights = {
                    'W1': [list(row) for row in ref.W1],
                    'b1': list(ref.b1),
                    'W2': [list(row) for row in ref.W2],
                    'b2': list(ref.b2)
                }
                console.log(f"[Population] Loaded reference weights: W1={len(weights['W1'])}x{len(weights['W1'][0])}")
                return weights
        except Exception as e:
            console.log(f"[Population] Error loading reference weights: {e}")
        return None
        
    def set_mode(self, mode):
        """Change evolution mode."""
        if mode in [self.MODE_SIMPLE, self.MODE_SBX, self.MODE_UNIFORM, self.MODE_OPTIMIZE]:
            self.mode = mode
            console.log(f"[Population] Mode set to: {mode}")
        else:
            console.log(f"[Population] Unknown mode: {mode}, keeping {self.mode}")
        
    def inject_champion(self, weights):
        """Inject champion weights into population slot 0 (preserved elite).

        This ensures the best-ever performer is never lost to mutation drift.
        Call this BEFORE evolve() to guarantee the champion survives.
        """
        if weights and self.agents:
            self.agents[0].set_weights(weights)
            self.agents[0].fitness = float('inf')  # Ensure it's always #1
            console.log("[Population] Champion weights injected into slot 0")

    def _clone_agent(self, agent):
        """Clone an agent, including its learned parameters and summary stats."""
        clone = NeuralAgent()
        clone.copy_from(agent)
        clone.fitness = agent.fitness
        clone.farthest_x = agent.farthest_x
        clone.won = agent.won
        clone.frames = agent.frames
        return clone

    def _get_agent_slot(self, target_agent, agents):
        """Get the slot index for an agent object within a list."""
        for idx, agent in enumerate(agents):
            if agent is target_agent:
                return idx
        return -1

    def _record_generation_event(self, slot, operator, parent_slots, preserved, mutated,
                                 mutation_rate=0.0, mutation_strength=0.0):
        """Record lineage data for frontend breeding visualizations."""
        self.last_generation_events.append({
            'slot': slot,
            'mode': self.mode,
            'operator': operator,
            'parent_slots': parent_slots,
            'preserved': preserved,
            'mutated': mutated,
            'mutation_rate': mutation_rate,
            'mutation_strength': mutation_strength
        })

    def get_last_generation_events(self):
        """Get lineage events from the most recent evolution step."""
        return [dict(event) for event in self.last_generation_events]

    def evolve(self):
        """Create next generation through selection and mutation/crossover."""
        # Sort by fitness
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        self.last_generation_events = []

        # Track best
        if self.agents[0].fitness > self.best_fitness:
            self.best_fitness = self.agents[0].fitness
            self.best_agent = NeuralAgent()
            self.best_agent.copy_from(self.agents[0])

        # Update elite pool (for crossover modes)
        self._update_elite_pool()

        # Dispatch to appropriate evolution method
        # Optimize mode uses simple evolution (mutation only) to fine-tune
        if self.mode == self.MODE_SIMPLE or self.mode == self.MODE_OPTIMIZE:
            self._evolve_simple()
        else:
            self._evolve_crossover()

        self.generation += 1

        # Reset all agents for new episode
        for agent in self.agents:
            agent.reset()

        mode_str = f" [{self.mode}]" if self.mode != self.MODE_SIMPLE else ""
        console.log(f"[Population] Generation {self.generation}{mode_str}, best fitness: {self.best_fitness:.0f}")
    
    def _roulette_wheel_select(self, agents):
        """Select an agent via fitness-proportional (roulette wheel) selection.

        Matches SuperMarioBros-AI reference.
        Higher fitness = higher chance of being selected.
        """
        # Get fitnesses (ensure all positive for roulette wheel)
        fitnesses = np.array([max(0.00001, a.fitness) for a in agents])
        total = fitnesses.sum()

        if total <= 0:
            # Fallback to random if all fitness is 0
            return agents[np.random.randint(len(agents))]

        # Roulette wheel: probability proportional to fitness
        probs = fitnesses / total
        idx = np.random.choice(len(agents), p=probs)
        return agents[idx]

    def _evolve_simple(self):
        """Mutation-only evolution for simple and optimize modes.

        Simple mode preserves the top 10 percent as elites.
        Optimize mode preserves only the champion after reference seeding.
        """
        elite_count = max(2, self.size // 10)
        preserved_count = 1 if self.mode == self.MODE_OPTIMIZE else elite_count
        new_agents = []

        for slot in range(preserved_count):
            preserved_agent = self._clone_agent(self.agents[slot])
            new_agents.append(preserved_agent)
            self._record_generation_event(
                slot=slot,
                operator='preserve',
                parent_slots=[slot],
                preserved=True,
                mutated=False
            )

        # Fill rest with mutations of elites using roulette wheel selection
        while len(new_agents) < self.size:
            # Roulette wheel select from elites (fitness-proportional)
            parent = self._roulette_wheel_select(self.agents[:elite_count])
            parent_slot = self._get_agent_slot(parent, self.agents)
            child = self._clone_agent(parent)
            # Reference: mutation_rate=0.05, gaussian_mutation_scale=0.2
            child.mutate(rate=0.05, strength=0.2)
            self._record_generation_event(
                slot=len(new_agents),
                operator='mutation',
                parent_slots=[parent_slot],
                preserved=False,
                mutated=True,
                mutation_rate=0.05,
                mutation_strength=0.2
            )
            new_agents.append(child)

        self.agents = new_agents
    
    def _evolve_crossover(self):
        """Crossover evolution: preserve champion, breed the rest every generation."""
        from .crossover import crossover_networks

        elite_count = max(2, self.size // 10)
        parent_pool = self.agents[:elite_count]
        new_agents = [self._clone_agent(self.agents[0])]
        self._record_generation_event(
            slot=0,
            operator='preserve',
            parent_slots=[0],
            preserved=True,
            mutated=False
        )

        while len(new_agents) < self.size:
            parent1, parent2 = self._select_parents(parent_pool)
            parent1_slot = self._get_agent_slot(parent1, self.agents)
            parent2_slot = self._get_agent_slot(parent2, self.agents)

            offspring_weights = crossover_networks(
                parent1.get_weights(),
                parent2.get_weights(),
                method=self.mode,
                eta=100.0  # High eta = offspring close to parents
            )

            child = NeuralAgent()
            child.set_weights(offspring_weights)
            child.mutate(rate=0.05, strength=0.2)
            self._record_generation_event(
                slot=len(new_agents),
                operator=self.mode,
                parent_slots=[parent1_slot, parent2_slot],
                preserved=False,
                mutated=True,
                mutation_rate=0.05,
                mutation_strength=0.2
            )

            new_agents.append(child)

        self.agents = new_agents
    
    def _update_elite_pool(self):
        """Refresh the elite pool from the current generation's top performers."""
        elite_count = max(2, self.size // 10)
        pool_count = min(self.elite_pool_size, elite_count, len(self.agents))
        self.elite_pool = [self._clone_agent(agent) for agent in self.agents[:pool_count]]
    
    def _select_parents(self, pool):
        """Select two parents from the current elite pool via roulette wheel selection.

        Using fitness-proportional selection to match reference implementation.
        """
        # Roulette wheel for parent 1
        parent1 = self._roulette_wheel_select(pool)

        # Roulette wheel for parent 2
        # Allow same parent (self-breeding) since reference doesn't prevent it
        parent2 = self._roulette_wheel_select(pool)

        return parent1, parent2
        
    def get_stats(self):
        """Get population statistics."""
        fitnesses = [a.fitness for a in self.agents]
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'avg_fitness': np.mean(fitnesses) if fitnesses else 0,
            'max_current': max(fitnesses) if fitnesses else 0,
            'mode': self.mode,
            'elite_pool_size': len(self.elite_pool)
        }
