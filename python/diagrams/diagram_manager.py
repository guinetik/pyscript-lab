"""
Diagram Manager - Clean Python-JavaScript Interop for Diagrams

This module provides a clean interface for managing and rendering infrastructure
diagrams in the browser. It eliminates code duplication by allowing Python files
to be the single source of truth for diagram definitions.

Architecture:
- Uses diagrams_base.DiagramsBase for all patching logic
- Maintains a registry of diagram examples
- Provides simple addExample() and generateExample() API
- Only exposes generateExample() to JavaScript via window object

Author: Guinetik
"""

print("🐍 Starting Diagram Manager...")

from pyscript import document, window
from js import console
from typing import Dict, Optional
from pyodide.http import open_url

# Import the shared base module (configured in py-config)
from diagrams_base import get_diagrams_base


class DiagramManager:
    """
    Manages diagram examples and coordinates browser-based rendering.
    
    Uses DiagramsBase for all patching logic, focuses on example registry
    and coordination.
    
    Attributes:
        examples (Dict): Registry of diagram examples with metadata.
        base: Reference to the shared DiagramsBase instance.
    """
    
    def __init__(self):
        """Initialize the DiagramManager using shared base."""
        self.examples: Dict[str, Dict] = {}
        self.base = get_diagrams_base()
        
        print("🐍 DiagramManager initialized")
    
    def addExample(self, name: str, example_id: str, file_path: str):
        """
        Register a diagram example.
        
        Args:
            name (str): Display name of the example.
            example_id (str): Unique identifier (e.g., "chart1").
            file_path (str): Path to the Python file containing the diagram code.
        """
        self.examples[example_id] = {
            "name": name,
            "file_path": file_path,
            "id": example_id
        }
        print(f"📝 Registered example: {name} ({example_id})")
    
    def generateExample(self, example_id: str):
        """
        Generate a diagram example by executing its Python file.
        
        This method is exposed to JavaScript via window.generateExample()
        and can be called to render or regenerate diagrams.
        
        Args:
            example_id (str): The unique identifier of the example to generate.
        """
        if example_id not in self.examples:
            console.error(f"❌ Unknown example: {example_id}")
            return
        
        example = self.examples[example_id]
        print(f"🔄 Generating: {example['name']}")
        
        try:
            # Set current chart ID on the base
            self.base.current_chart_id = example_id
            
            # Load and execute the Python file
            file_path = example["file_path"]
            print(f"📂 Loading file: {file_path}")
            
            # Read the Python file
            with open_url(file_path) as f:
                code = f.read()
            
            print(f"✅ File loaded: {len(code)} bytes")
            
            # Execute the diagram code
            exec(code, {"__name__": "__main__"})
            
            print(f"✅ Generated: {example['name']}")
            
        except FileNotFoundError as e:
            # Suppress FileNotFoundError (errno 44) - this is expected!
            # The patched render() returns a fake filename but doesn't create the file
            # because we use viz.js for rendering instead
            print(f"ℹ️ Suppressing expected FileNotFoundError for {example_id}: {str(e)}")
            print(f"✅ Generated: {example['name']}")
            
        except Exception as e:
            console.error(f"❌ Error generating {example_id}: {e}")
            import traceback
            console.error(traceback.format_exc())
            self.base.current_chart_id = None
    
    def generateAll(self):
        """
        Generate all registered diagram examples.
        
        Useful for initial page load to render all diagrams at once.
        """
        print(f"🚀 Generating all {len(self.examples)} examples...")
        
        for example_id in self.examples.keys():
            try:
                self.generateExample(example_id)
            except Exception as e:
                console.error(f"❌ Failed to generate {example_id}: {e}")
        
        print("✅ All examples generated!")


# Create global instance
manager = DiagramManager()

# Expose to JavaScript
window.manager = manager
window.generateExample = manager.generateExample
print("✅ window.manager and window.generateExample() exposed to JavaScript")

print("✅ Diagram Manager ready!")
