"""
Factored MLP for Grokking - Based on Google's Implementation

Architecture:
    Input (a, b) → Embed(tied) → Hidden(tied, no bias) → ReLU(h_a + h_b) → Out → Unembed(tied transpose)

Key features:
    - Tied embeddings (same matrix for input a, b, and output)
    - Tied hidden projection (same weights for both inputs)
    - No biases in linear layers
    - Hidden = ReLU(hidden_a + hidden_b) - element-wise addition BEFORE ReLU
    - AdamW optimizer with HIGH weight decay (the key to grokking!)

Reference: https://pair.withgoogle.com/explorables/grokking/
"""

import math
import random


class FactoredNetwork:
    """
    Factored Neural Network for modular addition grokking.
    
    This architecture is specifically designed to demonstrate the grokking
    phenomenon where the network first memorizes training data, then
    suddenly generalizes to test data after many more epochs.
    """
    
    def __init__(self, config):
        """
        Initialize the network.
        
        Args:
            config: Dictionary containing:
                - n_tokens: Modulus value (number of possible outputs)
                - embed_size: Embedding dimension
                - hidden_size: Hidden layer size
                - learning_rate: Learning rate for AdamW
                - weight_decay: Weight decay (L2 regularization) - KEY for grokking!
                - beta1: AdamW beta1 (default 0.9)
                - beta2: AdamW beta2 (default 0.98)
        """
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
        
        # Embedding matrix: (n_tokens, embed_size) - TIED for input and output
        self.embed = self._init_matrix(self.n_tokens, self.embed_size, embed_scale)
        
        # Hidden projection: (embed_size, hidden_size) - TIED for both inputs, NO BIAS
        self.W_hidden = self._init_matrix(self.embed_size, self.hidden_size, hidden_scale)
        
        # Output projection: (hidden_size, embed_size) - NO BIAS
        self.W_out = self._init_matrix(self.hidden_size, self.embed_size, out_scale)
        
        # Store activations for visualization
        self._hidden_activations = [0.0] * self.hidden_size
        self._output_activations = [0.0] * self.n_tokens
        
        # Initialize AdamW optimizer state
        self._init_adam_state()
        self.adam_t = 0
        
        # Epoch counter
        self.epoch = 0
    
    def _init_matrix(self, rows, cols, scale):
        """Initialize a matrix with variance scaling."""
        return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]
    
    def _init_adam_state(self):
        """Initialize AdamW optimizer state (first and second moments)."""
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
        """Reset gradient accumulators."""
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
        """
        Forward pass.
        
        Args:
            a: First input token (0 to n_tokens-1)
            b: Second input token (0 to n_tokens-1)
            
        Returns:
            dict: Cache containing intermediate values for backward pass
        """
        # 1. Embedding lookup (one-hot @ embed = just selecting rows)
        embedded_a = self.embed[a]
        embedded_b = self.embed[b]
        
        # 2. Hidden projection: embedded @ W_hidden
        hidden_a = [0.0] * self.hidden_size
        hidden_b = [0.0] * self.hidden_size
        
        for j in range(self.hidden_size):
            sum_a = 0.0
            sum_b = 0.0
            for i in range(self.embed_size):
                sum_a += embedded_a[i] * self.W_hidden[i][j]
                sum_b += embedded_b[i] * self.W_hidden[i][j]
            hidden_a[j] = sum_a
            hidden_b[j] = sum_b
        
        # 3. Combine and ReLU: ReLU(hidden_a + hidden_b)
        hidden_preact = [0.0] * self.hidden_size
        hidden = [0.0] * self.hidden_size
        
        for j in range(self.hidden_size):
            hidden_preact[j] = hidden_a[j] + hidden_b[j]
            hidden[j] = max(0.0, hidden_preact[j])  # ReLU
        
        # Store for visualization
        self._hidden_activations = hidden.copy()
        
        # 4. Output projection: hidden @ W_out
        out = [0.0] * self.embed_size
        for i in range(self.hidden_size):
            h = hidden[i]
            for j in range(self.embed_size):
                out[j] += h * self.W_out[i][j]
        
        # 5. Unembedding: out @ embed.T (tied weights!)
        logits = [0.0] * self.n_tokens
        for j in range(self.n_tokens):
            sum_val = 0.0
            for i in range(self.embed_size):
                sum_val += out[i] * self.embed[j][i]
            logits[j] = sum_val
        
        # 6. Softmax
        probs = self._softmax(logits)
        self._output_activations = probs.copy()
        
        # Cache for backward pass
        return {
            'a': a,
            'b': b,
            'embedded_a': embedded_a,
            'embedded_b': embedded_b,
            'hidden_a': hidden_a,
            'hidden_b': hidden_b,
            'hidden_preact': hidden_preact,
            'hidden': hidden,
            'out': out,
            'logits': logits,
            'probs': probs
        }
    
    def _softmax(self, logits):
        """Stable softmax computation."""
        max_val = max(logits)
        
        exp_vals = [math.exp(x - max_val) for x in logits]
        sum_exp = sum(exp_vals)
        
        return [e / sum_exp for e in exp_vals]
    
    def backward(self, target, cache):
        """
        Backward pass - accumulate gradients.
        
        Args:
            target: Target class (0 to n_tokens-1)
            cache: Cache from forward pass
        """
        a = cache['a']
        b = cache['b']
        embedded_a = cache['embedded_a']
        embedded_b = cache['embedded_b']
        hidden_preact = cache['hidden_preact']
        hidden = cache['hidden']
        out = cache['out']
        probs = cache['probs']
        
        # 1. Output gradient: dL/dlogits = probs - one_hot(target)
        d_logits = probs.copy()
        d_logits[target] -= 1.0
        
        # 2. Gradient through unembed: dL/dout = dLogits @ embed
        #    Also accumulate dL/dembed from unembed
        
        # Accumulate grad_embed (from output)
        for j in range(self.n_tokens):
            dL = d_logits[j]
            for i in range(self.embed_size):
                self.grad_embed[j][i] += dL * out[i]
        
        # Compute d_out
        d_out = [0.0] * self.embed_size
        for j in range(self.n_tokens):
            dL = d_logits[j]
            for i in range(self.embed_size):
                d_out[i] += dL * self.embed[j][i]
        
        # 3. Gradient through W_out: dL/dW_out = hidden.T @ d_out
        #    dL/dhidden = d_out @ W_out.T
        d_hidden = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            sum_val = 0.0
            for j in range(self.embed_size):
                self.grad_W_out[i][j] += hidden[i] * d_out[j]
                sum_val += d_out[j] * self.W_out[i][j]
            d_hidden[i] = sum_val
        
        # 4. Gradient through ReLU
        d_hidden_preact = [0.0] * self.hidden_size
        for j in range(self.hidden_size):
            d_hidden_preact[j] = d_hidden[j] if hidden_preact[j] > 0 else 0.0
        
        # 5. Gradient through hidden projection (tied for both a and b)
        d_embedded_a = [0.0] * self.embed_size
        d_embedded_b = [0.0] * self.embed_size
        
        for i in range(self.embed_size):
            sum_val = 0.0
            for j in range(self.hidden_size):
                # Accumulate W_hidden gradient (from both a and b paths)
                self.grad_W_hidden[i][j] += embedded_a[i] * d_hidden_preact[j]
                self.grad_W_hidden[i][j] += embedded_b[i] * d_hidden_preact[j]
                sum_val += d_hidden_preact[j] * self.W_hidden[i][j]
            d_embedded_a[i] = sum_val
            d_embedded_b[i] = sum_val
        
        # 6. Gradient through embedding lookup (accumulate at token indices)
        for i in range(self.embed_size):
            self.grad_embed[a][i] += d_embedded_a[i]
            self.grad_embed[b][i] += d_embedded_b[i]
        
        self.grad_count += 1
    
    def apply_adamw(self, batch_size):
        """
        Apply AdamW optimizer update.
        
        Args:
            batch_size: Batch size for gradient averaging
        """
        if self.grad_count == 0:
            return
        
        self.adam_t += 1
        lr = self.learning_rate
        wd = self.weight_decay
        scale = 1.0 / batch_size
        
        # Bias correction
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
                # AdamW: decoupled weight decay
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
        """
        Predict the output class.
        
        Args:
            a: First input token
            b: Second input token
            
        Returns:
            int: Predicted class
        """
        cache = self.forward(a, b)
        probs = cache['probs']
        
        max_idx = 0
        max_val = probs[0]
        for i in range(1, len(probs)):
            if probs[i] > max_val:
                max_val = probs[i]
                max_idx = i
        
        return max_idx
    
    def get_activations(self):
        """
        Get network activations for visualization.
        
        Returns:
            dict: Layer activations as lists (serializable)
        """
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
