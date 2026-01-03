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

        # ONLY apply button holds (jump consistency)
        # Vision reflexes and emergency reflex are DISABLED
        # They fight with network learning - let the network learn on its own
        actions = self._apply_button_holds(actions, simple_controls)

        return actions

    def _apply_vision_reflexes(self, state, output, simple_controls):
        """
        Apply reflexes based on vision and context features.

        Includes:
        - Enemy proximity (jump backwards when very close)
        - Obstacle detection (jump over tall obstacles)
        - Pit detection (jump across gaps)
        """
        vision_size = 16 * 7  # 112 elements
        if len(state) <= vision_size:
            return output  # No context features available

        context = state[vision_size:]

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
            # Only trigger jump when VERY close (0.9+) - let Mario build momentum first!
            # At medium distance (0.6-0.9): just ensure forward movement, no forced jump
            if obstacle_dist_norm > 0.6 and obstacle_height_norm > 0.2:
                # Always move forward toward obstacle, never back up
                output[RIGHT] = 1
                output[RUN] = 1
                output[LEFT] = 0

                # Only force JUMP when very close (about to hit wall)
                # This allows momentum to build before jumping
                if obstacle_dist_norm > 0.88:
                    output[JUMP] = 1

            # ===== REFLEX 4: Pit ahead =====
            if pit_dist_norm > 0.7:
                # FORCE jump ON for pit
                output[JUMP] = 1
                output[RIGHT] = 1  # Keep moving forward
                output[RUN] = 1    # Sprint jump for distance

        return output

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
        # Decoder always outputs 6-button array; A is index 4, B is index 5
        a_button_idx = 4
        b_button_idx = 5

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
