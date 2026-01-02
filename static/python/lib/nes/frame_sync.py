"""
Frame Synchronization Manager - Ensures agent and emulator run at same rate

Provides a callback-based interface that guarantees the agent observes
exactly once per NES frame, preventing timing drift and missed states.

The NES runs at exactly 60 FPS (16.666ms per frame) using requestAnimationFrame.
This module ensures the agent's observe-decide-act loop is called exactly once
per emulated frame, maintaining perfect synchronization.
"""

from js import window, console
from pyodide.ffi import create_proxy


class FrameSyncManager:
    """
    Manages frame-perfect synchronization between NES emulator and agent.

    Uses a callback mechanism where the JavaScript emulator notifies Python
    after each frame is generated, ensuring 1:1 frame correspondence.

    Both emulator and agent run at the same FPS (configured in FrameTimer).
    """

    def __init__(self):
        """Initialize frame synchronization manager."""
        self.frame_callback = None
        self.frame_count = 0
        self.is_active = False
        self.last_frame_time = 0
        self.sync_proxy = None

        # Stats for monitoring
        self.total_frames = 0
        self.missed_frames = 0

    def start(self, frame_callback):
        """
        Start frame synchronization.

        Args:
            frame_callback: Function to call each frame (should be agent.step())
        """
        if self.is_active:
            console.warn("⚠️ FrameSyncManager already active")
            return

        self.frame_callback = frame_callback
        self.is_active = True
        self.frame_count = 0
        self.last_frame_time = 0

        # Create proxy for JavaScript to call
        self.sync_proxy = create_proxy(self._on_frame_ready)

        # Register with emulator's frame timer
        # The emulator will call this after each frame is generated
        if hasattr(window, 'nesFrameSync'):
            window.nesFrameSync.registerCallback(self.sync_proxy)
            console.log("🔄 Frame sync registered with emulator")
        else:
            console.error("❌ nesFrameSync not available on window")

        console.log("✅ FrameSyncManager started - agent will observe every emulator frame")

    def stop(self):
        """Stop frame synchronization."""
        if not self.is_active:
            return

        self.is_active = False

        # Unregister from emulator
        if hasattr(window, 'nesFrameSync'):
            window.nesFrameSync.unregisterCallback()

        # Clean up proxy
        if self.sync_proxy:
            self.sync_proxy.destroy()
            self.sync_proxy = None

        console.log(f"⏹️ FrameSyncManager stopped (processed {self.total_frames} frames, missed {self.missed_frames})")

    def _on_frame_ready(self, frame_time):
        """
        Called by emulator after each frame is generated.

        Args:
            frame_time: Current timestamp from requestAnimationFrame
        """
        if not self.is_active or not self.frame_callback:
            return

        # Increment frame counter
        self.frame_count += 1
        self.total_frames += 1

        # Track timing (emulator runs at configured FPS, e.g., 30 FPS = 33.33ms)
        if self.last_frame_time > 0:
            delta = frame_time - self.last_frame_time
            # At 30 FPS, expect ~33.33ms between frames
            # Allow 10ms tolerance for timing variations
            if delta > 43:  # 33.33ms + 10ms tolerance
                console.warn(f"⚠️ Frame timing gap detected (delta={delta:.1f}ms)")
                self.missed_frames += 1

        self.last_frame_time = frame_time

        # Call agent's step function (1:1 with emulator frames)
        try:
            self.frame_callback()
        except Exception as e:
            console.error(f"❌ Error in frame callback: {e}")
            self.stop()

    def get_stats(self):
        """
        Get synchronization statistics.

        Returns:
            dict: Frame sync stats
        """
        return {
            'is_active': self.is_active,
            'total_frames': self.total_frames,
            'missed_frames': self.missed_frames,
            'accuracy': 100 * (1 - self.missed_frames / max(1, self.total_frames))
        }

    def reset_stats(self):
        """Reset frame statistics."""
        self.frame_count = 0
        self.total_frames = 0
        self.missed_frames = 0
        self.last_frame_time = 0


# Legacy compatibility: setTimeout-based polling
# This is the OLD method - kept for fallback but should not be used
class PollingFrameSync:
    """
    Legacy frame sync using setTimeout polling.

    WARNING: This approach causes timing drift and should be avoided.
    Use FrameSyncManager instead for frame-perfect synchronization.
    """

    def __init__(self, interval_ms=16):
        """
        Initialize polling-based sync.

        Args:
            interval_ms: Polling interval in milliseconds (default: 16)
        """
        self.interval_ms = interval_ms
        self.is_active = False
        self.callback = None
        self.timeout_proxy = None

        console.warn("⚠️ Using PollingFrameSync - consider upgrading to FrameSyncManager")

    def start(self, callback):
        """Start polling."""
        self.callback = callback
        self.is_active = True
        self._schedule_next()

    def stop(self):
        """Stop polling."""
        self.is_active = False
        if self.timeout_proxy:
            self.timeout_proxy.destroy()
            self.timeout_proxy = None

    def _poll(self):
        """Execute callback and schedule next poll."""
        if not self.is_active:
            return

        try:
            if self.callback:
                self.callback()
        except Exception as e:
            console.error(f"❌ Error in polling callback: {e}")

        self._schedule_next()

    def _schedule_next(self):
        """Schedule next poll."""
        if self.is_active:
            self.timeout_proxy = create_proxy(self._poll)
            from js import setTimeout
            setTimeout(self.timeout_proxy, self.interval_ms)