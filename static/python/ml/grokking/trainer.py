"""
Grokking Neural Network Trainer - NumPy Vectorized Version

Uses numpy for fast matrix operations, allowing original network parameters.
Runs on the main thread with asyncio yields to keep UI responsive.
"""

import numpy as np
import asyncio
from js import window

# ============================================================================
# UTILITIES
# ============================================================================

def generate_all_pairs(mod, symmetric=True):
    """Generate all pairs for modular addition: (a + b) mod p."""
    data = []
    for a in range(mod):
        for b in range(mod):
            if symmetric and a > b:
                continue
            c = (a + b) % mod
            data.append({'a': a, 'b': b, 'target': c})
    return data


def split_data(dataset, train_fraction=0.4):
    """Split dataset into train/test sets."""
    np.random.shuffle(dataset)
    split_idx = int(len(dataset) * train_fraction)
    return dataset[:split_idx], dataset[split_idx:]


# ============================================================================
# FACTORED NETWORK - NUMPY VECTORIZED
# ============================================================================

class FactoredNetwork:
    """
    Factored Neural Network for modular addition grokking.
    
    Uses numpy for fast matrix operations.
    Architecture: Input → Embed(tied) → Hidden(tied) → ReLU(h_a + h_b) → Out → Unembed(tied)
    """
    
    def __init__(self, config):
        self.n_tokens = config.get('n_tokens', 67)
        self.embed_size = config.get('embed_size', 500)
        self.hidden_size = config.get('hidden_size', 64)
        self.learning_rate = config.get('learning_rate', 0.01)
        self.weight_decay = config.get('weight_decay', 1.0)
        self.beta1 = config.get('beta1', 0.9)
        self.beta2 = config.get('beta2', 0.98)
        self.epsilon = 1e-8
        
        self._init_weights()
        self._init_adam_state()
        self.adam_t = 0
        self.epoch = 0
        
        # Activations for visualization
        self._hidden_activations = np.zeros(self.hidden_size)
        self._output_activations = np.zeros(self.n_tokens)
    
    def _init_weights(self):
        """Initialize weights with variance scaling."""
        embed_scale = np.sqrt(2.0 / self.n_tokens)
        hidden_scale = np.sqrt(2.0 / self.embed_size)
        out_scale = np.sqrt(2.0 / self.hidden_size)
        
        self.embed = np.random.randn(self.n_tokens, self.embed_size) * embed_scale
        self.W_hidden = np.random.randn(self.embed_size, self.hidden_size) * hidden_scale
        self.W_out = np.random.randn(self.hidden_size, self.embed_size) * out_scale
    
    def _init_adam_state(self):
        """Initialize AdamW optimizer state."""
        self.m_embed = np.zeros_like(self.embed)
        self.v_embed = np.zeros_like(self.embed)
        self.m_W_hidden = np.zeros_like(self.W_hidden)
        self.v_W_hidden = np.zeros_like(self.W_hidden)
        self.m_W_out = np.zeros_like(self.W_out)
        self.v_W_out = np.zeros_like(self.W_out)
        
        self.grad_embed = np.zeros_like(self.embed)
        self.grad_W_hidden = np.zeros_like(self.W_hidden)
        self.grad_W_out = np.zeros_like(self.W_out)
        self.grad_count = 0
    
    def reset_gradients(self):
        """Reset gradient accumulators."""
        self.grad_embed.fill(0)
        self.grad_W_hidden.fill(0)
        self.grad_W_out.fill(0)
        self.grad_count = 0
    
    def forward(self, a, b):
        """Forward pass through the network."""
        # Embedding lookup
        embedded_a = self.embed[a]  # (embed_size,)
        embedded_b = self.embed[b]  # (embed_size,)
        
        # Hidden projection: embedded @ W_hidden
        hidden_a = embedded_a @ self.W_hidden  # (hidden_size,)
        hidden_b = embedded_b @ self.W_hidden  # (hidden_size,)
        
        # Combine and ReLU: ReLU(hidden_a + hidden_b)
        hidden_preact = hidden_a + hidden_b
        hidden = np.maximum(0, hidden_preact)  # ReLU
        
        self._hidden_activations = hidden.copy()
        
        # Output projection: hidden @ W_out
        out = hidden @ self.W_out  # (embed_size,)
        
        # Unembedding (tied weights): out @ embed.T
        logits = out @ self.embed.T  # (n_tokens,)
        
        # Softmax
        logits_stable = logits - np.max(logits)
        exp_logits = np.exp(logits_stable)
        probs = exp_logits / np.sum(exp_logits)
        
        self._output_activations = probs.copy()
        
        return {
            'a': a, 'b': b,
            'embedded_a': embedded_a, 'embedded_b': embedded_b,
            'hidden_preact': hidden_preact, 'hidden': hidden,
            'out': out, 'probs': probs
        }
    
    def backward(self, target, cache):
        """Backward pass - accumulate gradients."""
        a, b = cache['a'], cache['b']
        embedded_a = cache['embedded_a']
        embedded_b = cache['embedded_b']
        hidden_preact = cache['hidden_preact']
        hidden = cache['hidden']
        out = cache['out']
        probs = cache['probs']
        
        # Output gradient: dL/dlogits = probs - one_hot(target)
        d_logits = probs.copy()
        d_logits[target] -= 1.0
        
        # Gradient through unembed: dL/dout and dL/dembed
        self.grad_embed += np.outer(d_logits, out)
        d_out = d_logits @ self.embed
        
        # Gradient through W_out: dL/dW_out and dL/dhidden
        self.grad_W_out += np.outer(hidden, d_out)
        d_hidden = d_out @ self.W_out.T
        
        # Gradient through ReLU
        d_hidden_preact = d_hidden * (hidden_preact > 0)
        
        # Gradient through hidden projection
        self.grad_W_hidden += np.outer(embedded_a, d_hidden_preact)
        self.grad_W_hidden += np.outer(embedded_b, d_hidden_preact)
        d_embedded = d_hidden_preact @ self.W_hidden.T
        
        # Gradient through embedding
        self.grad_embed[a] += d_embedded
        self.grad_embed[b] += d_embedded
        
        self.grad_count += 1
    
    def apply_adamw(self, batch_size):
        """Apply AdamW optimizer update."""
        if self.grad_count == 0:
            return
        
        self.adam_t += 1
        lr = self.learning_rate
        wd = self.weight_decay
        scale = 1.0 / batch_size
        
        bc1 = 1 - (self.beta1 ** self.adam_t)
        bc2 = 1 - (self.beta2 ** self.adam_t)
        
        # Update function
        def update(w, m, v, g):
            g = g * scale
            m[:] = self.beta1 * m + (1 - self.beta1) * g
            v[:] = self.beta2 * v + (1 - self.beta2) * g * g
            m_hat = m / bc1
            v_hat = v / bc2
            w[:] = w - lr * (m_hat / (np.sqrt(v_hat) + self.epsilon) + wd * w)
        
        update(self.embed, self.m_embed, self.v_embed, self.grad_embed)
        update(self.W_hidden, self.m_W_hidden, self.v_W_hidden, self.grad_W_hidden)
        update(self.W_out, self.m_W_out, self.v_W_out, self.grad_W_out)
        
        self.epoch += 1
        self.grad_count = 0
    
    def predict(self, a, b):
        """Predict the output class."""
        cache = self.forward(a, b)
        return int(np.argmax(cache['probs']))
    
    def get_activations(self):
        """Get network activations for visualization."""
        return {
            "hidden": self._hidden_activations.tolist(),
            "output": self._output_activations.tolist()
        }
    
    def reset(self):
        """Reset network to initial random state."""
        self._init_weights()
        self._init_adam_state()
        self.adam_t = 0
        self.epoch = 0


