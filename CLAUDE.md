# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyScript L.A.B is a collection of interactive examples demonstrating PyScript's capabilities for running Python directly in web browsers via WebAssembly. The project uses SvelteKit (Svelte 5 with runes), TailwindCSS v4, and PyScript 2025.2.1.

## Development Commands

**NEVER** run commands without explicitly being told to. Most of the time, user is running `npm run dev` on their system which is isolated from where you operate and it screws up node_modules and package_lock. If you absolutely need to run an npm command, ask first.

## Architecture

### PyScript Integration

**PyScript Configuration** (`src/app.html`):
- PyScript 2025.2.1 is loaded via CDN in the root HTML template
- Global packages are configured in `<py-config>` tag: bokeh, pandas, numpy, networkx, diagrams, scikit-learn, pillow, matplotlib, plotly
- Bokeh 3.6.2 and Plotly JavaScript libraries are loaded for visualization support
- A persistent Python console (using xterm.js) is available via the footer "Console" button

**PyScriptManager** (`src/lib/pyscript_manager.py`):
- Modern async/await-based Python module loader
- Handles loading external Python scripts and exposing functions to JavaScript
- Event-driven architecture with `signal_ready()` callback system
- Used by RL demo and other complex examples

### Component Architecture

**ExperimentCard Component** (`src/lib/components/ExperimentCard.svelte`):
- Standard layout wrapper for all example pages
- Split-pane design: interactive demo (left, 3/4 width) + documentation (right, 1/4 width)
- Two named slots:
  - `py_slot`: For the interactive PyScript demo area
  - `content_slot`: For documentation and explanation
- Footer contains `#script_gutter` div where Python output is rendered
- Navigation controls (Previous/Next) that link examples together
- Props: `{ previousPage: string, nextPage: string }`

### Code Organization Principles

**IMPORTANT: Follow these architectural guidelines strictly**

**1. Separation of Concerns - Use Controllers**

Keep Svelte components lean and focused on UI rendering. Extract complex logic to controller classes in `src/lib/controller/`:

- **Svelte Components** (`src/routes/` and `src/lib/components/`):
  - Handle only UI rendering, user interactions, and lifecycle management
  - Should be lightweight and readable
  - Import and use controllers for business logic

- **Controllers** (`src/lib/controller/`):
  - Contain all PyScript integration logic
  - Handle data transformations and business logic
  - Manage communication between Python and JavaScript
  - Examples: `RLController.js` (RL demo), `DiagramCreatorController.js`, `SentimentAnalysisController.js`

**Example structure:**
```javascript
// src/lib/controller/MyFeatureController.js
export class MyFeatureController {
  constructor() {
    this.pyScriptManager = new PyScriptManager('my-feature');
  }

  async initialize() {
    this.setupCallbacks();
    await this.pyScriptManager.runScript('/python/my_feature.py', 'body');
  }

  setupCallbacks() {
    window.handlePythonData = (data) => {
      // Transform and process data
      return this.processData(data);
    };
  }

  destroy() {
    // Cleanup
  }
}
```

**2. Data-Only Communication: Avoid innerHTML from Python**

**Never use `innerHTML` or direct DOM manipulation from Python.** Python should only send data, not HTML.

**❌ Bad Pattern:**
```python
# Python manipulating DOM directly
from pyscript import document
document.querySelector("#result").innerHTML = "<div>Result: 42</div>"
```

**✅ Good Pattern:**
```python
# Python sending only data
from js import window
window.updateResult({"value": 42, "status": "success"})
```

```javascript
// JavaScript/Svelte handling rendering
window.updateResult = (data) => {
  resultStore.set(data);  // Let Svelte reactivity handle the DOM
};
```

**Benefits:**
- Maintains Svelte's reactivity system
- Prevents XSS vulnerabilities
- Easier to test and debug
- Clear separation between data and presentation

### State Management

**Svelte Stores Pattern**:
- Stores are used for reactive state between Python and JavaScript
- Example: `src/lib/stores/digitRecognitionStore.js` for ML example
- JavaScript exposes update functions on `window` object for Python to call
- **Important**: Convert Pyodide proxies to plain JavaScript objects to avoid destruction errors

### Python File Organization

Python scripts are organized in `/static/python/` by category:
- `/static/python/basic/`: Simple examples (date.py, fibo.py, snek.py)
- `/static/python/bokeh/`: Bokeh visualization scripts
- `/static/python/matplotlib/`: Matplotlib charts and maps
- `/static/python/diagrams/`: Architecture diagram generators
- `/static/python/ml/`: Machine learning examples
  - `/static/python/ml/rl/`: Reinforcement learning demo files
    - `agent.py`: Main training agent (modular architecture)
    - `neural.py`: Base neural network class
    - `player_agent.py`: Legacy agent (deprecated)
  - `/static/python/lib/`: Shared utilities
    - `/static/python/lib/nes/`: NES emulator interaction
      - `game_controller.py`: All emulator interactions
      - `nes_ram_utils.py`: RAM extraction utilities
    - `/static/python/lib/neural/`: Neural network abstractions
      - `neural_controller.py`: Abstract neural network interface
- `/static/python/interop.py`: JavaScript ↔ Python communication demo

### RL Demo Architecture

The reinforcement learning demo uses a modular, event-driven architecture:

**JavaScript Side** (`src/lib/controller/RLController.js`):
- Manages UI state and emulator lifecycle
- Uses PyScriptManager to load Python modules
- Provides callbacks for Python to update UI

**Python Side** (`static/python/ml/rl/`):
- **agent.py**: Main training loop with clean architecture
  - `PlayerAgent` class orchestrates training
  - Uses composition: GameController + NeuralController + ActionDecoder
  - Implements neuroevolution with elite preservation
- **lib/nes/game_controller.py**: Encapsulates all emulator interactions
  - Vision extraction from RAM
  - Button execution
  - Mario state detection
- **lib/neural/neural_controller.py**: Abstract neural network interface
  - `SimpleNeuralController`: 3-layer feedforward network
  - `ActionDecoder`: Converts network outputs to button presses
  - Behavioral priors initialization (biases toward RIGHT+JUMP)

**Key Principles:**
- Python sends data only (never manipulates DOM)
- JavaScript handles all UI rendering
- Event-driven communication via `window` callbacks
- Modular, testable components

## Key Technical Notes

### Memory Management
- **Critical**: Always clean up PyScript resources in `onDestroy()` hooks
- Python script elements persist in DOM unless explicitly removed
- Each page navigation without cleanup adds memory overhead

### Canvas & Image Processing
- When passing canvas data to Python, use `canvas.toDataURL('image/png')` for base64 encoding
- Python can decode base64 images using PIL/Pillow
- For ML preprocessing, typical workflow: Canvas → Base64 → PIL Image → NumPy array → Model input

### Static Site Generation
- Uses `@sveltejs/adapter-static` for static site generation
- Build output is fully static (no server required)
- Base path `/python-ds` is configured for GitHub Pages hosting
- All routes must be pre-rendered at build time

## Browser Compatibility

Requires modern browsers with WebAssembly support:
- Chrome/Edge 90+
- Firefox 88+
- Safari 15+
