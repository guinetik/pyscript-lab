"""
Mario Agent - Modular Neuroevolution Training System

Clean architecture using dependency injection:
- MarioAgent: Observe-decide-act loop
- OnePlusOneES: Evolution strategy with elitism
- MarioFitnessCalculator: Configurable fitness function
- GenerationManager: Generation lifecycle
- MarioTrainer: Orchestrates all components

Author: Guinetik
"""

from js import console, window, setTimeout
from pyodide.ffi import create_proxy
import numpy as np
from lib.pyscript_manager import PyScriptManager
from lib.nes.game_controller import GameController
from lib.neural.neural_agent import MarioAgent
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder
from lib.reflexes import ReflexSystem
from lib.evolution import (
    OnePlusOneES,
    MarioFitnessCalculator,
    GenerationManager,
    GenerationLogger
)

# Bokeh for metrics visualization
try:
    from bokeh_utils import BokehFactory
    from bokeh.models import ColumnDataSource
    HAS_BOKEH = True
except ImportError:
    HAS_BOKEH = False
    BokehFactory = None
    ColumnDataSource = None

# Performance monitoring (optional)
try:
    import builtins
    PerformanceMonitor = builtins.PerformanceMonitor
    HAS_PERF_MONITOR = True
except (ImportError, AttributeError):
    HAS_PERF_MONITOR = False
    PerformanceMonitor = None

# Visualization constants
VIZ_UPDATE_FREQUENCY = 6
VIZ_WARMUP_FRAMES = 60


# =============================================================================
# CONFIGURATION (Declarative!)
# =============================================================================

CONFIG = {
    # Vision
    'vision_width': 16,
    'vision_height': 7,

    # Network
    'hidden_size': 32,  # Increased from 9 to give network more capacity for complex patterns
    'use_context_features': True,
    'encode_row': True,
    'simple_controls': True,  # 4-button mode [LEFT, RIGHT, A, B]
    'enable_reflexes': True,  # Reflexive enemy/pit avoidance (gives evolution a head start)

    # Evolution Strategy
    'mutation_rate': 0.01,  # Very small - only mutate 1% of weights per generation
    'mutation_scale': 0.05,  # Tiny changes - offspring very similar to parent
    'adaptive_mutation': True,
    'local_optimum_threshold': 5,

    # Fitness Function
    'distance_exponent': 1.8,
    'frame_penalty_exponent': 1.4,
    'enable_milestones': True,
    'score_multiplier': 10.0,

    # Generation Management
    'base_timeout_frames': 1800,
    'progressive_timeout': True,
    'base_stuck_threshold': 360,  # Increased from 150 (6 seconds vs 2.5s) - more exploration time
    'progressive_stuck_threshold': True
}


# =============================================================================
# TRAINER CLASS (Orchestrates Components)
# =============================================================================

