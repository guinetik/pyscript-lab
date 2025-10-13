"""
Mario Agent - Neural Network Controller for Super Mario Bros
Simplified single-agent version for real-time gameplay visualization
"""
from js import console, window
import numpy as np

# Import neural network (loaded as separate script)
# The NeuralNetwork class will be available globally after neural.py loads


class MarioAgent:
    """
    Neural network agent that plays Super Mario Bros.
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
        self.network = NeuralNetwork([input_size, hidden_size, output_size], seed=42)

        # Button mapping (NES controller)
        self.BUTTON_A = 0
        self.BUTTON_B = 1
        self.BUTTON_SELECT = 2
        self.BUTTON_START = 3
        self.BUTTON_UP = 4
        self.BUTTON_DOWN = 5
        self.BUTTON_LEFT = 6
        self.BUTTON_RIGHT = 7

        # Stats tracking
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self.max_frames = 1200  # Maximum frames per episode (20 seconds at 60fps)

        console.log("🧠 Mario Agent initialized")
        console.log(f"   Network: {input_size} → {hidden_size} → {output_size}")

    def get_game_state(self) -> np.ndarray:
        """
        Extract game state from emulator.
        Returns a flattened array of tiles around Mario.

        For now, returns random state as placeholder.
        TODO: Extract actual tile data from NES RAM.
        """
        # Placeholder: random vision grid
        # In real implementation, we'd read NES RAM to get:
        # - Mario's position
        # - Tiles around Mario (blocks, enemies, pipes, etc.)
        # - Encode as: 0 = empty, 1 = solid block, -1 = enemy

        state = np.random.randn(self.vision_width * self.vision_height)
        return state

    def get_mario_position(self):
        """
        Get Mario's X position from RAM.
        Address 0x6D contains Mario's X position on screen.
        Address 0x86 contains page (screen) number.
        """
        emulator = window.nesEmulator
        if not emulator or not emulator.controller or not emulator.controller.nes:
            return 0

        try:
            nes = emulator.controller.nes
            # Mario's X position on screen (0-255)
            x_position = nes.cpu.mem[0x6D]
            # Current page/screen (0-255)
            page = nes.cpu.mem[0x86]
            # Total X position
            total_x = page * 256 + x_position
            return total_x
        except:
            return 0

    def is_mario_alive(self):
        """
        Check if Mario is alive.
        Address 0x0E contains player state (0x0B = dying, 0x06 = dead)
        Address 0x770 contains Mario's Y position (> 240 means fallen)
        """
        emulator = window.nesEmulator
        if not emulator or not emulator.controller or not emulator.controller.nes:
            return True

        try:
            nes = emulator.controller.nes
            # Player state
            player_state = nes.cpu.mem[0x0E]
            # Y position
            y_position = nes.cpu.mem[0x00B5]

            # Dead if player_state indicates death or fell off screen
            is_dead = player_state in [0x0B, 0x06] or y_position > 240
            return not is_dead
        except:
            return True

    def is_in_gameplay(self):
        """
        Check if we're actually in gameplay (not title screen or game over).
        Address 0x770 contains game state (0x00 = title, 0x01 = gameplay, etc.)
        """
        emulator = window.nesEmulator
        if not emulator or not emulator.controller or not emulator.controller.nes:
            return False

        try:
            nes = emulator.controller.nes
            # Game state - 0x0770 or try 0x770
            game_state = nes.cpu.mem[0x0770]
            # In gameplay if state is non-zero
            return game_state != 0x00
        except:
            # If we can't read, assume we need to press start
            return False

    def press_start(self):
        """Press START button to get through menus."""
        emulator = window.nesEmulator
        if emulator:
            try:
                emulator.buttonDown(1, self.BUTTON_START)
                # Hold for a few frames
                from js import setTimeout
                from pyodide.ffi import create_proxy

                def release_start():
                    if emulator:
                        emulator.buttonUp(1, self.BUTTON_START)

                proxy = create_proxy(release_start)
                setTimeout(proxy, 100)  # Release after 100ms
            except:
                pass

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
            console.log("⚠️ Emulator not found")
            return

        # Check if emulator is ready and running
        if not emulator.controller or not emulator.controller.nes:
            console.log("⚠️ Emulator not fully initialized")
            return

        if not emulator.isRunning():
            console.log("⚠️ Emulator not running")
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
            console.log(f"❌ Error executing action: {e}")

    def step(self):
        """
        Execute one step of the agent:
        1. Check if in gameplay (press START if not)
        2. Observe game state
        3. Decide action
        4. Execute action
        5. Track progress
        """
        # Check if we're in gameplay (not title/game over screen)
        if not self.is_in_gameplay():
            # Press START to get into gameplay
            self.press_start()
            console.log("📱 Not in gameplay, pressing START...")
            return True  # Continue waiting for gameplay to start

        self.frames += 1

        # Check timeout - episode too long
        if self.frames >= self.max_frames:
            console.log(f"⏰ Timeout! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Check if Mario is still alive
        if not self.is_mario_alive():
            console.log(f"💀 Mario died! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Get current game state
        state = self.get_game_state()

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
            console.log(f"🚫 Mario stuck! Episode ended. Frames: {self.frames}, Max X: {self.max_x}")
            return False  # Signal episode ended

        # Log progress occasionally
        if self.frames % 60 == 0:
            console.log(f"🎮 Frame {self.frames}/{self.max_frames}, X: {current_x}, Max X: {self.max_x}, Stuck: {self.stuck_frames}")

        self.last_x = current_x
        return True  # Episode continues

    def reset(self):
        """Reset agent stats for new episode."""
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        console.log("🔄 Agent reset")

    def load_weights(self, weights_data):
        """
        Load pre-trained weights.

        Args:
            weights_data: Dictionary with 'weights' and 'biases' arrays
        """
        self.network.set_weights(weights_data['weights'], weights_data['biases'])
        console.log("✅ Loaded pre-trained weights")

    def randomize_weights(self):
        """Randomize network weights (for exploration)."""
        for i in range(len(self.network.weights)):
            self.network.weights[i] = np.random.randn(*self.network.weights[i].shape) * 0.5
            self.network.biases[i] = np.random.randn(*self.network.biases[i].shape) * 0.5
        console.log("🎲 Weights randomized")


# Create global agent instance
console.log("🐍 Initializing Mario Agent...")
mario_agent = MarioAgent()
console.log("✅ Mario Agent ready")

# Training state
is_training = False
training_interval_id = None
current_episode = 0
episode_reward = 0
best_distance = 0
total_episodes = 0


def training_loop():
    """
    Main training loop - runs continuously while training.
    Makes decisions at ~15fps (every 4 frames at 60fps).
    """
    global is_training, episode_reward, current_episode, best_distance

    if not is_training:
        return

    # Make a decision (returns False if Mario died)
    alive = mario_agent.step()

    if not alive:
        # Episode ended - Mario died
        end_episode()
        return

    # Schedule next decision (every ~67ms = ~15 decisions per second)
    # This gives Mario time to react to each action
    from js import setTimeout
    from pyodide.ffi import create_proxy

    # Create a proxy that won't be garbage collected
    proxy = create_proxy(training_loop)
    setTimeout(proxy, 67)


def end_episode():
    """Handle end of episode - calculate reward and restart."""
    global current_episode, episode_reward, best_distance, total_episodes

    # Calculate reward (how far Mario got)
    distance = mario_agent.max_x
    episode_reward = distance

    # Track if this was better than previous
    improved = distance > best_distance

    # Update best distance
    if improved:
        best_distance = distance
        console.log(f"🎉 New best distance: {best_distance}!")

    total_episodes += 1

    console.log(f"📊 Episode {total_episodes} complete: Distance = {distance}, Best = {best_distance}")

    # Update UI metrics
    window.updateRLMetrics(total_episodes, episode_reward, best_distance)

    # Mutation strategy: if doing poorly, mutate more aggressively
    if distance < best_distance * 0.5:  # Less than 50% of best
        console.log("🎲 Poor performance - large mutation")
        mario_agent.network.mutate(mutation_rate=0.3, mutation_scale=1.0)
    elif improved:
        console.log("✨ Improved - small mutation")
        mario_agent.network.mutate(mutation_rate=0.05, mutation_scale=0.2)
    else:
        console.log("🔄 Normal mutation")
        mario_agent.network.mutate(mutation_rate=0.15, mutation_scale=0.5)

    # Wait for game to restart naturally, then continue
    from js import setTimeout
    from pyodide.ffi import create_proxy

    def restart_episode():
        if is_training:
            start_new_episode()

    proxy = create_proxy(restart_episode)
    setTimeout(proxy, 3000)  # Wait 3 seconds for death animation


def start_new_episode():
    """Start a new training episode - just reset stats, game continues."""
    global episode_reward

    console.log(f"🔄 Starting new episode {total_episodes + 1}")

    # Calculate timeout based on episode number
    # Start at 20 seconds (1200 frames), increase by 10 seconds per episode
    # Cap at 200 seconds (12000 frames)
    base_timeout = 1200  # 20 seconds
    timeout_increase = 600  # 10 seconds per episode
    max_timeout = 12000  # 200 seconds

    new_timeout = min(base_timeout + (total_episodes * timeout_increase), max_timeout)
    mario_agent.max_frames = new_timeout

    timeout_seconds = new_timeout / 60
    console.log(f"⏱️ Episode timeout set to {timeout_seconds:.1f} seconds ({new_timeout} frames)")

    # Just reset agent stats - don't touch emulator
    # The game will naturally respawn Mario or restart level
    mario_agent.reset()
    episode_reward = 0

    # Continue training loop
    if is_training:
        training_loop()


def start_training():
    """Start AI training - Mario plays automatically."""
    global is_training

    console.log("🚀 Starting AI training...")

    emulator = window.nesEmulator
    if not emulator:
        console.log("❌ Emulator not found")
        return

    # Disable keyboard (AI takes over)
    emulator.disableKeyboard()

    # Start emulator if not running
    if not emulator.isRunning():
        console.log("▶️ Starting emulator for AI")
        emulator.start()
    else:
        console.log("✅ Emulator already running")

    # Reset agent stats
    mario_agent.reset()

    # Start training loop
    is_training = True
    training_loop()

    # Update UI
    window.updateRLStatus('training', 'AI is playing Mario! Watch and learn...')

    console.log("✅ AI training started")


def stop_training():
    """Stop AI training."""
    global is_training

    console.log("⏹️ Stopping AI training...")
    is_training = False

    # Stop emulator
    emulator = window.nesEmulator
    if emulator:
        emulator.stop()

    window.updateRLStatus('ready', 'AI training stopped. Ready for next action.')
    console.log("✅ AI training stopped")


def pause_training():
    """Pause/resume AI training."""
    global is_training

    if is_training:
        console.log("⏸️ Pausing AI training...")
        is_training = False
        window.updateRLStatus('paused', 'AI training paused')
    else:
        console.log("▶️ Resuming AI training...")
        is_training = True
        training_loop()
        window.updateRLStatus('training', 'AI training resumed')


def reset_training():
    """Reset AI and game."""
    console.log("🔄 Resetting AI training...")

    global is_training
    is_training = False

    mario_agent.reset()
    mario_agent.randomize_weights()

    emulator = window.nesEmulator
    if emulator:
        emulator.stop()
        emulator.reset()

    window.updateRLStatus('ready', 'AI reset. Click "Start Training" to begin.')
    console.log("✅ AI reset complete")


# Expose functions to JavaScript
window.startRLTraining = start_training
window.pauseRLTraining = pause_training
window.resetRLTraining = reset_training
window.stopRLTraining = stop_training

console.log("✅ Mario Agent functions exposed to window")
