"""
Mario AI Trainer - Event/Callback Based
Python controls the training loop, calls JS callbacks for state changes.
Yields after EACH generation to keep browser responsive.
"""

import asyncio
import numpy as np
from js import window, console
import json
import time

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
BACKGROUND_GENERATIONS = 10  # Generations per background phase
FOREGROUND_SESSIONS = 3      # How many times to show agent before training
MAX_GENERATIONS = 5000
MAX_FRAMES_PER_EPISODE = 3000
STUCK_THRESHOLD = 120


class Trainer:
    """Event-based trainer - Python controls everything."""
    
    def __init__(self):
        self.population = None
        self.headless_pool = None
        self.initial_state = None
        self.rom_data = None
        
        # State
        self.running = False
        self.total_generations = 0
        self.generations_since_foreground = 0
        
        # Track BEST BY DISTANCE (what we actually care about)
        self.best_distance_ever = 0
        self.best_distance_weights = None
        
        # Track best fitness too for stats
        self.best_fitness_ever = 0
        
        self.level_complete = False
        
        # Callbacks (set from JS)
        self.on_progress = None  # (gen, fitness, distance)
        self.on_foreground = None  # (weights_json) - show in emulator
        self.on_complete = None  # training finished
        self.on_state = None  # state change
        
    def initialize(self, rom_data, initial_state):
        """Initialize with ROM and state."""
        self.rom_data = rom_data
        self.initial_state = initial_state
        
        # Create population
        self.population = Population(20)
        self.population.initialize()
        
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
            console.log(f"[Trainer] HeadlessNES pool ready - initial Mario x={test_x}")
        else:
            console.error("[Trainer] HeadlessNES not available!")
            return False
            
        # Reset state
        self.running = False
        self.total_generations = 0
        self.generations_since_foreground = 0
        self.best_distance_ever = 0
        self.best_distance_weights = None
        self.best_fitness_ever = 0
        self.level_complete = False
        
        console.log("[Trainer] Initialized")
        return True
        
    async def start(self):
        """Start the training loop (async - yields after each generation).
        
        Flow: FOREGROUND (N sessions) -> BACKGROUND (X gens) -> FOREGROUND -> ...
        This lets you see the agent multiple times, then train to improve.
        """
        if self.running:
            console.log("[Trainer] Already running")
            return
            
        self.running = True
        console.log(f"[Trainer] Starting training loop ({FOREGROUND_SESSIONS} foreground, {BACKGROUND_GENERATIONS} background)")
        
        # Main training loop
        while self.running and self.total_generations < MAX_GENERATIONS:
            
            # === FOREGROUND PHASE ===
            # Show current best agent multiple times
            if self.on_state:
                self.on_state("FOREGROUND")
                
            for session in range(FOREGROUND_SESSIONS):
                if not self.running:
                    break
                    
                if self.on_foreground:
                    # Use best weights if we have them, otherwise use a random agent's weights
                    if self.best_distance_weights:
                        weights_json = json.dumps(self.best_distance_weights)
                        console.log(f"[Trainer] Foreground {session + 1}/{FOREGROUND_SESSIONS} - champion ({self.best_distance_ever}px)")
                    else:
                        # First run - use random weights from first agent
                        weights_json = json.dumps(self.population.agents[0].get_weights())
                        console.log(f"[Trainer] Foreground {session + 1}/{FOREGROUND_SESSIONS} - random agent")
                        
                    self.on_foreground(weights_json)
                    
                    # Wait for foreground to complete (death/stuck)
                    self._waiting_for_foreground = True
                    while self._waiting_for_foreground and self.running:
                        await asyncio.sleep(0.1)
                    
            if not self.running:
                break
                
            # === BACKGROUND PHASE ===
            # Train for X generations
            if self.on_state:
                self.on_state("BACKGROUND")
                await asyncio.sleep(0.05)  # Let UI render
                
            for _ in range(BACKGROUND_GENERATIONS):
                if not self.running:
                    break
                    
                await self._train_one_generation()
                
                # Check if level complete
                if self.level_complete:
                    console.log("[Trainer] LEVEL COMPLETE!")
                    if self.on_complete:
                        self.on_complete(True)
                    self.running = False
                    break
                    
        # Done
        self.running = False
        if self.on_state:
            self.on_state("IDLE")
        console.log("[Trainer] Training loop ended")
        
    async def _train_one_generation(self):
        """Train a single generation - yields to browser after."""
        start_time = time.time()
        
        # Evaluate all agents
        gen_best_distance = 0
        gen_best_agent = None
        
        for i, agent in enumerate(self.population.agents):
            if not self.running:
                break
                
            fitness = self._evaluate_agent(agent, i)
            agent.fitness = fitness
            
            # Track best distance this generation
            if agent.farthest_x > gen_best_distance:
                gen_best_distance = agent.farthest_x
                gen_best_agent = agent
                
            # Track best distance EVER
            if agent.farthest_x > self.best_distance_ever:
                self.best_distance_ever = agent.farthest_x
                self.best_distance_weights = agent.get_weights()
                console.log(f"[Trainer] NEW BEST DISTANCE: {self.best_distance_ever}")
                
            if agent.fitness > self.best_fitness_ever:
                self.best_fitness_ever = agent.fitness
                
            if agent.farthest_x > 3000:
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
            
        console.log(f"[Gen {self.total_generations}] best_dist={self.best_distance_ever}, gen_dist={gen_best_distance} ({elapsed:.1f}s)")
        
        # YIELD to browser - this is critical!
        await asyncio.sleep(0)
        
    def _evaluate_agent(self, agent, idx):
        """Evaluate agent using headless NES.
        
        Optimized: 
        - Uses getGameState() which reads only ~450 bytes vs 65KB!
        - Converts JsProxy to Python dict once per call to avoid repeated boundary crossing
        """
        nes = self.headless_pool.getInstance(idx % 4) if self.headless_pool else None
        if not nes:
            return 0
            
        nes.reset()
        agent.reset()
        
        frames = 0
        stuck_frames = 0
        state = None  # Reuse for final check
        
        while frames < MAX_FRAMES_PER_EPISODE:
            # Get state and convert to Python ONCE (avoids repeated JsProxy overhead)
            state = convert_state(nes.getGameState())
            inputs = build_inputs(state)
            outputs = agent.forward(inputs)
            buttons = agent.get_buttons(outputs)
            
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
                
            if is_dead(state) or did_win(state) or stuck_frames > STUCK_THRESHOLD:
                break
                
        return calculate_fitness(agent.farthest_x, frames, died=is_dead(state), won=did_win(state))
        
    def resume_from_foreground(self):
        """Called by JS when foreground display is done."""
        console.log("[Trainer] Foreground complete, resuming...")
        self._waiting_for_foreground = False
        
    def stop(self):
        """Stop training."""
        console.log("[Trainer] Stopping...")
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

