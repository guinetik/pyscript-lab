"""
Grokking Neural Network - Web Worker (Self-contained)

This module runs in a PyScript Web Worker (background thread) to perform
neural network training without blocking the main thread UI.

All code is included in this single file since workers run in isolation
and cannot import from the main thread's fetched modules.
"""

import math
import random

# ============================================================================
# UTILITIES
# ============================================================================

def shuffle(array):
    """Fisher-Yates shuffle - in-place array randomization."""
    for i in range(len(array) - 1, 0, -1):
        j = random.randint(0, i)
        array[i], array[j] = array[j], array[i]
    return array


def generate_all_pairs(mod, symmetric=True):
    """
    Generate all pairs dataset for modular addition: (a + b) mod p.
    
    Args:
        mod: Modulus value (number of possible outputs)
        symmetric: If True, only use pairs where a <= b
    """
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
    shuffled = dataset.copy()
    shuffle(shuffled)
    split_idx = int(len(shuffled) * train_fraction)
    return shuffled[:split_idx], shuffled[split_idx:]


def calc_accuracy(network, dataset):
    """Calculate prediction accuracy on a dataset."""
    if not dataset:
        return 0.0
    correct = 0
    for example in dataset:
        prediction = network.predict(example['a'], example['b'])
        if prediction == example['target']:
            correct += 1
    return correct / len(dataset)


# ============================================================================
# FACTORED NETWORK
# ============================================================================

