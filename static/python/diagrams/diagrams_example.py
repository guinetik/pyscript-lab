"""
Diagrams as Code - Infrastructure Architecture Visualization

This module demonstrates creating infrastructure architecture diagrams using Python
code instead of drag-and-drop tools. It uses the Diagrams library to generate
architecture diagrams and viz.js (Graphviz in WebAssembly) for browser rendering.

This example creates five different architecture patterns:
1. Grouped Workers - Load balancer distributing to multiple workers
2. Clustered Web Services - Web tier with database replication
3. Event-Driven Architecture - SNS/SQS/Lambda event processing
4. Microservices API - API Gateway with microservice backends
5. Data Analytics Pipeline - S3/Lambda/Athena data processing

These examples showcase:
- Infrastructure as Code principles for diagrams
- Graphviz DOT format generation and interception
- Browser-based diagram rendering with viz.js
- Multi-cloud architecture visualization
- Python-to-JavaScript interoperability

Author: Guinetik
"""

print("🐍 Starting Diagrams as Code example with viz.js rendering...")

from pyscript import document, window
from js import console
from typing import Dict, Optional, Callable
import io
import re
import json
from contextlib import redirect_stdout


class DiagramsRenderer:
    """
    A comprehensive diagrams-as-code renderer using Python's Diagrams library.

    This class handles the complex process of generating infrastructure diagrams
    in the browser by:
    1. Patching graphviz.Digraph to intercept DOT source generation
    2. Mocking subprocess calls to prevent native binary requirements
    3. Extracting and mapping cloud provider icon paths
    4. Coordinating with JavaScript viz.js for rendering

    Features:
    - Generates DOT format from Python Diagrams code
    - Captures and processes Graphviz output
    - Maps icon paths to GitHub URLs for fetching
    - Provides regeneration capabilities for each diagram
    - Supports all major cloud providers (AWS, Azure, GCP, K8s)

    Attributes:
        dot_outputs (Dict[str, str]): Mapping of chart IDs to DOT source code.
        current_chart_id (Optional[str]): Currently active chart ID for rendering.
        original_digraph: Reference to the original graphviz.Digraph class.
        diagram_generators (Dict[str, Callable]): Mapping of chart IDs to generator functions.
    """

    def __init__(self):
        """
        Initialize the DiagramsRenderer.

        Sets up the patching infrastructure for graphviz and subprocess,
        and prepares data structures for diagram generation.
        """
        self.dot_outputs: Dict[str, str] = {}
        self.current_chart_id: Optional[str] = None
        self.original_digraph = None
        self.diagram_generators: Dict[str, Callable] = {}

        print("🐍 DiagramsRenderer initialized")
        print("🐍 DiagramsRenderer initialized")

    def _patch_graphviz(self):
        """
        Patch graphviz.Digraph to intercept DOT source generation.

        This method replaces the standard Digraph class with a custom
        CaptureDigraph class that intercepts render() calls to capture
        the generated DOT source code instead of executing Graphviz.

        The captured DOT is then processed to:
        1. Extract icon paths from the diagrams library
        2. Map them to GitHub URLs for fetching
        3. Send to JavaScript for viz.js rendering with icon injection
        """
        import graphviz

        # Store reference to original
        self.original_digraph = graphviz.Digraph

        # Create reference to self for closure
        renderer = self

        class CaptureDigraph(renderer.original_digraph):
            """
            Custom Digraph class that captures DOT source.

            Intercepts the render() method to capture the DOT source
            instead of actually executing Graphviz subprocess.
            """

            def render(self, *args, **kwargs):
                """
                Intercept render to capture DOT source and coordinate rendering.

                Args:
                    *args: Variable positional arguments (filename, etc.)
                    **kwargs: Variable keyword arguments (format, cleanup, etc.)

                Returns:
                    str: Mock filename to simulate successful render.
                """
                # Get the DOT source
                dot_source = self.source

                # Extract filename
                filename = kwargs.get('filename') or (args[0] if args else 'diagram')
                filename = str(filename)

                print(f"🎯 Captured DOT from graphviz.Digraph: {len(dot_source)} bytes")
                print(f"📝 Filename: {filename}")
                print(f"📄 DOT source preview: {dot_source[:500]}")

                # Process icon paths and create mapping
                image_urls = renderer._extract_icon_urls(dot_source)
                print(f"✅ Found {len(image_urls)} unique images")

                # Determine chart ID
                if renderer.current_chart_id:
                    chart_id = renderer.current_chart_id
                    print(f"📊 Using preset chart ID: {chart_id}")
                else:
                    chart_id = f"chart{len(renderer.dot_outputs) + 1}"
                    print(f"📊 Auto-generated chart ID: {chart_id}")

                # Store DOT source
                renderer.dot_outputs[chart_id] = dot_source

                # Convert image mapping to JSON
                image_mapping = json.dumps(image_urls)

                # Call JavaScript to handle image fetching and rendering
                window.fetchAndRenderDiagram(chart_id, dot_source, image_mapping)

                # Reset chart ID for next use
                renderer.current_chart_id = None

                # Return mock result
                return f"{filename}.dot"

        # Replace Digraph class
        graphviz.Digraph = CaptureDigraph
        print("✅ graphviz.Digraph patched successfully")

    def _extract_icon_urls(self, dot_source: str) -> Dict[str, str]:
        """
        Extract icon paths from DOT source and map to GitHub URLs.

        The diagrams library references local file paths for icons.
        This method finds all image attributes in the DOT source and
        maps them to GitHub raw URLs for fetching in the browser.

        Args:
            dot_source (str): The Graphviz DOT source code.

        Returns:
            Dict[str, str]: Mapping of local paths to GitHub URLs.
        """
        image_urls = {}

        def collect_image_path(match):
            full_path = match.group(1)
            # Extract the relative path after '/resources/'
            if '/resources/' in full_path or '\\resources\\' in full_path:
                parts = re.split(r'[/\\]resources[/\\]', full_path)
                if len(parts) > 1:
                    relative_path = parts[1].replace('\\', '/')
                    github_url = f"https://raw.githubusercontent.com/mingrammer/diagrams/master/resources/{relative_path}"
                    image_urls[full_path] = github_url
                    print(f"🔄 Found image: {relative_path}")
            return match.group(0)

        # Find all image attributes
        re.sub(r'image="([^"]+)"', collect_image_path, dot_source)

        return image_urls

    def _patch_subprocess(self):
        """
        Patch subprocess to prevent actual Graphviz execution.

        Since we're running in the browser via WebAssembly, we can't
        execute subprocess commands. This method mocks subprocess.run()
        to intercept Graphviz calls and prevent errors.

        Note:
            In the browser environment, subprocess commands would fail
            anyway, so this is a safety measure to provide better errors.
        """
        import subprocess

        def mock_subprocess_run(args, **kwargs):
            """
            Mock subprocess calls to prevent execution errors.

            Args:
                args: Command and arguments list.
                **kwargs: Additional subprocess options.

            Returns:
                MockResult: A mock subprocess result object.

            Raises:
                OSError: For non-Graphviz subprocess calls.
            """
            if args and 'dot' in str(args[0]):
                print(f"🔧 Intercepting subprocess call: {args}")

                # Return mock result
                class MockResult:
                    returncode = 0
                    stdout = b''
                    stderr = b''

                    def check_returncode(self):
                        if self.returncode != 0:
                            raise subprocess.CalledProcessError(self.returncode, args)

                return MockResult()

            # For non-Graphviz calls, raise error
            raise OSError(138, "emscripten does not support processes")

        subprocess.run = mock_subprocess_run
        print("✅ subprocess.run patched successfully")

    def _load_diagrams_library(self) -> bool:
        """
        Load the diagrams library and AWS components.

        Attempts to import the diagrams library and commonly used
        AWS components for creating architecture diagrams.

        Returns:
            bool: True if library loaded successfully, False otherwise.
        """
        print("🐍 Loading diagrams library...")
        try:
            from diagrams import Diagram, Cluster
            from diagrams.aws.compute import EC2, ECS, Lambda
            from diagrams.aws.database import RDS, ElastiCache, Dynamodb
            from diagrams.aws.network import ELB, Route53, APIGateway
            from diagrams.aws.integration import SNS, SQS
            from diagrams.aws.storage import S3
            from diagrams.aws.analytics import Athena

            print("🐍 Diagrams library loaded successfully!")

            # Debug: Check library paths
            import diagrams
            import os
            diagrams_path = os.path.dirname(diagrams.__file__)
            print(f"📂 Diagrams library path: {diagrams_path}")

            resources_path = os.path.join(diagrams_path, "resources")
            if os.path.exists(resources_path):
                print(f"✅ Resources path exists: {resources_path}")
                try:
                    contents = os.listdir(resources_path)[:10]
                    print(f"📂 Resources contents: {contents}")
                except:
                    print("⚠️ Could not list resources directory")
            else:
                print(f"❌ Resources path not found: {resources_path}")

            return True

        except ImportError as e:
            print(f"❌ Error importing diagrams: {e}")
            console.error(f"❌ Import error: {e}")
            return False

    def _setup_diagram_generators(self):
        """
        Define and register all diagram generation functions.

        Creates generator functions for each of the five example diagrams
        and stores them in a dictionary for easy access and regeneration.
        """
        from diagrams import Diagram, Cluster
        from diagrams.aws.compute import EC2, ECS, Lambda
        from diagrams.aws.database import RDS, ElastiCache, Dynamodb
        from diagrams.aws.network import ELB, Route53, APIGateway
        from diagrams.aws.integration import SNS, SQS
        from diagrams.aws.storage import S3
        from diagrams.aws.analytics import Athena
        from datetime import datetime

        def generate_diagram_1():
            """Generate Grouped Workers diagram."""
            print("🔄 Regenerating diagram 1...")
            try:
                self.current_chart_id = "chart1"
                timestamp = datetime.now().isoformat()

                with Diagram(
                    "Grouped Workers",
                    show=False,
                    direction="TB",
                    filename="grouped_workers",
                    outformat="dot",
                    graph_attr={"splines": "ortho", "comment": timestamp}
                ):
                    ELB("lb") >> [
                        EC2("worker1"),
                        EC2("worker2"),
                        EC2("worker3"),
                        EC2("worker4"),
                        EC2("worker5")
                    ] >> RDS("events")

                print("✅ Diagram 1 regenerated!")
            except Exception as e:
                print(f"❌ Error regenerating diagram 1: {e}")

        def generate_diagram_2():
            """Generate Clustered Web Services diagram."""
            print("🔄 Regenerating diagram 2...")
            try:
                self.current_chart_id = "chart2"

                with Diagram(
                    "Clustered Web Services",
                    show=False,
                    filename="clustered_services",
                    outformat="dot"
                ):
                    dns = Route53("dns")
                    lb = ELB("lb")

                    with Cluster("Services"):
                        svc_group = [ECS("web1"), ECS("web2"), ECS("web3")]

                    with Cluster("DB Cluster"):
                        db_primary = RDS("userdb")
                        db_primary - [RDS("userdb ro")]

                    memcached = ElastiCache("memcached")

                    dns >> lb >> svc_group
                    svc_group >> db_primary
                    svc_group >> memcached

                print("✅ Diagram 2 regenerated!")
            except Exception as e:
                print(f"❌ Error regenerating diagram 2: {e}")

        def generate_diagram_3():
            """Generate Event-Driven Architecture diagram."""
            print("🔄 Regenerating diagram 3...")
            try:
                self.current_chart_id = "chart3"

                with Diagram(
                    "Event-Driven Architecture",
                    show=False,
                    filename="event_driven",
                    outformat="dot",
                    graph_attr={"splines": "ortho"}
                ):
                    source = EC2("event source")

                    with Cluster("Event Processing"):
                        topic = SNS("topic")
                        queue = SQS("queue")
                        workers = [Lambda("handler1"), Lambda("handler2"), Lambda("handler3")]

                    db = Dynamodb("state")

                    source >> topic >> queue >> workers >> db

                print("✅ Diagram 3 regenerated!")
            except Exception as e:
                print(f"❌ Error regenerating diagram 3: {e}")

        def generate_diagram_4():
            """Generate Microservices API diagram."""
            print("🔄 Regenerating diagram 4...")
            try:
                self.current_chart_id = "chart4"

                with Diagram(
                    "Microservices API",
                    show=False,
                    filename="microservices_api",
                    outformat="dot"
                ):
                    api = APIGateway("api")

                    with Cluster("Microservices"):
                        svc1 = Lambda("users")
                        svc2 = Lambda("orders")
                        svc3 = Lambda("products")

                    with Cluster("Data Layer"):
                        db1 = Dynamodb("users-db")
                        db2 = Dynamodb("orders-db")
                        db3 = Dynamodb("products-db")

                    api >> [svc1, svc2, svc3]
                    svc1 >> db1
                    svc2 >> db2
                    svc3 >> db3

                print("✅ Diagram 4 regenerated!")
            except Exception as e:
                print(f"❌ Error regenerating diagram 4: {e}")

        def generate_diagram_5():
            """Generate Data Analytics Pipeline diagram."""
            print("🔄 Regenerating diagram 5...")
            try:
                self.current_chart_id = "chart5"

                with Diagram(
                    "Data Analytics Pipeline",
                    show=False,
                    filename="data_pipeline",
                    outformat="dot",
                    graph_attr={"splines": "ortho"}
                ):
                    source = S3("raw-data")

                    with Cluster("Processing"):
                        etl = Lambda("transform")
                        processed = S3("processed")

                    analytics = Athena("analytics")
                    cache = ElastiCache("cache")

                    source >> etl >> processed >> analytics
                    analytics >> cache

                print("✅ Diagram 5 regenerated!")
            except Exception as e:
                print(f"❌ Error regenerating diagram 5: {e}")

        # Register all generators
        self.diagram_generators = {
            "chart1": generate_diagram_1,
            "chart2": generate_diagram_2,
            "chart3": generate_diagram_3,
            "chart4": generate_diagram_4,
            "chart5": generate_diagram_5,
        }

        print(f"✅ Registered {len(self.diagram_generators)} diagram generators")

    def _expose_to_javascript(self):
        """
        Expose diagram generator functions to JavaScript.

        Makes the generator functions available as window.regenerateDiagramN()
        so they can be called from HTML button onclick handlers.
        """
        window.regenerateDiagram1 = self.diagram_generators["chart1"]
        window.regenerateDiagram2 = self.diagram_generators["chart2"]
        window.regenerateDiagram3 = self.diagram_generators["chart3"]
        window.regenerateDiagram4 = self.diagram_generators["chart4"]
        window.regenerateDiagram5 = self.diagram_generators["chart5"]

        print("✅ Diagram generators exposed to JavaScript")

    def generate_all_diagrams(self):
        """
        Generate all five example diagrams initially.

        Calls each diagram generator function in sequence to create
        the initial set of diagrams when the page loads.
        """
        print("🐍 Generating all diagrams...")
        print("🐍 Starting initial diagram generation...")

        for i, (chart_id, generator) in enumerate(self.diagram_generators.items(), 1):
            print(f"🐍 Generating diagram {i}...")
            try:
                generator()
                print(f"✅ Diagram {i} generated!")
            except Exception as e:
                print(f"❌ Error generating diagram {i}: {e}")
                console.error(f"❌ Diagram {i} error: {e}")

        print("✅ All diagrams generated!")
        print("✅ All diagrams sent to JavaScript for rendering")

    def run(self):
        """
        Execute the complete diagrams rendering workflow.

        This method orchestrates the entire process:
        1. Patches graphviz.Digraph to intercept DOT generation
        2. Patches subprocess to prevent execution errors
        3. Loads the diagrams library with AWS components
        4. Sets up diagram generator functions
        5. Exposes generators to JavaScript for regeneration
        6. Generates all five example diagrams

        Note:
            The actual rendering happens in JavaScript using viz.js
            after the DOT source is captured and icons are fetched.
        """
        print("🐍 Starting DiagramsRenderer workflow...")
        print("🐍 Initializing DiagramsRenderer workflow...")

        try:
            # Apply patches
            self._patch_graphviz()
            self._patch_subprocess()

            # Load library
            if not self._load_diagrams_library():
                raise ImportError("Failed to load diagrams library")

            # Setup generators
            self._setup_diagram_generators()

            # Expose to JavaScript
            self._expose_to_javascript()

            # Generate all diagrams
            self.generate_all_diagrams()

            print("🐍 Diagrams as Code example complete!")
            print("🐍 Using viz.js (Graphviz compiled to WebAssembly) for browser rendering!")
            print("✅ DiagramsRenderer workflow complete!")

        except Exception as e:
            error_msg = f"DiagramsRenderer failed: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise


# Entry point: Create instance and run the workflow
if __name__ == "__main__":
    renderer = DiagramsRenderer()
    renderer.run()
