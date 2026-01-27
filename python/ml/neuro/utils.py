"""
NES RAM Utilities for Mario
Exact port of Agent.js logic for consistent input building.

Optimized: Uses getGameState() which reads only ~450 bytes instead of 65KB.
"""

import numpy as np

# Constants for tile lookup
TILE_PAGE_SIZE = 208

# Vision config (matches JS Agent)
START_ROW = 4
VIZ_WIDTH = 7
VIZ_HEIGHT = 10

SPRITE_WIDTH = 16
SPRITE_HEIGHT = 16


def convert_state(js_state):
    """Convert JsProxy state to pure Python dict for faster access.
    
    Call this once per state, then use the result for all operations.
    Avoids repeated JsProxy boundary crossing overhead.
    """
    if js_state is None:
        return None
        
    # Already a dict? Return as-is
    if isinstance(js_state, dict):
        return js_state
    
    # Convert JsProxy to Python
    if hasattr(js_state, 'to_py'):
        return js_state.to_py()
    
    # Manual conversion for JsProxy without to_py
    tiles = js_state['tiles']
    if hasattr(tiles, 'to_py'):
        tiles = tiles.to_py()
    else:
        tiles = list(tiles)
        
    enemies = js_state['enemies']
    if hasattr(enemies, 'to_py'):
        enemies = enemies.to_py()
    else:
        enemies = [dict(e) if hasattr(e, 'keys') else e for e in enemies]
    
    return {
        'playerXLevel': int(js_state['playerXLevel']),
        'playerXScreen': int(js_state['playerXScreen']),
        'playerXScreenOffset': int(js_state['playerXScreenOffset']),
        'playerYScreenOffset': int(js_state['playerYScreenOffset']),
        'playerYScreen': int(js_state['playerYScreen']),
        'playerVerticalScreen': int(js_state['playerVerticalScreen']),
        'playerState': int(js_state['playerState']),
        'playerFloatState': int(js_state['playerFloatState']),
        'tiles': tiles,
        'enemies': enemies
    }


def get_mario_location_in_level(state):
    """Get Mario's absolute X position in level (page * 256 + offset).
    
    Args:
        state: Game state object from getGameState() or full memory array
    """
    # Support both new state object and legacy full memory array
    if isinstance(state, dict) or hasattr(state, 'playerXLevel'):
        return state['playerXLevel'] * 256 + state['playerXScreen']
    else:
        # Legacy: full memory array
        return state[0x06D] * 256 + state[0x086]


def get_mario_location_on_screen(state):
    """Get Mario's screen position.
    
    Args:
        state: Game state object or full memory array
    """
    if isinstance(state, dict) or hasattr(state, 'playerXScreenOffset'):
        x = state['playerXScreenOffset']
        y = state['playerYScreen'] * state['playerVerticalScreen'] + SPRITE_HEIGHT
    else:
        x = state[0x3AD]
        y = state[0xCE] * state[0xB5] + SPRITE_HEIGHT
    return x, y


def get_mario_row_col(state):
    """Get Mario's tile row and column.
    
    Args:
        state: Game state object or full memory array
    """
    if isinstance(state, dict) or hasattr(state, 'playerYScreenOffset'):
        y = state['playerYScreenOffset'] + 16
        x = state['playerXScreenOffset'] + 12
    else:
        y = state[0x3B8] + 16
        x = state[0x3AD] + 12
    col = x // 16
    row = y // 16
    return row, col


