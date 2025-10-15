"""
Interactive Diagram Creator

Provides a clean interface for user-generated diagrams in the browser.
Uses shared diagrams_base.py for all patching logic.

Event-driven architecture: Python exposes functions to JS, JS calls them, Python renders results.

Author: PyScript Lab
"""
try:
    import js
    from js import console
    from pyscript import window

    print("🐍 Starting diagram creator initialization...")
    print("🐍 Starting diagram creator initialization...")

    print("🐍 Imports successful, loading diagrams_base...")
    print("🐍 Imports successful, loading diagrams_base...")

    # Import the shared base module (configured in py-config)
    from diagrams_base import get_diagrams_base

    print("🐍 diagrams_base imported successfully")
    print("🐍 diagrams_base imported successfully")

    # Get the shared base instance
    diagrams_base = get_diagrams_base()
    print("✅ Patches applied")
    print("✅ Patches applied")

except Exception as e:
    print(f"❌ Error during initialization: {str(e)}")
    console.error(f"❌ Error during initialization: {str(e)}")
    import traceback
    error_trace = traceback.format_exc()
    print(error_trace)
    console.error(error_trace)
    raise


def create_diagram(user_code):
    """
    Execute user's diagram code and render the result.
    
    Args:
        user_code: String containing the user's Python diagram code
    """
    print(f"🐍 Received code to execute ({len(user_code)} chars)")

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

        print("✅ Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except FileNotFoundError as e:
        # Suppress FileNotFoundError - this happens because we return a filename
        # from render() but don't actually create the file (we use viz.js instead)
        print(f"ℹ️ Suppressing expected FileNotFoundError: {str(e)}")
        print("✅ Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Error executing diagram code: {error_msg}")
        # Include line number if available
        import traceback
        tb = traceback.format_exc()
        print(f"📋 Traceback: {tb}")
        js.window.updateDiagramStatus('error', error_msg)


# Expose the function to JavaScript
try:
    print("🐍 Exposing create_diagram to window object...")
    print("🐍 Exposing create_diagram to window object...")

    window.create_diagram = create_diagram

    print("✅ Diagram creator ready!")
    print("✅ Diagram creator ready!")
    print("✅ window.create_diagram is now available")

except Exception as e:
    print(f"❌ Error exposing function: {str(e)}")
    console.error(f"❌ Error exposing function: {str(e)}")
    import traceback
    error_trace = traceback.format_exc()
    print(error_trace)
    console.error(error_trace)
