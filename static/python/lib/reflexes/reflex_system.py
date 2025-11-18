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

    def __init__(self, enable_reflexes=True, jump_hold_duration=6):
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

        # Apply vision-based reflexes (enemy, obstacle, pit)
        actions = self._apply_vision_reflexes(state, actions, simple_controls)

        # Apply emergency stuck-at-wall reflex
        actions = self._apply_emergency_reflex(state, actions, stuck_frames, simple_controls)

        # Apply button holds (jump consistency)
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

            # Button indices
            if simple_controls:
                LEFT, RIGHT, JUMP = 0, 1, 2
            else:
                LEFT, RIGHT, JUMP = 2, 3, 4

            # ===== REFLEX 1: Enemy on RIGHT (first Goomba) =====
            if enemy_right_dist < 4.0:
                if enemy_right_dist < 1.5:  # VERY CLOSE - EMERGENCY!
                    # Emergency brake: stop forward movement
                    output[RIGHT] = max(0.0, output[RIGHT] - 0.6)
                    # Maximum jump boost
                    output[JUMP] = min(1.0, output[JUMP] + 1.0)
                    # STRONG backward jump to dodge
                    output[LEFT] = min(1.0, output[LEFT] + 0.7)

                elif enemy_right_dist < 3.0:  # MEDIUM - PREPARE
                    # Moderate jump boost
                    output[JUMP] = min(1.0, output[JUMP] + 0.6)
                    # Slight backward positioning for spacing
                    output[LEFT] = min(1.0, output[LEFT] + 0.1)
                    # Cautious forward movement
                    output[RIGHT] = min(1.0, output[RIGHT] + 0.1)

            # ===== REFLEX 2: Enemy on LEFT =====
            if enemy_left_dist < 4.0:
                if enemy_left_dist < 1.5:  # VERY CLOSE - EMERGENCY!
                    # Emergency brake: stop backward movement
                    output[LEFT] = max(0.0, output[LEFT] - 0.6)
                    # Boost jump
                    output[JUMP] = min(1.0, output[JUMP] + 0.8)
                    # Move right to escape
                    output[RIGHT] = min(1.0, output[RIGHT] + 0.4)

                elif enemy_left_dist < 3.0:  # MEDIUM - PREPARE
                    # Boost right to move away
                    output[RIGHT] = min(1.0, output[RIGHT] + 0.3)
                    # Moderate jump boost
                    output[JUMP] = min(1.0, output[JUMP] + 0.4)

            # ===== REFLEX 3: Tall obstacle ahead =====
            if obstacle_dist_norm > 0.85 and obstacle_height_norm > 0.7:
                # Strong jump boost to clear obstacle
                output[JUMP] = min(1.0, output[JUMP] + 0.8)

                # If very close (likely stuck at wall), slow down
                if obstacle_dist_norm > 0.95:
                    output[RIGHT] = max(0.0, output[RIGHT] - 0.4)

            # ===== REFLEX 4: Pit ahead =====
            if pit_dist_norm > 0.7:
                # Boost jump proportional to pit proximity
                pit_boost = 0.6 * pit_dist_norm
                output[JUMP] = min(1.0, output[JUMP] + pit_boost)
                # Maintain forward movement to jump across
                output[RIGHT] = min(1.0, output[RIGHT] + 0.2)

        return output

    def _apply_emergency_reflex(self, state, actions, stuck_frames, simple_controls):
        """
        Apply emergency stuck-at-wall reflex.

        When Mario is stuck at a wall for 1+ seconds:
        Phase 1 (15 frames): Back up with RUN to build momentum
        Phase 2 (10 frames): Running jump forward (RIGHT + B + JUMP)
        """
        if stuck_frames <= 60:
            # Not stuck long enough, reset emergency state
            if self.emergency_active:
                console.log(f"   Emergency reflex complete - Mario escaped!")
            self.emergency_active = False
            self.emergency_phase = 0
            return actions

        # Get obstacle distance from context
        vision_size = 16 * 7
        if len(state) <= vision_size:
            return actions

        context = state[vision_size:]
        obstacle_dist_norm = context[4] if len(context) > 4 else 0.0

        # Only activate if stuck AND at a wall
        if obstacle_dist_norm <= 0.9:
            self.emergency_active = False
            self.emergency_phase = 0
            return actions

        # Button indices
        if simple_controls:
            left_idx, right_idx, a_idx, b_idx = 0, 1, 2, 3
        else:
            left_idx, right_idx, a_idx, b_idx = 2, 3, 4, 5

        # Activate emergency sequence
        if not self.emergency_active:
            self.emergency_active = True
            self.emergency_phase = 0
            console.log(f"🚨 EMERGENCY REFLEX: Stuck at wall (obstacle_dist={obstacle_dist_norm:.2f})")
            console.log(f"   Phase 1: Backing up to build momentum...")

        frames_stuck = stuck_frames - 60

        # PHASE 1: Back up with momentum (frames 0-14)
        if frames_stuck < 15:
            actions[left_idx] = 1   # Press LEFT
            actions[right_idx] = 0  # Release RIGHT
            actions[b_idx] = 1      # Press RUN for speed
            actions[a_idx] = 0      # Don't jump yet
            if frames_stuck == 0:
                self.emergency_phase = 0

        # PHASE 2: Running jump forward (frames 15-24)
        elif frames_stuck < 25:
            if self.emergency_phase == 0:
                console.log(f"   Phase 2: RUNNING JUMP!")
                self.emergency_phase = 1
            actions[left_idx] = 0   # Release LEFT
            actions[right_idx] = 1  # Press RIGHT
            actions[b_idx] = 1      # Press RUN
            actions[a_idx] = 1      # Press JUMP

        # PHASE 3: Reset after sequence
        else:
            self.emergency_active = False
            self.emergency_phase = 0

        return actions

    def _apply_button_holds(self, actions, simple_controls):
        """
        Apply button hold logic for consistent jump height.

        When A (jump) is pressed, hold it for several frames to ensure
        Mario gets a full-height jump instead of a weak hop.
        """
        a_button_idx = 4 if not simple_controls else 2

        # Start jump hold when A is pressed
        if actions[a_button_idx] > 0:
            self.jump_hold_counter = self.jump_hold_duration

        # Continue holding A for remaining frames
        if self.jump_hold_counter > 0:
            actions[a_button_idx] = 1
            self.jump_hold_counter -= 1

        return actions

    def reset(self):
        """Reset all reflex state (call at start of each generation)."""
        self.jump_hold_counter = 0
        self.emergency_active = False
        self.emergency_phase = 0
