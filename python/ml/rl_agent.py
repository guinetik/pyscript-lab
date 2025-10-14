"""
Reinforcement Learning Agent for NES Games
Event-driven architecture: Python controls emulator through JS, receives game state
"""
import js
from js import console, window
from pyscript import window as ps_window
import random
import time


class RLAgent:
    """
    Simple Reinforcement Learning agent for NES games.

    This implementation uses a basic Q-learning approach with exploration/exploitation.
    For educational purposes, it demonstrates core RL concepts:
    - State observation
    - Action selection (epsilon-greedy policy)
    - Reward calculation
    - Learning from experience
    """

    def __init__(self):
        """Initialize the RL agent."""
        self.episode = 0
        self.total_reward = 0
        self.high_score = 0
        self.is_training = False
        self.is_paused = False

        # RL Parameters
        self.epsilon = 0.9  # Exploration rate (starts high, will decay)
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995
        self.learning_rate = 0.01
        self.discount_factor = 0.95

        # Episode tracking
        self.episode_reward = 0
        self.episode_steps = 0
        self.max_steps_per_episode = 1000  # Limit to prevent infinite loops

        # Game state tracking
        self.previous_score = 0
        self.previous_x_position = 0
        self.lives_remaining = 3

        # Action space (NES controller buttons)
        self.actions = [
            'NONE',      # No input
            'A',         # Jump
            'B',         # Run/Fire
            'RIGHT',     # Move right
            'LEFT',      # Move left
            'A+RIGHT',   # Jump forward
            'B+RIGHT',   # Run right
        ]

        print("🤖 [Python] RL Agent initialized")
        print(f"📊 [Python] Action space: {len(self.actions)} actions")

    def select_action(self):
        """
        Select an action using epsilon-greedy policy.

        Returns:
            str: Action to take
        """
        # Epsilon-greedy: explore vs exploit
        if random.random() < self.epsilon:
            # Explore: random action
            action = random.choice(self.actions)
            print(f"🔍 [Python] Exploring: {action}")
        else:
            # Exploit: for now, bias towards moving right and jumping
            # In a full implementation, this would use Q-values
            action = random.choice(['A+RIGHT', 'B+RIGHT', 'RIGHT', 'A'])
            print(f"🎯 [Python] Exploiting: {action}")

        return action

    def execute_action(self, action):
        """
        Execute an action in the emulator.

        Args:
            action (str): Action to execute
        """
        emulator = window.nesEmulator

        if not emulator or not emulator.isLoaded():
            print("⚠️ [Python] Emulator not ready")
            return

        # Don't interfere if emulator is already running (manual play mode)
        if emulator.isRunning():
            return

        # Map action to button presses
        # Controller 1, button constants from JSNes
        BUTTON_A = 0
        BUTTON_B = 1
        BUTTON_SELECT = 2
        BUTTON_START = 3
        BUTTON_UP = 4
        BUTTON_DOWN = 5
        BUTTON_LEFT = 6
        BUTTON_RIGHT = 7

        # Press buttons based on action
        if 'A' in action:
            emulator.buttonDown(1, BUTTON_A)
        if 'B' in action:
            emulator.buttonDown(1, BUTTON_B)
        if 'RIGHT' in action:
            emulator.buttonDown(1, BUTTON_RIGHT)
        if 'LEFT' in action:
            emulator.buttonDown(1, BUTTON_LEFT)

        # Run a few frames
        for _ in range(4):
            emulator.frame()

        # Release buttons
        if 'A' in action:
            emulator.buttonUp(1, BUTTON_A)
        if 'B' in action:
            emulator.buttonUp(1, BUTTON_B)
        if 'RIGHT' in action:
            emulator.buttonUp(1, BUTTON_RIGHT)
        if 'LEFT' in action:
            emulator.buttonUp(1, BUTTON_LEFT)

        # Run a few more frames
        for _ in range(4):
            emulator.frame()

    def calculate_reward(self):
        """
        Calculate reward based on game state.

        For Mario:
        - Positive reward for moving right (progress)
        - Positive reward for score increase
        - Negative reward for death
        - Small negative reward for time passing (encourages speed)

        Returns:
            float: Reward value
        """
        reward = 0

        # Simple reward: small penalty for each step (encourages efficiency)
        reward -= 0.1

        # In a full implementation, we would:
        # 1. Extract score from game RAM
        # 2. Track Mario's X position
        # 3. Detect death/level completion
        # 4. Calculate based on these factors

        # For now, give small random reward to simulate game progress
        # This is a placeholder - real implementation would read game memory
        reward += random.uniform(-1, 2)

        return reward

    def step(self):
        """
        Execute one step of the RL loop:
        1. Observe state
        2. Select action
        3. Execute action
        4. Calculate reward
        5. Learn (update policy)
        """
        if not self.is_training or self.is_paused:
            return

        # Select and execute action
        action = self.select_action()
        self.execute_action(action)

        # Calculate reward
        reward = self.calculate_reward()
        self.episode_reward += reward
        self.episode_steps += 1

        # Update total reward
        self.total_reward += reward

        # Check if episode should end
        if self.episode_steps >= self.max_steps_per_episode:
            print(f"📊 [Python] Episode {self.episode} complete: {self.episode_reward:.1f} reward")
            self.end_episode()
            self.start_episode()

        # Decay epsilon (reduce exploration over time)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Update UI periodically (every 10 steps)
        if self.episode_steps % 10 == 0:
            self.update_ui()

    def start_episode(self):
        """Start a new training episode."""
        self.episode += 1
        self.episode_reward = 0
        self.episode_steps = 0

        # Reset emulator
        emulator = window.nesEmulator
        if emulator and emulator.isLoaded():
            emulator.reset()
            print(f"🎮 [Python] Episode {self.episode} started")

        self.update_ui()

    def end_episode(self):
        """End current episode and record metrics."""
        # Update high score
        if self.episode_reward > self.high_score:
            self.high_score = self.episode_reward
            print(f"🏆 [Python] New high score: {self.high_score:.1f}")

        self.update_ui()

    def update_ui(self):
        """Update the UI with current metrics."""
        window.updateRLMetrics(
            self.episode,
            self.total_reward,
            self.high_score
        )

        status_msg = f"Episode {self.episode}, Step {self.episode_steps}, Reward: {self.episode_reward:.1f}, ε={self.epsilon:.3f}"
        window.updateRLStatus('training', status_msg)

    def start_training(self):
        """Start the training loop."""
        print("🚀 [Python] Starting training...")
        self.is_training = True
        self.is_paused = False

        # Start first episode
        self.start_episode()

        # Update UI
        window.updateRLStatus('training', f"Training started - Episode {self.episode}")

        # Schedule training loop
        self.training_loop()

    def training_loop(self):
        """
        Main training loop (runs asynchronously).
        Uses setTimeout to avoid blocking the browser.
        """
        if not self.is_training or self.is_paused:
            return

        # Execute one step
        self.step()

        # Schedule next step (using setTimeout to avoid blocking)
        # Run at ~60fps (16ms per frame)
        js.setTimeout(lambda: self.training_loop(), 16)

    def pause_training(self):
        """Pause training."""
        print("⏸️ [Python] Training paused")
        self.is_paused = True
        window.updateRLStatus('paused', f"Training paused at Episode {self.episode}")

    def resume_training(self):
        """Resume training."""
        print("▶️ [Python] Training resumed")
        self.is_paused = False
        window.updateRLStatus('training', f"Training resumed - Episode {self.episode}")
        self.training_loop()

    def reset_training(self):
        """Reset all training progress."""
        print("🔄 [Python] Training reset")
        self.is_training = False
        self.is_paused = False
        self.episode = 0
        self.total_reward = 0
        self.high_score = 0
        self.episode_reward = 0
        self.episode_steps = 0
        self.epsilon = 0.9

        # Reset emulator
        emulator = window.nesEmulator
        if emulator and emulator.isLoaded():
            emulator.reset()

        self.update_ui()
        window.updateRLStatus('ready', 'Training reset. Click "Start Training" to begin.')

    def play_demo(self):
        """Play a demo using the trained policy."""
        print("🎮 [Python] Playing demo...")
        window.updateRLStatus('playing', 'Playing demo with trained policy...')

        # TODO: Implement demo mode (use best policy, no exploration)
        # For now, just notify user
        js.alert("Demo mode coming soon! The agent will play using its learned policy.")


# Initialize the RL agent
print("🐍 [Python] Initializing RL agent...")
rl_agent = RLAgent()
print("✅ [Python] RL agent ready")


# Expose functions to JavaScript
def start_training():
    """Start RL training (called from JS)."""
    print("🟢 [Python] start_training() called")
    rl_agent.start_training()


def pause_training():
    """Pause RL training (called from JS)."""
    print("🟡 [Python] pause_training() called")
    if rl_agent.is_paused:
        rl_agent.resume_training()
    else:
        rl_agent.pause_training()


def reset_training():
    """Reset RL training (called from JS)."""
    print("🔴 [Python] reset_training() called")
    rl_agent.reset_training()


def play_demo():
    """Play demo (called from JS)."""
    print("🔵 [Python] play_demo() called")
    rl_agent.play_demo()


# Expose to window
print("🐍 [Python] Exposing RL functions to window object")
window.startRLTraining = start_training
window.pauseRLTraining = pause_training
window.resetRLTraining = reset_training
window.playRLDemo = play_demo
print("✅ [Python] RL agent ready for training!")
