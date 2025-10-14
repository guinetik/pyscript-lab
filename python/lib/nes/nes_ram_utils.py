"""
NES RAM Utilities for Super Mario Bros
Extracts game state from NES memory for AI vision

Based on SMB memory map:
- Mario X position: RAM[0x6D] (screen) + RAM[0x86] * 256 (page)
- Mario Y position: RAM[0xCE] (screen Y), RAM[0xB5] (vertical screen)
- Mario state: RAM[0x0E] (0x0B=dying, 0x06=dead)
- Tile data: RAM[0x500] onwards (2 pages × 13 rows × 16 cols)
- Enemy slots: RAM[0x0F + i] for i in range(5)

Author: Adapted from SuperMarioBros-AI by chrispresso
"""

from js import console


class MarioRAM:
    """Memory address constants for Super Mario Bros"""

    # Mario position
    MARIO_X_SCREEN = 0x86       # Mario's X position on current screen (0-255)
    MARIO_X_PAGE = 0x6D         # Current page/screen number
    MARIO_Y_SCREEN = 0xCE       # Mario's Y position on screen
    MARIO_Y_VERTICAL = 0xB5     # Vertical screen position

    # Mario state
    MARIO_STATE = 0x0E          # Player state (0x0B=dying, 0x06=dead)

    # Enemies (5 slots, addresses are base + slot_number)
    ENEMY_DRAWN = 0x0F          # Is enemy drawn? (1=yes, 0=no)
    ENEMY_TYPE = 0x16           # Enemy type ID
    ENEMY_X_LEVEL = 0x6E        # Enemy X position in level
    ENEMY_X_SCREEN = 0x87       # Enemy X position on screen
    ENEMY_Y_SCREEN = 0xCF       # Enemy Y position on screen

    # Tile data
    TILE_DATA_START = 0x500     # Start of tile data

    # Screen dimensions
    SPRITE_SIZE = 16            # Pixels per tile
    SCREEN_WIDTH = 256
    SCREEN_HEIGHT = 240
    STATUS_BAR_HEIGHT = 32      # Top status bar (not part of playfield)

    # Tile pages
    TILES_PER_ROW = 16
    TILES_PER_COL = 13          # After status bar
    PAGE_SIZE = 208             # 13 rows × 16 cols
    NUM_PAGES = 2


def get_mario_position(nes):
    """
    Get Mario's position in the level.

    Args:
        nes: JSNes instance with cpu.mem

    Returns:
        tuple: (x, y) Mario's position in pixels
    """
    try:
        ram = nes.cpu.mem

        # X position = page * 256 + screen_x
        x_page = ram[MarioRAM.MARIO_X_PAGE]
        x_screen = ram[MarioRAM.MARIO_X_SCREEN]
        x_total = x_page * 256 + x_screen

        # Y position
        y = ram[MarioRAM.MARIO_Y_SCREEN]

        # Debug first call
        if not hasattr(get_mario_position, '_debug_printed'):
            console.log(f"🔍 [RAM] First position read: page={x_page}, screen={x_screen}, total={x_total}, y={y}")
            get_mario_position._debug_printed = True

        return (x_total, y)
    except Exception as e:
        console.error(f"Error getting Mario position: {e}")
        return (0, 0)


def get_mario_tile_position(nes):
    """
    Get Mario's position in tile coordinates.

    Args:
        nes: JSNes instance

    Returns:
        tuple: (col, row) in tiles
    """
    x, y = get_mario_position(nes)

    # Adjust Y for status bar
    y_adjusted = y + MarioRAM.SPRITE_SIZE - MarioRAM.STATUS_BAR_HEIGHT

    # Convert to tile coordinates
    col = x // MarioRAM.SPRITE_SIZE
    row = y_adjusted // MarioRAM.SPRITE_SIZE

    return (col, row)


