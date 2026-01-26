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
from lib.nes.frame_sync import FrameSyncManager
from lib.neural.neural_agent import MarioAgent
from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder
from lib.reflexes import ReflexSystem
from lib.evolution import (
    OnePlusOneES,
    MarioFitnessCalculator,
    GenerationManager,
    GenerationLogger,
    PopulationManager,
    Individual,
    breed_networks
)
from lib.evolution.background_trainer import BackgroundTrainer

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


class Logger:
    """
    Python wrapper for JavaScript marioLogger.
    Logs to browser dev console with proper tags/prefixes.
    Falls back to print() if marioLogger not available.
    """

    @staticmethod
    def _get_logger():
        """Get JS logger, returns None if not available."""
        try:
            return window.marioLogger
        except:
            return None

    @staticmethod
    def log(*args):
        """General log message."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.log(msg)
        else:
            print(msg)

    @staticmethod
    def debug(*args):
        """Debug level message."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.debug(msg)
        else:
            print(f"[DEBUG] {msg}")

    @staticmethod
    def info(*args):
        """Info level message."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.info(msg)
        else:
            print(f"[INFO] {msg}")

    @staticmethod
    def warn(*args):
        """Warning message."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.warn(msg)
        else:
            print(f"[WARN] {msg}")

    @staticmethod
    def error(*args):
        """Error message."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.error(msg)
        else:
            print(f"[ERROR] {msg}")

    @staticmethod
    def gen(gen_num, *args):
        """Generation-specific log."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.gen(gen_num, msg)
        else:
            print(f"[Gen {gen_num}] {msg}")

    @staticmethod
    def fitness(*args):
        """Fitness-related log."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.fitness(msg)
        else:
            print(f"[Fitness] {msg}")

    @staticmethod
    def evolution(*args):
        """Evolution-related log."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.evolution(msg)
        else:
            print(f"[Evolution] {msg}")

    @staticmethod
    def champion(*args):
        """Champion-related log."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.champion(msg)
        else:
            print(f"[Champion] {msg}")

    @staticmethod
    def vision(*args):
        """Vision grid log (debug level)."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.vision(msg)
        else:
            print(f"[Vision] {msg}")

    @staticmethod
    def network(*args):
        """Network-related log (debug level)."""
        msg = " ".join(str(a) for a in args)
        logger = Logger._get_logger()
        if logger:
            logger.network(msg)
        else:
            print(f"[Network] {msg}")

    @staticmethod
    def group(label):
        """Start a console group."""
        logger = Logger._get_logger()
        if logger:
            logger.group(label)
        else:
            print(f"\n{'='*60}\n{label}\n{'='*60}")

    @staticmethod
    def group_end():
        """End a console group."""
        logger = Logger._get_logger()
        if logger:
            logger.groupEnd()
        else:
            print("="*60 + "\n")


# Visualization constants
VIZ_UPDATE_FREQUENCY = 6
VIZ_WARMUP_FRAMES = 60


# =============================================================================
# CONFIGURATION (Matching SuperMarioBros-AI reference implementation)
# =============================================================================

