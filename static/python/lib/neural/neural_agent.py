"""
NeuralAgent - Base class for neural network-controlled agents

Provides core agent loop (observe, decide, act) without game-specific
or evolution-specific logic. Use composition to inject dependencies.

Author: Guinetik
"""

from abc import ABC, abstractmethod
import numpy as np


class NeuralAgent:
    """
    Base neural agent with observe-decide-act loop.
    Uses dependency injection for game controller, neural network, and action decoder.
    """

    def __init__(self, game_controller, neural_controller, action_decoder):
        """
        Initialize agent with injected dependencies.

        Args:
            game_controller: Handles game state observation and action execution
            neural_controller: Neural network for decision making
            action_decoder: Converts network outputs to actions
        """
        self.game = game_controller
        self.neural = neural_controller
        self.decoder = action_decoder

        # Statistics (managed by GenerationManager)
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0

    @abstractmethod
    def observe(self) -> np.ndarray:
        """
        Observe the current state.
        Must be implemented by subclass (game-specific).

        Returns:
            np.ndarray: State vector
        """
        pass

    def decide(self, state: np.ndarray) -> np.ndarray:
        """
        Decide action based on observation.

        Args:
            state: Observed game state

        Returns:
            np.ndarray: Action vector (button states)
        """
        # Forward pass through neural network
        output = self.neural.forward(state)

        # Decode to actions
        actions = self.decoder.decode(output)

        return actions

    def act(self, actions: np.ndarray):
        """
        Execute actions in the environment.

        Args:
            actions: Action vector to execute
        """
        self.game.execute_buttons(actions)

    def step(self) -> dict:
        """
        Execute one step of the agent loop: observe → decide → act.

        Returns:
            dict: Step information (position, alive status, etc.)
        """
        # Observe
        state = self.observe()

        # Decide
        actions = self.decide(state)

        # Act
        self.act(actions)

        # Track progress
        self.frames += 1
        current_x = self.game.get_mario_x()

        if current_x > self.max_x:
            self.max_x = current_x
            self.stuck_frames = 0
        else:
            self.stuck_frames += 1

        self.last_x = current_x

        # Return step info
        return {
            'frames': self.frames,
            'position': current_x,
            'max_position': self.max_x,
            'stuck_frames': self.stuck_frames,
            'alive': self.game.is_mario_alive()
        }

    def reset(self):
        """Reset agent statistics for new generation."""
        self.frames = 0
        self.max_x = 0
        self.stuck_frames = 0
        self.last_x = 0
        self._progress_grace_frames = 0  # Grace period after significant progress

    def get_weights(self):
        """Get neural network weights."""
        return self.neural.get_weights()

    def set_weights(self, weights, biases):
        """Set neural network weights."""
        self.neural.set_weights(weights, biases)

    def mutate(self, mutation_rate: float, mutation_scale: float):
        """Mutate neural network weights."""
        self.neural.mutate(mutation_rate, mutation_scale)


class MarioAgent(NeuralAgent):
    """
    Mario-specific agent implementation.
    Implements observe() with vision grid + context features + row encoding.
    """

    def __init__(
        self,
        game_controller,
        neural_controller,
        action_decoder,
        use_context_features: bool = True,
        encode_row: bool = True,
        num_rows: int = 15
    ):
        """
        Initialize Mario agent.

        Args:
            game_controller: GameController instance
            neural_controller: NeuralController instance
            action_decoder: ActionDecoder instance
            use_context_features: Include engineered context features (9 inputs)
            encode_row: Include one-hot row encoding (15 inputs)
            num_rows: Number of tile rows for encoding
        """
        super().__init__(game_controller, neural_controller, action_decoder)

        self.use_context_features = use_context_features
        self.encode_row = encode_row
        self.num_rows = num_rows

        # Mario-specific tracking
        self.visited_positions = set()
        self.backward_movement_frames = 0
        self.start_score = 0
        self.final_score = 0

    def observe(self) -> np.ndarray:
        """
        Observe Mario's state: vision + context + row encoding.

        Returns:
            np.ndarray: Combined state vector
        """
        # Vision grid (e.g., 16×7 = 112 floats)
        vision = self.game.get_vision_state()

        components = [vision]

        # Context features (9 floats: enemy distances, ground, pits, etc.)
        if self.use_context_features:
            context = self.game.get_context_features()
            components.append(context)

        # Row encoding (15 floats: one-hot of Mario's vertical position)
        if self.encode_row:
            _, mario_row = self.game.get_mario_tile_position()
            row_encoding = np.zeros(self.num_rows, dtype=np.float32)
            if 0 <= mario_row < self.num_rows:
                row_encoding[mario_row] = 1.0
            components.append(row_encoding)

        # Concatenate all components
        state = np.concatenate(components)
        return state

    def step(self) -> dict:
        """
        Execute one step with Mario-specific tracking.

        Returns:
            dict: Step info + Mario-specific metrics
        """
        # Base step
        info = super().step()

        # Mario-specific tracking
        current_x = info['position']

        # Track exploration (unique positions)
        position_bucket = int(current_x / 10) * 10
        self.visited_positions.add(position_bucket)

        # Track backward movement
        if current_x < self.last_x:
            self.backward_movement_frames += 1

        # Add Mario-specific info
        info['exploration'] = len(self.visited_positions)
        info['backward_frames'] = self.backward_movement_frames
        info['score'] = self.game.get_score()

        return info

    def reset(self):
        """Reset Mario-specific stats."""
        super().reset()
        self.visited_positions = set()
        self.backward_movement_frames = 0
        self.start_score = self.game.get_score()
        self.final_score = self.start_score