def init_trainer(on_progress, on_foreground, on_state, on_complete):
    """
    Initialize trainer with callbacks.
    
    ROM data and initial state are read directly from window to avoid proxy issues.
    
    Args:
        on_progress: callback(gen, fitness, distance)
        on_foreground: callback(weights_json) - show best agent
        on_state: callback(state) - 'IDLE', 'BACKGROUND', 'FOREGROUND'
        on_complete: callback(success) - training done
    """
    trainer = get_trainer()
    
    # Set callbacks
    trainer.on_progress = on_progress
    trainer.on_foreground = on_foreground
    trainer.on_state = on_state
    trainer.on_complete = on_complete
    
    # Get ROM and state directly from window (avoids proxy issues)
    rom_data = window._trainingRomData
    initial_state = window._trainingInitialState
    
    console.log(f"[Trainer] Got ROM ({len(str(rom_data))} chars) and state from window")
    
    return trainer.initialize(rom_data, initial_state)

def start_training():
    """Start async training loop."""
    trainer = get_trainer()
    # Launch async training
    asyncio.ensure_future(trainer.start())

def stop_training():
    """Stop training."""
    trainer = get_trainer()
    trainer.stop()

def foreground_complete():
    """Called by JS when foreground display is done."""
    trainer = get_trainer()
    trainer.resume_from_foreground()

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
    console.log("[Trainer] Reset")


def setup_js_bridge():
    """Register JS bridge functions."""
    window.initTrainer = init_trainer
    window.startTraining = start_training
    window.stopTraining = stop_training
    window.foregroundComplete = foreground_complete
    window.getTrainerStats = get_stats
    window.resetTrainer = reset_trainer
    console.log("[Trainer] JS bridge ready")
