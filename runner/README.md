# Headless Python Runner for Neuroevolution

This directory contains a standalone Python environment for training the Mario neuroevolution agent **without PyScript/browser overhead**.

## Why Headless?

Browser-based training is painfully slow:
- PyScript overhead
- JavaScript<->Python bridge latency
- Single-threaded execution
- Browser rendering blocking

Headless training is **10-100x faster** for pure compute tasks.

## Setup

### Option A: Virtual Environment (Recommended)

```bash
cd runner

# On WSL/Ubuntu, install python3-venv first if needed:
# sudo apt install python3.10-venv

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Option B: User Install (No venv)

```bash
cd runner
pip3 install --user -r requirements.txt
```

### Option C: System-wide Install (Use with caution)

```bash
cd runner
pip3 install -r requirements.txt
```

### 3. Test Import (Verify Setup)

```bash
python test_import.py
```

You should see:
```
✅ Imported SimpleNeuralController and ActionDecoder
✅ Imported OnePlusOneES evolution strategy
✅ Imported MarioFitnessCalculator
...
🎉 ALL TESTS PASSED!
```

## Architecture

### Mock Browser APIs (`mocks.py`)

Provides stub implementations of PyScript/browser APIs:
- `js.console` -> stdout
- `js.window` -> dict-like object
- `pyodide.ffi.create_proxy` -> identity function
- `pyodide.ffi.to_js` -> identity function

These mocks are auto-installed on import, so existing code runs without changes.

### Code Reuse

The runner imports code directly from `static/python/`:
- `lib/neural/neural_controller.py` - Neural network implementations
- `lib/evolution/` - Evolution strategies, fitness, generation management
- `ml/neural/agent.py` - Mario agent logic (with NES emulator abstraction)

No code duplication - we use the same code in browser and headless.

## Next Steps

1. **Abstract the NES emulator** - Create a headless environment that simulates Mario
2. **Build training loop** - Run 1000s of generations efficiently
3. **Save/load models** - Export trained weights to JSON
4. **Import to browser** - Load pre-trained weights into PyScript demo

## File Structure

```
runner/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── mocks.py              # Browser API mocks
├── test_import.py        # Import verification test
├── train.py              # [TODO] Full training loop
└── venv/                 # Virtual environment (gitignored)
```
