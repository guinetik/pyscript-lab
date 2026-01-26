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
        
    def init_random(self):
        """Initialize with random weights (Xavier initialization)."""
        self.W1 = np.random.randn(HIDDEN_SIZE, INPUT_SIZE) * np.sqrt(2.0 / INPUT_SIZE)
        self.b1 = np.zeros(HIDDEN_SIZE)
        self.W2 = np.random.randn(OUTPUT_SIZE, HIDDEN_SIZE) * np.sqrt(2.0 / HIDDEN_SIZE)
        self.b2 = np.zeros(OUTPUT_SIZE)
        
    def copy_from(self, other):
        """Copy weights from another agent."""
        self.W1 = other.W1.copy()
        self.b1 = other.b1.copy()
        self.W2 = other.W2.copy()
        self.b2 = other.b2.copy()
        
    def mutate(self, rate=0.1, strength=0.5):
        """Mutate weights with given rate and strength."""
        for param in [self.W1, self.b1, self.W2, self.b2]:
            mask = np.random.random(param.shape) < rate
            param[mask] += np.random.randn(*param.shape)[mask] * strength
            
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
    """Population of agents for evolutionary training."""
    
    def __init__(self, size=20):
        self.size = size
        self.agents = []
        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        
    def initialize(self):
        """Create initial random population."""
        self.agents = []
        for _ in range(self.size):
            agent = NeuralAgent()
            agent.init_random()
            self.agents.append(agent)
        self.generation = 0
        self.best_fitness = 0
        self.best_agent = None
        console.log(f"[Population] Initialized {self.size} agents")
        
    def evolve(self):
        """Create next generation through selection and mutation."""
        # Sort by fitness
        self.agents.sort(key=lambda a: a.fitness, reverse=True)
        
        # Track best
        if self.agents[0].fitness > self.best_fitness:
            self.best_fitness = self.agents[0].fitness
            self.best_agent = NeuralAgent()
            self.best_agent.copy_from(self.agents[0])
            
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
        self.generation += 1
        
        # Reset all agents for new episode
        for agent in self.agents:
            agent.reset()
            
        console.log(f"[Population] Generation {self.generation}, best fitness: {self.best_fitness:.0f}")
        
    def get_stats(self):
        """Get population statistics."""
        fitnesses = [a.fitness for a in self.agents]
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'avg_fitness': np.mean(fitnesses) if fitnesses else 0,
            'max_current': max(fitnesses) if fitnesses else 0
        }
