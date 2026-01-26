"""
HeadlessGameController - Sandboxed game controller for background training

Provides the same interface as GameController but uses an isolated HeadlessNES
instance that doesn't interfere with the foreground display.
"""

from js import window, console
import json


class HeadlessGameController:
    """
    Game controller for headless (background) training.

    Uses a separate HeadlessNES instance - completely isolated from
    the foreground emulator (window.nesEmulator).
    """

    # NES button constants (same as GameController)
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_SELECT = 2
    BUTTON_START = 3
    BUTTON_UP = 4
    BUTTON_DOWN = 5
    BUTTON_LEFT = 6
    BUTTON_RIGHT = 7

    # Mario RAM addresses (same as GameController)
    MARIO_X_POS = 0x0086
    MARIO_X_PAGE = 0x006D
    MARIO_Y_POS = 0x00CE
    MARIO_STATE = 0x000E
    PLAYER_STATE = 0x0770
    GAME_MODE = 0x0772
    SCORE_ADDR = [0x07DD, 0x07DE, 0x07DF, 0x07E0, 0x07E1, 0x07E2]
    LIVES_ADDR = 0x075A

    def __init__(self, vision_width: int = 7, vision_height: int = 10):
        """
        Initialize headless game controller.

        Args:
            vision_width: Width of vision grid in tiles
            vision_height: Height of vision grid in tiles
        """
        self.vision_width = vision_width
        self.vision_height = vision_height

        # Headless NES instance (created on demand)
        self.headless_nes = None
        self.saved_state = None

        # Button state tracking
        self.current_buttons = set()

        console.log("🔇 HeadlessGameController created")

    def initialize(self):
        """
        Initialize the headless NES with ROM from foreground emulator.
        Must be called after foreground emulator is loaded.
        """
        if not hasattr(window, 'createHeadlessNES'):
            raise RuntimeError("HeadlessNES factory not available")

        if not hasattr(window, 'nesEmulator') or not window.nesEmulator.controller:
            raise RuntimeError("Foreground emulator not loaded")

        # Get ROM from foreground emulator
        rom_data = window.nesEmulator.controller.romBinaryString
        if not rom_data:
            raise RuntimeError("ROM not loaded in foreground emulator")

        # Create isolated headless NES
        self.headless_nes = window.createHeadlessNES()
        self.headless_nes.initialize(rom_data)

        console.log("✅ HeadlessGameController initialized with isolated NES")

    def copy_state_from_foreground(self):
        """
        DEPRECATED: This copies the CURRENT state which might be dead/stuck Mario.
        Use load_state_from_file() instead for consistent starting position.
        """
        console.warn("⚠️ copy_state_from_foreground is deprecated - state might be invalid")
        if not hasattr(window, 'nesEmulator') or not window.nesEmulator.controller:
            console.error("❌ Foreground emulator not available")
            return False

        state = window.nesEmulator.controller.saveState()
        if state:
            self.saved_state = state
            console.log("📋 Copied CURRENT state from foreground")
            return True
        else:
            console.error("❌ Failed to get state from foreground emulator")
            return False
    
    async def load_state_from_file(self, state_path: str = '/data/nes_state.json'):
        """
        Load the saved starting state from file (same source as foreground).
        This ensures background evaluations start from the SAME position as foreground.
        
        Args:
            state_path: Path to state JSON file
        """
        try:
            from js import fetch, JSON
            
            # Fetch and parse state file
            response = await fetch(state_path)
            state_json = await response.text()
            state_obj = JSON.parse(state_json)
            
            # Store for later use
            self.saved_state = state_obj
            console.log(f"📋 Loaded state from {state_path}")
            return True
            
        except Exception as e:
            console.error(f"❌ Could not load state from file: {e}")
            return False

    async def load_saved_state(self):
        """Load the saved state into headless NES."""
        if not self.headless_nes:
            console.error("❌ load_saved_state: headless_nes is None!")
            return False
        if not self.saved_state:
            console.error("❌ load_saved_state: saved_state is None! Call load_state_from_file first.")
            return False
        
        # CRITICAL: Make a deep copy before loading!
        # The NES loadState() function MUTATES the state object it receives.
        # Without a copy, after the first network runs, saved_state is corrupted
        # and all subsequent networks start from an invalid state.
        from js import JSON
        state_copy = JSON.parse(JSON.stringify(self.saved_state))
        
        self.headless_nes.loadState(state_copy)
        
        # Run one frame to ensure RAM is populated correctly
        # Some emulators need a frame to sync internal state after fromJSON
        self.headless_nes.frame()
        
        self.current_buttons.clear()
        return True

    def frame(self):
        """Advance one frame in headless NES."""
        if self.headless_nes:
            self.headless_nes.frame()

    def read_ram(self, address: int) -> int:
        """Read RAM from headless NES."""
        if self.headless_nes:
            return self.headless_nes.readRAM(address)
        return 0

    def get_mario_x(self) -> int:
        """Get Mario's X position."""
        page = self.read_ram(self.MARIO_X_PAGE)
        x_pos = self.read_ram(self.MARIO_X_POS)
        return page * 256 + x_pos

    def get_mario_position(self) -> tuple:
        """Get Mario's (x, y) position."""
        x = self.get_mario_x()
        y = self.read_ram(self.MARIO_Y_POS)
        return (x, y)

    def get_mario_tile_position(self) -> tuple:
        """Get Mario's position in tile coordinates."""
        x, y = self.get_mario_position()
        tile_x = x // 16
        # MUST match foreground calculation in nes_ram_utils.get_mario_tile_position!
        # Adjust Y for status bar: y + SPRITE_SIZE(16) - STATUS_BAR_HEIGHT(32) = y - 16
        SPRITE_SIZE = 16
        STATUS_BAR_HEIGHT = 32
        y_adjusted = y + SPRITE_SIZE - STATUS_BAR_HEIGHT
        tile_y = y_adjusted // SPRITE_SIZE
        return (tile_x, tile_y)

    def is_mario_alive(self) -> bool:
        """Check if Mario is alive."""
        mario_state = self.read_ram(self.MARIO_STATE)
        player_state = self.read_ram(self.PLAYER_STATE)

        # Dead states
        if mario_state == 0x06:  # Dying
            return False
        if mario_state == 0x0B:  # Dead
            return False
        if player_state == 0x0B:  # Game over
            return False

        return True

    def get_score(self) -> int:
        """Get current score."""
        score = 0
        for i, addr in enumerate(self.SCORE_ADDR):
            digit = self.read_ram(addr)
            score += digit * (10 ** (5 - i))
        return score

    def get_lives(self) -> int:
        """Get remaining lives."""
        return self.read_ram(self.LIVES_ADDR)

    def get_vision_state(self) -> list:
        """
        Get vision grid from RAM - FULL IMPLEMENTATION.
        Reads actual tile data from NES RAM to detect pipes, blocks, enemies.
        
        Uses same tile extraction logic as nes_ram_utils.py but adapted for
        the HeadlessNES RAM reading interface.
        """
        # Constants (matching nes_ram_utils.py)
        TILE_DATA_START = 0x500
        TILES_PER_ROW = 16
        TILES_PER_COL = 13
        PAGE_SIZE = 208  # 13 rows × 16 cols
        NUM_PAGES = 2
        SPRITE_SIZE = 16
        STATUS_BAR_HEIGHT = 32
        
        vision = []

        # Get Mario's tile position (matching nes_ram_utils logic)
        mario_x, mario_y = self.get_mario_position()
        
        # Adjust Y for status bar (same as get_mario_tile_position in nes_ram_utils)
        y_adjusted = mario_y + SPRITE_SIZE - STATUS_BAR_HEIGHT
        mario_col = mario_x // SPRITE_SIZE
        mario_row = y_adjusted // SPRITE_SIZE

        # Read enemy positions (same logic as before but with proper Y conversion)
        enemy_tile_positions = set()
        for i in range(5):
            enemy_drawn = self.read_ram(0x000F + i)
            if enemy_drawn != 0:
                enemy_x_page = self.read_ram(0x006E + i)
                enemy_x_pos = self.read_ram(0x0087 + i)
                enemy_y = self.read_ram(0x00CF + i)
                enemy_x = enemy_x_page * 256 + enemy_x_pos
                
                # Convert to tile coordinates (same as Mario conversion)
                enemy_y_adjusted = enemy_y + (SPRITE_SIZE // 2) - STATUS_BAR_HEIGHT
                enemy_tile_x = enemy_x // SPRITE_SIZE
                enemy_tile_y = enemy_y_adjusted // SPRITE_SIZE
                enemy_tile_positions.add((enemy_tile_x, enemy_tile_y))

        # Vision grid centering (matching nes_ram_utils.extract_vision_grid)
        # 25% behind, 75% ahead
        tiles_behind = self.vision_width // 4  # 1 for width=7
        start_col = mario_col - tiles_behind
        
        # Vertical: Center vision around Mario (~1/3 above)
        rows_above = self.vision_height // 3  # 3 for height=10
        start_row = mario_row - rows_above

        # Build vision grid by reading actual tile data from RAM
        for row_offset in range(self.vision_height):
            row = start_row + row_offset

            for col_offset in range(self.vision_width):
                col = start_col + col_offset

                # Check for enemies first (higher priority)
                if (col, row) in enemy_tile_positions:
                    vision.append(-1.0)
                else:
                    # Read actual tile value from RAM
                    tile_value = self._get_tile_at(col, row, TILE_DATA_START, 
                                                   TILES_PER_ROW, TILES_PER_COL, 
                                                   PAGE_SIZE, NUM_PAGES)
                    
                    # Non-zero tile = solid (blocks, pipes, ground, etc.)
                    if tile_value != 0x00:
                        vision.append(1.0)  # Solid
                    else:
                        vision.append(0.0)  # Empty

        return vision
    
    def _get_tile_at(self, col, row, tile_start, tiles_per_row, tiles_per_col, 
                     page_size, num_pages) -> int:
        """
        Get tile value at given tile coordinates.
        
        Super Mario Bros stores level data in 2 alternating pages.
        Each page covers one screen (16 tiles wide × 13 tiles tall).
        """
        # Check bounds
        if row < 0 or row >= tiles_per_col:
            return 0x00  # Empty if out of bounds vertically
        
        # Determine which page (alternates every 16 tiles horizontally)
        page = (col // tiles_per_row) % num_pages
        
        # Position within page
        sub_col = col % tiles_per_row
        
        # Calculate RAM address: base + page_offset + row_offset + col_offset
        addr = (tile_start + 
                page * page_size + 
                row * tiles_per_row + 
                sub_col)
        
        return self.read_ram(addr)

    def execute_buttons(self, button_states):
        """
        Execute button presses on headless NES.

        Args:
            button_states: Binary array [UP, DOWN, LEFT, RIGHT, A, B] where 1=pressed
                          Same format as GameController.execute_buttons
        """
        if not self.headless_nes:
            return

        # Map from binary array indices to NES button constants
        # Array format: [UP, DOWN, LEFT, RIGHT, A, B]
        # NES format: A=0, B=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7
        INDEX_TO_NES = [
            self.BUTTON_UP,     # 0 → UP (4)
            self.BUTTON_DOWN,   # 1 → DOWN (5)
            self.BUTTON_LEFT,   # 2 → LEFT (6)
            self.BUTTON_RIGHT,  # 3 → RIGHT (7)
            self.BUTTON_A,      # 4 → A (0)
            self.BUTTON_B,      # 5 → B (1)
        ]

        # Convert binary array to set of NES button indices
        new_buttons = set()
        for i, pressed in enumerate(button_states):
            if i < len(INDEX_TO_NES) and pressed:
                new_buttons.add(INDEX_TO_NES[i])

        # Release buttons no longer pressed
        for btn in self.current_buttons - new_buttons:
            self.headless_nes.buttonUp(1, btn)

        # Press new buttons
        for btn in new_buttons - self.current_buttons:
            self.headless_nes.buttonDown(1, btn)

        self.current_buttons = new_buttons

    def reset(self):
        """Reset button state."""
        if self.headless_nes:
            for btn in self.current_buttons:
                self.headless_nes.buttonUp(1, btn)
        self.current_buttons.clear()

    def destroy(self):
        """Clean up headless NES."""
        if self.headless_nes:
            self.headless_nes.destroy()
            self.headless_nes = None
        console.log("🗑️ HeadlessGameController destroyed")