def get_tile_from_state(tiles, x, y):
    """Get tile at PIXEL position from pre-extracted tile array.
    
    Args:
        tiles: Array of 416 tile bytes (2 pages × 208)
        x: X position in pixels (level coordinates)
        y: Y position in pixels (screen coordinates)
    """
    page = (x // 256) % 2
    sub_x = (x % 256) // 16
    sub_y = (y - 32) // 16
    
    if sub_y < 0 or sub_y >= 13:
        return 0
        
    idx = page * TILE_PAGE_SIZE + sub_y * 16 + sub_x
    
    if idx < 0 or idx >= len(tiles):
        return 0
        
    tile = tiles[idx]
    return 1 if tile != 0 else 0


def get_enemies_from_state(enemies_data):
    """Get list of enemy positions from state.
    
    Args:
        enemies_data: Array of 5 enemy objects from getGameState()
    """
    enemies = []
    for e in enemies_data:
        # Handle both dict and JsProxy
        drawn = e.get('drawn', 0) if isinstance(e, dict) else e['drawn']
        if drawn:
            xLevel = e.get('xLevel', 0) if isinstance(e, dict) else e['xLevel']
            xScreen = e.get('xScreen', 0) if isinstance(e, dict) else e['xScreen']
            yScreen = e.get('yScreen', 0) if isinstance(e, dict) else e['yScreen']
            x = xLevel * 256 + xScreen
            enemies.append((x, yScreen))
    return enemies


def get_tiles_from_state(state):
    """Build tile dictionary from game state.
    
    Args:
        state: Game state dict (already converted via convert_state)
        
    Returns:
        Dict mapping (row, col) -> tile value (-1=enemy, 0=empty, 1=solid)
    """
    tiles_dict = {}
    
    mario_level_x = get_mario_location_in_level(state)
    mario_screen_x, _ = get_mario_location_on_screen(state)
    x_start = mario_level_x - mario_screen_x
    
    # State should already be converted - tiles is a list
    tiles_arr = state['tiles']
    enemies = get_enemies_from_state(state['enemies'])
    
    row = 0
    for y_pos in range(0, 240, 16):
        col = 0
        for x_pos in range(x_start, x_start + 256, 16):
            key = (row, col)
            
            if row < 2:
                tiles_dict[key] = 0
            else:
                tiles_dict[key] = get_tile_from_state(tiles_arr, x_pos, y_pos)
                
            # Check for enemies
            for ex, ey in enemies:
                ey_adjusted = ey + 8
                if abs(x_pos - ex) <= 8 and abs(y_pos - ey_adjusted) <= 8:
                    tiles_dict[key] = -1
                    
            col += 1
        row += 1
        
    return tiles_dict


_debug_counter = 0

def build_inputs(state, debug=False):
    """Build neural network input array from game state.
    
    Args:
        state: Game state object from getGameState() - only ~450 bytes!
        
    Returns:
        80-element numpy array: 70 vision tiles + 10 row encoding
    """
    global _debug_counter
    
    row, col = get_mario_row_col(state)
    tiles = get_tiles_from_state(state)
    
    inputs = []
    
    # Vision grid: 10 rows starting at row 4, 7 cols starting at mario_col
    for tile_row in range(START_ROW, START_ROW + VIZ_HEIGHT):
        for tile_col in range(col, col + VIZ_WIDTH):
            key = (tile_row, tile_col)
            tile = tiles.get(key, 0)
            
            if tile == -1:
                inputs.append(-1)  # Enemy
            elif tile == 1 or tile > 0:
                inputs.append(1)   # Solid
            else:
                inputs.append(0)   # Empty
                
    # Row encoding: one-hot for mario's row relative to vision start
    relative_row = row - START_ROW
    for i in range(VIZ_HEIGHT):
        if i == relative_row and 0 <= relative_row < VIZ_HEIGHT:
            inputs.append(1)
        else:
            inputs.append(0)
    
    # Debug logging (every 5000 calls - less noisy)
    _debug_counter += 1
    if _debug_counter % 5000 == 1:
        from js import console
        x = get_mario_location_in_level(state)
        solids = sum(1 for v in inputs[:70] if v == 1)
        enemies = sum(1 for v in inputs[:70] if v == -1)
        console.log(f"[PY Vision] x={x} row={row} col={col} | solids={solids} enemies={enemies}")
            
    return np.array(inputs, dtype=np.float64)


def is_dead(state):
    """Check if Mario is dead.
    
    Args:
        state: Game state object or full memory array
    """
    if isinstance(state, dict) or hasattr(state, 'playerState'):
        player_state = state['playerState']
    else:
        player_state = state[0x000E]
    return player_state in [0x06, 0x0B]


def did_win(state):
    """Check if Mario reached the flag.
    
    Args:
        state: Game state object or full memory array
    """
    if isinstance(state, dict) or hasattr(state, 'playerFloatState'):
        float_state = state['playerFloatState']
    else:
        float_state = state[0x001D]
    return float_state == 3


def calculate_fitness(distance, frames, score=0, died=False, won=False):
    """Calculate fitness score.
    
    Args:
        distance: X position reached
        frames: Number of frames taken
        score: Game score (optional)
        died: Whether Mario died
        won: Whether Mario reached flag
        
    Returns:
        Fitness value
    """
    # Base fitness is distance with exponential reward
    fitness = distance ** 1.5
    
    # Time penalty (encourage faster completion)
    fitness -= frames * 0.1
    
    # Score bonus
    fitness += score * 2
    
    # Death penalty
    if died:
        fitness -= 100
        
    # Win bonus
    if won:
        fitness += 10000
        
    return max(0, fitness)
