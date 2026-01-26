# Grokking Neural Network

This document describes the Grokking Neural Network demo, which demonstrates the fascinating "grokking" phenomenon in deep learning.

## Overview

Grokking is a phenomenon where neural networks suddenly generalize long after achieving perfect training accuracy. The network first memorizes the training data, then much later "groks" (suddenly understands) the underlying pattern and generalizes to unseen test data.

## Architecture

### Web Worker Setup

The demo uses PyScript Web Workers for background computation:

```
Main Thread (UI)          Web Worker (Background)
┌─────────────────┐       ┌─────────────────────┐
│  +page.svelte   │       │    worker.py        │
│  GrokController │◄─────►│    network.py       │
│  NeuralNetworkViz│       │    utils.py         │
│  MetricsChart   │       └─────────────────────┘
└─────────────────┘
```

### File Structure

```
src/
  routes/examples/ml/grokking/
    +page.svelte              # Main page component with worker declaration
  lib/
    controller/
      GrokController.js       # Worker↔JS communication bridge

static/
  mini-coi.js                 # CORS headers for Web Worker
  python/ml/grokking/
    __init__.py               # Module initialization
    worker.py                 # Web Worker entry point
    network.py                # FactoredNetwork class
    utils.py                  # Data generation utilities
```

## Neural Network Architecture

Based on Google's Factored MLP for grokking:

```
Input (a, b)
    │
    ▼
┌─────────────────┐
│   Embedding     │  n_tokens × embed_size (tied)
│   (shared)      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Hidden Layer   │  embed_size × hidden_size
│  ReLU(h_a + h_b)│
└─────────────────┘
    │
    ▼
┌─────────────────┐
│    Output       │  hidden_size × embed_size
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Unembed        │  embed.T (tied weights)
│  + Softmax      │
└─────────────────┘
    │
    ▼
  Prediction (0 to n_tokens-1)
```

### Key Features

1. **Tied Embeddings**: Same matrix for input embedding and output unembedding
2. **Tied Hidden Weights**: Same projection for both inputs a and b
3. **No Biases**: All linear layers have no bias terms
4. **ReLU After Sum**: Hidden = ReLU(h_a + h_b), not separate ReLUs

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| n_tokens | 67 | Modulus (number of classes) |
| embed_size | 500 | Embedding dimension |
| hidden_size | 64 | Hidden layer neurons |
| learning_rate | 0.01 | AdamW learning rate |
| weight_decay | 1.0 | **HIGH** - key to grokking! |
| train_fraction | 0.4 | 40% train, 60% test |

## The Task

The network learns modular addition:

```
(a + b) mod p = c
```

For p=67 (prime), there are:
- 67 × 67 = 4,489 total pairs
- With symmetry (a ≤ b): 2,278 unique pairs
- Training set: ~911 examples (40%)
- Test set: ~1,367 examples (60%)

## Why Grokking Happens

1. **Memorization First**: With enough capacity, the network can memorize all training examples
2. **Weight Decay Pressure**: High weight decay (L2 regularization) continuously pushes weights toward zero
3. **Simpler Solution**: The generalizing solution requires less "weight magnitude" than memorization
4. **Phase Transition**: Eventually, weight decay forces the network to find the efficient generalizing solution

## Training Timeline

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Memorization (epochs 0-1000)                 │
│   - Train accuracy: 0% → 100%                         │
│   - Test accuracy: ~random (~1.5%)                    │
├────────────────────────────────────────────────────────┤
│ Phase 2: Plateau (epochs 1000-10000+)                 │
│   - Train accuracy: ~100%                             │
│   - Test accuracy: slowly climbing (20-40%)           │
├────────────────────────────────────────────────────────┤
│ Phase 3: Grokking! (sudden transition)                │
│   - Train accuracy: ~100%                             │
│   - Test accuracy: jumps to ~100%                     │
└────────────────────────────────────────────────────────┘
```

## Web Worker Communication

### Exported Functions

```python
# worker.py exports:
__export__ = [
    "initialize",     # Initialize network and data
    "train_batch",    # Train N epochs, return progress
    "get_prediction", # Test a single prediction
    "get_state",      # Get current training state
    "reset",          # Reset network weights
    "stop"            # Stop training
]
```

### JavaScript Controller

```javascript
// GrokController.js usage:
const controller = new GrokController();

controller.setCallbacks({
    onProgress: (result) => { /* Update UI */ },
    onGrokDetected: (epoch) => { /* Celebrate! */ },
    onStatus: (msg) => { /* Update status bar */ }
});

await controller.initialize();
await controller.startTraining(50000);
```

## References

- [Google's Grokking Explorable](https://pair.withgoogle.com/explorables/grokking/)
- [Grokking: Generalization Beyond Overfitting](https://arxiv.org/abs/2201.02177) (Power et al., 2022)
- [PyScript Web Workers Documentation](https://docs.pyscript.net/user-guide/workers/)

## CORS Requirements

For Web Workers to function properly, the following CORS headers are required:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Resource-Policy: cross-origin
```

The project uses `mini-coi.js` to provide these headers via a service worker, enabling Web Worker functionality without server-side header configuration.
