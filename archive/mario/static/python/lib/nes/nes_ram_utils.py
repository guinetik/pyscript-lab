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
    LIVES_REMAINING = 0x075A    # Lives counter (0-99)

    # Score (BCD encoded, 6 digits)
    SCORE_ONES = 0x07DD         # Rightmost 2 digits (ones, tens)
    SCORE_HUNDREDS = 0x07DE     # Middle 2 digits (hundreds, thousands)
    SCORE_TEN_THOUSANDS = 0x07DF  # Leftmost 2 digits (ten thousands, hundred thousands)

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
            print(f"🔍 [RAM] First position read: page={x_page}, screen={x_screen}, total={x_total}, y={y}")
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
    # Mario's row formula: row = (y + SPRITE_SIZE - STATUS_BAR) // SPRITE_SIZE
    # Inverse: y_min = row * SPRITE_SIZE + STATUS_BAR - SPRITE_SIZE
    tile_x_min = col * MarioRAM.SPRITE_SIZE
    tile_x_max = tile_x_min + MarioRAM.SPRITE_SIZE
    tile_y_min = row * MarioRAM.SPRITE_SIZE + (MarioRAM.STATUS_BAR_HEIGHT - MarioRAM.SPRITE_SIZE)
    tile_y_max = tile_y_min + MarioRAM.SPRITE_SIZE

    # Check if any enemy overlaps this tile
    for enemy_x, enemy_y in enemies:
        # Enemy Y from RAM is the TOP of sprite, so add 8 to get center
        enemy_center_y = enemy_y + (MarioRAM.SPRITE_SIZE // 2)
        tile_center_x = tile_x_min + (MarioRAM.SPRITE_SIZE // 2)
        tile_center_y = tile_y_min + (MarioRAM.SPRITE_SIZE // 2)

        # Allow 8 pixel tolerance (half a tile)
        if (abs(enemy_x - tile_center_x) <= 8 and
            abs(enemy_center_y - tile_center_y) <= 8):
            return True

    return False


def extract_vision_grid(nes, width=7, height=10):
    """
    Extract a grid of tiles around Mario for AI vision.
    Vision is CENTERED on Mario (can see both ahead and behind).

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

    # Center vision horizontally on Mario
    # Reference uses 25% behind, 75% ahead
    tiles_behind = width // 4  # 25% behind (1 for width=7)
    start_col = mario_col - tiles_behind

    # Vertical: Center vision around Mario
    # About 1/3 above, Mario in middle, 2/3 below
    rows_above = height // 3  # About 3 for height=10
    start_row = mario_row - rows_above

    # Debug first call
    if not hasattr(extract_vision_grid, '_debug_printed'):
        print(f"🔍 [Vision] Mario at tile: col={mario_col}, row={mario_row}")
        print(f"🔍 [Vision] Horizontal span: {tiles_behind} tiles behind → {width - tiles_behind - 1} tiles ahead")
        print(f"🔍 [Vision] Scanning cols {start_col} to {start_col + width - 1}")
        print(f"🔍 [Vision] Scanning rows {start_row} to {start_row + height - 1}")

        # Sample a few tiles
        test_tiles = []
        for i in range(3):
            tile = get_tile_at(nes, mario_col + i, mario_row + 2)  # Below Mario
            test_tiles.append(hex(tile))
        print(f"🔍 [Vision] Sample tiles below Mario: {test_tiles}")
        extract_vision_grid._debug_printed = True

    for row_offset in range(height):
        row = start_row + row_offset

        for col_offset in range(width):
            col = start_col + col_offset

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


def get_score(nes):
    """
    Get Mario's current score.

    The score is stored in BCD (Binary Coded Decimal) format across 3 bytes:
    - Each byte stores 2 decimal digits (high nibble = tens, low nibble = ones)
    - Example: 0x12 = 12, 0x34 = 34

    Args:
        nes: JSNes instance

    Returns:
        int: Current score (0-999999)
    """
    try:
        ram = nes.cpu.mem

        # Read the 3 BCD bytes (6 digits total)
        ones_byte = ram[MarioRAM.SCORE_ONES]           # Rightmost 2 digits
        hundreds_byte = ram[MarioRAM.SCORE_HUNDREDS]   # Middle 2 digits
        ten_thousands_byte = ram[MarioRAM.SCORE_TEN_THOUSANDS]  # Leftmost 2 digits

        # Convert BCD to decimal
        # Each byte: high nibble * 10 + low nibble
        ones_tens = ((ones_byte >> 4) * 10) + (ones_byte & 0x0F)
        hundreds_thousands = ((hundreds_byte >> 4) * 10) + (hundreds_byte & 0x0F)
        ten_thousands_hundred_thousands = ((ten_thousands_byte >> 4) * 10) + (ten_thousands_byte & 0x0F)

        # Combine into final score
        score = (ten_thousands_hundred_thousands * 10000 +
                 hundreds_thousands * 100 +
                 ones_tens)

        return score
    except Exception as e:
        console.error(f"Error reading score: {e}")
        return 0


def get_lives(nes):
    """
    Get number of lives remaining.

    This is critical for detecting checkpoint respawns!
    When Mario dies after passing a checkpoint, the game may respawn him
    without setting the death flag, but the lives counter ALWAYS decrements.

    Args:
        nes: JSNes instance

    Returns:
        int: Lives remaining (0-99, typically starts at 3)
    """
    try:
        ram = nes.cpu.mem
        lives = ram[MarioRAM.LIVES_REMAINING]

        # Debug first call
        if not hasattr(get_lives, '_debug_printed'):
            print(f"🔍 [RAM] First lives read: {lives}")
            get_lives._debug_printed = True

        return lives
    except Exception as e:
        console.error(f"Error reading lives: {e}")
        return 3  # Default to 3 lives if can't read


# ============================================================================
# ENGINEERED FEATURES - High-level context features for better decision making
# ============================================================================

def get_nearest_enemy_distance(nes, max_scan_distance=10):
    """
    Get distance to nearest enemy in both directions.

    Args:
        nes: JSNes instance
        max_scan_distance: Maximum tiles to scan in each direction

    Returns:
        tuple: (distance_left, distance_right) in tiles
               Returns max_scan_distance if no enemy found
    """
    mario_col, mario_row = get_mario_tile_position(nes)
    enemies = get_enemy_positions(nes)

    nearest_left = max_scan_distance
    nearest_right = max_scan_distance

    for enemy_x, enemy_y in enemies:
        enemy_col = enemy_x // MarioRAM.SPRITE_SIZE
        enemy_row = (enemy_y + MarioRAM.SPRITE_SIZE - MarioRAM.STATUS_BAR_HEIGHT) // MarioRAM.SPRITE_SIZE

        # Only consider enemies at similar height (within 3 tiles vertically)
        if abs(enemy_row - mario_row) > 3:
            continue

        distance = enemy_col - mario_col

        if distance < 0:  # Enemy is to the left
            nearest_left = min(nearest_left, abs(distance))
        elif distance > 0:  # Enemy is to the right
            nearest_right = min(nearest_right, distance)

    return (nearest_left, nearest_right)


def get_distance_to_ground(nes, max_scan_depth=8):
    """
    Get distance from Mario to solid ground below.

    Args:
        nes: JSNes instance
        max_scan_depth: Maximum tiles to scan downward

    Returns:
        int: Distance to ground in tiles (0 if on ground, max_scan_depth if no ground found)
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    # Scan downward from Mario's position
    for depth in range(1, max_scan_depth + 1):
        tile_value = get_tile_at(nes, mario_col, mario_row + depth)
        if is_solid_tile(tile_value):
            return depth

    return max_scan_depth  # No ground found (pit!)


def get_nearest_pit_distance(nes, max_scan_distance=12):
    """
    Get distance to nearest pit (gap in the ground) ahead of Mario.

    Args:
        nes: JSNes instance
        max_scan_distance: Maximum tiles to scan ahead

    Returns:
        int: Distance to pit in tiles (max_scan_distance if no pit found)
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    # Scan ahead, checking ground level (2 tiles below Mario)
    ground_row = mario_row + 2

    for distance in range(1, max_scan_distance + 1):
        col = mario_col + distance

        # Check if there's ground at this position
        tile_value = get_tile_at(nes, col, ground_row)

        # If no solid ground, this might be a pit - verify by checking below too
        if not is_solid_tile(tile_value):
            # Check if it's truly a pit (no ground for next 2 tiles down)
            deep_tile = get_tile_at(nes, col, ground_row + 1)
            if not is_solid_tile(deep_tile):
                return distance  # Found a pit!

    return max_scan_distance  # No pit found


def get_nearest_obstacle_distance(nes, max_scan_distance=10):
    """
    Get distance to nearest obstacle (solid block) ahead at Mario's height.
    Useful for detecting walls, pipes, blocks that need jumping.

    Args:
        nes: JSNes instance
        max_scan_distance: Maximum tiles to scan ahead

    Returns:
        int: Distance to obstacle in tiles (max_scan_distance if none found)
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    # Scan ahead at Mario's height and one tile above
    for distance in range(1, max_scan_distance + 1):
        col = mario_col + distance

        # Check at Mario's height
        tile_at_height = get_tile_at(nes, col, mario_row)
        tile_above = get_tile_at(nes, col, mario_row - 1)

        if is_solid_tile(tile_at_height) or is_solid_tile(tile_above):
            return distance

    return max_scan_distance


def get_obstacle_height(nes, max_scan_distance=10):
    """
    Get the height of the nearest obstacle ahead that blocks Mario's path.
    Only considers obstacles at or above Mario's height (not ground tiles below).
    Helps the agent know if it needs to jump (and how high).

    Args:
        nes: JSNes instance
        max_scan_distance: Maximum tiles to scan ahead

    Returns:
        int: Height of obstacle in tiles (0 if no obstacle or just flat ground)
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    # First find an obstacle at or above Mario's height
    obstacle_col = None
    obstacle_row = None

    for distance in range(1, max_scan_distance + 1):
        col = mario_col + distance

        # Check at Mario's height and above (don't count ground below as obstacle)
        tile_at_height = get_tile_at(nes, col, mario_row)
        tile_above = get_tile_at(nes, col, mario_row - 1)

        if is_solid_tile(tile_at_height):
            obstacle_col = col
            obstacle_row = mario_row
            break
        elif is_solid_tile(tile_above):
            obstacle_col = col
            obstacle_row = mario_row - 1
            break

    if obstacle_col is None:
        return 0  # No obstacle blocking Mario's path

    # Now measure how tall the obstacle extends upward from where we found it
    height = 1  # Count the tile we found

    # Scan upward to find the top of the obstacle
    for check_row in range(obstacle_row - 1, max(0, obstacle_row - 5), -1):
        if is_solid_tile(get_tile_at(nes, obstacle_col, check_row)):
            height += 1
        else:
            break  # Found the top

    return height


def is_on_ground(nes):
    """
    Check if Mario is standing on solid ground.

    Args:
        nes: JSNes instance

    Returns:
        bool: True if on ground, False if in air
    """
    mario_col, mario_row = get_mario_tile_position(nes)

    # Check tile directly below Mario
    tile_below = get_tile_at(nes, mario_col, mario_row + 1)

    return is_solid_tile(tile_below)


def extract_context_features(nes):
    """
    Extract high-level engineered features for better decision making.

    Returns:
        list: Array of 9 normalized feature values [0.0-1.0]:
              [enemy_left_dist, enemy_right_dist, ground_dist, pit_dist,
               obstacle_dist, obstacle_height, is_on_ground, mario_y_normalized, enemy_nearby]
    """
    # Distance features (normalize to 0-1 range)
    enemy_left, enemy_right = get_nearest_enemy_distance(nes, max_scan_distance=10)
    ground_dist = get_distance_to_ground(nes, max_scan_depth=8)
    pit_dist = get_nearest_pit_distance(nes, max_scan_distance=12)
    obstacle_dist = get_nearest_obstacle_distance(nes, max_scan_distance=10)
    obstacle_height = get_obstacle_height(nes, max_scan_distance=10)

    # Normalize distances (inverse: closer = higher value)
    enemy_left_norm = 1.0 - (enemy_left / 10.0)
    enemy_right_norm = 1.0 - (enemy_right / 10.0)
    ground_dist_norm = ground_dist / 8.0  # Higher = further from ground
    pit_dist_norm = 1.0 - (pit_dist / 12.0)  # Higher = pit is closer (danger!)
    obstacle_dist_norm = 1.0 - (obstacle_dist / 10.0)  # Higher = obstacle closer
    obstacle_height_norm = max(0.0, min(1.0, obstacle_height / 3.0))  # 0-3 tiles = 0.0-1.0

    # Binary features
    on_ground = 1.0 if is_on_ground(nes) else 0.0

    # Mario's Y position (normalized 0-1, lower Y = higher in screen = higher value)
    _, mario_y = get_mario_position(nes)
    y_normalized = 1.0 - (mario_y / 240.0)  # Invert: jumping = higher value

    # Enemy proximity alert (any enemy within 5 tiles)
    enemy_nearby = 1.0 if (enemy_left < 5 or enemy_right < 5) else 0.0

    return [
        enemy_left_norm,
        enemy_right_norm,
        ground_dist_norm,
        pit_dist_norm,
        obstacle_dist_norm,
        obstacle_height_norm,  # NEW: tells agent how tall the obstacle is!
        on_ground,
        y_normalized,
        enemy_nearby
    ]