CONFIG = {
    # Vision - MATCHING REFERENCE: 7 tiles wide × 10 tiles tall
    'vision_width': 7,
    'vision_height': 10,

    # Network - MATCHING REFERENCE: 9 hidden neurons
    # Reference: input_dims = (4, 7, 10) → 80 inputs → 9 hidden → 6 outputs
    'hidden_size': 9,  # Matching reference exactly
    'use_context_features': False,  # Reference doesn't use context features
    'encode_row': True,  # Reference uses row encoding (+10 inputs)
    'simple_controls': False,  # 6 buttons [UP, DOWN, LEFT, RIGHT, A, B] - matching reference
    'enable_reflexes': False,  # Disabled - matching reference (no hard-coded behaviors)

    # Evolution Strategy - MATCHING REFERENCE
    # Reference: mutation_rate = 0.05, gaussian_mutation_scale = 0.2
    # Increased to 0.15 to help escape local optima (stuck at pipe)
    'mutation_rate': 0.15,  # Higher than reference for faster exploration
    'mutation_scale': 0.2,  # Matching reference
    'adaptive_mutation': False,  # Reference uses static mutation
    'local_optimum_threshold': 5,

    # Fitness Function - MATCHING REFERENCE FORMULA
    # Reference: max(distance^1.8 - frames^1.5 + milestone + win_bonus, 0.00001)
    # Frame penalty is CRITICAL - forces efficient movement, not standing still!
    'distance_exponent': 1.8,  # Matching reference
    'frame_penalty_exponent': 1.5,  # Matching reference - significant frame penalty!
    'enable_milestones': True,
    'score_multiplier': 0.0,  # Reference doesn't multiply game score
    'win_bonus': 1_000_000,  # Huge bonus for beating the level

    # Generation Management
    # Reference: stuck threshold = 60*3 = 180 frames (3 seconds at 60fps)
    'base_timeout_frames': 1800,
    'progressive_timeout': True,
    'base_stuck_threshold': 180,  # 3s without progress (matching reference)
    'progressive_stuck_threshold': False,  # Reference uses fixed threshold

    # Background Training (headless population)
    # Uses isolated HeadlessNES instance - completely separate from foreground
    'enable_background_training': True,
    'background_population_size': 50,  # Large population for proper evolution
    'background_eval_interval': 2  # Transfer best weights every 2 foreground generations
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

        # Stuck detection for full restart
        self.generations_since_improvement = 0
        self.restart_threshold = 15  # Full restart after 15 gens without improvement

        # Visualization
        self._viz_enabled = False
        self._viz_paused = False
        self._viz_warmup_frames = 0
        self._decision_count = 0

        # Performance monitoring
        self.perf_monitor = PerformanceMonitor() if HAS_PERF_MONITOR else None

        # Frame synchronization (emulator and agent both run at same FPS)
        self.frame_sync = FrameSyncManager()

        # Reflex system (handles all instinctive behaviors)
        # jump_hold_duration=12 ensures full-height jumps to clear tall pipes (at 30 FPS)
        self.reflex_system = ReflexSystem(
            enable_reflexes=CONFIG['enable_reflexes'],
            jump_hold_duration=12
        )

        # Population management for breeding
        self.population_manager = PopulationManager(
            elite_size=5,  # Keep top 5 individuals
            breeding_interval=2  # Breed every 2 generations (was 4, faster genetic diversity)
        )
        self.is_breeding_generation = False

        # Background trainer (headless population training)
        self.background_trainer = None
        self.pending_champion = None  # Champion waiting to be loaded into foreground
        self.background_eval_counter = 0

        if CONFIG['enable_background_training']:
            self.background_trainer = BackgroundTrainer(
                population_size=CONFIG['background_population_size'],
                mutation_rate=CONFIG['mutation_rate'],
                mutation_scale=CONFIG['mutation_scale']
            )
            # Set callback for when background finds new champion
            self.background_trainer.on_champion_found = self._on_background_champion

        # Create metrics chart (one-time setup)
        self._create_metrics_chart()

    async def start_training(self, network_type='simple-4button'):
        """
        Start training loop.

        Args:
            network_type: Network type identifier (for UI compatibility)
        """
        Logger.log(f"🚀 Starting training with {network_type}")

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

        # Load saved state
        window.updateRLStatus('training', '📂 Loading game state...')
        await self.agent.game.load_saved_state()

        # Reset and start
        self.agent.reset()
        self.is_training = True

        # Update UI
        window.updateRLStatus('training', '🎮 Starting Generation 1...')

        # Start generation
        await self.run_generation()

        Logger.log("✅ Training started")

    async def run_generation(self):
        """Run one complete generation."""
        if not self.is_training:
            return

        # Start generation
        self.gen_manager.start_generation(self.generation)
        self.logger.log_generation_start(self.generation, self.best_distance)

        # Check if next generation will be breeding
        next_gen_is_breeding = self.population_manager.should_breed(self.generation + 1)
        if next_gen_is_breeding and len(self.population_manager.elites) >= 2:
            breed_info = f" | 🧬 Next: Breeding (Elite pool: {len(self.population_manager.elites)})"
        else:
            breed_info = ""

        # Update UI with generation status
        gen_status = f"Gen {self.generation + 1} starting... | Best: {self.best_distance}px{breed_info}"
        window.updateRLStatus('training', gen_status)

        # Load state and reset
        await self.agent.game.load_saved_state()
        self.agent.reset()

        # Reset reflex system
        self.reflex_system.reset()

        # Reset diagnostic flag for fresh logging each generation
        if hasattr(self, '_pipe_diagnostic_logged'):
            del self._pipe_diagnostic_logged

        # Resume visualization with warmup
        self._viz_paused = False
        self._viz_warmup_frames = 0

        # IMPORTANT: Wait for state to fully load before starting loop
        # Without this delay, Mario continues from death position instead of save state
        def start_loop():
            if self.is_training:
                # Start frame-synchronized training loop at 30 FPS
                self.frame_sync.start(self.training_loop)

        proxy = create_proxy(start_loop)
        setTimeout(proxy, 500)  # 500ms delay to ensure state loads

    def training_loop(self):
        """
        Main training loop - called by FrameSyncManager at 30 FPS.

        Both emulator and agent run at 30 FPS (33.33ms intervals),
        ensuring perfect 1:1 frame synchronization.
        """
        if not self.is_training:
            self.frame_sync.stop()
            return

        # Execute one step
        step_info = self.step_with_visualization()

        # Check if generation should end
        should_end, death_cause = self.gen_manager.check_generation_end(step_info)

        if should_end:
            # Stop frame sync and handle generation end
            self.frame_sync.stop()
            self.on_generation_end(step_info, death_cause)
            return

        # Log progress periodically (every 60 observations = 2 seconds at 30 FPS)
        if step_info['frames'] % 60 == 0:
            self.logger.log_progress(
                step_info['frames'],
                step_info['position'],
                step_info['max_position'],
                self.gen_manager.max_frames
            )

            # Update UI every 180 observations (6 seconds at 30 FPS)
            if step_info['frames'] % 180 == 0:
                progress_pct = int((step_info['position'] / self.best_distance * 100)) if self.best_distance > 0 else 0
                window.updateRLStatus('training', f"🏃 Gen {self.generation + 1}: {step_info['position']}px ({progress_pct}% of best)")

        # Frame sync will automatically call this again in 33.33ms

    def step_with_visualization(self) -> dict:
        """
        Execute one step with visualization support.

        SYNCHRONIZATION STRATEGY:
        - Emulator runs at 30 FPS (FrameTimer configured for 30 FPS)
        - Agent observes at 30 FPS (FrameSyncManager called every frame)
        - Perfect 1:1 frame correspondence: no missed frames, no duplicates
        - Each observation captures current game state in real-time
        - Both run at SAME rate for perfect synchronization

        Returns:
            dict: Step information
        """
        # Increment counters
        self._decision_count += 1
        if self._viz_warmup_frames < VIZ_WARMUP_FRAMES:
            self._viz_warmup_frames += 1

        # Observe current game state (synced to ~60 FPS)
        state = self.agent.observe()

        # === DIAGNOSTIC: Log state at first pipe (430-440px) ===
        current_x = self.agent.game.get_mario_x()
        if 430 <= current_x <= 440 and not hasattr(self, '_pipe_diagnostic_logged'):
            self._pipe_diagnostic_logged = True
            raw_pos = self.agent.game.get_mario_position()
            tile_pos = self.agent.game.get_mario_tile_position()
            console.log("=" * 60)
            console.log("🔬 FOREGROUND DIAGNOSTIC AT PIPE")
            console.log(f"   Raw position: x={raw_pos[0]}, y={raw_pos[1]}")
            console.log(f"   Tile position: col={tile_pos[0]}, row={tile_pos[1]}")
            console.log(f"   State shape: {state.shape}")
            console.log(f"   Vision (first 20): {state[:20].tolist()}")
            console.log(f"   Row encoding (last 10): {state[-10:].tolist()}")
            console.log(f"   State sum: {state.sum():.4f}")
            console.log("=" * 60)

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
            progress = current_x - self.agent.max_x
            self.agent.max_x = current_x
            self.agent.stuck_frames = 0
            
            # Grace period after ANY progress (especially after clearing obstacles)
            # Lower threshold (10px) and longer grace period (180 frames = 6 seconds)
            # This prevents false "stuck" detection right after clearing obstacles
            if progress >= 10:
                if not hasattr(self.agent, '_progress_grace_frames'):
                    self.agent._progress_grace_frames = 0
                self.agent._progress_grace_frames = 180  # 6 seconds grace period
            elif progress > 0:
                # Even small progress gets a shorter grace period
                if not hasattr(self.agent, '_progress_grace_frames'):
                    self.agent._progress_grace_frames = 0
                self.agent._progress_grace_frames = max(self.agent._progress_grace_frames, 90)  # 3 seconds minimum
        else:
            # Check if we're in grace period after progress
            if hasattr(self.agent, '_progress_grace_frames') and self.agent._progress_grace_frames > 0:
                self.agent._progress_grace_frames -= 1
                # Don't count as stuck during grace period
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
            vision_width = CONFIG['vision_width']  # 7
            vision_height = CONFIG['vision_height']  # 10
            vision_size = vision_width * vision_height  # 70
            vision = final_state[:vision_size]
            row_encoding = final_state[vision_size:]  # Row encoding (10)

            Logger.group(f"💀 DEATH VISION LOG - Gen {self.generation + 1}")
            Logger.vision(f"Death cause: {death_cause}")
            Logger.vision(f"Final position: {step_info['max_position']}px")
            Logger.vision(f"Frames survived: {step_info['frames']}")
            Logger.vision(f"Vision grid ({vision_width}×{vision_height}):")

            # Mario position in grid: 1 tile behind (col 1), 3 rows from top
            mario_col_in_grid = vision_width // 4  # 1 for width=7
            mario_row_in_grid = vision_height // 3  # 3 for height=10

            # Print vision as grid
            for row in range(vision_height):
                line = ""
                for col in range(vision_width):
                    idx = row * vision_width + col
                    val = vision[idx]
                    if col == mario_col_in_grid and row == mario_row_in_grid:
                        line += "M "
                    elif val == -1.0:
                        line += "E "  # Enemy
                    elif val == 1.0:
                        line += "# "  # Solid
                    else:
                        line += ". "  # Empty
                # Row labels
                if row == 0:
                    label = f"{mario_row_in_grid} above"
                elif row == mario_row_in_grid:
                    label = "Mario"
                elif row == vision_height - 1:
                    label = f"{vision_height - mario_row_in_grid - 1} below"
                else:
                    label = ""
                Logger.vision(f"  {line} {label}")

            Logger.vision(f"Row encoding: {row_encoding}")
            
            # Log network outputs and button presses when stuck
            if death_cause == 'stuck':
                try:
                    # Get final network output
                    network_output = self.agent.neural.forward(final_state, capture_activations=False)
                    decoded_actions = self.agent.decoder.decode(network_output)
                    
                    Logger.vision(f"\n🔍 Network Analysis (when stuck):")
                    Logger.vision(f"   Raw outputs: {network_output}")
                    Logger.vision(f"   Decoded buttons: {decoded_actions}")
                    button_names = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A(JUMP)', 'B(RUN)']
                    pressed = [name for name, pressed in zip(button_names, decoded_actions) if pressed]
                    Logger.vision(f"   Pressed: {pressed if pressed else 'NONE'}")
                except Exception as e:
                    Logger.warn(f"Could not log network outputs: {e}")
            
            Logger.group_end()
        except Exception as e:
            Logger.warn(f"Could not log vision: {e}")

        # Capture final score
        self.agent.final_score = step_info['score']
        score_gained = self.agent.final_score - self.agent.start_score

        # Build generation info
        gen_info = {
            'generation': self.generation,
            'distance': step_info['max_position'],
            'frames': step_info['frames'],
            'score_gained': score_gained,
            'death_cause': death_cause,
            'best_distance': self.best_distance  # For preservation mode in evolution strategy
        }

        # Calculate fitness
        fitness = self.fitness_calc.calculate(gen_info)

        # Track individual in population (for breeding)
        current_weights = self.agent.get_weights()
        individual = Individual(
            weights=current_weights,
            fitness=fitness,
            distance=gen_info['distance'],
            generation=self.generation
        )

        # Update elite pool
        was_added_to_elites = self.population_manager.update_elites(individual)

        # Check for improvement
        improved = fitness > self.best_fitness
        did_restart = False  # Track if we did a full restart

        if improved:
            # New champion!
            self.best_fitness = fitness
            self.best_distance = gen_info['distance']
            self.champion_weights = self.agent.get_weights()
            self.logger.log_new_champion(self.best_distance, fitness)
            self.generations_since_improvement = 0  # Reset counter
        else:
            self.generations_since_improvement += 1

            # Check for full restart (stuck for too long)
            needs_restart = self.generations_since_improvement >= self.restart_threshold

            if needs_restart:
                Logger.group("🔥 FULL RESTART")
                Logger.warn(f"No improvement for {self.restart_threshold} generations!")
                Logger.warn(f"Best was {self.best_distance}px - starting fresh with new random network")
                Logger.group_end()

                # Reset network with new random weights (no priors - matching reference)
                self.agent.neural.randomize()

                # Keep best_distance for reference but reset champion
                # This gives evolution a fresh start
                self.champion_weights = None
                self.best_fitness = 0
                self.generations_since_improvement = 0

                # Clear elite pool for fresh start
                self.population_manager.elites = []
                did_restart = True

                window.updateRLStatus('training', f'🔥 RESTART! Stuck at {self.best_distance}px - trying fresh network')
            elif self.champion_weights:
                # Restore champion (ELITISM!) - only if not restarting
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

        # === LEARNING PROGRESS LOG (every 5 generations) ===
        if (self.generation + 1) % 5 == 0 or improved:
            console.log(f"")
            console.log(f"📈 === FOREGROUND LEARNING PROGRESS ===")
            console.log(f"   Generation: {self.generation + 1}")
            console.log(f"   This run: {gen_info['distance']}px in {gen_info['frames']} frames")
            console.log(f"   Best ever: {self.best_distance}px (fitness: {self.best_fitness:.0f})")
            console.log(f"   Stagnation: {self.generations_since_improvement} gens without improvement")
            if improved:
                console.log(f"   🎯 NEW RECORD! +{gen_info['distance'] - (self.best_distance - gen_info['distance'] if improved else 0)}px improvement")
            console.log(f"")

        # Update UI metrics (send both current distance and best distance)
        current_gen_distance = gen_info['distance']
        Logger.debug(f"Sending to UI: gen={self.generation + 1}, fitness={fitness:.1f}, best={self.best_distance}, current={current_gen_distance}")

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

        # Increment generation FIRST (for breeding check)
        self.generation += 1

        # Skip breeding/mutation if we just did a full restart (network is already fresh)
        if did_restart:
            Logger.evolution("Skipping mutation - fresh network already initialized")

        # Check if this is a breeding generation
        elif self.population_manager.should_breed(self.generation):
            # BREEDING GENERATION!
            Logger.group(f"🧬 BREEDING GENERATION {self.generation}")

            # Select parents from elite pool
            try:
                parent1, parent2 = self.population_manager.select_parents(method='tournament')

                # Log breeding event
                Logger.evolution(f"Parent 1: Gen {parent1.generation}, Fitness {parent1.fitness:.1f}, {parent1.distance}px")
                Logger.evolution(f"Parent 2: Gen {parent2.generation}, Fitness {parent2.fitness:.1f}, {parent2.distance}px")

                # Perform crossover + mutation
                mutation_rate, mutation_scale = self.evolution.get_mutation_params(gen_info)
                offspring_weights = breed_networks(
                    parent1.weights,
                    parent2.weights,
                    mutation_rate=mutation_rate * 0.5,  # Reduce mutation during breeding
                    mutation_scale=mutation_scale * 0.7,  # Less aggressive mutations
                    crossover_method='sbx',
                    eta=100.0  # High eta for offspring close to parents
                )

                # Set offspring as current network
                self.agent.set_weights(
                    offspring_weights['weights'],
                    offspring_weights['biases']
                )

                # Log breeding to history
                self.population_manager.log_breeding_event(
                    parent1, parent2, offspring_weights, self.generation
                )

                # Update UI
                breed_msg = f"🧬 Gen {self.generation}: Breeding offspring from Gen {parent1.generation} × Gen {parent2.generation}"
                window.updateRLStatus('training', breed_msg)
                Logger.evolution("✅ Offspring created via SBX crossover")
                Logger.group_end()

            except ValueError as e:
                Logger.warn(f"Breeding failed: {e}, falling back to mutation")
                # Fall back to normal mutation
                mutation_rate, mutation_scale = self.evolution.get_mutation_params(gen_info)
                Logger.evolution(f"Creating offspring via mutation (rate={mutation_rate}, scale={mutation_scale})")
                self.agent.mutate(mutation_rate, mutation_scale)

        else:
            # NORMAL MUTATION GENERATION
            # Get adaptive mutation params from evolution strategy
            mutation_rate, mutation_scale = self.evolution.get_mutation_params(gen_info)

            # Mutate for next generation (creates offspring)
            Logger.evolution(f"Creating offspring via mutation (rate={mutation_rate}, scale={mutation_scale})")
            self.agent.mutate(mutation_rate, mutation_scale)

        # Age all elites
        self.population_manager.age_elites()

        # Inject current champion into background population (if improved)
        if improved and self.background_trainer:
            weight_data = self.agent.get_weights()
            self.background_trainer.inject_champion(
                weight_data['weights'], weight_data['biases'],
                fitness, gen_info['distance']
            )

        # State machine: handle generation transition
        # Instead of running background in parallel, we run it BETWEEN generations
        # Flow: END_GEN → BACKGROUND_TRAIN (optional) → START_NEW_GEN
        async def handle_generation_transition():
            if not self.is_training:
                return

            # === PHASE 1: Background Training (if enabled and due) ===
            self.background_eval_counter += 1
            should_run_background = (
                self.background_trainer and
                self.background_eval_counter >= CONFIG['background_eval_interval']
            )
            
            if should_run_background:
                self.background_eval_counter = 0
                
                # Show training UI - emulator is already paused from frame_sync.stop()
                window.updateRLStatus('background_training', f'🧬 Training {CONFIG["background_population_size"]} networks in background...')
                console.log("🧬 === BACKGROUND TRAINING PHASE ===")
                
                try:
                    # Run all background evaluations (foreground is paused)
                    await self._run_background_evaluations()
                    
                    # Check if background found better weights
                    if self.pending_champion:
                        await self._apply_pending_champion()
                        
                except Exception as e:
                    console.error(f"❌ Background training error: {e}")
                
                console.log("🧬 === BACKGROUND TRAINING COMPLETE ===")
            
            # === PHASE 2: Start New Generation ===
            # Small delay to let UI update, then start next generation
            window.updateRLStatus('training', f'🎮 Starting generation {self.generation + 1}...')
            await self.run_generation()

        proxy = create_proxy(handle_generation_transition)
        setTimeout(proxy, 1500)  # 1.5 second delay (reduced from 2s)

    def stop_training(self):
        """Stop training."""
        Logger.log("⏹️ Stopping training...")
        self.is_training = False
        self.frame_sync.stop()
        self.agent.game.stop_emulator()
        window.updateRLStatus('ready', 'Training stopped')
        Logger.log("✅ Training stopped")

    def pause_training(self):
        """Pause/resume training."""
        if self.is_training:
            Logger.log("⏸️ Pausing training...")
            self.is_training = False
            self.frame_sync.stop()
            window.updateRLStatus('paused', 'Training paused')
        else:
            Logger.log("▶️ Resuming training...")
            self.is_training = True
            self.frame_sync.start(self.training_loop)
            window.updateRLStatus('training', 'Training resumed')

    def reset_training(self):
        """Reset and start fresh."""
        Logger.log("🔄 Resetting trainer...")

        # Stop training
        self.is_training = False
        self.frame_sync.stop()

        # Stop emulator (don't reset it - that causes issues)
        self.agent.game.stop_emulator()

        # Reset training state
        self.generation = 0
        self.best_distance = 0
        self.best_fitness = 0
        self.champion_weights = None

        # Reset population manager
        self.population_manager.elites = []
        self.population_manager.breeding_history = []

        # Reset agent stats
        self.agent.reset()

        # Reinitialize neural network (no priors - matching reference)
        self.agent.neural.randomize()

        window.updateRLStatus('ready', 'Agent reset. Ready to train!')
        Logger.log("✅ Reset complete")

    async def load_reference_weights(self):
        """
        Load pre-trained reference weights from SuperMarioBros-AI project.
        These weights successfully beat World 1-1 after 1213 generations.
        
        This is useful for debugging - if reference weights work, our
        emulator/button mapping is correct. If they don't, something's broken.
        """
        from js import fetch
        import json
        
        try:
            console.log("📥 Loading reference weights (gen 1213, beats World 1-1)...")
            
            # Fetch the JSON file
            response = await fetch('/data/reference_weights.json')
            if not response.ok:
                console.error(f"❌ Failed to fetch reference weights: {response.status}")
                return False
            
            text = await response.text()
            data = json.loads(text)
            
            # Convert lists back to numpy arrays
            W1 = np.array(data['W1'], dtype=np.float32)
            W2 = np.array(data['W2'], dtype=np.float32)
            b1 = np.array(data['b1'], dtype=np.float32)
            b2 = np.array(data['b2'], dtype=np.float32)
            
            console.log(f"   W1: {W1.shape}, b1: {b1.shape}")
            console.log(f"   W2: {W2.shape}, b2: {b2.shape}")
            
            # Verify architecture matches
            expected_arch = data.get('architecture', [80, 9, 6])
            our_arch = self.agent.neural.network.layer_sizes
            if list(our_arch) != expected_arch:
                console.error(f"❌ Architecture mismatch! Reference: {expected_arch}, Ours: {list(our_arch)}")
                return False
            
            # Load weights into network
            self.agent.neural.set_weights([W1, W2], [b1, b2])
            
            # Also set as champion - but DON'T set artificial high fitness!
            # Let actual performance determine fitness, otherwise background training
            # will never be able to beat this "fake" fitness value
            self.champion_weights = self.agent.get_weights()
            # Reset fitness tracking so background/foreground can compete fairly
            self.best_distance = 0
            self.best_fitness = 0
            
            console.log("✅ Reference weights loaded!")
            console.log("🎮 Starting fresh - performance will be measured from actual runs")
            
            window.updateRLStatus('ready', '✅ Reference weights loaded! Start training to test.')
            return True
            
        except Exception as e:
            console.error(f"❌ Error loading reference weights: {e}")
            return False

    def toggle_visualization(self, enabled: bool = None):
        """Toggle network visualization."""
        if enabled is None:
            self._viz_enabled = not self._viz_enabled
        else:
            self._viz_enabled = enabled

        status = "ENABLED" if self._viz_enabled else "DISABLED"
        Logger.network(f"Visualization {status}")
        return self._viz_enabled

    def get_population_stats(self):
        """Get current population statistics for display."""
        stats = self.population_manager.get_statistics()

        # Format for display
        if stats['elite_count'] > 0:
            return {
                'elite_count': stats['elite_count'],
                'best_fitness': stats['best_fitness'],
                'avg_fitness': stats['avg_fitness'],
                'diversity': stats['diversity'],
                'next_breeding': self.population_manager.breeding_interval - (self.generation % self.population_manager.breeding_interval)
            }
        return None

    # =========================================================================
    # BACKGROUND TRAINING METHODS
    # =========================================================================

    def _on_background_champion(self, champion: dict, result: dict):
        """
        Callback when background training finds a new champion.
        Stores it as pending - will be applied when foreground generation ends.

        Args:
            champion: Champion network dict with weights/biases
            result: Evaluation result dict with fitness/distance
        """
        # Only accept if better than current foreground champion
        if result['fitness'] > self.best_fitness:
            self.pending_champion = {
                'weights': champion['weights'],
                'biases': champion['biases'],
                'fitness': result['fitness'],
                'distance': result['distance']
            }
            console.log(f"🏆 Background found new champion: {result['distance']}px (pending)")
            Logger.champion(f"Background champion queued: {result['distance']}px (waiting for foreground gen to end)")
        else:
            console.log(f"⏭️ Background champion rejected: {result['distance']}px (fitness {result['fitness']:.0f}) not better than current best (fitness {self.best_fitness:.0f})")

    async def _run_background_evaluations(self):
        """
        Run headless background population evaluations.
        Called between foreground generations.

        Uses ISOLATED HeadlessNES - never touches foreground emulator.
        """
        if not self.background_trainer:
            return

        console.log("🔄 Starting background population evaluation...")
        console.log("   (Using isolated HeadlessNES - foreground unaffected)")

        # Initialize population if first time
        if len(self.background_trainer.population) == 0:
            # BackgroundTrainer creates its own HeadlessGameController
            # IMPORTANT: Create a COPY of the neural network for background training!
            # Sharing the same object would cause background evaluations to modify
            # the foreground agent's weights, causing chaos.
            from lib.neural.neural_controller import SimpleNeuralController, ActionDecoder
            
            # Create isolated copy with same architecture
            bg_neural = SimpleNeuralController(
                input_size=self.agent.neural.input_size,
                hidden_size=self.agent.neural.hidden_size,
                output_size=self.agent.neural.output_size,
                enable_reflexes=False
            )
            
            # Create isolated action decoder
            bg_decoder = ActionDecoder(
                use_variable_threshold=False,
                max_buttons=3,
                simple_controls=CONFIG['simple_controls']
            )
            
            # Create isolated reflex system
            from lib.reflexes import ReflexSystem
            bg_reflex = ReflexSystem(
                enable_reflexes=CONFIG['enable_reflexes'],
                jump_hold_duration=12
            )
            
            self.background_trainer.neural_template = bg_neural
            self.background_trainer.action_decoder = bg_decoder
            self.background_trainer.reflex_system = bg_reflex
            self.background_trainer.fitness_calculator = self.fitness_calc  # This one is OK to share (stateless)
            self.background_trainer.initialize_population(self.agent.neural)
            
            # Initialize headless NES immediately (loads starting state from file)
            await self.background_trainer.initialize_headless()

        # Refresh state from file before evaluating (ensures consistent starting point)
        await self.background_trainer.refresh_state()

        # Evaluate all networks headlessly (isolated NES)
        await self.background_trainer.evaluate_population()

        # Breed for next round
        self.background_trainer.breed_population()

        console.log(f"✅ Background evaluation complete (champion: {self.background_trainer.champion_distance}px)")

    async def _apply_pending_champion(self):
        """
        Apply pending champion from background training.
        Shows announcement and loads new weights.
        """
        if not self.pending_champion:
            return

        champion = self.pending_champion
        self.pending_champion = None

        # RE-CHECK if still better (foreground might have improved since queued)
        if champion['fitness'] <= self.best_fitness:
            console.log(f"⏭️ Skipping pending champion ({champion['distance']}px) - foreground already better ({self.best_distance}px)")
            return

        # Update best tracking
        old_best = self.best_distance
        self.best_distance = champion['distance']
        self.best_fitness = champion['fitness']

        # Store as champion weights
        self.champion_weights = {
            'weights': champion['weights'],
            'biases': champion['biases']
        }

        # Announce new champion! 🎉
        Logger.group("🏆 NEW CHAMPION FROM BACKGROUND TRAINING")
        Logger.champion(f"Distance: {champion['distance']}px (was {old_best}px)")
        Logger.champion(f"Improvement: +{champion['distance'] - old_best}px")
        Logger.group_end()

        # Show announcement on UI
        window.updateRLStatus(
            'champion',
            f"🏆 NEW CHAMPION! {champion['distance']}px (+{champion['distance'] - old_best}px from background training)"
        )

        # Brief pause to show announcement
        from js import Promise
        await Promise.new(lambda resolve, reject: setTimeout(create_proxy(resolve), 2000))

        # Load champion weights into foreground agent
        self.agent.set_weights(champion['weights'], champion['biases'])

        console.log(f"✅ Loaded background champion weights ({champion['distance']}px)")

    def _create_metrics_chart(self):
        """
        Create initial Bokeh metrics chart (called once during initialization).
        Chart will be updated from JavaScript using Bokeh's client-side API.
        """
        if not HAS_BOKEH:
            Logger.warn("Bokeh not available, metrics chart disabled")
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

            Logger.log("✅ Metrics chart created")

        except Exception as e:
            console.error(f"❌ Failed to create metrics chart: {e}")
            Logger.error(f"Failed to create metrics chart: {e}")


# =============================================================================
# COMPONENT INITIALIZATION (Dependency Injection)
# =============================================================================

Logger.log("🐍 Initializing Mario Training System...")

# Game controller
game = GameController(
    vision_width=CONFIG['vision_width'],
    vision_height=CONFIG['vision_height']
)

# Calculate input size (matching reference: 7×10 + 10 row encoding = 80)
vision_size = CONFIG['vision_width'] * CONFIG['vision_height']
context_size = 0  # Reference doesn't use context features
row_size = CONFIG['vision_height'] if CONFIG['encode_row'] else 0  # One input per row
input_size = vision_size + row_size  # 70 + 10 = 80

# Neural network
output_size = 4 if CONFIG['simple_controls'] else 6
neural = SimpleNeuralController(
    input_size=input_size,
    hidden_size=CONFIG['hidden_size'],
    output_size=output_size,
    enable_reflexes=False  # Reflexes now handled by ReflexSystem
)

# NO BEHAVIORAL PRIORS - matching reference implementation
# Reference uses pure random uniform[-1, 1] initialization with sigmoid outputs
# Network learns what buttons to press purely through evolution
# The 0.5 threshold on sigmoid output determines button presses
print("🎮 No behavioral priors applied (matching reference implementation)")

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
    encode_row=CONFIG['encode_row'],
    num_rows=CONFIG['vision_height']  # 10 rows to match reference
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

Logger.log("✅ Mario Training System ready")
Logger.log(f"   Configuration:")
Logger.log(f"   - Vision: {CONFIG['vision_width']}×{CONFIG['vision_height']}")
Logger.log(f"   - Network: {input_size} → {CONFIG['hidden_size']} → {output_size}")
Logger.log(f"   - Controls: {'4-button (simplified)' if CONFIG['simple_controls'] else '6-button (full)'}")
Logger.log(f"   - Mutation: {CONFIG['mutation_rate']} rate, {CONFIG['mutation_scale']} scale")
Logger.log(f"   - Adaptive mutation: {CONFIG['adaptive_mutation']}")


# =============================================================================
# EXPORTS (JavaScript API)
# =============================================================================

manager = PyScriptManager("agent")
manager.signal_ready(extra_exports={
    'startRLTraining': trainer.start_training,
    'pauseRLTraining': trainer.pause_training,
    'resetRLTraining': trainer.reset_training,
    'stopRLTraining': trainer.stop_training,
    'toggleNetworkVisualization': trainer.toggle_visualization,
    'loadReferenceWeights': trainer.load_reference_weights
})

Logger.log("✅ Functions exported to JavaScript")
