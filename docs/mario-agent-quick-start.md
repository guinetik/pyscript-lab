# Mario Agent Quick Start Guide

## TL;DR

The new modular architecture splits the monolithic agent into three focused components:

- **GameController** - Talks to the emulator (in `lib/nes/`)
- **NeuralController** - Makes decisions (in `lib/`)
- **PlayerAgent** - Orchestrates training (in `ml/rl/agent.py`)

## File Overview

| File | Purpose | Key Feature |
|------|---------|-------------|
| `lib/nes/game_controller.py` | Emulator interaction | Clean interface to NES |
| `lib/neural_controller.py` | Neural network abstraction | Plug & play different NNs |
| `ml/rl/agent.py` | Training orchestration (PlayerAgent) | Episode management & fitness |
| `ml/rl/player_agent.py` | Old monolithic agent (MarioAgent) | Keep as reference |

## Quick Examples

### 1. Use the GameController Directly

```python
from lib.game_controller import GameController

game = GameController(vision_width=13, vision_height=10)

# Get game state
vision = game.get_vision_state()  # Returns np.array
x, y = game.get_mario_position()
alive = game.is_mario_alive()

# Control the game
buttons = [0, 0, 0, 1, 1, 0]  # [UP, DOWN, LEFT, RIGHT, A, B]
game.execute_buttons(buttons)

# Debug vision
game.visualize_vision(vision)
```

### 2. Create a Custom Neural Controller

```python
from lib.neural_controller import NeuralController
import numpy as np

class MyCustomController(NeuralController):
    """Your custom neural network"""
    
    def __init__(self, input_size, output_size):
        self.input_size = input_size
        self.output_size = output_size
        # Initialize your network
        
    def forward(self, state):
        # Your forward pass logic
        output = np.random.rand(self.output_size)
        return output
    
    def mutate(self, mutation_rate=0.1, mutation_scale=0.5):
        # Your mutation logic
        pass
    
    def get_weights(self):
        return {'weights': [], 'biases': []}
    
    def set_weights(self, weights, biases):
        pass
    
    def randomize(self):
        pass
```

### 3. Use the New Agent

```python
from ml.rl.agent import PlayerAgent

# Create agent with default settings
agent = PlayerAgent()

# Or customize
agent = PlayerAgent(
    vision_width=13,
    vision_height=10,
    hidden_size=64  # Bigger brain!
)

# Train
await agent.start_training()

# Control
agent.pause_training()
agent.stop_training()
agent.reset_training()
```

### 4. Swap Neural Networks

```python
from ml.rl.agent import PlayerAgent
from lib.neural_controller import SimpleNeuralController

# Create agent
agent = PlayerAgent()

# Swap to bigger network
agent.neural = SimpleNeuralController(
    input_size=130,
    hidden_size=128,  # 4x bigger!
    output_size=6
)

# Train with new brain
await agent.start_training()
```

## Key Differences from Old Agent

### Old Way (player_agent.py)
```python
# Everything in one class
class MarioAgent:
    def __init__(self):
        # Game stuff
        self.nes = ...
        # Network stuff
        self.network = ...
        # Training stuff
        self.episodes = ...
    
    def _get_nes(self):
        # Emulator access
        pass
    
    def get_game_state(self):
        # Vision extraction
        pass
    
    def decide_action(self, state):
        # Neural network
        pass
    
    # ... 586 lines total
```

### New Way (modular - PlayerAgent)
```python
# Separated concerns
class PlayerAgent:
    def __init__(self):
        self.game = GameController()    # Game stuff
        self.neural = NeuralController() # Network stuff
        # Training stuff here
    
    def observe(self):
        return self.game.get_vision_state()
    
    def decide(self, state):
        return self.neural.forward(state)
    
    def act(self, buttons):
        self.game.execute_buttons(buttons)
```

## Common Patterns

### Pattern 1: Observe → Decide → Act
```python
# The core agent loop
state = agent.observe()        # Get game state
buttons = agent.decide(state)  # Neural network decides
agent.act(buttons)             # Execute on game
```

### Pattern 2: Custom Fitness Function
```python
from ml.rl.agent import PlayerAgent

class MyAgent(PlayerAgent):
    def calculate_fitness(self):
        # Your custom fitness logic
        distance = self.max_x
        time = self.frames
        
        # Example: Reward speed
        return distance / time * 1000
```

### Pattern 3: Multiple Agents
```python
from ml.rl.agent import PlayerAgent

# Create multiple agents with different brains
agents = [
    PlayerAgent(hidden_size=32),   # Small brain
    PlayerAgent(hidden_size=64),   # Medium brain
    PlayerAgent(hidden_size=128),  # Big brain
]

# Train them independently or compete
for agent in agents:
    await agent.start_training()
```

