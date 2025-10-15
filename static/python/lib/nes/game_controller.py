"""
Game Controller - Handles all NES emulator interactions for Super Mario Bros

This class encapsulates all game-related functionality:
- Emulator access and state management
- Button input execution
- Game state extraction (vision, position, status)
- Uses nes_ram_utils for memory reading

Author: Guinetik
"""

from js import window, console
import numpy as np
from lib.nes.nes_ram_utils import (
    extract_vision_grid,
    extract_context_features,
    get_mario_position,
    get_mario_state,
    get_mario_tile_position,
    get_score
)


class GameController:
    """
    Manages all interactions with the NES emulator.
    Provides clean interface for agents to observe and control the game.
    """

    # NES controller button constants
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_SELECT = 2
    BUTTON_START = 3
    BUTTON_UP = 4
    BUTTON_DOWN = 5
    BUTTON_LEFT = 6
    BUTTON_RIGHT = 7

    def __init__(self, vision_width: int = 16, vision_height: int = 7):
        """
        Initialize game controller.

        Args:
            vision_width: Width of vision grid in tiles (default: 16)
            vision_height: Height of vision grid in tiles (default: 7)

        Vision distribution (7 tiles vertical):
            3 tiles above Mario (jumps, blocks, platforms)
            1 tile (Mario's current row)
            3 tiles below Mario (pits, ground, enemies)
        """
        self.vision_width = vision_width
        self.vision_height = vision_height

        console.log("🎮 GameController initialized")
        console.log(f"   Vision: {vision_width}×{vision_height} tiles")

    def get_emulator(self):
        """
        Get the NES emulator instance.

        Returns:
            Emulator object or None if not available
        """
        try:
            return window.nesEmulator
        except:
            return None

    def get_nes(self):
        """
        Get the NES instance from emulator.

        Returns:
            NES object or None if not available
        """
        emulator = self.get_emulator()
        if not emulator or not emulator.controller or not emulator.controller.nes:
            return None
        return emulator.controller.nes

    def is_emulator_ready(self) -> bool:
        """
        Check if emulator is fully initialized and ready.

        Returns:
            bool: True if emulator is ready to use
        """
        emulator = self.get_emulator()
        if not emulator:
            return False
        
        return (emulator.controller and 
                emulator.controller.nes and 
                emulator.isRunning())

    def get_vision_state(self) -> np.ndarray:
        """
        Extract vision grid from game state.
        Returns flattened array of tile values.

        Returns:
            np.ndarray: Vision grid (width × height floats)
                       0.0 = empty, 1.0 = solid, -1.0 = enemy
        """
        nes = self.get_nes()
        if not nes:
            return np.zeros(self.vision_width * self.vision_height)

        try:
            vision = extract_vision_grid(
                nes,
                width=self.vision_width,
                height=self.vision_height
            )
            return np.array(vision, dtype=np.float32)
        except Exception as e:
            console.error(f"❌ Error extracting vision: {e}")
            return np.zeros(self.vision_width * self.vision_height)

    def get_context_features(self) -> np.ndarray:
        """
        Extract high-level engineered features.

        Returns:
            np.ndarray: Array of 8 context features (normalized 0-1):
                       [enemy_left_dist, enemy_right_dist, ground_dist, pit_dist,
                        obstacle_dist, is_on_ground, mario_y_normalized, enemy_nearby]
        """
        nes = self.get_nes()
        if not nes:
            return np.zeros(8, dtype=np.float32)

        try:
            features = extract_context_features(nes)
            return np.array(features, dtype=np.float32)
        except Exception as e:
            console.error(f"❌ Error extracting context features: {e}")
            return np.zeros(8, dtype=np.float32)

    def get_mario_position(self) -> tuple:
        """
        Get Mario's current position in pixels.

        Returns:
            tuple: (x, y) position in pixels
        """
        nes = self.get_nes()
        if not nes:
            return (0, 0)

        return get_mario_position(nes)

    def get_mario_x(self) -> int:
        """
        Get Mario's X position only.

        Returns:
            int: X position in pixels
        """
        x, _ = self.get_mario_position()
        return x

    def is_mario_alive(self) -> bool:
        """
        Check if Mario is alive.

        Returns:
            bool: True if alive, False if dying or dead
        """
        nes = self.get_nes()
        if not nes:
            return True  # Assume alive if can't check

        state = get_mario_state(nes)
        return state == 'alive'

    def get_score(self) -> int:
        """
        Get Mario's current score.

        Returns:
            int: Current score (0-999999)
        """
        nes = self.get_nes()
        if not nes:
            return 0

        return get_score(nes)

    def execute_buttons(self, button_states: np.ndarray):
        """
        Execute button presses on the emulator.
        Button array format: [UP, DOWN, LEFT, RIGHT, A, B]

        Args:
            button_states: Array of 0/1 for each button state
        """
        emulator = self.get_emulator()
        if not emulator:
            console.warn("⚠️ Emulator not found")
            return

        if not self.is_emulator_ready():
            console.warn("⚠️ Emulator not ready")
            return

        try:
            # Ensure button_states is a 1D array with 6 elements
            buttons = np.array(button_states).flatten()

            if len(buttons) != 6:
                console.error(f"❌ Invalid button array size: {len(buttons)}, expected 6")
                return

            # Map button indices to NES controller buttons
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

            # Press buttons that are active
            for i in range(6):
                if buttons[i]:
                    emulator.buttonDown(1, button_map[i])
        except Exception as e:
            console.error(f"❌ Error executing buttons: {e}")

    def start_emulator(self):
        """Start the emulator if not running."""
        emulator = self.get_emulator()
        if not emulator:
            console.error("❌ Emulator not found")
            return False

        if not emulator.isRunning():
            emulator.start()
            console.log("▶️ Emulator started")
            return True
        return True

    def stop_emulator(self):
        """Stop the emulator."""
        emulator = self.get_emulator()
        if emulator:
            emulator.stop()
            console.log("⏹️ Emulator stopped")

    def reset_emulator(self):
        """Reset the emulator."""
        emulator = self.get_emulator()
        if emulator:
            emulator.reset()
            console.log("🔄 Emulator reset")

    def disable_keyboard(self):
        """Disable keyboard input (for AI control)."""
        emulator = self.get_emulator()
        if emulator:
            emulator.disableKeyboard()

    def enable_keyboard(self):
        """Enable keyboard input (for manual control)."""
        emulator = self.get_emulator()
        if emulator:
            emulator.enableKeyboard()

    async def load_saved_state(self, state_path: str = '/data/nes_state.json'):
        """
        Load a saved game state.

        Args:
            state_path: Path to state JSON file
        """
        try:
            from js import fetch, JSON

            emulator = self.get_emulator()
            if not emulator:
                console.error("❌ Emulator not found")
                return False

            # Fetch and parse state
            response = await fetch(state_path)
            state_json = await response.text()
            state_obj = JSON.parse(state_json)

            # Load into emulator
            if emulator.controller and emulator.controller.loadState:
                emulator.controller.loadState(state_obj)
                console.log(f"♻️ Loaded saved state from {state_path}")
                return True
            
            return False
        except Exception as e:
            console.error(f"⚠️ Could not load state: {e}")
            return False

    def print_vision(self, state: np.ndarray):
        """
        Print ASCII representation of vision grid.
        Vision is centered on Mario (can see behind and ahead).
        Useful for debugging.

        Args:
            state: Flattened vision array
        """
        # Get Mario's actual position for context
        x, y = self.get_mario_position()

        console.log(f"\n👁️ Mario's Vision (X: {x}px, Y: {y}px):")
        vision_2d = state.reshape(self.vision_height, self.vision_width)

        # Mario is at column index = vision_width // 4 (25% from left, 75% from right)
        mario_col_index = self.vision_width // 4
        mario_row_index = 3  # Looking 3 tiles up (for 7 tile height: 3 above, 1 current, 3 below)

        for i, row in enumerate(vision_2d):
            line = ""
            for j, val in enumerate(row):
                # Mark Mario's position (centered in vision)
                if i == mario_row_index and j == mario_col_index:
                    if val < -0.5:
                        line += "E"  # Enemy at Mario's position (danger!)
                    elif val > 0.5:
                        line += "#"  # Solid at Mario's position
                    else:
                        line += "M"  # Show Mario's position
                elif val < -0.5:      # Enemy
                    line += "E"
                elif val > 0.5:     # Solid
                    line += "#"
                else:               # Empty
                    line += "."

            # Add row labels to understand what we're looking at
            if i == mario_row_index:
                line += " ← Mario's row"
            elif i < mario_row_index:
                line += f" ← {mario_row_index - i} tiles above"
            else:
                line += f" ← {i - mario_row_index} tiles below"

            console.log(line)

        console.log(f"  ↑ {mario_col_index} tiles behind M | {self.vision_width - mario_col_index - 1} tiles ahead ↑")
        console.log("")

