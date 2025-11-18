"""
Mock browser APIs for headless Python execution.

This module provides stub implementations of PyScript/browser APIs
so the neuroevolution code can run without a browser.
"""

import sys
from typing import Any, Callable
from unittest.mock import MagicMock


class MockConsole:
    """Mock browser console for logging"""

    @staticmethod
    def log(*args, **kwargs):
        print("[console.log]", *args)

    @staticmethod
    def error(*args, **kwargs):
        print("[console.error]", *args, file=sys.stderr)

    @staticmethod
    def warn(*args, **kwargs):
        print("[console.warn]", *args)

    @staticmethod
    def info(*args, **kwargs):
        print("[console.info]", *args)


class MockWindow:
    """Mock browser window object"""

    def __init__(self):
        self._callbacks = {}

    def __setattr__(self, name: str, value: Any):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._callbacks[name] = value

    def __getattr__(self, name: str):
        return self._callbacks.get(name, MagicMock())


class MockDocument:
    """Mock browser document object"""

    def querySelector(self, selector: str):
        return MagicMock()

    def getElementById(self, element_id: str):
        return MagicMock()


# Mock Pyodide FFI functions
def create_proxy(func: Callable) -> Callable:
    """Mock create_proxy - just returns the function as-is"""
    return func


def to_js(obj: Any, **kwargs) -> Any:
    """Mock to_js conversion - returns object as-is"""
    return obj


# Mock setTimeout
def setTimeout(callback: Callable, delay: int):
    """Mock setTimeout - executes immediately in headless mode"""
    # For headless, we can either skip or execute immediately
    # callback()  # Uncomment to execute immediately
    pass


# Create module-level instances
console = MockConsole()
window = MockWindow()
document = MockDocument()


# Mock the 'js' module
class MockJSModule:
    """Mock JavaScript module for imports"""
    console = console
    window = window
    document = document
    setTimeout = setTimeout
    Object = type('Object', (), {
        'fromEntries': lambda x: dict(x) if not isinstance(x, dict) else x
    })


# Mock the 'pyodide.ffi' module
class MockPyodideFfi:
    """Mock Pyodide FFI module"""
    create_proxy = staticmethod(create_proxy)
    to_js = staticmethod(to_js)


# Install mocks into sys.modules BEFORE imports
def install_mocks():
    """Install mock modules into sys.modules"""
    sys.modules['js'] = MockJSModule()

    # Create pyodide package if it doesn't exist
    if 'pyodide' not in sys.modules:
        sys.modules['pyodide'] = type('Module', (), {})()

    sys.modules['pyodide.ffi'] = MockPyodideFfi()

    print("✅ Browser API mocks installed")


def load_neural_network():
    """
    Import and register NeuralNetwork class into builtins.
    This mimics what neural.py does in PyScript environment.
    """
    import builtins

    # Import the NeuralNetwork class (which auto-registers to builtins)
    # We need to import it to trigger the builtins.NeuralNetwork = NeuralNetwork
    try:
        from ml.neural.neural import NeuralNetwork
        # It should already be in builtins from the import, but ensure it
        if not hasattr(builtins, 'NeuralNetwork'):
            builtins.NeuralNetwork = NeuralNetwork
        print("✅ NeuralNetwork class loaded into builtins")
    except ImportError as e:
        print(f"⚠️  Could not import NeuralNetwork: {e}")
        print("   Make sure ml/neural/neural.py is in PYTHONPATH")


# Auto-install on import
install_mocks()
load_neural_network()