## Architecture Flow

```
User clicks "Start Training"
    ↓
JavaScript calls startRLTraining()
    ↓
Python: agent.start_training()
    ↓
┌─────────────────────────┐
│   Training Loop         │
│  (runs every 67ms)      │
│                         │
│  1. observe()           │ ← GameController.get_vision_state()
│  2. decide(state)       │ ← NeuralController.forward()
│  3. act(buttons)        │ ← GameController.execute_buttons()
│  4. check progress      │
│                         │
│  if episode ends:       │
│    → calculate_fitness()│
│    → mutate()           │
│    → start_new_episode()│
└─────────────────────────┘
```

## Extending the System

### Add a New Neural Network Type

1. Create class inheriting from `NeuralController`
2. Implement abstract methods
3. Use with agent:

```python
from lib.neural_controller import NeuralController
from ml.rl.agent import PlayerAgent

class DeepController(NeuralController):
    # Implement methods...
    pass

agent = PlayerAgent()
agent.neural = DeepController(130, 6)
```

### Add New Game Observations

1. Extend `GameController`:

```python
from lib.nes.game_controller import GameController
from lib.nes.nes_ram_utils import get_enemy_positions

class ExtendedGameController(GameController):
    def get_enemies_count(self):
        """Count how many enemies on screen"""
        nes = self.get_nes()
        return len(get_enemy_positions(nes))
```

2. Use in agent:

```python
from ml.rl.agent import PlayerAgent

agent = PlayerAgent()
agent.game = ExtendedGameController()
```

## Debugging Tips

### Visualize Vision
```python
# In agent.step()
if self.frames % 300 == 0:
    self.game.visualize_vision(state)
```

### Check Button Presses
```python
buttons = agent.decide(state)
console.log(f"Buttons: {buttons}")
# Output: [0, 0, 0, 1, 1, 0]  (RIGHT + A)
```

### Monitor Network Output
```python
output = agent.neural.forward(state)
console.log(f"Raw output: {output}")
console.log(f"Max activation: {np.max(output)}")
```

## Performance Tuning

### Decision Rate
```python
# In training_loop(), change timeout
setTimeout(proxy, 67)  # ~15 decisions/sec (default)
setTimeout(proxy, 33)  # ~30 decisions/sec (faster)
setTimeout(proxy, 100) # ~10 decisions/sec (slower)
```

### Vision Size
```python
# Larger vision = more context, slower
agent = MarioAgent(vision_width=20, vision_height=15)

# Smaller vision = faster, less context
agent = MarioAgent(vision_width=7, vision_height=7)
```

### Network Size
```python
# Larger network = more capacity, slower
agent = MarioAgent(hidden_size=128)

# Smaller network = faster, less capacity
agent = MarioAgent(hidden_size=16)
```

## Testing Components

### Test GameController
```python
game = GameController()
vision = game.get_vision_state()
assert len(vision) == 130  # 13×10
assert game.is_emulator_ready()
```

### Test NeuralController
```python
neural = SimpleNeuralController(130, 32, 6)
state = np.random.rand(130)
output = neural.forward(state)
assert output.shape == (6,)
assert all(0 <= x <= 1 for x in output)  # Sigmoid outputs
```

### Test Full Agent
```python
agent = MarioAgent()
agent.reset()
assert agent.frames == 0
assert agent.max_x == 0
```

## Troubleshooting

### "Emulator not found"
- Ensure `window.nesEmulator` is initialized
- Check if emulator loaded before agent

### "Vision is all zeros"
- Check if game is running
- Verify emulator is at gameplay (not menu)
- Use `visualize_vision()` to debug

### "Agent not learning"
- Increase mutation rate
- Check fitness function
- Ensure episodes are restarting properly

### "Too slow"
- Reduce vision size
- Reduce hidden layer size
- Increase decision interval (setTimeout)

## Next Steps

1. Read [full architecture doc](./mario-agent-architecture.md)
2. Try running the new agent: `agent.py`
3. Experiment with custom neural controllers
4. Compare with old agent: `player_agent.py`
5. Implement your own fitness function

## Questions?

Check these files for more details:
- Architecture: `docs/mario-agent-architecture.md`
- Game API: `lib/game_controller.py`
- Neural API: `lib/neural_controller.py`
- Agent implementation: `ml/rl/agent.py`
- RAM utilities: `lib/nes_ram_utils.py`

