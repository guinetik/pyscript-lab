"""
Player Agent - Neural Network Controller for Super Mario Bros

Reinforcement Learning agent that learns to play Mario through trial and error.
Uses PyScriptManager for clean event-driven initialization.

Author: Guinetik
"""
from js import console, window, setTimeout
from pyodide.ffi import create_proxy
import numpy as np
from lib.pyscript_manager import PyScriptManager
from lib.nes.nes_ram_utils import (
    extract_vision_grid,
    get_mario_position,
    get_mario_state,
    get_mario_tile_position
)

# Import neural network (loaded as separate script)
# The NeuralNetwork class will be available globally after neural.py loads


class MarioAgent:
    """
    Neural network agent that plays Super Player Bros.
    Observes game state and outputs controller inputs.
    """

    def __init__(self, vision_width: int = 13, vision_height: int = 10):
        """
        Initialize Mario agent.

        Args:
            vision_width: How many tiles wide Mario can "see"
            vision_height: How many tiles tall Mario can "see"
        """
        self.vision_width = vision_width
        self.vision_height = vision_height

        # Neural network architecture
        input_size = vision_width * vision_height  # Tile grid around Mario
        hidden_size = 32  # Hidden layer
        output_size = 6  # [UP, DOWN, LEFT, RIGHT, A, B]

        # Get NeuralNetwork class from builtins (loaded by neural.py)
        import builtins
        NeuralNetwork = builtins.NeuralNetwork
        # Use random seed for diverse weight initialization
        self.network = NeuralNetwork([input_size, hidden_size, output_size], seed=None)

        # Button mapping (NES controller)
        self.BUTTON_A = 0
        self.BUTTON_B = 1
        self.BUTTON_SELECT = 2
        self.BUTTON_START = 3
        self.BUTTON_UP = 4
        self.BUTTON_DOWN = 5
        self.BUTTON_LEFT = 6
        self.BUTTON_RIGHT = 7

        # Episode stats tracking
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.max_frames = 1200  # Maximum frames per episode (20 seconds at 60fps)

        # Training state
        self.is_training = False
        self.current_episode = 0
        self.episode_reward = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.total_episodes = 0

        # Death tracking
        self.death_cause = None  # 'enemy', 'pit', 'timeout', 'stuck'

        print("🧠 Mario Agent initialized")
        print(f"   Network: {input_size} → {hidden_size} → {output_size}")

    def get_game_state(self) -> np.ndarray:
        """
        Extract game state (vision grid) from emulator.

        Returns:
            np.ndarray: Vision grid (width × height floats)
        """
        nes = self._get_nes()
        if not nes:
            return np.zeros(self.vision_width * self.vision_height)

        try:
            # Delegate to utility function
            vision = extract_vision_grid(nes, width=self.vision_width, height=self.vision_height)
            return np.array(vision, dtype=np.float32)
        except Exception as e:
            print(f"❌ Error extracting game state: {e}")
            return np.zeros(self.vision_width * self.vision_height)

    def _get_nes(self):
        """
        Get NES instance from emulator.
        Returns None if not available.
        """
        emulator = window.nesEmulator
        if not emulator or not emulator.controller or not emulator.controller.nes:
            return None
        return emulator.controller.nes

    def get_mario_position(self):
        """Get Mario's X position in pixels."""
        nes = self._get_nes()
        if not nes:
            return 0

        x, y = get_mario_position(nes)
        return x

    def is_mario_alive(self):
        """Check if Mario is alive."""
        nes = self._get_nes()
        if not nes:
            return True

        state = get_mario_state(nes)
        return state == 'alive'

    def decide_action(self, state: np.ndarray) -> np.ndarray:
        """
        Use neural network to decide which buttons to press.

        Args:
            state: Game state (flattened tile grid)

        Returns:
            Button states [UP, DOWN, LEFT, RIGHT, A, B]
        """
        # Forward pass through network
        output = self.network.forward(state)

        # Use variable threshold instead of fixed 0.5
        # This adds more variety to the button combinations
        thresholds = np.random.uniform(0.4, 0.6, size=output.shape)
        buttons = (output > thresholds).astype(int).flatten()

        return buttons

    def execute_action(self, buttons: np.ndarray):
        """
        Execute button presses on the emulator.
        Buttons stay pressed until next action.

        Args:
            buttons: Array of button states [UP, DOWN, LEFT, RIGHT, A, B]
        """
        emulator = window.nesEmulator

        if not emulator:
            print("⚠️ Emulator not found")
            return

        # Check if emulator is ready and running
        if not emulator.controller or not emulator.controller.nes:
            print("⚠️ Emulator not fully initialized")
            return

        if not emulator.isRunning():
            print("⚠️ Emulator not running")
            return

        try:
            # Map network outputs to NES controller buttons
            button_map = [
                self.BUTTON_UP,
                self.BUTTON_DOWN,
                self.BUTTON_LEFT,
                self.BUTTON_RIGHT,
                self.BUTTON_A,
                self.BUTTON_B
            ]

            # Release all buttons first
            for button in button_map:
                emulator.buttonUp(1, button)

            # Press buttons that are "on"
            for i, pressed in enumerate(buttons):
                if pressed:
                    emulator.buttonDown(1, button_map[i])
        except Exception as e:
            print(f"❌ Error executing action: {e}")

    def visualize_vision(self, state):
        """
        Print a visual representation of what Mario sees.
        Helps debug the vision system.

        Args:
            state: Flattened vision array
        """
        print("\n👁️ Mario's Vision:")
        vision_2d = state.reshape(self.vision_height, self.vision_width)

        for row in vision_2d:
            line = ""
            for val in row:
                if val < -0.5:      # Enemy
                    line += "E"
                elif val > 0.5:     # Solid
                    line += "#"
                else:               # Empty
                    line += "."
            print(line)
        print("")

    def step(self):
        """
        Execute one step of the agent:
        1. Observe game state
        2. Decide action
        3. Execute action
        4. Track progress

        Note: User must manually start the game before training.
        """
        self.frames += 1

        # Check timeout - episode too long
        if self.frames >= self.max_frames:
            self.death_cause = 'timeout'
            print(f"⏰ Timeout! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Check if Mario is still alive
        if not self.is_mario_alive():
            self.death_cause = 'enemy'  # Most deaths are from enemies
            print(f"💀 Mario died! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Get current game state
        state = self.get_game_state()

        # Debug: visualize vision every 5 seconds
        if self.frames % 300 == 0:
            self.visualize_vision(state)

        # Decide what to do
        buttons = self.decide_action(state)

        # Execute action
        self.execute_action(buttons)

        # Track progress using actual X position
        current_x = self.get_mario_position()

        if current_x > self.max_x:
            self.max_x = current_x
            self.stuck_frames = 0
        else:
            self.stuck_frames += 1

        # Check if stuck (no progress for 1 second)
        if self.stuck_frames > 60:  # 1 second at 60fps
            self.death_cause = 'stuck'
            print(f"🚫 Mario stuck! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Log progress occasionally
        if self.frames % 60 == 0:
            print(f"🎮 Frame {self.frames}/{self.max_frames}, X: {current_x}, Max X: {self.max_x}, Stuck: {self.stuck_frames}")

            # Debug: Check if we're actually getting vision data
            if self.frames == 60:
                print(f"🔍 Debug - Vision sample: {state[:10]}...")
                print(f"🔍 Debug - Vision has data: {not all(v == 0 for v in state)}")

        self.last_x = current_x
        return True  # Episode continues

    def reset(self):
        """Reset agent stats for new episode."""
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.death_cause = None
        print("🔄 Agent reset")

    def load_weights(self, weights_data):
        """
        Load pre-trained weights.

        Args:
            weights_data: Dictionary with 'weights' and 'biases' arrays
        """
        self.network.set_weights(weights_data['weights'], weights_data['biases'])
        print("✅ Loaded pre-trained weights")

    def randomize_weights(self):
        """Randomize network weights (for exploration)."""
        for i in range(len(self.network.weights)):
            self.network.weights[i] = np.random.randn(*self.network.weights[i].shape) * 0.5
            self.network.biases[i] = np.random.randn(*self.network.biases[i].shape) * 0.5
        print("🎲 Weights randomized")


    def training_loop(self):
        """
        Main training loop - runs continuously while training.
        Makes decisions at ~15fps (every 4 frames at 60fps).
        """
        if not self.is_training:
            return

        # Make a decision (returns False if Mario died)
        alive = self.step()

        if not alive:
            # Episode ended - Mario died
            self.end_episode()
            return

        # Schedule next decision (every ~67ms = ~15 decisions per second)
        # This gives Mario time to react to each action
        proxy = create_proxy(self.training_loop)
        setTimeout(proxy, 67)


    def calculate_fitness(self):
        """
        Calculate fitness score for this episode.

        Inspired by chrispresso's SMB-AI project fitness function:
        - Rewards distance exponentially (going far is REALLY good)
        - Penalizes taking too long (encourages moving quickly)
        - Penalizes deaths (especially early deaths)
        - Small bonus for reaching certain milestones

        Returns:
            float: Fitness score
        """
        distance = self.max_x
        frames = self.frames

        # Base fitness: exponential reward for distance
        # distance^1.5 rewards going far exponentially
        # 50 pixels = 353, 100 pixels = 1000, 200 pixels = 2828
        distance_reward = (distance ** 1.5) if distance > 0 else 0

        # Time penalty: None for now, just focus on distance
        # (We'll add this back later with neuroevolution)
        time_penalty = 0

        # Death penalty based on cause (very light - just a nudge)
        death_penalty = 0
        if self.death_cause == 'enemy':
            death_penalty = 50  # Slight penalty for dying to enemy
        elif self.death_cause == 'stuck':
            death_penalty = 20  # Very light penalty for getting stuck
        elif self.death_cause == 'timeout':
            death_penalty = 0  # No penalty for timeout!

        # Milestone bonuses (encourage progress)
        milestone_bonus = 0
        if distance > 50:    # Got past first goomba area
            milestone_bonus += 200
        if distance > 100:   # Significant progress
            milestone_bonus += 500
        if distance > 200:   # Really good!
            milestone_bonus += 1000
        if distance > 400:   # Excellent!
            milestone_bonus += 2000
        if distance > 800:   # Amazing!
            milestone_bonus += 5000

        # Calculate final fitness
        # Max with small positive to avoid negative fitness (breaks roulette selection)
        fitness = max(distance_reward - time_penalty - death_penalty + milestone_bonus, 1.0)

        return fitness

    def end_episode(self):
        """Handle end of episode - calculate fitness and mutate."""
        distance = self.max_x

        # Calculate fitness score
        fitness = self.calculate_fitness()
        self.episode_reward = fitness

        # Track if this was better than previous
        improved_distance = distance > self.best_distance
        improved_fitness = fitness > self.best_fitness

        # Update bests
        if improved_distance:
            self.best_distance = distance
            print(f"🎉 New best distance: {self.best_distance}!")

        if improved_fitness:
            self.best_fitness = fitness
            print(f"🏆 New best fitness: {self.best_fitness:.1f}!")

        self.total_episodes += 1

        print(f"📊 Episode {self.total_episodes} complete:")
        print(f"   Distance: {distance}, Fitness: {fitness:.1f}")
        print(f"   Cause: {self.death_cause}, Frames: {self.frames}")
        print(f"   Best Distance: {self.best_distance}, Best Fitness: {self.best_fitness:.1f}")

        # Update UI metrics (show fitness as reward)
        window.updateRLMetrics(self.total_episodes, self.episode_reward, self.best_distance)

        # Mutation strategy based on fitness improvement
        if fitness < self.best_fitness * 0.3:  # Really bad performance
            print("🎲 Terrible performance - very large mutation")
            self.network.mutate(mutation_rate=0.5, mutation_scale=1.5)
        elif fitness < self.best_fitness * 0.6:  # Poor performance
            print("🎲 Poor performance - large mutation")
            self.network.mutate(mutation_rate=0.3, mutation_scale=1.0)
        elif improved_fitness:  # Improvement!
            print("✨ Improved - small mutation to refine")
            self.network.mutate(mutation_rate=0.05, mutation_scale=0.2)
        else:  # Decent but not improving
            print("🔄 Normal mutation")
            self.network.mutate(mutation_rate=0.15, mutation_scale=0.5)

        # Wait a bit then restart with saved state
        async def restart_episode():
            if self.is_training:
                await self.start_new_episode()

        proxy = create_proxy(restart_episode)
        setTimeout(proxy, 1000)  # Wait 1 second then reload state


    async def start_new_episode(self):
        """Start a new training episode - reset to saved state."""
        print(f"🔄 Starting new episode {self.total_episodes + 1}")

        # Calculate timeout based on episode number
        # Start at 20 seconds (1200 frames), increase by 10 seconds per episode
        # Cap at 200 seconds (12000 frames)
        base_timeout = 1200  # 20 seconds
        timeout_increase = 600  # 10 seconds per episode
        max_timeout = 12000  # 200 seconds

        new_timeout = min(base_timeout + (self.total_episodes * timeout_increase), max_timeout)
        self.max_frames = new_timeout

        timeout_seconds = new_timeout / 60
        print(f"⏱️ Episode timeout set to {timeout_seconds:.1f} seconds ({new_timeout} frames)")

        # Load saved state to restart at level 1-1
        await self._load_saved_state()

        # Reset agent stats
        self.reset()
        self.episode_reward = 0

        # Continue training loop
        if self.is_training:
            self.training_loop()

    async def _load_saved_state(self):
        """Helper to load the saved state file."""
        try:
            from js import fetch, JSON

            emulator = window.nesEmulator
            if not emulator:
                return

            # Fetch and parse state
            response = await fetch('/data/nes_state.json')
            state_json = await response.text()
            state_obj = JSON.parse(state_json)

            # Load into emulator
            if emulator.controller and emulator.controller.loadState:
                emulator.controller.loadState(state_obj)
                print("♻️ Reloaded saved state")
        except Exception as e:
            print(f"⚠️ Could not reload state: {e}")


    async def start_training(self):
        """Start AI training - Mario plays automatically."""
        print("🚀 Starting AI training...")

        emulator = window.nesEmulator
        if not emulator:
            print("❌ Emulator not found")
            return

        # Disable keyboard (AI takes over)
        emulator.disableKeyboard()

        # Start emulator if not running
        if not emulator.isRunning():
            print("▶️ Starting emulator for AI")
            emulator.start()
        else:
            print("✅ Emulator already running")

        # Load saved state to start at beginning of level 1-1
        print("📂 Loading saved state from /data/nes_state.json...")
        await self._load_saved_state()

        # Reset agent stats
        self.reset()

        # Start training loop
        self.is_training = True
        self.training_loop()

        # Update UI
        window.updateRLStatus('training', 'AI is playing Mario! Watch and learn...')

        print("✅ AI training started")

    def stop_training(self):
        """Stop AI training."""
        print("⏹️ Stopping AI training...")
        self.is_training = False

        # Stop emulator
        emulator = window.nesEmulator
        if emulator:
            emulator.stop()

        window.updateRLStatus('ready', 'AI training stopped. Ready for next action.')
        print("✅ AI training stopped")

    def pause_training(self):
        """Pause/resume AI training."""
        if self.is_training:
            print("⏸️ Pausing AI training...")
            self.is_training = False
            window.updateRLStatus('paused', 'AI training paused')
        else:
            print("▶️ Resuming AI training...")
            self.is_training = True
            self.training_loop()
            window.updateRLStatus('training', 'AI training resumed')

    def reset_training(self):
        """Reset AI and game."""
        print("🔄 Resetting AI training...")

        self.is_training = False
        self.reset()
        self.randomize_weights()

        # Reset training stats
        self.total_episodes = 0
        self.best_distance = 0
        self.episode_reward = 0

        emulator = window.nesEmulator
        if emulator:
            emulator.stop()
            emulator.reset()

        window.updateRLStatus('ready', 'AI reset. Click "Start Training" to begin.')
        print("✅ AI reset complete")


# Create global instance
print("🐍 Initializing Mario Agent...")
_mario_agent = MarioAgent()
print("✅ Mario Agent ready")

# Signal ready via PyScriptManager with exported functions
# Module name must match the filename (player_agent) for script ID matching
manager = PyScriptManager("player_agent")
manager.signal_ready(extra_exports={
    'startRLTraining': _mario_agent.start_training,
    'pauseRLTraining': _mario_agent.pause_training,
    'resetRLTraining': _mario_agent.reset_training,
    'stopRLTraining': _mario_agent.stop_training
})

print("✅ Mario Agent functions exposed and signaled to JavaScript")
