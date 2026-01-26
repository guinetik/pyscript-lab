"""
Background Trainer - Headless population training for faster evolution

Runs multiple neural networks in headless mode (no rendering) between
visible foreground generations. When a new champion is found, it's sent
to the foreground for display.

Architecture:
- Foreground: 1 agent playing visibly at 60 FPS (30 observations/sec)
- Background: N agents evaluated headlessly at max speed
- Champion weights flow from background → foreground

ISOLATION: Background uses HeadlessGameController with its own NES instance.
           It NEVER touches window.nesEmulator (foreground's emulator).
"""

import numpy as np
from js import window, console
from typing import Callable, List, Tuple, Optional
from lib.nes.headless_game_controller import HeadlessGameController


class BackgroundTrainer:
    """
    Manages a population of neural networks trained headlessly.

    Uses a completely isolated HeadlessNES instance that doesn't
    interfere with the foreground display.
    """

    def __init__(
        self,
        population_size: int = 5,
        mutation_rate: float = 0.05,
        mutation_scale: float = 0.2
    ):
        """
        Initialize background trainer.

        Args:
            population_size: Number of networks in population
            mutation_rate: Probability of mutating each weight
            mutation_scale: Standard deviation of mutation noise
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale

        # Population: list of (weights, biases, fitness) tuples
        self.population: List[dict] = []

        # Champion tracking
        self.champion: Optional[dict] = None
        self.champion_fitness: float = 0
        self.champion_distance: int = 0

        # Callbacks
        self.on_champion_found: Optional[Callable] = None
        self.on_evaluation_complete: Optional[Callable] = None

        # State
        self.generation = 0
        self.is_running = False
        self.total_evaluations = 0

        # ISOLATED headless game controller (NOT the foreground one)
        self.headless_game = None

        # Neural network template (for cloning architecture)
        self.neural_template = None
        self.action_decoder = None
        self.reflex_system = None
        self.fitness_calculator = None

        # Vision dimensions (must match foreground)
        self.vision_width = 7
        self.vision_height = 10

        print(f"🧬 BackgroundTrainer initialized (population={population_size})")
        print(f"   Using ISOLATED HeadlessNES (not window.nesEmulator)")

    async def initialize_headless(self):
        """
        Initialize the isolated headless game controller.
        Must be called after foreground emulator is ready.
        """
        if self.headless_game:
            return  # Already initialized

        self.headless_game = HeadlessGameController(
            vision_width=self.vision_width,
            vision_height=self.vision_height
        )
        self.headless_game.initialize()

        # Load starting state from FILE (same source as foreground)
        # This ensures consistent starting position across all evaluations
        await self.headless_game.load_state_from_file('/data/nes_state.json')

        console.log("✅ Background trainer has isolated headless NES")

    def initialize_population(self, neural_controller):
        """
        Initialize population with random networks.

        Args:
            neural_controller: Template neural controller to get weights from
                             (NOT stored - use set neural_template separately for isolated copy)
        """
        # DON'T overwrite neural_template here! It may have been set to an isolated copy
        # in agent.py to avoid shared reference bugs. Only set if not already configured.
        if self.neural_template is None:
            self.neural_template = neural_controller
        self.population = []

        # Get template weights (returns {'weights': [...], 'biases': [...]}
        weight_data = neural_controller.get_weights()
        template_weights = weight_data['weights']
        template_biases = weight_data['biases']

        for i in range(self.population_size):
            # Clone and randomize weights
            weights = [w.copy() for w in template_weights]
            biases = [b.copy() for b in template_biases]

            # Add random noise - but preserve output layer biases (behavioral priors)!
            # Using smaller noise scale (0.15) to avoid destroying learned behaviors
            noise_scale = 0.15
            
            for layer_idx, w in enumerate(weights):
                # Slightly higher noise for hidden layers, lower for output
                layer_noise = noise_scale if layer_idx < len(weights) - 1 else noise_scale * 0.5
                w += np.random.randn(*w.shape).astype(np.float32) * layer_noise
            
            for layer_idx, b in enumerate(biases):
                is_output_layer = (layer_idx == len(biases) - 1)
                if is_output_layer:
                    # PRESERVE output biases (behavioral priors: RIGHT, JUMP, RUN)
                    # Only add tiny noise to encourage exploration without breaking priors
                    b += np.random.randn(*b.shape).astype(np.float32) * 0.05
                else:
                    # Hidden layer biases can have more noise
                    b += np.random.randn(*b.shape).astype(np.float32) * noise_scale

            self.population.append({
                'weights': weights,
                'biases': biases,
                'fitness': 0,
                'distance': 0
            })

        print(f"✅ Population initialized: {self.population_size} networks")

    async def run_headless_evaluation(self, network_idx: int) -> dict:
        """
        Evaluate one network headlessly (no rendering).

        Uses the ISOLATED headless NES - never touches foreground emulator.

        Args:
            network_idx: Index of network in population

        Returns:
            dict: Evaluation results {fitness, distance, frames, death_cause}
        """
        if not self.headless_game:
            await self.initialize_headless()

        network = self.population[network_idx]

        # Load network weights into template
        self.neural_template.set_weights(network['weights'], network['biases'])

        # Restore save state in HEADLESS emulator (not foreground!)
        loaded = await self.headless_game.load_saved_state()
        if not loaded:
            console.warn(f"⚠️ Network {network_idx}: Failed to load saved state!")
            return {'fitness': 0, 'distance': 0, 'frames': 0, 'death_cause': 'no_state'}

        # Reset reflex system
        if self.reflex_system:
            self.reflex_system.reset()
        
        # Debug: Check initial Mario position after state load
        initial_x, initial_y = self.headless_game.get_mario_position()
        if network_idx == 0:  # Only log first network to avoid spam
            console.log(f"🔍 Initial Mario position after state load: ({initial_x}, {initial_y})")

        # Run headless loop
        max_frames = 3600  # 2 minutes at 60 FPS
        stuck_threshold = 300  # 5 seconds without progress

        frames = 0
        max_position = 0
        stuck_frames = 0
        death_cause = "timeout"

        while frames < max_frames:
            # Advance HEADLESS emulator frame (not foreground!)
            self.headless_game.frame()

            # Get state from HEADLESS emulator
            vision = self.headless_game.get_vision_state()
            position, _ = self.headless_game.get_mario_position()

            # Check if alive
            alive = self.headless_game.is_mario_alive()
            if not alive:
                death_cause = "enemy"
                break

            # Track progress
            if position > max_position:
                max_position = position
                stuck_frames = 0
            else:
                stuck_frames += 1

            # Check stuck
            if stuck_frames >= stuck_threshold:
                death_cause = "stuck"
                break

            # Build observation (vision + row encoding)
            mario_col, mario_row = self.headless_game.get_mario_tile_position()
            clamped_row = max(0, min(mario_row, self.vision_height - 1))
            row_encoding = np.zeros(self.vision_height, dtype=np.float32)
            row_encoding[clamped_row] = 1.0

            state = np.concatenate([np.array(vision, dtype=np.float32), row_encoding])

            # === DIAGNOSTIC: Log state at first pipe (430-440px) ===
            if 430 <= position <= 440 and network_idx == 0:
                if not hasattr(self, '_bg_pipe_diagnostic_logged'):
                    self._bg_pipe_diagnostic_logged = True
                    raw_pos = self.headless_game.get_mario_position()
                    console.log("=" * 60)
                    console.log("🔬 BACKGROUND DIAGNOSTIC AT PIPE (Network 0)")
                    console.log(f"   Raw position: x={raw_pos[0]}, y={raw_pos[1]}")
                    console.log(f"   Tile position: col={mario_col}, row={mario_row}")
                    console.log(f"   Clamped row: {clamped_row}")
                    console.log(f"   State shape: {state.shape}")
                    console.log(f"   Vision (first 20): {state[:20].tolist()}")
                    console.log(f"   Row encoding (last 10): {state[-10:].tolist()}")
                    console.log(f"   State sum: {state.sum():.4f}")
                    console.log("=" * 60)

            # Forward pass through network
            output = self.neural_template.forward(state)

            # Decode to buttons FIRST (returns binary array: [UP, DOWN, LEFT, RIGHT, A, B])
            actions = self.action_decoder.decode(output)

            # Apply reflexes AFTER decoding (modifies binary button states)
            # IMPORTANT: Must use simple_controls=True to match foreground (4 buttons)
            if self.reflex_system:
                actions = self.reflex_system.apply_reflexes(
                    state, actions, stuck_frames, simple_controls=True
                )
            
            # actions is now [UP, DOWN, LEFT, RIGHT, A, B] format
            # HeadlessGameController.execute_buttons expects this format directly
            self.headless_game.execute_buttons(actions)

            frames += 1

        # Calculate fitness using generation info format
        gen_info = {
            'distance': max_position,
            'frames': frames,
            'score_gained': 0,
            'generation': self.generation + 1,  # Add generation to suppress "Gen 0" spam
            'best_distance': self.champion_distance  # For preservation mode
        }
        fitness = self.fitness_calculator.calculate(gen_info)

        # Update network stats
        network['fitness'] = fitness
        network['distance'] = max_position

        self.total_evaluations += 1

        return {
            'fitness': fitness,
            'distance': max_position,
            'frames': frames,
            'death_cause': death_cause
        }

    async def evaluate_population(self):
        """Evaluate all networks in population headlessly."""
        console.log(f"🔄 Evaluating {self.population_size} networks headlessly...")
        console.log(f"   (Using isolated HeadlessNES - foreground unaffected)")

        # Reset diagnostic flag for fresh logging each generation
        if hasattr(self, '_bg_pipe_diagnostic_logged'):
            del self._bg_pipe_diagnostic_logged

        prev_champion_dist = self.champion_distance
        
        for i in range(self.population_size):
            result = await self.run_headless_evaluation(i)
            console.log(f"   Network {i+1}: {result['distance']}px (fitness: {result['fitness']:.0f})")

            # Check for new champion
            if result['fitness'] > self.champion_fitness:
                self.champion = self.population[i].copy()
                self.champion_fitness = result['fitness']
                self.champion_distance = result['distance']

                console.log(f"🏆 NEW CHAMPION! {result['distance']}px")

                if self.on_champion_found:
                    self.on_champion_found(self.champion, result)

        # === LEARNING PROGRESS LOG ===
        distances = [p['distance'] for p in self.population]
        fitnesses = [p['fitness'] for p in self.population]
        
        best_dist = max(distances)
        worst_dist = min(distances)
        avg_dist = sum(distances) / len(distances)
        
        best_fit = max(fitnesses)
        avg_fit = sum(fitnesses) / len(fitnesses)
        
        # Count how many beat a threshold
        past_pipe = sum(1 for d in distances if d > 450)  # First pipe ~434px
        positive_fitness = sum(1 for f in fitnesses if f > 0)
        
        console.log(f"📊 === GEN {self.generation} LEARNING STATS ===")
        console.log(f"   Distance: best={best_dist}px, avg={avg_dist:.0f}px, worst={worst_dist}px")
        console.log(f"   Fitness:  best={best_fit:.0f}, avg={avg_fit:.0f}")
        console.log(f"   Progress: {past_pipe}/{self.population_size} past first pipe (>450px)")
        console.log(f"   Viable:   {positive_fitness}/{self.population_size} with positive fitness")
        
        if self.champion_distance > prev_champion_dist:
            console.log(f"   🎯 IMPROVEMENT! Champion: {prev_champion_dist}px → {self.champion_distance}px (+{self.champion_distance - prev_champion_dist}px)")
        else:
            console.log(f"   ⏸️ No improvement. Champion still at {self.champion_distance}px")

        if self.on_evaluation_complete:
            self.on_evaluation_complete(self.generation, self.champion_fitness)

    def breed_population(self):
        """
        Breed population using tournament selection and mutation.
        """
        # Sort by fitness
        sorted_pop = sorted(self.population, key=lambda x: x['fitness'], reverse=True)

        # Keep top 2 as elites
        new_population = [sorted_pop[0].copy(), sorted_pop[1].copy()]

        # Fill rest with mutated offspring from top performers
        while len(new_population) < self.population_size:
            # Tournament selection (pick best of 2 random)
            parent_idx = self._tournament_select(sorted_pop)
            parent = sorted_pop[parent_idx]

            # Clone and mutate
            child = self._mutate(parent)
            new_population.append(child)

        self.population = new_population
        self.generation += 1

        console.log(f"🧬 Population bred - Generation {self.generation}")

    def _tournament_select(self, sorted_pop: List[dict], k: int = 2) -> int:
        """Tournament selection - pick best of k random individuals."""
        indices = np.random.choice(len(sorted_pop), size=min(k, len(sorted_pop)), replace=False)
        # Find the one with highest fitness among selected
        best_idx = min(indices, key=lambda i: sorted_pop[int(i)]['fitness'], default=0)
        # Actually want MAX fitness, not min
        best_idx = max(indices, key=lambda i: sorted_pop[int(i)]['fitness'])
        return int(best_idx)

    def _mutate(self, parent: dict) -> dict:
        """Create mutated offspring from parent."""
        child = {
            'weights': [w.copy() for w in parent['weights']],
            'biases': [b.copy() for b in parent['biases']],
            'fitness': 0,
            'distance': 0
        }

        # Mutate weights
        for w in child['weights']:
            mask = np.random.random(w.shape) < self.mutation_rate
            noise = np.random.randn(*w.shape).astype(np.float32) * self.mutation_scale
            w += mask * noise

        # Mutate biases
        for b in child['biases']:
            mask = np.random.random(b.shape) < self.mutation_rate
            noise = np.random.randn(*b.shape).astype(np.float32) * self.mutation_scale
            b += mask * noise

        return child

    def get_champion_weights(self) -> Optional[Tuple[List, List]]:
        """Get current champion's weights and biases."""
        if self.champion is None:
            return None
        return (self.champion['weights'], self.champion['biases'])

    def inject_champion(self, weights: List, biases: List, fitness: float, distance: int):
        """
        Inject an external champion (e.g., from foreground training).

        Args:
            weights: Network weights
            biases: Network biases
            fitness: Champion fitness
            distance: Distance achieved
        """
        self.champion = {
            'weights': [w.copy() for w in weights],
            'biases': [b.copy() for b in biases],
            'fitness': fitness,
            'distance': distance
        }
        self.champion_fitness = fitness
        self.champion_distance = distance

        # Also add to population if better than worst
        if len(self.population) > 0:
            worst_idx = min(range(len(self.population)), key=lambda i: self.population[i]['fitness'])
            if fitness > self.population[worst_idx]['fitness']:
                self.population[worst_idx] = self.champion.copy()

        console.log(f"💉 Injected champion: {distance}px (fitness: {fitness:.0f})")

    async def refresh_state(self):
        """
        Refresh the saved state from file.
        Call this before running evaluations to ensure consistent starting point.
        """
        if self.headless_game:
            await self.headless_game.load_state_from_file('/data/nes_state.json')
        else:
            console.warn("⚠️ refresh_state: headless_game not initialized yet!")

    def destroy(self):
        """Clean up resources."""
        if self.headless_game:
            self.headless_game.destroy()
            self.headless_game = None
        console.log("🗑️ BackgroundTrainer destroyed")