def get_tile_at(nes, col, row):
    """
    Get tile value at given tile coordinates.

    Super Mario Bros stores level data in 2 alternating pages.
    Each page covers one screen (16 tiles wide × 13 tiles tall).

    Args:
        nes: JSNes instance
        col: Column (tile X coordinate)
        row: Row (tile Y coordinate, 0 = top of playfield)

    Returns:
        int: Tile value (0x00 = empty, others = various tile types)
    """
    try:
        ram = nes.cpu.mem

        # Check bounds
        if row < 0 or row >= MarioRAM.TILES_PER_COL:
            return 0x00  # Empty if out of bounds vertically

        # Determine which page (alternates every 256 pixels / 16 tiles)
        page = (col // MarioRAM.TILES_PER_ROW) % MarioRAM.NUM_PAGES

        # Position within page
        sub_col = col % MarioRAM.TILES_PER_ROW

        # Calculate address: base + page_offset + row_offset + col_offset
        addr = (MarioRAM.TILE_DATA_START +
                page * MarioRAM.PAGE_SIZE +
                row * MarioRAM.TILES_PER_ROW +
                sub_col)

        return ram[addr]
    except Exception as e:
        console.error(f"Error getting tile at ({col}, {row}): {e}")
        return 0x00


def is_solid_tile(tile_value):
    """
    Check if a tile is solid (Mario can stand on it or collide with it).

    Args:
        tile_value: Tile byte from RAM

    Returns:
        bool: True if solid, False if empty/passable
    """
    # In SMB:
    # 0x00 = empty/air
    # Non-zero = some kind of object (block, pipe, coin block, etc.)
    # We simplify: 0 = empty, non-zero = solid
    return tile_value != 0x00


def get_enemy_positions(nes):
    """
    Get positions of all active enemies on screen.
    SMB can only display 5 enemies at once.

    Args:
        nes: JSNes instance

    Returns:
        list: List of (x, y) tuples for each active enemy in pixels
    """
    enemies = []

    try:
        ram = nes.cpu.mem

        for i in range(5):  # 5 enemy slots
            # Check if enemy is drawn
            is_drawn = ram[MarioRAM.ENEMY_DRAWN + i]

            if is_drawn:
                # Get enemy position
                x_level = ram[MarioRAM.ENEMY_X_LEVEL + i]
                x_screen = ram[MarioRAM.ENEMY_X_SCREEN + i]
                x_total = x_level * 256 + x_screen

                y = ram[MarioRAM.ENEMY_Y_SCREEN + i]

                enemies.append((x_total, y))
    except Exception as e:
        console.error(f"Error getting enemy positions: {e}")

    return enemies


def is_enemy_at_tile(nes, col, row):
    """
    Check if there's an enemy at the given tile position.

    Args:
        nes: JSNes instance
        col: Tile column
        row: Tile row

    Returns:
        bool: True if enemy present
    """
    enemies = get_enemy_positions(nes)

    # Convert tile to pixel bounds
    tile_x_min = col * MarioRAM.SPRITE_SIZE
    tile_x_max = tile_x_min + MarioRAM.SPRITE_SIZE
    tile_y_min = row * MarioRAM.SPRITE_SIZE + MarioRAM.STATUS_BAR_HEIGHT
    tile_y_max = tile_y_min + MarioRAM.SPRITE_SIZE

    # Check if any enemy overlaps this tile
    for enemy_x, enemy_y in enemies:
        # Enemy is considered "at" this tile if center overlaps
        # Allow 8 pixel tolerance (half a tile)
        if (abs(enemy_x - (tile_x_min + 8)) <= 8 and
            abs(enemy_y - (tile_y_min + 8)) <= 8):
            return True

    return False


def extract_vision_grid(nes, width=7, height=10):
    """
    Extract a grid of tiles around Mario for AI vision.

    Encoding:
    - 0.0 = empty/air
    - 1.0 = solid tile (blocks, pipes, etc.)
    - -1.0 = enemy

    Args:
        nes: JSNes instance
        width: Number of tiles wide (centered on Mario)
        height: Number of tiles tall

    Returns:
        list: Flattened list of encoded tile values (width × height)
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    vision = []

    # Start from Mario's row minus offset
    start_row = mario_row - 2  # Look 2 tiles above

    # Debug first call
    if not hasattr(extract_vision_grid, '_debug_printed'):
        console.log(f"🔍 [Vision] Mario at tile: col={mario_col}, row={mario_row}")
        console.log(f"🔍 [Vision] Scanning rows {start_row} to {start_row + height}")

        # Sample a few tiles
        test_tiles = []
        for i in range(3):
            tile = get_tile_at(nes, mario_col + i, mario_row + 2)  # Below Mario
            test_tiles.append(hex(tile))
        console.log(f"🔍 [Vision] Sample tiles below Mario: {test_tiles}")
        extract_vision_grid._debug_printed = True

    for row_offset in range(height):
        row = start_row + row_offset

        for col_offset in range(width):
            col = mario_col + col_offset

            # Check for enemy first (higher priority)
            if is_enemy_at_tile(nes, col, row):
                vision.append(-1.0)
            else:
                # Check tile type
                tile_value = get_tile_at(nes, col, row)
                if is_solid_tile(tile_value):
                    vision.append(1.0)
                else:
                    vision.append(0.0)

    return vision


def get_mario_state(nes):
    """
    Get Mario's current state.

    Args:
        nes: JSNes instance

    Returns:
        str: 'alive', 'dying', or 'dead'
    """
    try:
        ram = nes.cpu.mem
        state_byte = ram[MarioRAM.MARIO_STATE]

        if state_byte == 0x0B:
            return 'dying'
        elif state_byte == 0x06:
            return 'dead'
        else:
            return 'alive'
    except:
        return 'alive'
