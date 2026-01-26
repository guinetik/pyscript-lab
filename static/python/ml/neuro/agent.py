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
        
    def init_random(self, use_reference_biases=False):
        """Initialize with random weights.
        
        Args:
            use_reference_biases: If True, use reference biases (simple mode).
                                  If False, use uniform(-1, 1) for everything (crossover mode).
        """
        # Weights are always random uniform(-1, 1)
        self.W1 = np.random.uniform(-1, 1, size=(HIDDEN_SIZE, INPUT_SIZE))
        self.W2 = np.random.uniform(-1, 1, size=(OUTPUT_SIZE, HIDDEN_SIZE))
        
        if use_reference_biases:
            # Use reference biases - gives agents a "behavioral prior" to move right and jump
            # These evolved biases from SuperMarioBros-AI default to RIGHT+B
            self.b1 = np.array([-0.757, 0.683, 0.998, -0.501, -0.335, -0.573, -0.111, 0.029, 0.780])
            self.b2 = np.array([-0.393, 0.464, 0.458, 0.999, 0.393, 0.992])  # HIGH: RIGHT(0.999), B(0.992)
        else:
            # Full random - matches SuperMarioBros-AI exactly
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
    - 'simple': Mutation only (original behavior)
    - 'sbx': Two-parent SBX crossover + mutation
    - 'uniform': Two-parent uniform crossover + mutation
    """
    
    # Evolution mode constants
    MODE_SIMPLE = 'simple'
    MODE_SBX = 'sbx'
    MODE_UNIFORM = 'uniform'
    
    def __init__(self, size=20, mode='simple', breeding_interval=3):
        """
        Initialize population.
        
        Args:
            size: Population size
            mode: Evolution mode ('simple', 'sbx', 'uniform')
            breeding_interval: For crossover modes, breed every N generations
        """
        self.size = size
        self.mode = mode
        self.breeding_interval = breeding_interval
        self.agents = []
        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        
        # Elite pool for crossover modes (tracks best across generations)
        self.elite_pool = []
        self.elite_pool_size = 5
        
    def initialize(self):
        """Create initial random population.
        
        For simple mode: uses reference biases (behavioral prior to move right).
        For crossover modes: uses full random initialization.
        """
        self.agents = []
        use_ref_biases = (self.mode == self.MODE_SIMPLE)
        for _ in range(self.size):
            agent = NeuralAgent()
            agent.init_random(use_reference_biases=use_ref_biases)
            self.agents.append(agent)
        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        self.elite_pool = []
        bias_str = " (reference biases)" if use_ref_biases else " (full random)"
        console.log(f"[Population] Initialized {self.size} agents (mode: {self.mode}){bias_str}")
        
    def set_mode(self, mode):
        """Change evolution mode."""
        if mode in [self.MODE_SIMPLE, self.MODE_SBX, self.MODE_UNIFORM]:
            self.mode = mode
            console.log(f"[Population] Mode set to: {mode}")
        else:
            console.log(f"[Population] Unknown mode: {mode}, keeping {self.mode}")
        
    def evolve(self):
        """Create next generation through selection and mutation/crossover."""
        # Sort by fitness
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Track best
        if self.agents[0].fitness > self.best_fitness:
            self.best_fitness = self.agents[0].fitness
            self.best_agent = NeuralAgent()
            self.best_agent.copy_from(self.agents[0])
            
        # Update elite pool (for crossover modes)
        self._update_elite_pool()
        
        # Dispatch to appropriate evolution method
        if self.mode == self.MODE_SIMPLE:
            self._evolve_simple()
        else:
            self._evolve_crossover()
            
        self.generation += 1
        
        # Reset all agents for new episode
        for agent in self.agents:
            agent.reset()
            
        mode_str = f" [{self.mode}]" if self.mode != self.MODE_SIMPLE else ""
        console.log(f"[Population] Generation {self.generation}{mode_str}, best fitness: {self.best_fitness:.0f}")
    
    def _evolve_simple(self):
        """Simple evolution: mutation only (original behavior)."""
        # Keep top performers
        elite_count = max(2, self.size // 5)
        new_agents = self.agents[:elite_count]
        
        # Fill rest with mutations of elites
        while len(new_agents) < self.size:
            parent = self.agents[np.random.randint(0, elite_count)]
            child = NeuralAgent()
            child.copy_from(parent)
            child.mutate(rate=0.1, strength=0.3)
            new_agents.append(child)
            
        self.agents = new_agents
    
    def _evolve_crossover(self):
        """Crossover evolution: two-parent breeding + mutation."""
        from .crossover import crossover_networks
        
        # Keep top performers as elites
        elite_count = max(2, self.size // 5)
        new_agents = self.agents[:elite_count]
        
        # Decide if this is a breeding generation
        is_breeding_gen = (self.generation > 0 and 
                          self.generation % self.breeding_interval == 0 and
                          len(self.elite_pool) >= 2)
        
        while len(new_agents) < self.size:
            if is_breeding_gen and len(self.elite_pool) >= 2:
                # Two-parent crossover from elite pool
                parent1, parent2 = self._select_parents()
                
                offspring_weights = crossover_networks(
                    parent1.get_weights(),
                    parent2.get_weights(),
                    method=self.mode,
                    eta=100.0  # High eta = offspring close to parents
                )
                
                child = NeuralAgent()
                child.set_weights(offspring_weights)
                # Light mutation after crossover
                child.mutate(rate=0.05, strength=0.2)
            else:
                # Regular mutation from current generation elites
                parent = self.agents[np.random.randint(0, elite_count)]
                child = NeuralAgent()
                child.copy_from(parent)
                child.mutate(rate=0.1, strength=0.3)
                
            new_agents.append(child)
            
        if is_breeding_gen:
            console.log(f"[Population] 🧬 Breeding generation! Elite pool: {len(self.elite_pool)}")
            
        self.agents = new_agents
    
    def _update_elite_pool(self):
        """Update elite pool with best performers."""
        # Add current best to elite pool if good enough
        current_best = self.agents[0]
        
        if len(self.elite_pool) < self.elite_pool_size:
            # Pool not full, add current best
            elite = NeuralAgent()
            elite.copy_from(current_best)
            elite.fitness = current_best.fitness
            elite.farthest_x = current_best.farthest_x
            self.elite_pool.append(elite)
        else:
            # Pool full, replace worst if current is better
            worst_idx = min(range(len(self.elite_pool)), 
                          key=lambda i: self.elite_pool[i].fitness)
            if current_best.fitness > self.elite_pool[worst_idx].fitness:
                elite = NeuralAgent()
                elite.copy_from(current_best)
                elite.fitness = current_best.fitness
                elite.farthest_x = current_best.farthest_x
                self.elite_pool[worst_idx] = elite
    
    def _select_parents(self):
        """Select two parents from elite pool via tournament selection."""
        pool = self.elite_pool
        
        # Tournament for parent 1
        t1 = np.random.choice(len(pool), size=min(3, len(pool)), replace=False)
        parent1_idx = max(t1, key=lambda i: pool[i].fitness)
        parent1 = pool[parent1_idx]
        
        # Tournament for parent 2 (different from parent 1)
        remaining = [i for i in range(len(pool)) if i != parent1_idx]
        if len(remaining) == 0:
            parent2 = parent1  # Self-breeding if only one elite
        else:
            t2 = np.random.choice(remaining, size=min(3, len(remaining)), replace=False)
            parent2_idx = max(t2, key=lambda i: pool[i].fitness)
            parent2 = pool[parent2_idx]
        
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
