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
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder


class PlayerAgent:
    """
    Reinforcement learning agent that learns to play Super Mario Bros.
    Uses composition for clean separation of concerns.
    """

    def __init__(
        self,
        vision_width: int = 13,
        vision_height: int = 10,
        hidden_size: int = 32
    ):
        """
        Initialize Player agent with modular components.

        Args:
            vision_width: Width of vision grid in tiles
            vision_height: Height of vision grid in tiles
            hidden_size: Number of hidden neurons
        """
        # Game controller - handles all emulator interaction
        self.game = GameController(
            vision_width=vision_width,
            vision_height=vision_height
        )

        # Neural controller - handles decision making
        input_size = vision_width * vision_height
        output_size = 6  # [UP, DOWN, LEFT, RIGHT, A, B]
        
        self.neural = SimpleNeuralController(
            input_size=input_size,
            hidden_size=hidden_size,
            output_size=output_size,
            seed=None  # Random initialization
        )

        # Action decoder - converts neural outputs to buttons
        self.decoder = ActionDecoder(use_variable_threshold=True)

        # Episode tracking
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.max_frames = 1200  # 20 seconds at 60fps

        # Training state
        self.is_training = False
        self.total_episodes = 0
        self.episode_reward = 0
        self.best_distance = 0
        self.best_fitness = 0

        # Elite preservation - save champion weights
        self.champion_weights = None

        # Death tracking
        self.death_cause = None  # 'enemy', 'timeout', 'stuck'

        # Current neural network type
        self.network_type = 'simple-feedforward'

        console.log("🤖 PlayerAgent initialized with modular architecture")
        console.log(f"   Input: {input_size}, Hidden: {hidden_size}, Output: {output_size}")
        console.log(f"   Network type: {self.network_type}")

    def observe(self) -> np.ndarray:
        """
        Observe the current game state.

        Returns:
            np.ndarray: Vision grid (flattened)
        """
        return self.game.get_vision_state()

    def decide(self, state: np.ndarray) -> np.ndarray:
        """
        Decide which buttons to press based on observation.

        Args:
            state: Observed game state

        Returns:
            np.ndarray: Button states [UP, DOWN, LEFT, RIGHT, A, B]
        """
        # Neural network forward pass
        output = self.neural.forward(state)
        
        # Decode to button presses
        buttons = self.decoder.decode(output)
        
        return buttons

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
            console.log(f"⏰ Timeout! Frames: {self.frames}, Max X: {self.max_x}")
            return False

        # Check if Mario is alive
        if not self.game.is_mario_alive():
            self.death_cause = 'enemy'
            console.log(f"💀 Mario died! Frames: {self.frames}, Max X: {self.max_x}")
            return False

        # Observe
        state = self.observe()

        # Debug: visualize vision periodically
        if self.frames % 300 == 0:
            self.game.visualize_vision(state)

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
            console.log(f"🚫 Mario stuck! Frames: {self.frames}, Max X: {self.max_x}")
            return False

        # Log progress occasionally
        if self.frames % 60 == 0:
            console.log(f"🎮 Frame {self.frames}/{self.max_frames}, X: {current_x}, Max: {self.max_x}")

            # Update UI every 3 seconds (180 frames) with live progress
            if self.frames % 180 == 0:
                progress_pct = int((current_x / self.best_distance * 100)) if self.best_distance > 0 else 0
                window.updateRLStatus('training', f"🏃 Episode {self.total_episodes + 1}: {current_x}px ({progress_pct}% of best)")

        self.last_x = current_x
        return True  # Episode continues

    def calculate_fitness(self) -> float:
        """
        Calculate fitness score for this episode.

        Fitness function:
        - Exponential reward for distance (distance^1.5)
        - Light penalties for different death types
        - Milestone bonuses for progress

        Returns:
            float: Fitness score (always > 0)
        """
        distance = self.max_x

        # Base fitness: exponential distance reward
        distance_reward = (distance ** 1.5) if distance > 0 else 0

        # Death penalties
        death_penalty = 0
        if self.death_cause == 'enemy':
            death_penalty = 50
        elif self.death_cause == 'stuck':
            death_penalty = 20
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
            distance_reward - death_penalty + milestone_bonus,
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
        fitness = self.calculate_fitness()
        self.episode_reward = fitness

        # Track improvements
        improved_distance = distance > self.best_distance
        improved_fitness = fitness > self.best_fitness

        if improved_distance:
            self.best_distance = distance
            console.log(f"🎉 New best distance: {self.best_distance}!")

        if improved_fitness:
            self.best_fitness = fitness
            console.log(f"🏆 New best fitness: {self.best_fitness:.1f}!")

            # Save champion weights for elite preservation
            self.champion_weights = self.neural.get_weights()
            console.log("💾 Saved champion weights")

        self.total_episodes += 1

        console.log(f"📊 Episode {self.total_episodes} complete:")
        console.log(f"   Distance: {distance}, Fitness: {fitness:.1f}")
        console.log(f"   Cause: {self.death_cause}, Frames: {self.frames}")
        console.log(f"   Best Distance: {self.best_distance}, Best Fitness: {self.best_fitness:.1f}")

        # Update UI metrics
        window.updateRLMetrics(self.total_episodes, self.episode_reward, self.best_distance)

        # User-friendly status message based on what happened
        death_messages = {
            'enemy': '💀 Hit an enemy',
            'stuck': '🚫 Got stuck',
            'timeout': '⏰ Time ran out'
        }
        death_msg = death_messages.get(self.death_cause, '❌ Episode ended')

        # Show different messages for improvements
        if improved_fitness:
            status_msg = f"🎉 New record! Distance: {distance}px | {death_msg}"
        else:
            status_msg = f"Episode {self.total_episodes}: {distance}px | {death_msg} | Best: {self.best_distance}px"

        window.updateRLStatus('training', status_msg)

        # Adaptive mutation based on performance with elite preservation
        mutation_strategy = ""
        if fitness < self.best_fitness * 0.3:
            # Really bad - restore champion and try tiny variations
            if self.champion_weights:
                console.log("🏆 Restoring champion and trying tiny mutation")
                mutation_strategy = "Back to champion, trying variation..."

                # IMPORTANT: Make deep copies so we don't mutate the champion itself!
                import copy
                champion_weights_copy = copy.deepcopy(self.champion_weights['weights'])
                champion_biases_copy = copy.deepcopy(self.champion_weights['biases'])

                self.neural.set_weights(champion_weights_copy, champion_biases_copy)
                # VERY gentle mutation - only 2% of weights, very small changes
                self.neural.mutate(mutation_rate=0.02, mutation_scale=0.1)
            else:
                console.log("🎲 Terrible performance - large mutation")
                mutation_strategy = "Trying radical changes..."
                self.neural.mutate(mutation_rate=0.3, mutation_scale=0.8)
        elif fitness < self.best_fitness * 0.6:
            console.log("🎲 Poor performance - moderate mutation")
            mutation_strategy = "Exploring new strategies..."
            self.neural.mutate(mutation_rate=0.15, mutation_scale=0.5)
        elif improved_fitness:
            console.log("✨ Improved - tiny mutation to refine")
            mutation_strategy = "Refining winning strategy..."
            self.neural.mutate(mutation_rate=0.02, mutation_scale=0.1)
        else:
            console.log("🔄 Normal mutation")
            mutation_strategy = "Making small adjustments..."
            self.neural.mutate(mutation_rate=0.08, mutation_scale=0.3)

        # Show mutation strategy briefly
        if mutation_strategy:
            window.updateRLStatus('training', f"🧬 {mutation_strategy}")

        # Wait then restart episode
        async def restart_episode():
            if self.is_training:
                await self.start_new_episode()

        proxy = create_proxy(restart_episode)
        setTimeout(proxy, 1000)

    async def start_new_episode(self):
        """Start a new training episode."""
        console.log(f"🔄 Starting episode {self.total_episodes + 1}")

        # Progressive timeout (increases with episodes)
        base_timeout = 1200  # 20 seconds
        timeout_increase = 600  # 10 seconds per episode
        max_timeout = 12000  # 200 seconds cap

        new_timeout = min(
            base_timeout + (self.total_episodes * timeout_increase),
            max_timeout
        )
        self.max_frames = new_timeout

        timeout_seconds = new_timeout / 60
        console.log(f"⏱️ Timeout: {timeout_seconds:.1f}s ({new_timeout} frames)")

        # Update UI with episode start
        window.updateRLStatus('training', f"🎮 Starting Episode {self.total_episodes + 1}... (Best: {self.best_distance}px)")

        # Load saved state to restart level
        await self.game.load_saved_state()

        # Reset stats
        self.reset()
        self.episode_reward = 0

        # Continue training
        if self.is_training:
            self.training_loop()

    async def start_training(self, network_type='simple-feedforward'):
        """
        Start AI training.

        Args:
            network_type: Type of neural network to use ('simple-feedforward', 'dqn', 'neat', etc.)
        """
        console.log(f"🚀 Starting AI training with network: {network_type}")

        # Check if network type changed - if so, reset everything
        if network_type != self.network_type:
            console.log(f"🔄 Network type changed: {self.network_type} → {network_type}")
            console.log("🔄 Resetting agent for new network...")

            self.network_type = network_type

            # Reset all training stats
            self.total_episodes = 0
            self.best_distance = 0
            self.best_fitness = 0
            self.episode_reward = 0
            self.champion_weights = None

            # Reinitialize neural network based on type
            # For now, we only have simple-feedforward
            if network_type == 'simple-feedforward':
                console.log("✅ Using Simple Feedforward network")
                self.neural.randomize()
            else:
                console.log(f"⚠️ Network type '{network_type}' not yet implemented, using simple-feedforward")
                self.network_type = 'simple-feedforward'
                self.neural.randomize()

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
        console.log("📂 Loading saved state...")
        await self.game.load_saved_state()

        # Reset and start
        self.reset()
        self.is_training = True

        # Start first episode
        window.updateRLStatus('training', '🎮 Starting Episode 1... Let\'s learn!')
        self.training_loop()

        console.log("✅ Training started")

    def stop_training(self):
        """Stop AI training."""
        console.log("⏹️ Stopping training...")
        self.is_training = False
        self.game.stop_emulator()
        window.updateRLStatus('ready', 'Training stopped')
        console.log("✅ Training stopped")

    def pause_training(self):
        """Pause/resume training."""
        if self.is_training:
            console.log("⏸️ Pausing training...")
            self.is_training = False
            window.updateRLStatus('paused', 'Training paused')
        else:
            console.log("▶️ Resuming training...")
            self.is_training = True
            self.training_loop()
            window.updateRLStatus('training', 'Training resumed')

    def reset_training(self):
        """Reset agent and start fresh."""
        console.log("🔄 Resetting agent...")

        self.is_training = False
        self.reset()
        self.neural.randomize()

        # Reset training stats
        self.total_episodes = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.episode_reward = 0
        self.champion_weights = None  # Clear saved champion

        self.game.stop_emulator()
        self.game.reset_emulator()

        window.updateRLStatus('ready', 'Agent reset. Ready to train!')
        console.log("✅ Reset complete")

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
        console.log("✅ Weights loaded")


# Create global instance
console.log("🐍 Initializing PlayerAgent (modular)...")
_mario_agent = PlayerAgent()
console.log("✅ PlayerAgent ready")

# Export functions via PyScriptManager
manager = PyScriptManager("agent")
manager.signal_ready(extra_exports={
    'startRLTraining': _mario_agent.start_training,
    'pauseRLTraining': _mario_agent.pause_training,
    'resetRLTraining': _mario_agent.reset_training,
    'stopRLTraining': _mario_agent.stop_training
})

console.log("✅ PlayerAgent functions exported to JavaScript")

