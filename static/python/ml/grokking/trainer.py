"""
Grokking Neural Network Trainer - Fully Batched NumPy

All forward/backward passes are batched matrix multiplies across the
entire training set. No per-example Python loops in the hot path.
"""

import numpy as np
import asyncio
from js import window


def generate_all_pairs(mod, symmetric=True):
    """Generate all pairs for modular addition: (a + b) mod p."""
    data = []
    for a in range(mod):
        for b in range(mod):
            if symmetric and a > b:
                continue
            data.append((a, b, (a + b) % mod))
    return data


class FactoredNetwork:
    """
    Factored MLP for modular addition grokking — fully batched.

    Architecture: Embed(tied) → Hidden(tied) → ReLU → Out → Unembed(tied)
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

        self._hidden_activations = np.zeros(self.hidden_size)
        self._output_activations = np.zeros(self.n_tokens)

    def _init_weights(self):
        embed_scale = np.sqrt(2.0 / self.n_tokens)
        hidden_scale = np.sqrt(2.0 / self.embed_size)
        out_scale = np.sqrt(2.0 / self.hidden_size)
        self.embed = np.random.randn(self.n_tokens, self.embed_size) * embed_scale
        self.W_hidden = np.random.randn(self.embed_size, self.hidden_size) * hidden_scale
        self.W_out = np.random.randn(self.hidden_size, self.embed_size) * out_scale

    def _init_adam_state(self):
        self.m_embed = np.zeros_like(self.embed)
        self.v_embed = np.zeros_like(self.embed)
        self.m_W_hidden = np.zeros_like(self.W_hidden)
        self.v_W_hidden = np.zeros_like(self.W_hidden)
        self.m_W_out = np.zeros_like(self.W_out)
        self.v_W_out = np.zeros_like(self.W_out)

    # ------------------------------------------------------------------
    # Batched forward + backward (entire dataset in one call)
    # ------------------------------------------------------------------

    def train_batch(self, a_arr, b_arr, t_arr):
        """
        Full forward + backward + AdamW update for one epoch.
        All ops are batched numpy — no Python per-example loop.

        a_arr, b_arr, t_arr: int32 arrays of shape (N,)
        """
        N = len(a_arr)
        embed = self.embed
        W_h = self.W_hidden
        W_o = self.W_out

        # --- Forward ---
        emb_a = embed[a_arr]          # (N, E)
        emb_b = embed[b_arr]          # (N, E)
        h_pre = (emb_a + emb_b) @ W_h  # (N, H)
        h = np.maximum(0, h_pre)      # ReLU  (N, H)
        out = h @ W_o                 # (N, E)
        logits = out @ embed.T        # (N, T)

        # Stable softmax
        logits -= logits.max(axis=1, keepdims=True)
        exp_l = np.exp(logits)
        probs = exp_l / exp_l.sum(axis=1, keepdims=True)  # (N, T)

        # --- Backward ---
        d_logits = probs.copy()                       # (N, T)
        d_logits[np.arange(N), t_arr] -= 1.0          # cross-entropy grad

        # Unembed grads
        g_embed = d_logits.T @ out                    # (T, E)
        d_out = d_logits @ embed                      # (N, E)

        # W_out grads
        g_W_out = h.T @ d_out                         # (H, E)

        # Hidden grads
        d_h = d_out @ W_o.T                           # (N, H)
        d_h_pre = d_h * (h_pre > 0)                   # ReLU mask  (N, H)

        # W_hidden grads
        g_W_hidden = (emb_a + emb_b).T @ d_h_pre     # (E, H)

        # Embedding grads (from input side)
        d_emb = d_h_pre @ W_h.T                       # (N, E)
        np.add.at(g_embed, a_arr, d_emb)
        np.add.at(g_embed, b_arr, d_emb)

        # --- AdamW update ---
        self.adam_t += 1
        lr = self.learning_rate
        wd = self.weight_decay
        scale = 1.0 / N
        bc1 = 1 - self.beta1 ** self.adam_t
        bc2 = 1 - self.beta2 ** self.adam_t

        def update(w, m, v, g):
            g = g * scale
            m[:] = self.beta1 * m + (1 - self.beta1) * g
            v[:] = self.beta2 * v + (1 - self.beta2) * g * g
            m_hat = m / bc1
            v_hat = v / bc2
            w[:] = w - lr * (m_hat / (np.sqrt(v_hat) + self.epsilon) + wd * w)

        update(self.embed,    self.m_embed,    self.v_embed,    g_embed)
        update(self.W_hidden, self.m_W_hidden, self.v_W_hidden, g_W_hidden)
        update(self.W_out,    self.m_W_out,    self.v_W_out,    g_W_out)

        self.epoch += 1
        return probs  # for accuracy calc if needed

    # ------------------------------------------------------------------
    # Batched inference (for accuracy)
    # ------------------------------------------------------------------

    def predict_batch(self, a_arr, b_arr):
        """Batched prediction — returns int array of predicted classes."""
        emb_a = self.embed[a_arr]
        emb_b = self.embed[b_arr]
        h = np.maximum(0, (emb_a + emb_b) @ self.W_hidden)
        logits = (h @ self.W_out) @ self.embed.T
        return np.argmax(logits, axis=1)

    # ------------------------------------------------------------------
    # Single-example (for UI predict button)
    # ------------------------------------------------------------------

    def predict(self, a, b):
        emb_a = self.embed[a]
        emb_b = self.embed[b]
        h = np.maximum(0, (emb_a + emb_b) @ self.W_hidden)
        logits = (h @ self.W_out) @ self.embed.T
        return int(np.argmax(logits))

    def save_activations(self, a, b):
        """Run one forward pass and store activations for viz."""
        emb_a = self.embed[a]
        emb_b = self.embed[b]
        h = np.maximum(0, (emb_a + emb_b) @ self.W_hidden)
        logits = (h @ self.W_out) @ self.embed.T
        logits_stable = logits - np.max(logits)
        exp_l = np.exp(logits_stable)
        probs = exp_l / exp_l.sum()
        self._hidden_activations = h.copy()
        self._output_activations = probs.copy()

    def get_activations(self):
        return {
            "hidden": self._hidden_activations.tolist(),
            "output": self._output_activations.tolist()
        }

    def reset(self):
        self._init_weights()
        self._init_adam_state()
        self.adam_t = 0
        self.epoch = 0


def calc_accuracy_batched(network, a_arr, b_arr, t_arr, sample_size=200):
    """Batched accuracy — single matrix multiply, no Python loop."""
    n = len(a_arr)
    if n == 0:
        return 0.0
    if n > sample_size:
        idx = np.random.choice(n, sample_size, replace=False)
        a_s, b_s, t_s = a_arr[idx], b_arr[idx], t_arr[idx]
    else:
        a_s, b_s, t_s = a_arr, b_arr, t_arr
    preds = network.predict_batch(a_s, b_s)
    return float(np.mean(preds == t_s))


# ============================================================================
# TRAINER
# ============================================================================

class GrokTrainer:
    def __init__(self):
        self.network = None
        self.running = False
        self.grok_detected = False
        self.grok_epoch = -1
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0
        self.ema_alpha = 0.1

        self.config = {
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

    def initialize(self, config=None):
        if config:
            if hasattr(config, 'to_py'):
                config = config.to_py()
            self.config.update(config)

        self.network = FactoredNetwork(self.config)
        all_data = generate_all_pairs(self.config['n_tokens'], self.config['symmetric'])

        np.random.shuffle(all_data)
        split_idx = int(len(all_data) * self.config['train_fraction'])
        train_list = all_data[:split_idx]
        test_list = all_data[split_idx:]

        self.train_a = np.array([t[0] for t in train_list], dtype=np.int32)
        self.train_b = np.array([t[1] for t in train_list], dtype=np.int32)
        self.train_t = np.array([t[2] for t in train_list], dtype=np.int32)
        self.test_a = np.array([t[0] for t in test_list], dtype=np.int32)
        self.test_b = np.array([t[1] for t in test_list], dtype=np.int32)
        self.test_t = np.array([t[2] for t in test_list], dtype=np.int32)
        self.n_train = len(train_list)
        self.n_test = len(test_list)

        self.grok_detected = False
        self.grok_epoch = -1
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0

        print(f"[Trainer] Initialized: {self.n_train} train, {self.n_test} test")
        return self.n_train, self.n_test

    async def train(self, max_epochs=50000, epochs_per_yield=10, ui_update_interval=100):
        """
        Fully batched training loop.

        epochs_per_yield: epochs between asyncio yields (higher = faster, less responsive)
        ui_update_interval: epochs between JS UI updates
        """
        self.running = True
        epoch = 0

        while self.running and epoch < max_epochs:
            for _ in range(epochs_per_yield):
                if not self.running or epoch >= max_epochs:
                    break

                # Shuffle training data order
                perm = np.random.permutation(self.n_train)
                a_s = self.train_a[perm]
                b_s = self.train_b[perm]
                t_s = self.train_t[perm]

                # One full epoch = one batched call (no Python loop)
                self.network.train_batch(a_s, b_s, t_s)
                epoch += 1

            await asyncio.sleep(0)

            if not self.running:
                break

            if epoch % ui_update_interval == 0 or epoch <= ui_update_interval:
                raw_train_acc = calc_accuracy_batched(
                    self.network, self.train_a, self.train_b, self.train_t, 200)
                raw_test_acc = calc_accuracy_batched(
                    self.network, self.test_a, self.test_b, self.test_t, 300)

                if epoch <= ui_update_interval:
                    self.ema_train_acc = raw_train_acc
                    self.ema_test_acc = raw_test_acc
                else:
                    self.ema_train_acc = self.ema_alpha * raw_train_acc + (1 - self.ema_alpha) * self.ema_train_acc
                    self.ema_test_acc = self.ema_alpha * raw_test_acc + (1 - self.ema_alpha) * self.ema_test_acc

                if not self.grok_detected and raw_train_acc > 0.95 and raw_test_acc > 0.9:
                    self.grok_detected = True
                    self.grok_epoch = epoch
                    print(f"[Trainer] GROKKING at epoch {epoch}!")

                # Save activations from a representative example
                self.network.save_activations(
                    int(self.train_a[0]), int(self.train_b[0]))
                activations = self.network.get_activations()

                if hasattr(window, 'onGrokProgress'):
                    window.onGrokProgress({
                        'epoch': epoch,
                        'train_acc': self.ema_train_acc,
                        'test_acc': self.ema_test_acc,
                        'grok_detected': self.grok_detected,
                        'grok_epoch': self.grok_epoch,
                        'activations': activations,
                        'layer_sizes': [2, self.config['hidden_size'], self.config['n_tokens']]
                    })

        self.running = False
        if hasattr(window, 'onGrokComplete'):
            window.onGrokComplete()

    def stop(self):
        self.running = False

    def reset(self):
        if self.network:
            self.network.reset()
        self.grok_detected = False
        self.grok_epoch = -1
        self.ema_train_acc = 0.0
        self.ema_test_acc = 0.0

    def predict(self, a, b):
        if not self.network:
            return None
        prediction = self.network.predict(a, b)
        target = (a + b) % self.config['n_tokens']
        return {
            'a': a, 'b': b,
            'target': target,
            'prediction': prediction,
            'correct': prediction == target,
        }


trainer = GrokTrainer()


def grok_initialize(config=None):
    if config and hasattr(config, 'to_py'):
        config = config.to_py()
    return trainer.initialize(config)


async def grok_train(max_epochs=50000):
    await trainer.train(max_epochs)


def grok_stop():
    trainer.stop()


def grok_reset():
    trainer.reset()


def grok_predict(a, b):
    return trainer.predict(a, b)


print("[Grokking] Fully batched trainer loaded")
if hasattr(window, 'onGrokReady'):
    window.onGrokReady()
