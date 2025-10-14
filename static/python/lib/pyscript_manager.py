"""
PyScript lifecycle management for JavaScript interop.

Provides utilities for Python scripts to signal readiness and export functions
to the JavaScript PyScriptManager.

Example:
    from lib.pyscript_manager import PyScriptManager

    manager = PyScriptManager('my_module')

    def my_function(x):
        return x * 2

    manager.export('myFunction', my_function)
    manager.signal_ready()

Author: Guinetik
"""

from js import window, Object, console, document
from pyodide.ffi import to_js, create_proxy
from typing import Dict, Any, Callable, Optional
import traceback


class PyScriptManager:
    """
    Lifecycle manager for PyScript modules.

    Handles:
    - Signaling readiness to JavaScript
    - Exporting Python functions to window
    - Error reporting with traceback
    - Automatic proxy creation for callables

    This is the Python-side counterpart to the JavaScript PyScriptManager class.
    """

    def __init__(self, module_name: str):
        """
        Initialize the PyScript manager.

        Args:
            module_name: Unique identifier for this module (e.g., 'diagram_creator').
                         Must match the script ID expected by JavaScript.
        """
        self.module_name = module_name
        self._exports = {}
        self._proxies = []  # Keep proxies alive to prevent garbage collection
        print(f"🔧 [PyScriptManager:{module_name}] Initializing...")

    def export(self, name: str, func: Callable) -> None:
        """
        Export a Python function to JavaScript.

        Automatically creates a Pyodide proxy for the function and
        attaches it to the window object for JavaScript access.

        Args:
            name: JavaScript function name (will be accessible as window[name])
            func: Python callable to export

        Example:
            def calculate(x):
                return x * 2

            manager.export('calculate', calculate)
            # JavaScript can now call: window.calculate(5)
        """
        if not callable(func):
            console.warn(f"⚠️ [PyScriptManager:{self.module_name}] Cannot export non-callable: {name}")
            return

        try:
            # Create proxy to make Python function callable from JS
            proxy = create_proxy(func)
            self._proxies.append(proxy)  # Keep reference to prevent GC
            self._exports[name] = proxy

            # Attach to window for global access
            setattr(window, name, proxy)

            print(f"📤 [PyScriptManager:{self.module_name}] Exported: {name}")
        except Exception as e:
            console.error(f"❌ [PyScriptManager:{self.module_name}] Failed to export {name}: {str(e)}")
            traceback.print_exc()

    def signal_ready(self, extra_exports: Optional[Dict[str, Callable]] = None) -> None:
        """
        Signal to JavaScript that this module is ready.

        This triggers the 'script:ready' event in the JavaScript PyScriptManager,
        resolving any promises waiting for this module.

        Args:
            extra_exports: Optional dict of additional functions to export before signaling.
                          Keys are JavaScript names, values are Python callables.

        Example:
            manager.signal_ready({
                'createDiagram': create_diagram,
                'saveDiagram': save_diagram
            })
        """
        try:
            # Export any additional functions
            if extra_exports:
                for name, func in extra_exports.items():
                    self.export(name, func)

            # Convert exports to JavaScript object
            exports_dict = {'module': self.module_name}
            exports_dict.update(self._exports)

            exports_js = to_js(
                exports_dict,
                dict_converter=Object.fromEntries
            )

            # Get the actual script ID set by JavaScript PyScriptManager
            script_id = self._get_script_id()
            if script_id != self.module_name:
                print(f"🔍 [PyScriptManager:{self.module_name}] Found script ID: {script_id}")

            # Call JavaScript callback (use getattr to avoid Python name mangling)
            py_script_ready = getattr(window, '__pyScriptReady', None)
            if py_script_ready:
                py_script_ready(script_id, exports_js)
                print(f"✅ [PyScriptManager:{self.module_name}] Ready! Exported {len(self._exports)} functions.")
            else:
                console.error(f"❌ [PyScriptManager:{self.module_name}] window.__pyScriptReady not found!")
                console.error("Make sure JavaScript PyScriptManager is initialized.")

        except Exception as e:
            console.error(f"❌ [PyScriptManager:{self.module_name}] Error signaling ready: {str(e)}")
            traceback.print_exc()
            self.signal_error(e)

    def _get_script_id(self) -> str:
        """
        Find the actual script ID set by JavaScript PyScriptManager.

        Returns:
            The script ID if found, otherwise falls back to module_name
        """
        script_id = self.module_name  # fallback
        try:
            scripts = document.querySelectorAll('script[type="py"]')
            for script in scripts:
                script_src = str(getattr(script, 'src', ''))
                if self.module_name in script_src or self.module_name in str(script.id):
                    if hasattr(script, 'dataset') and hasattr(script.dataset, 'scriptId'):
                        return str(script.dataset.scriptId)
                    elif hasattr(script, 'id') and script.id:
                        return str(script.id)
        except Exception:
            pass
        return script_id

    def signal_error(self, error: Exception) -> None:
        """
        Signal an error to JavaScript.

        This triggers the 'script:error' event in the JavaScript PyScriptManager,
        rejecting any promises waiting for this module.

        Args:
            error: The exception that occurred
        """
        error_msg = f"{type(error).__name__}: {str(error)}"
        error_trace = traceback.format_exc()

        console.error(f"❌ [PyScriptManager:{self.module_name}] Error: {error_msg}")
        console.error(error_trace)

        # Get the actual script ID
        script_id = self._get_script_id()

        # Call JavaScript error callback (use getattr to avoid Python name mangling)
        py_script_error = getattr(window, '__pyScriptError', None)
        if py_script_error:
            py_script_error(script_id, error_msg)
        else:
            console.error(f"❌ [PyScriptManager:{self.module_name}] window.__pyScriptError not found!")

    def cleanup(self) -> None:
        """
        Clean up exported functions and proxies.

        Should be called when the module is no longer needed.
        Removes functions from window and destroys proxies.
        """
        # Remove from window
        for name in self._exports.keys():
            if hasattr(window, name):
                delattr(window, name)

        # Destroy proxies
        for proxy in self._proxies:
            try:
                proxy.destroy()
            except Exception:
                pass

        self._exports.clear()
        self._proxies.clear()

        print(f"🧹 [PyScriptManager:{self.module_name}] Cleaned up")


def quick_ready(module_name: str, **exports: Callable) -> PyScriptManager:
    """
    Convenience function for creating and signaling ready in one call.

    Useful for simple modules that just need to export a few functions.

    Args:
        module_name: Unique identifier for this module
        **exports: Keyword arguments where keys are JS function names and values are Python callables

    Returns:
        The created PyScriptManager instance

    Example:
        from lib.pyscript_manager import quick_ready

        def add(a, b):
            return a + b

        def multiply(a, b):
            return a * b

        quick_ready('math_module', add=add, multiply=multiply)
    """
    manager = PyScriptManager(module_name)
    manager.signal_ready(exports)
    return manager
