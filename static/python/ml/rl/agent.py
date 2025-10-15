"""
Mario Agent - Modular Reinforcement Learning Agent for Super Mario Bros

Clean, decoupled architecture:
- GameController: Handles all emulator interactions
- NeuralController: Abstract neural network interface
- Agent: Orchestrates training loop and fitness calculation

Author: Guinetik
"""

from js import console, window, setTimeout
from pyodide.ffi import create_proxy
import numpy as np
from lib.pyscript_manager import PyScriptManager
from lib.nes.game_controller import GameController
from lib.neural.neural_controller import SimpleNeuralController, NEATController, ConvNeuralController, ActionDecoder

# Visualization update frequency (every N decisions)
VIZ_UPDATE_FREQUENCY = 4


class PlayerAgent:
    """
    Reinforcement learning agent that learns to play Super Mario Bros.
    Uses composition for clean separation of concerns.
    """

    def __init__(
        self,
        vision_width: int = 16,
        vision_height: int = 7,
        hidden_size: int = 32,
        use_context_features: bool = True
    ):
        """
        Initialize Player agent with modular components.

        Args:
            vision_width: Width of vision grid in tiles (default: 16)
            vision_height: Height of vision grid in tiles (default: 7)
            hidden_size: Number of hidden neurons
            use_context_features: Whether to use engineered context features (8 extra inputs)

        Vision distribution (7 tiles vertical):
            3 tiles above Mario (jumps, blocks, platforms)
            1 tile (Mario's current row)
            3 tiles below Mario (pits, ground, enemies)
        """
        # Game controller - handles all emulator interaction
        self.game = GameController(
            vision_width=vision_width,
            vision_height=vision_height
        )

        self.use_context_features = use_context_features

        # Neural controller - handles decision making
        vision_size = vision_width * vision_height
        context_size = 8 if use_context_features else 0
        input_size = vision_size + context_size  # 112 vision + 8 context = 120
        output_size = 6  # [UP, DOWN, LEFT, RIGHT, A, B]

        # Mario-specific behavioral priors (agent owns domain knowledge)
        # Button order: [UP, DOWN, LEFT, RIGHT, A, B]
        self.behavioral_priors = {
            'UP': -5.0,      # Discourage (rarely useful)
            'DOWN': -1.5,    # Discourage (crouching rarely helps)
            'LEFT': -3.0,    # Strongly discourage (moving backward is bad)
            'RIGHT': 2.0,    # Encourage (primary goal!)
            'A': 2.0,        # Encourage jumping (essential for Mario)
            'B': 1.1         # Slightly encourage running
        }

        # Network will be created in _create_network()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Set default network type (can be changed via start_training)
        self.network_type = 'simple-feedforward'

        # Create initial network
        self.neural = self._create_network(self.network_type)

        # Initialize network and apply priors if supported
        self._initialize_network()

        # Action decoder - converts neural outputs to buttons
        self.decoder = ActionDecoder(use_variable_threshold=True)

        # Episode tracking
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.max_frames = 1800  # 30 seconds at 60fps
        self.start_score = 0  # Score at episode start
        self.final_score = 0  # Score at episode end

        # Training state
        self.is_training = False
        self.generation = 0  # Current generation number
        self.current_fitness = 0  # Fitness of current generation
        self.best_distance = 0
        self.best_fitness = 0

        # Elite preservation - save champion weights
        self.champion_weights = None

        # Death tracking
        self.death_cause = None  # 'enemy', 'timeout', 'stuck'

        # Local minima detection
        self.generations_stuck = 0  # Consecutive generations at same distance

        print("🤖 PlayerAgent initialized with modular architecture")
        print(f"   Input: {input_size} (vision: {vision_size}, context: {context_size}), Hidden: {hidden_size}, Output: {output_size}")
        print(f"   Network type: {self.network_type}")
        print(f"   Context features: {'ENABLED' if use_context_features else 'DISABLED'}")

    def _create_network(self, network_type: str):
        """
        Factory method to create neural network based on type.

        Args:
            network_type: Type of network ('simple-feedforward', 'neat', 'conv', etc.)

        Returns:
            NeuralController instance
        """
        if network_type == 'simple-feedforward':
            return SimpleNeuralController(
                input_size=self.input_size,
                hidden_size=self.hidden_size,
                output_size=self.output_size,
                seed=None
            )
        elif network_type == 'neat':
            return NEATController(
                input_size=self.input_size,
                hidden_size=self.hidden_size,  # Ignored by NEAT
                output_size=self.output_size,
                seed=None
            )
        elif network_type == 'conv':
            return ConvNeuralController(
                vision_shape=(7, 16),  # Height × Width
                context_size=8 if self.use_context_features else 0,
                num_filters=4,
                hidden_size=self.hidden_size,
                output_size=self.output_size,
                seed=None
            )
        else:
            console.warn(f"⚠️ Unknown network type '{network_type}', defaulting to simple-feedforward")
            return SimpleNeuralController(
                input_size=self.input_size,
                hidden_size=self.hidden_size,
                output_size=self.output_size,
                seed=None
            )

    def _initialize_network(self):
        """
        Initialize neural network with random weights and apply behavioral priors if supported.
        Separates network initialization from domain-specific knowledge (priors).
        """
        # Randomize weights
        self.neural.randomize()

        # Apply behavioral priors if network supports it
        if hasattr(self.neural, 'apply_priors'):
            # Convert dict to array in button order
            prior_values = [
                self.behavioral_priors['UP'],
                self.behavioral_priors['DOWN'],
                self.behavioral_priors['LEFT'],
                self.behavioral_priors['RIGHT'],
                self.behavioral_priors['A'],
                self.behavioral_priors['B']
            ]
            self.neural.apply_priors(prior_values)
            print(f"✅ Applied behavioral priors: {self.behavioral_priors}")
        else:
            print("ℹ️ Network does not support behavioral priors (using random initialization)")

    def observe(self) -> np.ndarray:
        """
        Observe the current game state.
        Combines vision grid with engineered context features.

        Returns:
            np.ndarray: Combined state vector (vision + context features)
        """
        vision = self.game.get_vision_state()

        if self.use_context_features:
            context = self.game.get_context_features()
            # Concatenate vision (112) + context (8) = 120 inputs
            state = np.concatenate([vision, context])
        else:
            state = vision

        return state

    def decide(self, state: np.ndarray) -> np.ndarray:
        """
        Decide which buttons to press based on observation.

        Args:
            state: Observed game state

        Returns:
            np.ndarray: Button states [UP, DOWN, LEFT, RIGHT, A, B]
        """
        # Debug vision occasionally (every 100 decisions)
        if not hasattr(self, '_decision_count'):
            self._decision_count = 0
            self._viz_enabled = False  # Visualization toggle

        self._decision_count += 1

        if self._decision_count % 100 == 0:
            # Check if vision has any non-zero values (enemies/obstacles)
            num_obstacles = np.sum(state != 0.0)
            num_enemies = np.sum(state == -1.0)
            num_solid = np.sum(state == 1.0)
            print(f"👁️ Vision check (decision {self._decision_count}): {num_obstacles} non-empty tiles ({num_enemies} enemies, {num_solid} solid)")

        # Capture activations on EVERY decision if visualization enabled
        capture = self._viz_enabled

        # Neural network forward pass
        output = self.neural.forward(state, capture_activations=capture)

        # Send visualization data to JavaScript at configured frequency
        if self._viz_enabled and (self._decision_count % VIZ_UPDATE_FREQUENCY == 0):
            self._visualize_network()

        # Debug: check output shape and values (only log once)
        if not hasattr(self, '_logged_shapes'):
            print(f"🔍 Debug - State shape: {state.shape}, Output shape: {output.shape}")
            print(f"🔍 Sample state values: min={state.min():.2f}, max={state.max():.2f}, mean={state.mean():.2f}")

            if self.use_context_features:
                # Show context features separately
                vision_part = state[:112]
                context_part = state[112:]
                print(f"🔍 Vision part: {len(vision_part)} values")
                print(f"🔍 Context features: {context_part}")
                print(f"   [enemy_left, enemy_right, ground_dist, pit_dist, obstacle_dist, on_ground, y_pos, enemy_nearby]")

            print(f"🔍 Raw output values (before threshold): {output}")
            print(f"🔍 Output interpretation: UP={output[0]:.3f}, DOWN={output[1]:.3f}, LEFT={output[2]:.3f}, RIGHT={output[3]:.3f}, A={output[4]:.3f}, B={output[5]:.3f}")
            self._logged_shapes = True

        # Decode to button presses
        buttons = self.decoder.decode(output)

        # Ensure we return exactly 6 buttons
        if len(buttons) != 6:
            console.error(f"❌ Decoder returned {len(buttons)} buttons, expected 6!")
            return np.array([0, 0, 0, 1, 0, 0])  # Default: just press RIGHT

        return buttons

    def _visualize_network(self):
        """
        Visualize network activations and weights.
        Sends data to JavaScript for visualization.
        """
        try:
            viz_data = self.neural.get_visualization_data()

            # Send to JavaScript if callback exists
            if hasattr(window, 'onNetworkVisualization'):
                from pyodide.ffi import to_js
                from js import Object

                # Use to_js with dict_converter to create plain JS objects (not Maps)
                # This prevents .values from being a function
                js_data = to_js(viz_data, dict_converter=Object.fromEntries)
                window.onNetworkVisualization(js_data)

        except Exception as e:
            console.error(f"❌ Error visualizing network: {e}")

    def toggle_visualization(self, enabled: bool = None):
        """
        Toggle network visualization on/off.

        Args:
            enabled: If provided, set to this value. Otherwise toggle current state.
        """
        if enabled is None:
            self._viz_enabled = not getattr(self, '_viz_enabled', False)
        else:
            self._viz_enabled = enabled

        status = "ENABLED" if self._viz_enabled else "DISABLED"
        print(f"🎨 Network visualization {status}")

        if self._viz_enabled:
            print(f"   Activations will be captured on every decision")
            print(f"   Visualization updates every {VIZ_UPDATE_FREQUENCY} decisions")
            print(f"   First update will appear momentarily...")

        return self._viz_enabled

    def act(self, buttons: np.ndarray):
        """
        Execute button presses on the game.

        Args:
            buttons: Button states to execute
        """
        self.game.execute_buttons(buttons)

    def step(self) -> bool:
        """
        Execute one step of the agent loop:
        1. Observe game state
        2. Decide action
        3. Execute action
        4. Track progress

        Returns:
            bool: True if episode continues, False if episode ended
        """
        self.frames += 1

        # Check timeout
        if self.frames >= self.max_frames:
            self.death_cause = 'timeout'
            print(f"⏰ Timeout! Frames: {self.frames}, Max X: {self.max_x}")
            return False

        # Check if Mario is alive
        if not self.game.is_mario_alive():
            self.death_cause = 'enemy'
            print(f"💀 Mario died! Frames: {self.frames}, Max X: {self.max_x}")
            return False

        # Observe
        state = self.observe()

        # Debug: print vision periodically
        if self.frames % 300 == 0:
            self.game.print_vision(state[:112] if len(state) > 112 else state)

        # Decide
        buttons = self.decide(state)

        # Act
        self.act(buttons)

        # Track progress
        current_x = self.game.get_mario_x()

        if current_x > self.max_x:
            self.max_x = current_x
            self.stuck_frames = 0
        else:
            self.stuck_frames += 1

        # Check if stuck (no progress for 1 second)
        if self.stuck_frames > 60:
            self.death_cause = 'stuck'
            print(f"🚫 Mario stuck! Frames: {self.frames}, Max X: {self.max_x}")

            # Print what Mario sees when stuck (for debugging)
            print("👁️ Vision at stuck position:")
            # Extract just the vision part (first 112 values)
            vision_only = state[:112] if len(state) > 112 else state
            self.game.print_vision(vision_only)

            # Show context features too if enabled
            if self.use_context_features and len(state) >= 120:
                context_features = state[112:120]
                print(f"🎯 Context features: {context_features}")
                print(f"   [enemy_left={context_features[0]:.2f}, enemy_right={context_features[1]:.2f}, ground_dist={context_features[2]:.2f}, pit_dist={context_features[3]:.2f}, obstacle_dist={context_features[4]:.2f}, on_ground={context_features[5]:.2f}, y_pos={context_features[6]:.2f}, enemy_nearby={context_features[7]:.2f}]")

            return False

        # Log progress occasionally
        if self.frames % 60 == 0:
            print(f"🎮 Frame {self.frames}/{self.max_frames}, X: {current_x}, Max: {self.max_x}")

            # Update UI every 3 seconds (180 frames) with live progress
            if self.frames % 180 == 0:
                progress_pct = int((current_x / self.best_distance * 100)) if self.best_distance > 0 else 0
                window.updateRLStatus('training', f"🏃 Generation {self.generation + 1}: {current_x}px ({progress_pct}% of best)")

        self.last_x = current_x
        return True  # Episode continues

    def calculate_fitness(self) -> float:
        """
        Calculate fitness score for this episode.

        Fitness function:
        - Exponential reward for distance (distance^1.5)
        - Score gained during episode (multiplied by 2 to incentivize enemy stomping)
        - Light penalties for different death types
        - Milestone bonuses for progress

        Returns:
            float: Fitness score (always > 0)
        """
        distance = self.max_x
        score_gained = self.final_score - self.start_score

        # Base fitness: exponential distance reward
        distance_reward = (distance ** 1.5) if distance > 0 else 0

        # Score reward (2x multiplier to encourage enemy engagement)
        score_reward = score_gained * 2

        # Death penalties
        death_penalty = 0
        if self.death_cause == 'enemy':
            death_penalty = 50
        elif self.death_cause == 'stuck':
            death_penalty = 100  # Increased from 20 - getting stuck is really bad!
        # No penalty for timeout

        # Milestone bonuses
        milestone_bonus = 0
        if distance > 50:
            milestone_bonus += 200
        if distance > 100:
            milestone_bonus += 500
        if distance > 200:
            milestone_bonus += 1000
        if distance > 400:
            milestone_bonus += 2000
        if distance > 800:
            milestone_bonus += 5000

        # Calculate final fitness (always positive)
        fitness = max(
            distance_reward + score_reward - death_penalty + milestone_bonus,
            1.0
        )

        return fitness

    def reset(self):
        """Reset episode stats."""
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.death_cause = None
        # Capture starting score for this episode
        self.start_score = self.game.get_score()
        self.final_score = self.start_score

    def training_loop(self):
        """
        Main training loop - runs continuously while training.
        Makes decisions at ~15fps (every 67ms).
        """
        if not self.is_training:
            return

        # Execute one step
        alive = self.step()

        if not alive:
            # Episode ended
            self.end_episode()
            return

        # Schedule next step (~15 decisions per second)
        proxy = create_proxy(self.training_loop)
        setTimeout(proxy, 67)

    def end_episode(self):
        """Handle end of episode - calculate fitness and mutate."""
        distance = self.max_x

        # Capture final score
        self.final_score = self.game.get_score()
        score_gained = self.final_score - self.start_score

        fitness = self.calculate_fitness()
        self.current_fitness = fitness

        # Track improvements
        improved_distance = distance > self.best_distance
        improved_fitness = fitness > self.best_fitness

        if improved_distance:
            self.best_distance = distance
            print(f"🎉 New best distance: {self.best_distance}!")

        if improved_fitness:
            self.best_fitness = fitness
            print(f"🏆 New best fitness: {self.best_fitness:.1f}!")

            # Save champion weights for elite preservation
            self.champion_weights = self.neural.get_weights()
            print("💾 Saved champion weights")

        self.generation += 1

        print(f"📊 Generation {self.generation} complete:")
        print(f"   Distance: {distance}, Fitness: {fitness:.1f}")
        print(f"   Score gained: {score_gained} (Start: {self.start_score}, End: {self.final_score})")
        print(f"   Cause: {self.death_cause}, Frames: {self.frames}")
        print(f"   Best Distance: {self.best_distance}, Best Fitness: {self.best_fitness:.1f}")

        # Update UI metrics
        window.updateRLMetrics(self.generation, self.current_fitness, self.best_distance)

        # User-friendly status message based on what happened
        death_messages = {
            'enemy': '💀 Hit an enemy',
            'stuck': '🚫 Got stuck',
            'timeout': '⏰ Time ran out'
        }
        death_msg = death_messages.get(self.death_cause, '❌ Generation ended')

        # Show different messages for improvements
        if improved_fitness:
            score_msg = f" | +{score_gained} points" if score_gained > 0 else ""
            status_msg = f"🎉 New record! Distance: {distance}px{score_msg} | {death_msg}"
        else:
            score_msg = f" | +{score_gained}pts" if score_gained > 0 else ""
            status_msg = f"Gen {self.generation}: {distance}px{score_msg} | {death_msg} | Best: {self.best_distance}px"

        window.updateRLStatus('training', status_msg)

        # Adaptive mutation based on performance with elite preservation
        mutation_strategy = ""

        # Check if we're stuck in local minima (same distance for 5+ generations)
        if distance == self.best_distance:
            self.generations_stuck += 1
        else:
            self.generations_stuck = 0

        # Escape local minima with random restart (with behavioral priors)
        if self.generations_stuck >= 5:
            print("⚠️ STUCK IN LOCAL MINIMA - Random restart with priors!")
            mutation_strategy = "Escaping local minima (5 stuck generations)..."
            self._initialize_network()  # Full reset with priors
            self.generations_stuck = 0
        elif fitness < self.best_fitness * 0.3:
            # Really bad - restore champion and try moderate variations
            if self.champion_weights:
                print("🏆 Restoring champion with small mutation")
                mutation_strategy = "Back to champion, trying variations..."

                # IMPORTANT: Make deep copies so we don't mutate the champion itself!
                import copy

                # Handle different network weight formats
                if 'genome' in self.champion_weights:
                    # NEAT format
                    champion_genome = copy.deepcopy(self.champion_weights['genome'])
                    self.neural.set_weights({'genome': champion_genome}, None)
                elif 'kernels' in self.champion_weights:
                    # Conv format (dict-based like NEAT)
                    champion_weights_copy = copy.deepcopy(self.champion_weights)
                    self.neural.set_weights(champion_weights_copy, None)
                else:
                    # Simple feedforward format
                    champion_weights_copy = copy.deepcopy(self.champion_weights['weights'])
                    champion_biases_copy = copy.deepcopy(self.champion_weights['biases'])
                    self.neural.set_weights(champion_weights_copy, champion_biases_copy)

                # Small mutation - 10% of weights, moderate changes
                self.neural.mutate(mutation_rate=0.1, mutation_scale=0.4)
            else:
                print("🎲 Terrible performance - moderate mutation")
                mutation_strategy = "Trying new strategies..."
                self.neural.mutate(mutation_rate=0.2, mutation_scale=0.5)
        elif fitness < self.best_fitness * 0.6:
            print("🎲 Poor performance - moderate mutation")
            mutation_strategy = "Exploring alternatives..."
            self.neural.mutate(mutation_rate=0.15, mutation_scale=0.4)
        elif improved_fitness:
            print("✨ Improved - tiny mutation to refine")
            mutation_strategy = "Refining winning strategy..."
            self.neural.mutate(mutation_rate=0.05, mutation_scale=0.2)
        else:
            print("🔄 Normal mutation")
            mutation_strategy = "Making small adjustments..."
            self.neural.mutate(mutation_rate=0.1, mutation_scale=0.3)

        # Show mutation strategy briefly
        if mutation_strategy:
            window.updateRLStatus('training', f"🧬 {mutation_strategy}")

        # Wait then restart episode
        async def restart_episode():
            if self.is_training:
                await self.start_new_episode()

        proxy = create_proxy(restart_episode)
        setTimeout(proxy, 2000)  # 2 seconds to allow state loading

    async def start_new_episode(self):
        """Start a new training generation."""
        print(f"🔄 Starting generation {self.generation + 1}")

        # Progressive timeout (increases with generations)
        base_timeout = 1800  # 30 seconds
        timeout_increase = 600  # 10 seconds per generation
        max_timeout = 12000  # 200 seconds cap

        new_timeout = min(
            base_timeout + (self.generation * timeout_increase),
            max_timeout
        )
        self.max_frames = new_timeout

        timeout_seconds = new_timeout / 60
        print(f"⏱️ Timeout: {timeout_seconds:.1f}s ({new_timeout} frames)")

        # Update UI with generation start
        window.updateRLStatus('training', f"🎮 Starting Generation {self.generation + 1}... (Best: {self.best_distance}px)")

        # Load saved state to restart level
        await self.game.load_saved_state()

        # Reset stats
        self.reset()
        self.current_fitness = 0

        # Continue training
        if self.is_training:
            self.training_loop()

    async def start_training(self, network_type='simple-feedforward'):
        """
        Start AI training.

        Args:
            network_type: Type of neural network to use ('simple-feedforward', 'dqn', 'neat', etc.)
        """
        print(f"🚀 Starting AI training with network: {network_type}")

        # Check if network type changed - if so, reset everything
        if network_type != self.network_type:
            print(f"🔄 Network type changed: {self.network_type} → {network_type}")
            print("🔄 Resetting agent for new network...")

            self.network_type = network_type

            # Reset all training stats
            self.generation = 0
            self.best_distance = 0
            self.best_fitness = 0
            self.current_fitness = 0
            self.champion_weights = None

            # Reinitialize neural network based on type
            print(f"✅ Switching to {network_type} network")
            self.neural = self._create_network(network_type)
            self._initialize_network()

            window.updateRLStatus('training', f'🔄 Switched to {network_type}. Starting fresh...')

        if not self.game.get_emulator():
            console.error("❌ Emulator not found")
            window.updateRLStatus('error', '❌ Emulator not found')
            return

        # Update UI - initializing
        window.updateRLStatus('training', '🔧 Initializing neural network...')

        # Take control from keyboard
        self.game.disable_keyboard()

        # Start emulator
        if not self.game.start_emulator():
            console.error("❌ Failed to start emulator")
            window.updateRLStatus('error', '❌ Failed to start emulator')
            return

        # Load saved state
        window.updateRLStatus('training', '📂 Loading game state...')
        print("📂 Loading saved state...")
        await self.game.load_saved_state()

        # Reset and start
        self.reset()
        self.is_training = True

        # Start first generation
        window.updateRLStatus('training', '🎮 Starting Generation 1... Let evolution begin!')
        self.training_loop()

        print("✅ Evolution started")

    def stop_training(self):
        """Stop AI training."""
        print("⏹️ Stopping training...")
        self.is_training = False
        self.game.stop_emulator()
        window.updateRLStatus('ready', 'Training stopped')
        print("✅ Training stopped")

    def pause_training(self):
        """Pause/resume training."""
        if self.is_training:
            print("⏸️ Pausing training...")
            self.is_training = False
            window.updateRLStatus('paused', 'Training paused')
        else:
            print("▶️ Resuming training...")
            self.is_training = True
            self.training_loop()
            window.updateRLStatus('training', 'Training resumed')

    def reset_training(self):
        """Reset agent and start fresh."""
        print("🔄 Resetting agent...")

        self.is_training = False
        self.reset()
        self._initialize_network()  # Reset with priors

        # Reset training stats
        self.generation = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.current_fitness = 0
        self.champion_weights = None  # Clear saved champion
        self.generations_stuck = 0

        self.game.stop_emulator()
        self.game.reset_emulator()

        window.updateRLStatus('ready', 'Agent reset. Ready to train!')
        print("✅ Reset complete")

    def load_weights(self, weights_data: dict):
        """
        Load pre-trained weights.

        Args:
            weights_data: Dict with 'weights' and 'biases'
        """
        self.neural.set_weights(
            weights_data['weights'],
            weights_data['biases']
        )
        print("✅ Weights loaded")


# Create global instance
print("🐍 Initializing PlayerAgent (modular)...")
_mario_agent = PlayerAgent()
print("✅ PlayerAgent ready")

# Export functions via PyScriptManager
manager = PyScriptManager("agent")
manager.signal_ready(extra_exports={
    'startRLTraining': _mario_agent.start_training,
    'pauseRLTraining': _mario_agent.pause_training,
    'resetRLTraining': _mario_agent.reset_training,
    'stopRLTraining': _mario_agent.stop_training,
    'toggleNetworkVisualization': _mario_agent.toggle_visualization
})

print("✅ PlayerAgent functions exported to JavaScript")

