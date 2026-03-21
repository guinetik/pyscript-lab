"""
Mario AI Trainer - Event/Callback Based
Python controls the training loop, calls JS callbacks for state changes.
Yields after EACH generation to keep browser responsive.
"""

import asyncio
import numpy as np
from js import window
import json
import time
import copy


def tlog(message, data=None):
    """Log to telemetry system."""
    if hasattr(window, 'telemetryLog'):
        window.telemetryLog('trainer', message, data)


def tlog_frame(frame_num, state):
    """Log frame state to telemetry for comparison."""
    if hasattr(window, 'telemetryLogFrame'):
        window.telemetryLogFrame('headless', frame_num, state)

from .agent import NeuralAgent, Population
from .utils import (
    get_mario_location_in_level, 
    build_inputs, 
    is_dead, 
    did_win,
    calculate_fitness,
    convert_state
)


# Training config
BACKGROUND_GENERATIONS = 3  # Generations per background phase
FOREGROUND_SESSIONS = 3      # How many times to show agent before training
MAX_GENERATIONS = 5000
MAX_FRAMES_PER_EPISODE = 3000
STUCK_THRESHOLD = 120

# Auto-restart config
AUTO_RESTART_GENERATIONS = 25  # Check progress after this many generations
AUTO_RESTART_MIN_DISTANCE = 500  # Must reach this distance or restart


