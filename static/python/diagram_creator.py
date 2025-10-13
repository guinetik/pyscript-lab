"""
Interactive Diagram Creator

Provides a clean interface for user-generated diagrams in the browser.
Uses shared diagrams_base.py for all patching logic.

Event-driven architecture: Python exposes functions to JS, JS calls them, Python renders results.

Author: PyScript Lab
"""
import js
from js import console
from pyscript import window

# Import the shared base module (configured in py-config)
from diagrams_base import get_diagrams_base

console.log("🐍 Initializing diagram creator...")

# Get the shared base instance
diagrams_base = get_diagrams_base()
console.log("✅ Patches applied")


def create_diagram(user_code):
    """
    Execute user's diagram code and render the result.
    
    Args:
        user_code: String containing the user's Python diagram code
    """
    console.log(f"🐍 Received code to execute ({len(user_code)} chars)")

    try:
        # Notify UI that we're processing
        js.window.updateDiagramStatus('processing', 'Generating diagram...')

        # Set chart ID for the base renderer
        diagrams_base.current_chart_id = "user-diagram-output"

        # Execute the user's code
        # The patched graphviz will intercept the render() call
        exec(user_code, {
            '__name__': '__main__',
            '__builtins__': __builtins__
        })

        console.log("✅ Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except FileNotFoundError as e:
        # Suppress FileNotFoundError - this happens because we return a filename
        # from render() but don't actually create the file (we use viz.js instead)
        console.log(f"ℹ️ Suppressing expected FileNotFoundError: {str(e)}")
        console.log("✅ Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        console.log(f"❌ Error executing diagram code: {error_msg}")
        # Include line number if available
        import traceback
        tb = traceback.format_exc()
        console.log(f"📋 Traceback: {tb}")
        js.window.updateDiagramStatus('error', error_msg)


# Expose the function to JavaScript
console.log("🐍 Exposing create_diagram to window object")
js.window.create_diagram = create_diagram
console.log("✅ Diagram creator ready!")