def calc_accuracy(network, dataset, sample_size=100):
    """
    Calculate prediction accuracy on a SAMPLE of the dataset.
    Sampling dramatically improves performance while giving accurate estimates.
    """
    if not dataset:
        return 0.0
    
    # Sample for speed - don't loop through entire dataset
    if len(dataset) > sample_size:
        indices = np.random.choice(len(dataset), sample_size, replace=False)
        sample = [dataset[i] for i in indices]
    else:
        sample = dataset
    
    correct = sum(1 for ex in sample if network.predict(ex['a'], ex['b']) == ex['target'])
    return correct / len(sample)


# ============================================================================
# TRAINER CLASS
# ============================================================================

class GrokTrainer:
    """Manages training with UI callbacks."""
    
    def __init__(self):
        self.network = None
        self.train_data = []
        self.test_data = []
        self.running = False
        self.grok_detected = False
        self.grok_epoch = -1
        
        # Smoothed metrics (exponential moving average)
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0
        self.ema_alpha = 0.1  # Smoothing factor (lower = smoother)
        
        # ORIGINAL parameters that work for grokking!
        self.config = {
            'n_tokens': 67,       # Original value
            'embed_size': 500,    # Original value
            'hidden_size': 64,    # Original value
            'learning_rate': 0.01,
            'weight_decay': 1.0,  # HIGH - key to grokking!
            'beta1': 0.9,
            'beta2': 0.98,
            'train_fraction': 0.4,
            'symmetric': True
        }
    
    def initialize(self, config=None):
        """Initialize network and data."""
        if config:
            # Convert JsProxy to Python dict if needed
            if hasattr(config, 'to_py'):
                config = config.to_py()
            self.config.update(config)
        
        self.network = FactoredNetwork(self.config)
        all_data = generate_all_pairs(self.config['n_tokens'], self.config['symmetric'])
        self.train_data, self.test_data = split_data(all_data, self.config['train_fraction'])
        self.grok_detected = False
        self.grok_epoch = -1
        
        # Reset smoothed metrics
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0
        
        print(f"[Trainer] Initialized: {len(self.train_data)} train, {len(self.test_data)} test")
        return len(self.train_data), len(self.test_data)
    
    async def train(self, max_epochs=50000, epochs_per_yield=3, ui_update_interval=15):
        """
        Train with periodic yields for UI responsiveness.
        
        Args:
            max_epochs: Maximum epochs to train
            epochs_per_yield: Train this many epochs before yielding (balance speed vs responsiveness)
            ui_update_interval: How often to send metrics (cheap with sampling!)
        """
        self.running = True
        epoch = 0
        train_acc = 0
        test_acc = 0
        
        while self.running and epoch < max_epochs:
            # Train multiple epochs before yielding (reduces async overhead)
            for _ in range(epochs_per_yield):
                if not self.running or epoch >= max_epochs:
                    break
                    
                # Shuffle training data
                np.random.shuffle(self.train_data)
                self.network.reset_gradients()
                
                # Process all training examples (full batch gradient descent)
                for ex in self.train_data:
                    cache = self.network.forward(ex['a'], ex['b'])
                    self.network.backward(ex['target'], cache)
                
                self.network.apply_adamw(len(self.train_data))
                epoch += 1
            
            # Yield to UI
            await asyncio.sleep(0)
            
            if not self.running:
                break
            
            # Calculate and send metrics (fast with sampling!)
            if epoch % ui_update_interval == 0 or epoch <= ui_update_interval:
                # Sample-based accuracy with larger samples for stability
                raw_train_acc = calc_accuracy(self.network, self.train_data, sample_size=200)
                raw_test_acc = calc_accuracy(self.network, self.test_data, sample_size=300)
                
                # Apply exponential moving average for smooth chart
                if epoch <= ui_update_interval:
                    # First few updates - initialize EMA to raw value
                    self.ema_train_acc = raw_train_acc
                    self.ema_test_acc = raw_test_acc
                else:
                    # EMA update: new_ema = alpha * raw + (1-alpha) * old_ema
                    self.ema_train_acc = self.ema_alpha * raw_train_acc + (1 - self.ema_alpha) * self.ema_train_acc
                    self.ema_test_acc = self.ema_alpha * raw_test_acc + (1 - self.ema_alpha) * self.ema_test_acc
                
                train_acc = self.ema_train_acc
                test_acc = self.ema_test_acc
                
                # Check for grokking (use raw values for detection to be accurate)
                if not self.grok_detected and raw_train_acc > 0.95 and raw_test_acc > 0.9:
                    self.grok_detected = True
                    self.grok_epoch = epoch
                    print(f"[Trainer] GROKKING at epoch {epoch}!")
                
                # Send progress to JS
                activations = self.network.get_activations()
                if hasattr(window, 'onGrokProgress'):
                    window.onGrokProgress({
                        'epoch': epoch,
                        'train_acc': train_acc,
                        'test_acc': test_acc,
                        'grok_detected': self.grok_detected,
                        'grok_epoch': self.grok_epoch,
                        'activations': activations,
                        # Input(2) → Hidden(64) → Output(67) for correct labels
                        'layer_sizes': [2, self.config['hidden_size'], self.config['n_tokens']]
                    })
        
        self.running = False
        if hasattr(window, 'onGrokComplete'):
            window.onGrokComplete()
    
    def stop(self):
        """Stop training."""
        self.running = False
    
    def reset(self):
        """Reset network."""
        if self.network:
            self.network.reset()
        self.grok_detected = False
        self.grok_epoch = -1
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0
    
    def predict(self, a, b):
        """Get prediction for a single input."""
        if not self.network:
            return None
        
        cache = self.network.forward(a, b)
        probs = cache['probs']
        prediction = int(np.argmax(probs))
        target = (a + b) % self.config['n_tokens']
        
        return {
            'a': a, 'b': b,
            'target': target,
            'prediction': prediction,
            'correct': prediction == target,
            'confidence': float(probs[prediction])
        }


# Global trainer instance
trainer = GrokTrainer()


# ============================================================================
# API FUNCTIONS (called from JS)
# ============================================================================

def grok_initialize(config=None):
    """Initialize the trainer."""
    if config and hasattr(config, 'to_py'):
        config = config.to_py()
    return trainer.initialize(config)


async def grok_train(max_epochs=50000):
    """Start training."""
    await trainer.train(max_epochs)


def grok_stop():
    """Stop training."""
    trainer.stop()


def grok_reset():
    """Reset network."""
    trainer.reset()


def grok_predict(a, b):
    """Get a prediction."""
    return trainer.predict(a, b)


# Signal ready
print("[Grokking] NumPy-vectorized trainer loaded")
if hasattr(window, 'onGrokReady'):
    window.onGrokReady()