class MarioTrainer:
    """
    Orchestrates Mario training using composed components.
    Thin wrapper that wires everything together via dependency injection.
    """

    def __init__(
        self,
        agent: MarioAgent,
        evolution_strategy,
        fitness_calculator,
        generation_manager
    ):
        """
        Initialize trainer with injected dependencies.

        Args:
            agent: MarioAgent instance
            evolution_strategy: EvolutionStrategy instance
            fitness_calculator: FitnessCalculator instance
            generation_manager: GenerationManager instance
        """
        self.agent = agent
        self.evolution = evolution_strategy
        self.fitness_calc = fitness_calculator
        self.gen_manager = generation_manager
        self.logger = GenerationLogger()

        # Training state
        self.is_training = False
        self.generation = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.champion_weights = None

        # Visualization
        self._viz_enabled = False
        self._viz_paused = False
        self._viz_warmup_frames = 0
        self._decision_count = 0

        # Performance monitoring
        self.perf_monitor = PerformanceMonitor() if HAS_PERF_MONITOR else None
        self.decision_interval = 16  # ~60 FPS to sync observations with NES frame rate

        # Reflex system (handles all instinctive behaviors)
        self.reflex_system = ReflexSystem(
            enable_reflexes=CONFIG['enable_reflexes'],
            jump_hold_duration=6
        )

        # Create metrics chart (one-time setup)
        self._create_metrics_chart()

    async def start_training(self, network_type='simple-4button'):
        """
        Start training loop.

        Args:
            network_type: Network type identifier (for UI compatibility)
        """
        print(f"🚀 Starting training with {network_type}")

        if not self.agent.game.get_emulator():
            console.error("❌ Emulator not found")
            window.updateRLStatus('error', '❌ Emulator not found')
            return

        # Take control from keyboard
        self.agent.game.disable_keyboard()

        # Start emulator
        if not self.agent.game.start_emulator():
            console.error("❌ Failed to start emulator")
            window.updateRLStatus('error', '❌ Failed to start emulator')
            return

        # Log synchronization info
        console.log(f"🎮 Agent observing at {1000/self.decision_interval:.1f} FPS (synced with NES 60 FPS)")
        console.log("📺 Emulator runs independently - agent observes in real-time")

        # Load saved state
        window.updateRLStatus('training', '📂 Loading game state...')
        await self.agent.game.load_saved_state()

        # Reset and start
        self.agent.reset()
        self.is_training = True

        # Update UI
        window.updateRLStatus('training', '🎮 Starting Generation 1...')

        # Start first generation
        await self.run_generation()

        print("✅ Training started")

    async def run_generation(self):
        """Run one complete generation."""
        if not self.is_training:
            return

        # Start generation
        self.gen_manager.start_generation(self.generation)
        self.logger.log_generation_start(self.generation, self.best_distance)

        # Load state and reset
        await self.agent.game.load_saved_state()
        self.agent.reset()

        # Reset reflex system
        self.reflex_system.reset()

        # Resume visualization with warmup
        self._viz_paused = False
        self._viz_warmup_frames = 0

        # IMPORTANT: Wait for state to fully load before starting loop
        # Without this delay, Mario continues from death position instead of save state
        def start_loop():
            if self.is_training:
                self.training_loop()

        proxy = create_proxy(start_loop)
        setTimeout(proxy, 500)  # 500ms delay to ensure state loads

    def training_loop(self):
        """
        Main training loop - runs continuously while training.
        Executes one step per call.
        """
        if not self.is_training:
            return

        # Execute one step
        step_info = self.step_with_visualization()

        # Check if generation should end
        should_end, death_cause = self.gen_manager.check_generation_end(step_info)

        if should_end:
            # Generation ended - handle asynchronously
            self.on_generation_end(step_info, death_cause)
            return

        # Log progress periodically
        if step_info['frames'] % 60 == 0:
            self.logger.log_progress(
                step_info['frames'],
                step_info['position'],
                step_info['max_position'],
                self.gen_manager.max_frames
            )

            # Update UI every 3 seconds
            if step_info['frames'] % 180 == 0:
                progress_pct = int((step_info['position'] / self.best_distance * 100)) if self.best_distance > 0 else 0
                window.updateRLStatus('training', f"🏃 Gen {self.generation + 1}: {step_info['position']}px ({progress_pct}% of best)")

        # Schedule next step
        proxy = create_proxy(self.training_loop)
        setTimeout(proxy, self.decision_interval)

    def step_with_visualization(self) -> dict:
        """
        Execute one step with visualization support.

        SYNCHRONIZATION STRATEGY:
        - Emulator runs independently at 60 FPS (smooth animations, audio)
        - Agent observes at 60 FPS (~16ms intervals) to stay synced
        - Each observation captures current game state in real-time
        - No manual frame stepping - game flows naturally

        Returns:
            dict: Step information
        """
        # Increment counters
        self._decision_count += 1
        if self._viz_warmup_frames < VIZ_WARMUP_FRAMES:
            self._viz_warmup_frames += 1

        # Observe current game state (synced to ~60 FPS)
        state = self.agent.observe()

        # Decide with visualization capture
        capture = self._viz_enabled and not self._viz_paused
        output = self.agent.neural.forward(state, capture_activations=capture)

        # Visualize periodically
        if (self._viz_enabled and
            not self._viz_paused and
            self._viz_warmup_frames >= VIZ_WARMUP_FRAMES and
            (self._decision_count % VIZ_UPDATE_FREQUENCY == 0)):
            self._visualize_network()

        # Decode and execute actions
        actions = self.agent.decoder.decode(output)

        # Apply all reflexes (enemy avoidance, obstacle detection, emergency stuck, button holds)
        simple_controls = CONFIG['simple_controls']
        actions = self.reflex_system.apply_reflexes(
            state=state,
            actions=actions,
            stuck_frames=self.agent.stuck_frames,
            simple_controls=simple_controls
        )

        self.agent.act(actions)

        # Track progress
        self.agent.frames += 1
        current_x = self.agent.game.get_mario_x()

        if current_x > self.agent.max_x:
            self.agent.max_x = current_x
            self.agent.stuck_frames = 0
        else:
            self.agent.stuck_frames += 1

        # Track exploration
        position_bucket = int(current_x / 10) * 10
        self.agent.visited_positions.add(position_bucket)

        if current_x < self.agent.last_x:
            self.agent.backward_movement_frames += 1

        # Store last_x before updating
        last_x = self.agent.last_x
        self.agent.last_x = current_x

        # Return step info
        return {
            'frames': self.agent.frames,
            'position': current_x,
            'max_position': self.agent.max_x,
            'stuck_frames': self.agent.stuck_frames,
            'alive': self.agent.game.is_mario_alive(),
            'score': self.agent.game.get_score(),
            'lives': self.agent.game.get_lives(),
            'last_position': last_x
        }

    def _visualize_network(self):
        """Send network visualization to JavaScript."""
        try:
            viz_data = self.agent.neural.get_visualization_data()

            if hasattr(window, 'onNetworkVisualization'):
                from pyodide.ffi import to_js
                from js import Object
                js_data = to_js(viz_data, dict_converter=Object.fromEntries)
                window.onNetworkVisualization(js_data)
        except Exception as e:
            console.error(f"❌ Error visualizing network: {e}")

    def on_generation_end(self, step_info: dict, death_cause: str):
        """
        Handle end of generation using evolution strategy.

        Args:
            step_info: Final step information
            death_cause: How generation ended ('enemy', 'timeout', 'stuck')
        """
        # Pause visualization
        self._viz_paused = True

        # LOG VISION BEFORE DEATH (for debugging)
        try:
            final_state = self.agent.observe()
            vision_size = 16 * 7  # 16×7 vision grid
            vision = final_state[:vision_size]
            context = final_state[vision_size:]

            print(f"\n{'='*60}")
            print(f"💀 DEATH VISION LOG - Gen {self.generation + 1}")
            print(f"{'='*60}")
            print(f"Death cause: {death_cause}")
            print(f"Final position: {step_info['max_position']}px")
            print(f"Frames survived: {step_info['frames']}")
            print(f"\nVision grid (16×7):")

            # Print vision as grid
            for row in range(7):
                line = ""
                for col in range(16):
                    idx = row * 16 + col
                    val = vision[idx]
                    if col == 4 and row == 3:  # Mario's position
                        line += "M "
                    elif val == -1.0:
                        line += "E "  # Enemy
                    elif val == 1.0:
                        line += "# "  # Solid
                    else:
                        line += ". "  # Empty
                line_label = ["3 above", "", "", "Mario", "", "", "3 below"][row]
                print(f"  {line} {line_label}")

            print(f"\nContext features: {context}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"⚠️ Could not log vision: {e}")

        # Capture final score
        self.agent.final_score = step_info['score']
        score_gained = self.agent.final_score - self.agent.start_score

        # Build generation info
        gen_info = {
            'generation': self.generation,
            'distance': step_info['max_position'],
            'frames': step_info['frames'],
            'score_gained': score_gained,
            'death_cause': death_cause
        }

        # Calculate fitness
        fitness = self.fitness_calc.calculate(gen_info)

        # Check for improvement
        improved = fitness > self.best_fitness

        if improved:
            # New champion!
            self.best_fitness = fitness
            self.best_distance = gen_info['distance']
            self.champion_weights = self.agent.get_weights()
            self.logger.log_new_champion(self.best_distance, fitness)
        else:
            # Restore champion (ELITISM!)
            if self.champion_weights:
                self.logger.log_restore_champion(self.best_distance)
                self.agent.set_weights(
                    self.champion_weights['weights'],
                    self.champion_weights['biases']
                )

        # Log generation summary
        self.logger.log_generation_end(
            gen_info,
            fitness,
            self.best_distance,
            self.best_fitness
        )

        # Update UI metrics (send both current distance and best distance)
        current_gen_distance = gen_info['distance']
        print(f"📊 [DEBUG] Sending to UI: gen={self.generation + 1}, fitness={fitness:.1f}, best={self.best_distance}, current={current_gen_distance}")

        window.updateRLMetrics(
            self.generation + 1,
            fitness,
            self.best_distance,
            current_gen_distance  # Current generation's distance (can vary)
        )

        # Update UI status
        death_messages = {
            'enemy': '💀 Hit an enemy',
            'stuck': '🚫 Got stuck',
            'timeout': '⏰ Time ran out',
            'checkpoint_respawn': '🔄 Checkpoint respawn detected'
        }
        death_msg = death_messages.get(death_cause, '❌ Generation ended')

        if improved:
            score_msg = f" | +{score_gained} points" if score_gained > 0 else ""
            status_msg = f"🎉 New record! {gen_info['distance']}px{score_msg} | {death_msg}"
        else:
            score_msg = f" | +{score_gained}pts" if score_gained > 0 else ""
            status_msg = f"Gen {self.generation + 1}: {gen_info['distance']}px{score_msg} | {death_msg} | Best: {self.best_distance}px"

        window.updateRLStatus('training', status_msg)

        # Get adaptive mutation params from evolution strategy
        mutation_rate, mutation_scale = self.evolution.get_mutation_params(gen_info)

        # Mutate for next generation (creates offspring)
        print(f"🧬 Creating offspring via mutation (rate={mutation_rate}, scale={mutation_scale})")
        self.agent.mutate(mutation_rate, mutation_scale)

        # Increment generation
        self.generation += 1

        # Wait then start next generation
        async def restart_generation():
            if self.is_training:
                await self.run_generation()

        proxy = create_proxy(restart_generation)
        setTimeout(proxy, 2000)  # 2 second delay

    def stop_training(self):
        """Stop training."""
        print("⏹️ Stopping training...")
        self.is_training = False
        self.agent.game.stop_emulator()
        window.updateRLStatus('ready', 'Training stopped')
        print("✅ Training stopped")

    def pause_training(self):
        """Pause/resume training."""
        if self.is_training:
            print("⏸️ Pausing training...")
            self.is_training = False
            window.updateRLStatus('paused', 'Training paused')
        else:
            print("▶️ Resuming training...")
            self.is_training = True
            self.training_loop()
            window.updateRLStatus('training', 'Training resumed')

    def reset_training(self):
        """Reset and start fresh."""
        print("🔄 Resetting trainer...")

        # Stop training
        self.is_training = False

        # Stop emulator (don't reset it - that causes issues)
        self.agent.game.stop_emulator()

        # Reset training state
        self.generation = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.champion_weights = None

        # Reset agent stats
        self.agent.reset()

        # Reinitialize neural network with priors
        self.agent.neural.randomize()
        if hasattr(self.agent.neural, 'apply_priors'):
            priors = [0.2, 3.0, 3.0, 1.5]  # [LEFT, RIGHT, A, B]
            self.agent.neural.apply_priors(priors)

        window.updateRLStatus('ready', 'Agent reset. Ready to train!')
        print("✅ Reset complete")

    def toggle_visualization(self, enabled: bool = None):
        """Toggle network visualization."""
        if enabled is None:
            self._viz_enabled = not self._viz_enabled
        else:
            self._viz_enabled = enabled

        status = "ENABLED" if self._viz_enabled else "DISABLED"
        print(f"🎨 Network visualization {status}")
        return self._viz_enabled

    def _create_metrics_chart(self):
        """
        Create initial Bokeh metrics chart (called once during initialization).
        Chart will be updated from JavaScript using Bokeh's client-side API.
        """
        if not HAS_BOKEH:
            print("⚠️ Bokeh not available, metrics chart disabled")
            return

        try:
            factory = BokehFactory()

            # Create empty data source with structure
            source = ColumnDataSource(data={
                'generation': [],
                'fitness': [],
                'distance': []  # Per-generation distance (can vary)
            })

            # Create figure with three lines
            fig = factory.create_figure(
                title="Training Metrics",
                x_axis_label="Generation",
                y_axis_label="Fitness (normalized) / Distance (px)",
                height=300,
                sizing_mode='stretch_width',
                tooltips=[
                    ("Generation", "@generation"),
                    ("Fitness (÷500)", "@fitness{0.1f}"),
                    ("Distance", "@distance{0.1f} px")
                ]
            )

            # Add two line glyphs (sharing generation x-axis)
            # Note: Fitness is normalized (/500) in JavaScript for intuitive scale
            fig.line('generation', 'fitness', source=source,
                     line_color='green', line_width=2, legend_label='Fitness (normalized)')
            fig.line('generation', 'distance', source=source,
                     line_color='purple', line_width=2, legend_label='Distance')

            fig.legend.location = 'top_left'
            fig.legend.click_policy = 'hide'

            # Embed into container (will be controlled by Svelte visibility)
            factory.embed(fig, 'metrics-chart-container')

            print("✅ Metrics chart created (will be updated from JavaScript)")

        except Exception as e:
            console.error(f"❌ Failed to create metrics chart: {e}")
            print(f"❌ Failed to create metrics chart: {e}")


# =============================================================================
# COMPONENT INITIALIZATION (Dependency Injection)
# =============================================================================

print("🐍 Initializing Mario Training System...")

# Game controller
game = GameController(
    vision_width=CONFIG['vision_width'],
    vision_height=CONFIG['vision_height']
)

# Calculate input size
vision_size = CONFIG['vision_width'] * CONFIG['vision_height']
context_size = 9 if CONFIG['use_context_features'] else 0
row_size = 15 if CONFIG['encode_row'] else 0
input_size = vision_size + context_size + row_size

# Neural network
output_size = 4 if CONFIG['simple_controls'] else 6
neural = SimpleNeuralController(
    input_size=input_size,
    hidden_size=CONFIG['hidden_size'],
    output_size=output_size,
    enable_reflexes=False  # Reflexes now handled by ReflexSystem
)

# Apply behavioral priors
# BALANCED BIAS: Forward progress with controlled jumping
# RIGHT=0.6 → 65% baseline (clear forward preference, still overrideable for backtracking)
# A=1.3 → 79% baseline (jump at obstacles but not constantly)
# B=1.2 → 77% baseline (run for speed and longer jumps)
# Network can learn when NOT to jump (near edges) and when to back up (tall obstacles)
if CONFIG['simple_controls']:
    priors = [0.0, 0.6, 1.3, 1.2]  # [LEFT, RIGHT, A, B]
else:
    priors = [0.0, 0.0, 0.0, 0.6, 1.3, 1.2]  # [UP, DOWN, LEFT, RIGHT, A, B]

neural.apply_priors(priors)

# Action decoder
decoder = ActionDecoder(
    use_variable_threshold=False,
    max_buttons=3,
    simple_controls=CONFIG['simple_controls']
)

# Mario agent
agent = MarioAgent(
    game_controller=game,
    neural_controller=neural,
    action_decoder=decoder,
    use_context_features=CONFIG['use_context_features'],
    encode_row=CONFIG['encode_row']
)

# Evolution strategy
evolution = OnePlusOneES(
    mutation_rate=CONFIG['mutation_rate'],
    mutation_scale=CONFIG['mutation_scale'],
    adaptive_mutation=CONFIG['adaptive_mutation'],
    local_optimum_threshold=CONFIG['local_optimum_threshold']
)

# Fitness calculator
fitness_calc = MarioFitnessCalculator(
    distance_exponent=CONFIG['distance_exponent'],
    frame_penalty_exponent=CONFIG['frame_penalty_exponent'],
    enable_milestones=CONFIG['enable_milestones'],
    score_multiplier=CONFIG['score_multiplier']
)

# Generation manager
gen_manager = GenerationManager(
    base_timeout_frames=CONFIG['base_timeout_frames'],
    progressive_timeout=CONFIG['progressive_timeout'],
    base_stuck_threshold=CONFIG['base_stuck_threshold'],
    progressive_stuck_threshold=CONFIG['progressive_stuck_threshold']
)

# Trainer (orchestrates everything)
trainer = MarioTrainer(
    agent=agent,
    evolution_strategy=evolution,
    fitness_calculator=fitness_calc,
    generation_manager=gen_manager
)

print("✅ Mario Training System ready")
print(f"   Configuration:")
print(f"   - Vision: {CONFIG['vision_width']}×{CONFIG['vision_height']}")
print(f"   - Network: {input_size} → {CONFIG['hidden_size']} → {output_size}")
print(f"   - Controls: {'4-button (simplified)' if CONFIG['simple_controls'] else '6-button (full)'}")
print(f"   - Mutation: {CONFIG['mutation_rate']} rate, {CONFIG['mutation_scale']} scale")
print(f"   - Adaptive mutation: {CONFIG['adaptive_mutation']}")


# =============================================================================
# EXPORTS (JavaScript API)
# =============================================================================

manager = PyScriptManager("agent")
manager.signal_ready(extra_exports={
    'startRLTraining': trainer.start_training,
    'pauseRLTraining': trainer.pause_training,
    'resetRLTraining': trainer.reset_training,
    'stopRLTraining': trainer.stop_training,
    'toggleNetworkVisualization': trainer.toggle_visualization
})

print("✅ Functions exported to JavaScript")
