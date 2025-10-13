"""
Diagrams Base Module - Reusable Diagram Rendering Logic

This module provides the core functionality for rendering Diagrams library code
in the browser using viz.js. It patches graphviz and subprocess to intercept
DOT generation instead of executing native binaries.

Author: PyScript L.A.B
"""

from pyscript import window
from js import console
from typing import Dict
import re
import json


class DiagramsBase:
    """
    Base class for diagram rendering that patches graphviz to work in browser.

    Handles:
    - Patching graphviz.Digraph to intercept DOT generation
    - Mocking subprocess to prevent Emscripten errors
    - Extracting and mapping icon URLs
    - Coordinating with JavaScript viz.js for rendering
    """

    def __init__(self):
        """Initialize the base renderer."""
        self.dot_outputs: Dict[str, str] = {}
        self.current_chart_id = None
        self.original_digraph = None
        self.is_patched = False

        console.log("🐍 [Python] DiagramsBase initialized")

    def patch_graphviz(self):
        """
        Patch graphviz.Digraph to intercept DOT generation.

        Replaces the render() method to capture DOT source and coordinate
        with JavaScript for viz.js rendering instead of executing subprocess.
        """
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
                """
                Intercept render to capture DOT and coordinate JS rendering.
                """
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
                chart_id = base.current_chart_id or f"user-diagram-output"
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
        """
        Mock subprocess to prevent Emscripten process errors.

        Since we can't execute subprocess in browser, intercept calls
        to prevent OSError about missing process support.
        """
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
        """
        Extract icon paths and map to GitHub URLs.

        Args:
            dot_source: The Graphviz DOT source code

        Returns:
            Mapping of local paths to GitHub raw URLs
        """
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


# Global instance for reuse
_global_base = None

def get_diagrams_base():
    """Get or create the global DiagramsBase instance."""
    global _global_base
    if _global_base is None:
        _global_base = DiagramsBase()
        _global_base.setup()
    return _global_base