class Trainer:
    """Event-based trainer - Python controls everything."""
    
    def __init__(self):
        self.population = None
        self.headless_pool = None
        self.initial_state = None
        self.rom_data = None
        self.mode = 'simple'  # Evolution mode

        # State
        self.running = False
        self.total_generations = 0
        self.generations_since_foreground = 0
        
        # Track BEST BY DISTANCE (what we actually care about)
        self.best_distance_ever = 0
        self.best_distance_weights = None

        # Track best fitness too for stats
        self.best_fitness_ever = 0

        # Track wins
        self.total_wins = 0
        self.best_win_frames = float('inf')  # Fewest frames to win
        self.best_win_weights = None

        self.level_complete = False
        
        # Callbacks (set from JS)
        self.on_progress = None  # (gen, fitness, distance)
        self.on_foreground = None  # (weights_json) - show in emulator
        self.on_breeding = None  # (breeding_json) - lineage events for frontend viz
        self.on_complete = None  # training finished
        self.on_state = None  # state change
        
    def initialize(self, rom_data, initial_state, mode='simple'):
        """Initialize with ROM and state.

        Args:
            rom_data: NES ROM binary
            initial_state: NES state to start from
            mode: Evolution mode ('simple', 'sbx', 'uniform', 'optimize')
        """
        self.rom_data = rom_data
        self.initial_state = initial_state
        self.mode = mode  # Store mode for later checks

        # Create population with specified mode
        # Reference uses 100 agents (10 parents + 90 offspring)
        self.population = Population(100, mode=mode)
        self.population.initialize()
        self.mode = self.population.mode
        
        # Create headless pool - pass window references directly to avoid proxy issues
        if hasattr(window, 'createHeadlessNESPool'):
            self.headless_pool = window.createHeadlessNESPool(4)
            # Use window._trainingRomData and window._trainingInitialState directly
            # This ensures JS gets native JS objects, not PyScript proxies
            self.headless_pool.initialize(
                window._trainingRomData,
                window._trainingInitialState
            )
            
            # Verify pool is working
            test_nes = self.headless_pool.getInstance(0)
            test_x = test_nes.getMarioX()
            tlog('HeadlessNES pool ready', {'initialX': test_x})
        else:
            tlog('HeadlessNES not available!')
            return False
            
        # Reset state
        self.running = False
        self.total_generations = 0
        self.generations_since_foreground = 0
        self.best_distance_ever = 0
        self.best_distance_weights = None
        self.best_fitness_ever = 0
        self.total_wins = 0
        self.best_win_frames = float('inf')
        self.best_win_weights = None
        self.level_complete = False
        
        tlog('Initialized')
        return True
        
    async def start(self):
        """Start the training loop (async - yields after each generation).
        
        Flow: FOREGROUND (N sessions) -> BACKGROUND (X gens) -> FOREGROUND -> ...
        This lets you see the agent multiple times, then train to improve.
        """
        if self.running:
            tlog('Already running')
            return

        self.running = True
        tlog('Starting training loop', {'foregroundSessions': FOREGROUND_SESSIONS, 'backgroundGenerations': BACKGROUND_GENERATIONS})
        
        # Main training loop
        while self.running and self.total_generations < MAX_GENERATIONS:
            
            # === FOREGROUND PHASE ===
            # Show current best agent multiple times
            if hasattr(window, 'telemetrySetPhase'):
                window.telemetrySetPhase('foreground')
            if self.on_state:
                self.on_state("FOREGROUND")
                
            self._foreground_won = False  # Track if agent wins during foreground
            for session in range(FOREGROUND_SESSIONS):
                if not self.running:
                    break

                if self.on_foreground:
                    # Priority: fastest winner > best distance > random
                    if self.best_win_weights:
                        weights_json = json.dumps(self.best_win_weights)
                        tlog('Foreground session', {'session': session + 1, 'total': FOREGROUND_SESSIONS, 'type': 'WINNER', 'frames': self.best_win_frames})
                    elif self.best_distance_weights:
                        weights_json = json.dumps(self.best_distance_weights)
                        w1_sum = sum(sum(row) for row in self.best_distance_weights['W1'])
                        tlog('Foreground session', {'session': session + 1, 'total': FOREGROUND_SESSIONS, 'type': 'champion', 'distance': self.best_distance_ever, 'W1sum': w1_sum})
                    else:
                        # First run - use random weights from first agent
                        weights_json = json.dumps(self.population.agents[0].get_weights())
                        tlog('Foreground session', {'session': session + 1, 'total': FOREGROUND_SESSIONS, 'type': 'random'})

                    self.on_foreground(weights_json)

                    # Wait for foreground to complete (death/stuck/win)
                    self._waiting_for_foreground = True
                    while self._waiting_for_foreground and self.running:
                        await asyncio.sleep(0.1)

                    # If agent won, skip remaining foreground sessions
                    if self._foreground_won:
                        tlog('Agent won - skipping remaining foreground sessions')
                        break
                    
            if not self.running:
                break
                
            # === BACKGROUND PHASE ===
            # Train for X generations
            if hasattr(window, 'telemetrySetPhase'):
                window.telemetrySetPhase('background')
            if self.on_state:
                self.on_state("BACKGROUND")
                await asyncio.sleep(0.05)  # Let UI render
                
            for _ in range(BACKGROUND_GENERATIONS):
                if not self.running:
                    break
                    
                await self._train_one_generation()
                
                # Check if level complete
                if self.level_complete:
                    tlog('LEVEL COMPLETE!')
                    if self.on_complete:
                        self.on_complete(True)
                    self.running = False
                    break
                
                # Auto-restart: if stuck after N generations, start fresh
                # Skip for optimize mode since we're starting from good weights
                if (self.mode != 'optimize' and
                    self.total_generations == AUTO_RESTART_GENERATIONS and
                    self.best_distance_ever < AUTO_RESTART_MIN_DISTANCE):
                    tlog('AUTO-RESTART', {'distance': self.best_distance_ever, 'generations': AUTO_RESTART_GENERATIONS, 'minRequired': AUTO_RESTART_MIN_DISTANCE})
                    self._auto_restart()
                    break  # Exit inner loop to restart foreground phase

            # Dump telemetry at end of background phase
            if hasattr(window, 'telemetryDump'):
                window.telemetryDump(f'Background Phase (Gen {self.total_generations})')

        # Done
        self.running = False
        if self.on_state:
            self.on_state("IDLE")
        tlog('Training loop ended')
        
    async def _train_one_generation(self):
        """Train a single generation - yields to browser after."""
        start_time = time.time()

        # Sanity check: if best_win_frames is impossibly low, it's from a bug - reset it
        if self.best_win_frames < 500:
            tlog('Invalid best_win_frames - resetting', {'bestWinFrames': self.best_win_frames})
            self.best_win_frames = float('inf')
            self.best_win_weights = None

        # CRITICAL: Inject best-ever weights into population slot 0
        # This prevents losing the champion to mutation drift
        champion_weights = self.best_win_weights or self.best_distance_weights
        champion_injected = False
        if champion_weights:
            self.population.inject_champion(champion_weights)
            champion_injected = True

        # Evaluate all agents
        gen_best_distance = 0
        gen_best_agent = None
        gen_wins = 0

        for i, agent in enumerate(self.population.agents):
            if not self.running:
                break

            # Skip evaluation for injected champion (slot 0) - preserve its guaranteed top position
            if i == 0 and champion_injected:
                # Give champion a high fitness based on its known performance
                if self.best_win_weights and self.best_win_frames >= 500:
                    agent.fitness = 500000 + (3000 - self.best_win_frames) * 100  # Match win fitness formula
                    agent.won = True
                    agent.frames = self.best_win_frames
                    agent.farthest_x = 3200  # Past finish line
                    gen_wins += 1  # Count champion's win in gen stats
                else:
                    agent.fitness = self.best_fitness_ever
                    agent.farthest_x = self.best_distance_ever
                # Track for gen stats
                if agent.farthest_x > gen_best_distance:
                    gen_best_distance = agent.farthest_x
                    gen_best_agent = agent
                tlog('Champion preserved', {'slot': 0, 'fitness': agent.fitness, 'distance': agent.farthest_x})
                continue

            fitness = self._evaluate_agent(agent, i)
            agent.fitness = fitness

            # Track wins (sanity check: must take at least 500 frames to actually win)
            if getattr(agent, 'won', False) and agent.frames >= 500:
                gen_wins += 1
                self.total_wins += 1
                # Track fastest win
                if agent.frames < self.best_win_frames:
                    self.best_win_frames = agent.frames
                    self.best_win_weights = copy.deepcopy(agent.get_weights())
                    tlog('NEW FASTEST WIN', {'frames': agent.frames})

            # Track best distance this generation
            if agent.farthest_x > gen_best_distance:
                gen_best_distance = agent.farthest_x
                gen_best_agent = agent

            # Track best distance EVER
            if agent.farthest_x > self.best_distance_ever:
                self.best_distance_ever = agent.farthest_x
                # CRITICAL: Deep copy weights to prevent mutation issues
                self.best_distance_weights = copy.deepcopy(agent.get_weights())
                # Debug: log weight signature to verify saves
                w1_sum = sum(sum(row) for row in self.best_distance_weights['W1'])
                tlog('NEW BEST DISTANCE', {'distance': self.best_distance_ever, 'W1sum': w1_sum})

            if agent.fitness > self.best_fitness_ever:
                self.best_fitness_ever = agent.fitness

            # In optimize mode, don't stop on level complete - keep training for better performance
            if agent.farthest_x > 3000 and self.mode != 'optimize':
                self.level_complete = True

        # Evolve population
        self.population.evolve()
        self.total_generations += 1

        elapsed = time.time() - start_time

        # Progress callback
        if self.on_progress:
            self.on_progress(
                self.total_generations,
                self.best_fitness_ever,
                self.best_distance_ever
            )

        if self.on_breeding:
            self.on_breeding(json.dumps({
                'generation': self.total_generations,
                'mode': self.population.mode,
                'events': self.population.get_last_generation_events()
            }))

        # Log generation summary
        tlog('Generation complete', {
            'generation': self.total_generations,
            'bestDistance': self.best_distance_ever,
            'genDistance': gen_best_distance,
            'genWins': gen_wins,
            'bestWinFrames': self.best_win_frames if self.best_win_frames < float('inf') else None,
            'elapsed': elapsed,
            'bestFitness': self.best_fitness_ever
        })
        
        # YIELD to browser - this is critical!
        await asyncio.sleep(0)
        
    def _evaluate_agent(self, agent, idx):
        """Evaluate agent using headless NES.
        
        Optimized: 
        - Uses getGameState() which reads only ~450 bytes vs 65KB!
        - Converts JsProxy to Python dict once per call to avoid repeated boundary crossing
        - Early termination for agents moving backwards (LEFT button at start)
        """
        nes = self.headless_pool.getInstance(idx % 4) if self.headless_pool else None
        if not nes:
            return 0
            
        nes.reset()
        agent.reset()
        
        frames = 0
        stuck_frames = 0
        state = None  # Reuse for final check
        
        # Early termination tracking
        EARLY_CHECK_FRAMES = 60  # Check direction in first 60 frames
        BACKWARDS_THRESHOLD = 3  # Kill if pressing LEFT this many times early
        backwards_count = 0
        
        while frames < MAX_FRAMES_PER_EPISODE:
            # Get state and convert to Python ONCE (avoids repeated JsProxy overhead)
            state = convert_state(nes.getGameState())
            inputs = build_inputs(state)
            outputs = agent.forward(inputs)
            buttons = agent.get_buttons(outputs)

            # Debug: log first few frames to compare with JS
            if frames < 5 or frames in [60, 120, 180]:
                x = get_mario_location_in_level(state)
                row, col = (state['playerYScreenOffset'] + 16) // 16, (state['playerXScreenOffset'] + 12) // 16
                solids = sum(1 for v in inputs[:70] if v == 1)
                # Raw RAM values for comparison
                yOff = state['playerYScreenOffset']
                xOff = state['playerXScreenOffset']
                tlog_frame(frames, {
                    'x': x, 'row': row, 'col': col, 'solids': solids,
                    'yOff': yOff, 'xOff': xOff, 'buttons': list(buttons)
                })
            
            # Early termination: if agent keeps pressing LEFT at start, kill it
            # LEFT button index is 6 in JSNes
            if frames < EARLY_CHECK_FRAMES:
                if 6 in buttons and 7 not in buttons:  # LEFT without RIGHT
                    backwards_count += 1
                    if backwards_count >= BACKWARDS_THRESHOLD:
                        # Agent is going backwards - waste of time
                        agent.farthest_x = 0
                        return 0  # Zero fitness for backwards agents
            
            nes.setButtons(buttons)
            nes.frame()
            frames += 1
            
            # Get state for position check (convert once)
            state = convert_state(nes.getGameState())
            x = get_mario_location_in_level(state)
            
            if x > agent.farthest_x:
                agent.farthest_x = x
                stuck_frames = 0
            else:
                stuck_frames += 1
                
            won = did_win(state)
            if is_dead(state) or won or stuck_frames > STUCK_THRESHOLD:
                # Store win info on agent for tracking
                agent.won = won
                agent.frames = frames
                break

        won = did_win(state) if state else False
        agent.won = won
        agent.frames = frames
        return calculate_fitness(agent.farthest_x, frames, died=is_dead(state) if state else False, won=won)
        
    def _auto_restart(self):
        """Reset population and stats for a fresh start."""
        tlog('Resetting population for fresh start')

        # Reset population with fresh random weights
        self.population.initialize()
        self.mode = self.population.mode

        # Reset tracking stats
        self.total_generations = 0
        self.best_distance_ever = 0
        self.best_distance_weights = None
        self.best_fitness_ever = 0

        # Clear elite pool if using crossover modes
        if hasattr(self.population, 'elite_pool'):
            self.population.elite_pool = []

        tlog('Fresh population ready - restarting training')
        
    def resume_from_foreground(self, did_win=False):
        """Called by JS when foreground display is done."""
        tlog('Foreground complete', {'won': did_win})
        self._foreground_won = did_win
        self._waiting_for_foreground = False

    def stop(self):
        """Stop training."""
        tlog('Stopping')
        self.running = False
        self._waiting_for_foreground = False
        
    def get_stats(self):
        """Get current stats."""
        return {
            'generation': self.total_generations,
            'best_fitness': self.best_fitness_ever,
            'best_distance': self.best_distance_ever,
            'level_complete': self.level_complete,
            'running': self.running
        }


