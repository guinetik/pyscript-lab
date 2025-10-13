"""
Interactive Diagram Creator
Event-driven architecture: Python exposes functions to JS, JS calls them, Python renders results
"""
import js
from js import console
from pyscript import window
from typing import Dict
import re
import json


class DiagramsBase:
    """
    Base class for diagram rendering that patches graphviz to work in browser.
    """

    def __init__(self):
        """Initialize the base renderer."""
        self.dot_outputs: Dict[str, str] = {}
        self.current_chart_id = None
        self.original_digraph = None
        self.is_patched = False
        console.log("🐍 [Python] DiagramsBase initialized")

    def patch_graphviz(self):
        """Patch graphviz.Digraph to intercept DOT generation."""
        if self.is_patched:
            console.log("⚠️ [Python] Already patched, skipping")
            return

        import graphviz

        # Store original
        self.original_digraph = graphviz.Digraph

        # Create reference for closure
        base = self

        class CaptureDigraph(base.original_digraph):
            """Custom Digraph that captures DOT source."""

            def render(self, *args, **kwargs):
                """Intercept render to capture DOT and coordinate JS rendering."""
                # Get DOT source
                dot_source = self.source

                # Extract filename
                filename = kwargs.get('filename') or (args[0] if args else 'diagram')
                filename = str(filename)

                console.log(f"🎯 [Python] Captured DOT: {len(dot_source)} bytes")

                # Extract icon URLs
                image_urls = base._extract_icon_urls(dot_source)
                console.log(f"✅ [Python] Found {len(image_urls)} images")

                # Determine chart ID
                chart_id = base.current_chart_id or "user-diagram-output"
                console.log(f"📊 [Python] Chart ID: {chart_id}")

                # Store DOT
                base.dot_outputs[chart_id] = dot_source

                # Convert image mapping to JSON
                image_mapping = json.dumps(image_urls)

                # Call JavaScript to render
                window.fetchAndRenderDiagram(chart_id, dot_source, image_mapping)

                # Reset chart ID
                base.current_chart_id = None

                return f"{filename}.dot"

        # Replace Digraph
        graphviz.Digraph = CaptureDigraph
        self.is_patched = True
        console.log("✅ [Python] graphviz.Digraph patched")

    def patch_subprocess(self):
        """Mock subprocess to prevent Emscripten process errors."""
        import subprocess

        def mock_subprocess_run(args, **kwargs):
            """Mock subprocess calls."""
            if args and 'dot' in str(args[0]):
                console.log(f"🔧 [Python] Intercepting subprocess: {args}")

                class MockResult:
                    returncode = 0
                    stdout = b''
                    stderr = b''

                    def check_returncode(self):
                        if self.returncode != 0:
                            raise subprocess.CalledProcessError(self.returncode, args)

                return MockResult()

            # Non-Graphviz calls error
            raise OSError(138, "emscripten does not support processes")

        subprocess.run = mock_subprocess_run
        console.log("✅ [Python] subprocess.run patched")

    def _extract_icon_urls(self, dot_source: str) -> Dict[str, str]:
        """Extract icon paths and map to GitHub URLs."""
        image_urls = {}

        def collect_image_path(match):
            full_path = match.group(1)
            if '/resources/' in full_path or '\\resources\\' in full_path:
                parts = re.split(r'[/\\]resources[/\\]', full_path)
                if len(parts) > 1:
                    relative_path = parts[1].replace('\\', '/')
                    github_url = f"https://raw.githubusercontent.com/mingrammer/diagrams/master/resources/{relative_path}"
                    image_urls[full_path] = github_url
            return match.group(0)

        # Find all image attributes
        re.sub(r'image="([^"]+)"', collect_image_path, dot_source)

        return image_urls

    def setup(self):
        """Apply all necessary patches."""
        console.log("🐍 [Python] Setting up DiagramsBase patches...")
        self.patch_graphviz()
        self.patch_subprocess()
        console.log("✅ [Python] DiagramsBase setup complete")


# Initialize the patches
console.log("🐍 [Python] Initializing diagram creator...")
diagrams_base = DiagramsBase()
diagrams_base.setup()
console.log("✅ [Python] Patches applied")

def create_diagram(user_code):
    """
    Execute user's diagram code and render the result
    Args:
        user_code: String containing the user's Python diagram code
    """
    console.log(f"🐍 [Python] Received code to execute ({len(user_code)} chars)")

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

        console.log("✅ [Python] Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except FileNotFoundError as e:
        # Suppress FileNotFoundError - this happens because we return a filename
        # from render() but don't actually create the file (we use viz.js instead)
        console.log(f"ℹ️ [Python] Suppressing expected FileNotFoundError: {str(e)}")
        console.log("✅ [Python] Diagram code executed successfully")
        js.window.updateDiagramStatus('success', 'Diagram generated!')

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        console.log(f"❌ [Python] Error executing diagram code: {error_msg}")
        # Include line number if available
        import traceback
        tb = traceback.format_exc()
        console.log(f"📋 [Python] Traceback: {tb}")
        js.window.updateDiagramStatus('error', error_msg)

# Expose the function to JavaScript
console.log("🐍 [Python] Exposing create_diagram to window object")
js.window.create_diagram = create_diagram
console.log("✅ [Python] Diagram creator ready!")