class FactoredNetwork:
    """
    Factored Neural Network for modular addition grokking.
    
    Architecture:
        Input (a, b) → Embed(tied) → Hidden(tied, no bias) → ReLU(h_a + h_b) → Out → Unembed(tied)
    
    Key features:
        - Tied embeddings (same matrix for input and output)
        - Tied hidden projection (same weights for both inputs)
        - No biases in linear layers
        - ReLU after element-wise addition
        - AdamW optimizer with HIGH weight decay (key to grokking!)
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
        
        # Initialize weights with variance scaling
        embed_scale = math.sqrt(2.0 / self.n_tokens)
        hidden_scale = math.sqrt(2.0 / self.embed_size)
        out_scale = math.sqrt(2.0 / self.hidden_size)
        
        # Weight matrices
        self.embed = self._init_matrix(self.n_tokens, self.embed_size, embed_scale)
        self.W_hidden = self._init_matrix(self.embed_size, self.hidden_size, hidden_scale)
        self.W_out = self._init_matrix(self.hidden_size, self.embed_size, out_scale)
        
        # Activations for visualization
        self._hidden_activations = [0.0] * self.hidden_size
        self._output_activations = [0.0] * self.n_tokens
        
        # Initialize AdamW state
        self._init_adam_state()
        self.adam_t = 0
        self.epoch = 0
    
    def _init_matrix(self, rows, cols, scale):
        return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
    
    def _init_adam_state(self):
        # Moments for embed
        self.m_embed = [[0.0] * self.embed_size for _ in range(self.n_tokens)]
        self.v_embed = [[0.0] * self.embed_size for _ in range(self.n_tokens)]
        # Moments for W_hidden
        self.m_W_hidden = [[0.0] * self.hidden_size for _ in range(self.embed_size)]
        self.v_W_hidden = [[0.0] * self.hidden_size for _ in range(self.embed_size)]
        # Moments for W_out
        self.m_W_out = [[0.0] * self.embed_size for _ in range(self.hidden_size)]
        self.v_W_out = [[0.0] * self.embed_size for _ in range(self.hidden_size)]
        # Gradient accumulators
        self.grad_embed = [[0.0] * self.embed_size for _ in range(self.n_tokens)]
        self.grad_W_hidden = [[0.0] * self.hidden_size for _ in range(self.embed_size)]
        self.grad_W_out = [[0.0] * self.embed_size for _ in range(self.hidden_size)]
        self.grad_count = 0
    
    def reset_gradients(self):
        for i in range(self.n_tokens):
            for j in range(self.embed_size):
                self.grad_embed[i][j] = 0.0
        for i in range(self.embed_size):
            for j in range(self.hidden_size):
                self.grad_W_hidden[i][j] = 0.0
        for i in range(self.hidden_size):
            for j in range(self.embed_size):
                self.grad_W_out[i][j] = 0.0
        self.grad_count = 0
    
    def forward(self, a, b):
        """Forward pass through the network."""
        # 1. Embedding lookup
        embedded_a = self.embed[a]
        embedded_b = self.embed[b]
        
        # 2. Hidden projection
        hidden_a = [0.0] * self.hidden_size
        hidden_b = [0.0] * self.hidden_size
        for j in range(self.hidden_size):
            sum_a = sum_b = 0.0
            for i in range(self.embed_size):
                sum_a += embedded_a[i] * self.W_hidden[i][j]
                sum_b += embedded_b[i] * self.W_hidden[i][j]
            hidden_a[j] = sum_a
            hidden_b[j] = sum_b
        
        # 3. Combine and ReLU
        hidden_preact = [0.0] * self.hidden_size
        hidden = [0.0] * self.hidden_size
        for j in range(self.hidden_size):
            hidden_preact[j] = hidden_a[j] + hidden_b[j]
            hidden[j] = max(0.0, hidden_preact[j])
        
        self._hidden_activations = hidden.copy()
        
        # 4. Output projection
        out = [0.0] * self.embed_size
        for i in range(self.hidden_size):
            h = hidden[i]
            for j in range(self.embed_size):
                out[j] += h * self.W_out[i][j]
        
        # 5. Unembedding (tied weights)
        logits = [0.0] * self.n_tokens
        for j in range(self.n_tokens):
            sum_val = 0.0
            for i in range(self.embed_size):
                sum_val += out[i] * self.embed[j][i]
            logits[j] = sum_val
        
        # 6. Softmax
        probs = self._softmax(logits)
        self._output_activations = probs.copy()
        
        return {
            'a': a, 'b': b,
            'embedded_a': embedded_a, 'embedded_b': embedded_b,
            'hidden_a': hidden_a, 'hidden_b': hidden_b,
            'hidden_preact': hidden_preact, 'hidden': hidden,
            'out': out, 'logits': logits, 'probs': probs
        }
    
    def _softmax(self, logits):
        max_val = max(logits)
        exp_vals = [math.exp(x - max_val) for x in logits]
        sum_exp = sum(exp_vals)
        return [e / sum_exp for e in exp_vals]
    
    def backward(self, target, cache):
        """Backward pass - accumulate gradients."""
        a, b = cache['a'], cache['b']
        embedded_a, embedded_b = cache['embedded_a'], cache['embedded_b']
        hidden_preact, hidden = cache['hidden_preact'], cache['hidden']
        out, probs = cache['out'], cache['probs']
        
        # 1. Output gradient
        d_logits = probs.copy()
        d_logits[target] -= 1.0
        
        # 2. Gradient through unembed
        for j in range(self.n_tokens):
            dL = d_logits[j]
            for i in range(self.embed_size):
                self.grad_embed[j][i] += dL * out[i]
        
        d_out = [0.0] * self.embed_size
        for j in range(self.n_tokens):
            dL = d_logits[j]
            for i in range(self.embed_size):
                d_out[i] += dL * self.embed[j][i]
        
        # 3. Gradient through W_out
        d_hidden = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            sum_val = 0.0
            for j in range(self.embed_size):
                self.grad_W_out[i][j] += hidden[i] * d_out[j]
                sum_val += d_out[j] * self.W_out[i][j]
            d_hidden[i] = sum_val
        
        # 4. Gradient through ReLU
        d_hidden_preact = [d_hidden[j] if hidden_preact[j] > 0 else 0.0 for j in range(self.hidden_size)]
        
        # 5. Gradient through hidden projection
        for i in range(self.embed_size):
            for j in range(self.hidden_size):
                self.grad_W_hidden[i][j] += embedded_a[i] * d_hidden_preact[j]
                self.grad_W_hidden[i][j] += embedded_b[i] * d_hidden_preact[j]
        
        d_embedded = [0.0] * self.embed_size
        for i in range(self.embed_size):
            for j in range(self.hidden_size):
                d_embedded[i] += d_hidden_preact[j] * self.W_hidden[i][j]
        
        # 6. Gradient through embedding
        for i in range(self.embed_size):
            self.grad_embed[a][i] += d_embedded[i]
            self.grad_embed[b][i] += d_embedded[i]
        
        self.grad_count += 1
    
    def apply_adamw(self, batch_size):
        """Apply AdamW optimizer update."""
        if self.grad_count == 0:
            return
        
        self.adam_t += 1
        lr, wd = self.learning_rate, self.weight_decay
        scale = 1.0 / batch_size
        bc1 = 1 - (self.beta1 ** self.adam_t)
        bc2 = 1 - (self.beta2 ** self.adam_t)
        
        # Update embed
        for i in range(self.n_tokens):
            for j in range(self.embed_size):
                g = self.grad_embed[i][j] * scale
                self.m_embed[i][j] = self.beta1 * self.m_embed[i][j] + (1 - self.beta1) * g
                self.v_embed[i][j] = self.beta2 * self.v_embed[i][j] + (1 - self.beta2) * g * g
                m_hat = self.m_embed[i][j] / bc1
                v_hat = self.v_embed[i][j] / bc2
                self.embed[i][j] -= lr * (m_hat / (math.sqrt(v_hat) + self.epsilon) + wd * self.embed[i][j])
        
        # Update W_hidden
        for i in range(self.embed_size):
            for j in range(self.hidden_size):
                g = self.grad_W_hidden[i][j] * scale
                self.m_W_hidden[i][j] = self.beta1 * self.m_W_hidden[i][j] + (1 - self.beta1) * g
                self.v_W_hidden[i][j] = self.beta2 * self.v_W_hidden[i][j] + (1 - self.beta2) * g * g
                m_hat = self.m_W_hidden[i][j] / bc1
                v_hat = self.v_W_hidden[i][j] / bc2
                self.W_hidden[i][j] -= lr * (m_hat / (math.sqrt(v_hat) + self.epsilon) + wd * self.W_hidden[i][j])
        
        # Update W_out
        for i in range(self.hidden_size):
            for j in range(self.embed_size):
                g = self.grad_W_out[i][j] * scale
                self.m_W_out[i][j] = self.beta1 * self.m_W_out[i][j] + (1 - self.beta1) * g
                self.v_W_out[i][j] = self.beta2 * self.v_W_out[i][j] + (1 - self.beta2) * g * g
                m_hat = self.m_W_out[i][j] / bc1
                v_hat = self.v_W_out[i][j] / bc2
                self.W_out[i][j] -= lr * (m_hat / (math.sqrt(v_hat) + self.epsilon) + wd * self.W_out[i][j])
        
        self.epoch += 1
        self.grad_count = 0
    
    def predict(self, a, b):
        """Predict the output class."""
        cache = self.forward(a, b)
        probs = cache['probs']
        return max(range(len(probs)), key=lambda i: probs[i])
    
    def get_activations(self):
        """Get network activations for visualization."""
        return {
            "hidden": self._hidden_activations.copy(),
            "output": self._output_activations.copy()
        }
    
    def reset(self):
        """Reset network to initial random state."""
        embed_scale = math.sqrt(2.0 / self.n_tokens)
        hidden_scale = math.sqrt(2.0 / self.embed_size)
        out_scale = math.sqrt(2.0 / self.hidden_size)
        self.embed = self._init_matrix(self.n_tokens, self.embed_size, embed_scale)
        self.W_hidden = self._init_matrix(self.embed_size, self.hidden_size, hidden_scale)
        self.W_out = self._init_matrix(self.hidden_size, self.embed_size, out_scale)
        self._init_adam_state()
        self.adam_t = 0
        self.epoch = 0


# ============================================================================
# WORKER API
# ============================================================================

# Global state
network = None
train_data = []
test_data = []
epoch = 0
grok_detected = False
grok_epoch = -1

DEFAULT_CONFIG = {
    'n_tokens': 67,
    'embed_size': 500,
    'hidden_size': 64,
    'learning_rate': 0.01,
    'weight_decay': 1.0,
    'beta1': 0.9,
    'beta2': 0.98,
    'train_fraction': 0.4,
    'symmetric': True
}


def initialize(config=None):
    """Initialize the network and generate training/test data."""
    global network, train_data, test_data, epoch, grok_detected, grok_epoch
    
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    network = FactoredNetwork(cfg)
    all_data = generate_all_pairs(cfg['n_tokens'], cfg['symmetric'])
    train_data, test_data = split_data(all_data, cfg['train_fraction'])
    epoch = 0
    grok_detected = False
    grok_epoch = -1
    
    print(f"[Worker] Initialized: {len(train_data)} train, {len(test_data)} test samples")
    
    return {
        "status": "ready",
        "train_size": len(train_data),
        "test_size": len(test_data),
        "n_tokens": cfg['n_tokens'],
        "hidden_size": cfg['hidden_size']
    }


def train_batch(epochs_per_batch=10):
    """Train the network for a batch of epochs."""
    global epoch, grok_detected, grok_epoch
    
    if network is None:
        return {"error": "Network not initialized"}
    
    for _ in range(epochs_per_batch):
        shuffled_train = shuffle(train_data.copy())
        network.reset_gradients()
        
        for example in shuffled_train:
            cache = network.forward(example['a'], example['b'])
            network.backward(example['target'], cache)
        
        network.apply_adamw(len(shuffled_train))
        epoch += 1
    
    train_acc = calc_accuracy(network, train_data)
    test_acc = calc_accuracy(network, test_data)
    
    if not grok_detected and train_acc > 0.95 and test_acc > 0.9:
        grok_detected = True
        grok_epoch = epoch
        print(f"[Worker] GROKKING DETECTED at epoch {epoch}!")
    
    activations = network.get_activations()
    
    return {
        "epoch": epoch,
        "train_acc": float(train_acc),
        "test_acc": float(test_acc),
        "grok_detected": grok_detected,
        "grok_epoch": grok_epoch,
        "activations": activations,
        "layer_sizes": [network.n_tokens * 2, network.hidden_size, network.n_tokens]
    }


def get_prediction(a, b):
    """Get network prediction for a single input pair."""
    if network is None:
        return {"error": "Network not initialized"}
    
    cache = network.forward(a, b)
    probs = cache['probs']
    prediction = max(range(len(probs)), key=lambda i: probs[i])
    target = (a + b) % network.n_tokens
    
    return {
        "a": a, "b": b,
        "target": target,
        "prediction": prediction,
        "correct": prediction == target,
        "confidence": float(probs[prediction])
    }


def get_state():
    """Get current training state."""
    if network is None:
        return {"status": "not_initialized"}
    return {
        "status": "ready",
        "epoch": epoch,
        "grok_detected": grok_detected,
        "grok_epoch": grok_epoch
    }


def reset():
    """Reset the network to initial state."""
    global epoch, grok_detected, grok_epoch
    if network is not None:
        network.reset()
        epoch = 0
        grok_detected = False
        grok_epoch = -1
    return {"status": "reset"}


def stop():
    """Stop training placeholder."""
    return {"status": "stopped"}


# Export functions for PyScript worker
__export__ = ["initialize", "train_batch", "get_prediction", "get_state", "reset", "stop"]