# Global instance
_trainer = None

def get_trainer():
    global _trainer
    if _trainer is None:
        _trainer = Trainer()
    return _trainer


# === JS Bridge ===

def init_trainer(on_progress, on_foreground, on_state, on_complete, mode='simple', on_breeding=None):
    """
    Initialize trainer with callbacks.
    
    ROM data and initial state are read directly from window to avoid proxy issues.
    
    Args:
        on_progress: callback(gen, fitness, distance)
        on_foreground: callback(weights_json) - show best agent
        on_state: callback(state) - 'IDLE', 'BACKGROUND', 'FOREGROUND'
        on_complete: callback(success) - training done
        mode: Evolution mode ('simple', 'sbx', 'uniform')
    """
    trainer = get_trainer()
    
    # Set callbacks
    trainer.on_progress = on_progress
    trainer.on_foreground = on_foreground
    trainer.on_state = on_state
    trainer.on_complete = on_complete
    trainer.on_breeding = on_breeding
    
    # Get ROM and state directly from window (avoids proxy issues)
    rom_data = window._trainingRomData
    initial_state = window._trainingInitialState

    tlog('Got ROM and state from window', {'romLength': len(str(rom_data)), 'mode': mode})
    
    return trainer.initialize(rom_data, initial_state, mode=mode)

def start_training():
    """Start async training loop."""
    trainer = get_trainer()
    # Launch async training
    asyncio.ensure_future(trainer.start())

def stop_training():
    """Stop training."""
    trainer = get_trainer()
    trainer.stop()

def foreground_complete(did_win=False):
    """Called by JS when foreground display is done."""
    trainer = get_trainer()
    trainer.resume_from_foreground(did_win)

def get_stats():
    """Get current training stats as JSON."""
    trainer = get_trainer()
    return json.dumps(trainer.get_stats())

def reset_trainer():
    """Reset trainer for fresh start."""
    global _trainer
    if _trainer:
        _trainer.stop()
    _trainer = None
    tlog('Reset')


def setup_js_bridge():
    """Register JS bridge functions."""
    window.initTrainer = init_trainer
    window.startTraining = start_training
    window.stopTraining = stop_training
    window.foregroundComplete = foreground_complete
    window.getTrainerStats = get_stats
    window.resetTrainer = reset_trainer
    tlog('JS bridge ready')
