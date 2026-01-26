"""
Reflex System - Coordinated instinctive behaviors for Mario

Manages all hard-coded reflexive responses:
- Enemy avoidance (jump backwards when close)
- Obstacle detection (jump over tall obstacles)
- Emergency stuck-at-wall (backup → running jump sequence)
- Button holds (consistent jump height)
- Pit detection (jump across gaps)
"""

import numpy as np
from js import console


class ReflexSystem:
    """
    Centralized reflex system for managing all instinctive behaviors.

    Reflexes give evolution a head start by providing basic survival instincts
    that would take thousands of generations to evolve from scratch.
    """

    def __init__(self, enable_reflexes=True, jump_hold_duration=10):
        """
        Initialize reflex system.

        Args:
            enable_reflexes: Enable/disable all reflexes (default: True)
            jump_hold_duration: How many frames to hold jump button (default: 6)
        """
        self.enable_reflexes = enable_reflexes

        # Button hold state
        self.jump_hold_counter = 0
        self.jump_hold_duration = jump_hold_duration

        # Emergency reflex state (stuck-at-wall sequence)
        self.emergency_active = False
        self.emergency_phase = 0
        self.emergency_cycle = 0
        self._emergency_start_frame = 0  # Track when emergency started
        self._emergency_last_end_frame = -9999  # Cooldown between emergencies

    def apply_reflexes(self, state, actions, stuck_frames, simple_controls=True):
        """
        Apply all reflexes to network output.

        Args:
            state: Full input state (vision + context features)
            actions: Network output (button presses) as numpy array
            stuck_frames: How long Mario has been stuck (for emergency reflex)
            simple_controls: If True, 4-button mode [L,R,A,B], else 6-button [U,D,L,R,A,B]

        Returns:
            Modified actions with all reflexes applied
        """
        if not self.enable_reflexes:
            return actions

        # Get network output BEFORE decoding (for vision reflexes to modify)
        # We need to apply vision reflexes to network outputs, then decode
        # But we're called AFTER decoding... so we need to work with binary actions
        
        # For now, apply vision reflexes by directly setting buttons when obstacles detected
        # This is less ideal but works with the current architecture
        actions = self._apply_vision_reflexes_to_actions(state, actions, simple_controls)

        # Apply emergency stuck reflex (modifies binary actions)
        actions = self._apply_emergency_reflex(state, actions, stuck_frames, simple_controls)

        # Apply button holds (jump consistency)
        actions = self._apply_button_holds(actions, simple_controls)

        return actions

    def _apply_vision_reflexes(self, state, output, simple_controls):
        """
        Apply reflexes based on vision and context features.

        Includes:
        - Enemy proximity (jump backwards when very close)
        - Obstacle detection (jump over tall obstacles) - works from vision OR context
        - Pit detection (jump across gaps)
        """
        # Detect vision size dynamically (could be 7×10=70 or 16×7=112)
        # Vision is at the start, followed by optional context/row encoding
        vision_width = 7  # Default assumption
        vision_height = 10  # Default assumption
        
        # Try to detect actual vision size
        if len(state) >= 70:
            # Could be 7×10 or other sizes
            # Check if we have context features (9 elements) or row encoding (10-15 elements)
            if len(state) >= 79:  # 70 vision + 9 context
                vision_size = 70  # Likely 7×10
                vision_width, vision_height = 7, 10
            elif len(state) >= 80:  # 70 vision + 10 row encoding
                vision_size = 70
                vision_width, vision_height = 7, 10
            elif len(state) >= 112:  # Could be 16×7
                vision_size = 112
                vision_width, vision_height = 16, 7
            else:
                vision_size = 70  # Default to 7×10
        else:
            vision_size = len(state)  # Use all if too small
        
        # Extract vision grid
        vision = state[:vision_size] if len(state) > vision_size else state
        
        # Try to get context features if available
        context = state[vision_size:] if len(state) > vision_size else []

        # Extract context features
        if len(context) >= 9:
            enemy_left_norm = context[0]    # 1.0 = enemy very close on left
            enemy_right_norm = context[1]   # 1.0 = enemy very close on right
            pit_dist_norm = context[3]      # Higher = pit closer
            obstacle_dist_norm = context[4] # Higher = obstacle closer
            obstacle_height_norm = context[5] # Higher = taller obstacle
            on_ground = context[6]          # 1.0 = Mario is on ground

            # Convert normalized distances to approximate tile distances
            enemy_left_dist = (1.0 - enemy_left_norm) * 10.0
            enemy_right_dist = (1.0 - enemy_right_norm) * 10.0

            # Button indices (decoder always outputs 6 buttons: [UP, DOWN, LEFT, RIGHT, A, B])
            if simple_controls:
                LEFT, RIGHT, JUMP, RUN = 2, 3, 4, 5
            else:
                LEFT, RIGHT, JUMP, RUN = 2, 3, 4, 5

            # ===== REFLEX 1: Enemy on RIGHT (first Goomba) =====
            # IMPORTANT: Only trigger if no obstacle is blocking the path to the enemy!
            # Enemies behind pipes should NOT trigger this reflex (we can't reach them yet)
            obstacle_blocking_right = obstacle_dist_norm > 0.5 and obstacle_height_norm > 0.2

            if enemy_right_dist < 4.0 and not obstacle_blocking_right:
                if enemy_right_dist < 1.5:  # VERY CLOSE - EMERGENCY!
                    output[RIGHT] = 0  # Stop moving into enemy
                    output[JUMP] = 1   # Jump over
                    output[LEFT] = 1   # Back away

                elif enemy_right_dist < 3.0:  # MEDIUM - PREPARE TO JUMP
                    output[JUMP] = 1   # Jump over enemy
                    output[RUN] = 1    # Sprint for distance

            # ===== REFLEX 2: Enemy on LEFT =====
            if enemy_left_dist < 4.0:
                if enemy_left_dist < 1.5:  # VERY CLOSE - EMERGENCY!
                    output[LEFT] = 0   # Stop backing into enemy
                    output[JUMP] = 1   # Jump
                    output[RIGHT] = 1  # Escape right

                elif enemy_left_dist < 3.0:  # MEDIUM - PREPARE
                    output[RIGHT] = 1  # Move away
                    output[JUMP] = 1   # Jump

            # ===== REFLEX 3: Obstacle ahead (pipe detection) =====
            # Try context features first, fall back to vision-based detection
            obstacle_detected = False
            obstacle_very_close = False
            
            if len(context) >= 9:
                obstacle_dist_norm = context[4]
                obstacle_height_norm = context[5]
                obstacle_detected = obstacle_dist_norm > 0.6 and obstacle_height_norm > 0.2
                obstacle_very_close = obstacle_dist_norm > 0.88
            else:
                # Vision-based obstacle detection (when context features disabled)
                # Mario is typically at column 1-2 (left side of vision)
                # Scan ahead for solid blocks (# = 1.0)
                mario_col = vision_width // 4  # Mario's column in vision
                mario_row = vision_height // 3  # Mario's row in vision
                
                # Check 1-3 tiles ahead at Mario's height and above
                for dist in range(1, min(4, vision_width - mario_col)):
                    col = mario_col + dist
                    # Check at Mario's height and 1-2 tiles above
                    for row_offset in [0, -1, -2]:
                        row = mario_row + row_offset
                        if 0 <= row < vision_height and 0 <= col < vision_width:
                            idx = row * vision_width + col
                            if idx < len(vision) and vision[idx] == 1.0:  # Solid block
                                obstacle_detected = True
                                if dist <= 2:  # Very close (1-2 tiles)
                                    obstacle_very_close = True
                                break
                    if obstacle_detected:
                        break
            
            if obstacle_detected:
                # Always move forward toward obstacle, never back up
                output[RIGHT] = 1
                output[RUN] = 1
                output[LEFT] = 0

                # Only force JUMP when very close (about to hit wall)
                # This allows momentum to build before jumping
                if obstacle_very_close:
                    output[JUMP] = 1

            # ===== REFLEX 4: Pit ahead =====
            if pit_dist_norm > 0.7:
                # FORCE jump ON for pit
                output[JUMP] = 1
                output[RIGHT] = 1  # Keep moving forward
                output[RUN] = 1    # Sprint jump for distance

        return output

    def _apply_vision_reflexes_to_actions(self, state, actions, simple_controls):
        """
        Apply vision-based reflexes directly to binary button actions.
        Works when reflexes are called after decoding.
        """
        # Detect vision size dynamically
        vision_width = 7
        vision_height = 10
        vision_size = 70  # 7×10 default
        
        if len(state) >= 70:
            vision_size = 70
        else:
            vision_size = len(state)
        
        vision = state[:vision_size] if len(state) > vision_size else state
        
        # Button indices (actions are already decoded: [UP, DOWN, LEFT, RIGHT, A, B])
        LEFT_IDX, RIGHT_IDX, JUMP_IDX, RUN_IDX = 2, 3, 4, 5
        
        # Vision-based obstacle detection
        mario_col = vision_width // 4
        mario_row = vision_height // 3
        
        # Check 1-2 tiles ahead for solid blocks
        obstacle_very_close = False
        for dist in range(1, min(3, vision_width - mario_col)):
            col = mario_col + dist
            for row_offset in [0, -1]:
                row = mario_row + row_offset
                if 0 <= row < vision_height and 0 <= col < vision_width:
                    idx = row * vision_width + col
                    if idx < len(vision) and vision[idx] == 1.0:  # Solid block
                        obstacle_very_close = True
                        break
            if obstacle_very_close:
                break
        
        if obstacle_very_close:
            # Force forward movement and jump when obstacle is very close
            actions[RIGHT_IDX] = 1
            actions[RUN_IDX] = 1
            actions[JUMP_IDX] = 1
            actions[LEFT_IDX] = 0  # Never back up when obstacle detected
        
        return actions

    def _apply_emergency_reflex(self, state, actions, stuck_frames, simple_controls):
        """
        Apply emergency stuck-at-wall reflex.

        When Mario is stuck for 1+ seconds (30 frames at 30 FPS):
        Phase 1 (20 frames): Back up with RUN to build momentum
        Phase 2 (25 frames): Running jump forward (RIGHT + B + JUMP held)
        Phase 3 (15 frames): Continue forward with small hops
        Total: 60 frames (2 seconds)

        IMPORTANT: Once activated, the emergency sequence runs to completion.
        We don't check obstacle distance mid-cycle because backing up naturally
        increases the distance, which would falsely cancel the sequence.
        """
        # Button indices (decoder output is always [UP, DOWN, LEFT, RIGHT, A, B])
        if simple_controls:
            left_idx, right_idx, a_idx, b_idx = 2, 3, 4, 5
        else:
            left_idx, right_idx, a_idx, b_idx = 2, 3, 4, 5

        # Check if Mario escaped (progress was made → stuck_frames reset)
        if stuck_frames <= 15:
            # Mario made progress! End emergency gracefully
            if self.emergency_active:
                console.log(f"   ✅ Emergency reflex SUCCESS - Mario escaped!")
            self.emergency_active = False
            self.emergency_phase = 0
            self.emergency_cycle = 0
            self._emergency_last_end_frame = stuck_frames
            return actions

        # Not stuck long enough to trigger emergency (wait ~3s = 90 frames)
        if stuck_frames <= 90 and not self.emergency_active:
            return actions

        # Cooldown after an emergency to avoid rapid re-triggers
        if (not self.emergency_active) and (stuck_frames - self._emergency_last_end_frame < 120):
            return actions

        # Get obstacle info for initial activation decision only
        vision_size = 16 * 7
        context = state[vision_size:] if len(state) > vision_size else []
        obstacle_dist_norm = context[4] if len(context) > 4 else 0.0
        obstacle_height_norm = context[5] if len(context) > 5 else 0.0

        # ACTIVATION: Only check wall proximity when NOT already in emergency
        # Once emergency is active, complete the full cycle regardless of distance
        if not self.emergency_active:
            # Need to be VERY close to wall (0.95) to trigger emergency backup
            # This prevents emergency from interfering during active jump attempts
            # (obstacle reflex handles jump attempts at dist > 0.5)
            if obstacle_dist_norm < 0.95 or obstacle_height_norm < 0.2:
                return actions

            # Activate emergency sequence!
            self.emergency_active = True
            self.emergency_phase = 0
            self.emergency_cycle = 0
            self._emergency_start_frame = stuck_frames
            print(f"🚨 EMERGENCY REFLEX ACTIVATED! dist={obstacle_dist_norm:.2f}, height={obstacle_height_norm:.2f}")
            console.log(f"🚨 EMERGENCY REFLEX ACTIVATED!")
            console.log(f"   Obstacle: dist={obstacle_dist_norm:.2f}, height={obstacle_height_norm:.2f}")
            console.log(f"   Starting backup → sprint jump sequence...")

        # Calculate position in emergency sequence
        # Use frames since emergency started, NOT total stuck frames
        frames_in_emergency = stuck_frames - self._emergency_start_frame
        cycle_length = 70  # Slightly longer cycle for better momentum
        cycle_position = frames_in_emergency % cycle_length

        # Abort after 2 full cycles to avoid infinite backing behavior
        if frames_in_emergency >= cycle_length * 2:
            console.log(f"   Emergency reflex cooldown (2 cycles done)")
            self.emergency_active = False
            self.emergency_phase = 0
            self.emergency_cycle = 0
            self._emergency_last_end_frame = stuck_frames
            return actions

        # Track cycle number for logging
        current_cycle = frames_in_emergency // cycle_length
        if current_cycle != self.emergency_cycle:
            self.emergency_cycle = current_cycle
            if current_cycle > 0:
                console.log(f"🔄 Emergency reflex cycle {current_cycle + 1} (still stuck!)")

        # PHASE 1: Back up with momentum (frames 0-24) - 25 frames
        if cycle_position < 25:
            if self.emergency_phase != 1:
                print("   Phase 1: Backing up (LEFT + RUN)")
                console.log(f"   Phase 1: Backing up (LEFT + RUN)")
                self.emergency_phase = 1
            actions[left_idx] = 1   # Press LEFT
            actions[right_idx] = 0  # Release RIGHT
            actions[b_idx] = 1      # Press RUN for speed
            actions[a_idx] = 0      # Don't jump yet

        # PHASE 2: Sprint jump forward (frames 25-54) - 30 frames
        elif cycle_position < 55:
            if self.emergency_phase != 2:
                print("   Phase 2: SPRINT JUMP! (RIGHT + RUN + JUMP)")
                console.log(f"   Phase 2: SPRINT JUMP! (RIGHT + RUN + JUMP)")
                self.emergency_phase = 2
            actions[left_idx] = 0   # Release LEFT
            actions[right_idx] = 1  # Press RIGHT
            actions[b_idx] = 1      # Press RUN (B button for sprint)
            actions[a_idx] = 1      # Press JUMP (held by button_holds)

        # PHASE 3: Continue forward with hop attempts (frames 55-69) - 15 frames
        else:
            if self.emergency_phase != 3:
                print("   Phase 3: Continue forward + hops")
                console.log(f"   Phase 3: Continue forward + hops")
                self.emergency_phase = 3
            actions[left_idx] = 0   # Release LEFT
            actions[right_idx] = 1  # Press RIGHT
            actions[b_idx] = 1      # Keep running
            # Small hops to potentially clear shorter obstacles
            actions[a_idx] = 1 if (cycle_position % 8 < 4) else 0

        return actions

    def _apply_button_holds(self, actions, simple_controls):
        """
        Apply button hold logic for consistent jump height.

        When A (jump) is pressed, hold it for several frames to ensure
        Mario gets a full-height jump instead of a weak hop.
        """
        # Button indices depend on control mode:
        # simple_controls=True:  [LEFT, RIGHT, A, B] → indices 0, 1, 2, 3
        # simple_controls=False: [UP, DOWN, LEFT, RIGHT, A, B] → indices 0, 1, 2, 3, 4, 5
        if simple_controls:
            a_button_idx = 2  # A (jump) is index 2 in 4-button mode
            b_button_idx = 3  # B (run) is index 3 in 4-button mode
        else:
            a_button_idx = 4  # A (jump) is index 4 in 6-button mode
            b_button_idx = 5  # B (run) is index 5 in 6-button mode

        # Start jump hold when A is pressed (value > 0 catches both 1 and floats)
        if actions[a_button_idx] > 0:
            self.jump_hold_counter = self.jump_hold_duration

        # Continue holding A for remaining frames (ensures full height jump)
        if self.jump_hold_counter > 0:
            actions[a_button_idx] = 1
            actions[b_button_idx] = 1  # Also hold RUN for longer jumps
            self.jump_hold_counter -= 1

        return actions

    def reset(self):
        """Reset all reflex state (call at start of each generation)."""
        self.jump_hold_counter = 0
        self.emergency_active = False
        self.emergency_phase = 0
        self.emergency_cycle = 0
        self._emergency_start_frame = 0