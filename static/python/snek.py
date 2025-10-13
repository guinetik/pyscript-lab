"""
Snake Matrix Traversal Animation

This module demonstrates animated snake traversal through a matrix using Python in PyScript.
It shows DOM manipulation, animation timing, and the snake pattern (also known as
boustrophedon or "ox-turning" traversal).

The snake pattern traverses a matrix row by row, alternating direction:
- Left to right on even rows
- Right to left on odd rows

Author: PyScript L.A.B
"""

from js import setTimeout
from pyodide.ffi import create_proxy
from pyscript import document
from typing import List, Tuple


class SnakeMatrixExample:
    """
    A class-based example that demonstrates snake traversal animation through a matrix.

    This example shows:
    - Matrix generation and snake pattern traversal
    - DOM element creation and manipulation
    - Animation using JavaScript setTimeout
    - State management for animation loops
    - Integration between Python and JavaScript APIs

    Attributes:
        rows (int): Number of rows in the matrix.
        cols (int): Number of columns in the matrix.
        animation_delay (int): Delay between animation frames in milliseconds.
        container_id (str): ID of the HTML container element.
        matrix (List[List[int]]): The 2D matrix of numbers.
        snake (List[int]): The snake traversal path through the matrix.
        index (int): Current position in the snake path during animation.
        table_element: Reference to the created table DOM element.
    """

    def __init__(
        self,
        rows: int = 4,
        cols: int = 5,
        animation_delay: int = 500,
        container_id: str = "matrix-container"
    ):
        """
        Initialize the SnakeMatrixExample with matrix dimensions and animation settings.

        Args:
            rows (int, optional): Number of rows in the matrix. Defaults to 4.
            cols (int, optional): Number of columns in the matrix. Defaults to 5.
            animation_delay (int, optional): Milliseconds between animation frames.
                                            Defaults to 500.
            container_id (str, optional): ID of the HTML container element.
                                         Defaults to "matrix-container".

        Example:
            >>> example = SnakeMatrixExample()
            >>> example = SnakeMatrixExample(rows=6, cols=8, animation_delay=300)
        """
        self.rows = rows
        self.cols = cols
        self.animation_delay = animation_delay
        self.container_id = container_id
        self.index = 0
        self.table_element = None

        # Generate matrix and snake path
        self.matrix = self._generate_matrix()
        self.snake = self._generate_snake_path()

    def _generate_matrix(self) -> List[List[int]]:
        """
        Generate a 2D matrix filled with sequential numbers.

        Creates a matrix where each cell contains a unique number based on its position.
        Numbers increase from left to right, top to bottom.

        Returns:
            List[List[int]]: A 2D list representing the matrix.

        Example:
            For a 3x4 matrix:
            [[0, 1, 2, 3],
             [4, 5, 6, 7],
             [8, 9, 10, 11]]
        """
        return [[i + j * self.cols for i in range(self.cols)] for j in range(self.rows)]

    def _generate_snake_path(self) -> List[int]:
        """
        Generate the snake traversal path through the matrix.

        The snake pattern alternates direction on each row:
        - Even rows (0, 2, 4...): left to right
        - Odd rows (1, 3, 5...): right to left

        Returns:
            List[int]: A flat list of numbers in snake traversal order.

        Example:
            For a 3x4 matrix:
            [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11]
        """
        snake = []
        for i, row in enumerate(self.matrix):
            # Even rows: left to right, Odd rows: right to left
            snake += row if i % 2 == 0 else row[::-1]
        return snake

    def _create_table_element(self):
        """
        Create and style the HTML table element for displaying the matrix.

        Builds a table with:
        - Bordered cells
        - Monospace font
        - Centered text
        - Unique IDs for each cell (for animation)

        Returns:
            The created table DOM element.
        """
        table = document.createElement("table")
        table.style.borderCollapse = "collapse"
        table.style.fontFamily = "monospace"
        table.id = "matrix-table"

        for row in self.matrix:
            tr = document.createElement("tr")
            for val in row:
                td = document.createElement("td")
                td.innerText = str(val)
                td.style.border = "1px solid black"
                td.style.padding = "4px"
                td.style.textAlign = "center"
                td.id = f"cell-{val}"
                tr.appendChild(td)
            table.appendChild(tr)

        return table

    def _render_table(self):
        """
        Render the table into the specified container element.

        Clears any existing content in the container and appends the new table.
        """
        container = document.getElementById(self.container_id)
        if not container:
            print(f"❌ Container element '{self.container_id}' not found!")
            return

        container.innerHTML = ""
        self.table_element = self._create_table_element()
        container.appendChild(self.table_element)
        print(f"✅ Matrix table rendered in #{self.container_id}")

    def _animate_step(self):
        """
        Perform a single animation step.

        This method:
        1. Checks if the container still exists (stops animation if removed)
        2. Resets animation when reaching the end of the path
        3. Highlights the current cell with the snake emoji
        4. Clears the previous cell
        5. Schedules the next animation frame

        This is called recursively via setTimeout to create the animation effect.
        """
        # Safety check: stop animation if container is removed from DOM
        if not document.getElementById(self.container_id):
            print("⚠️ Container removed, stopping animation")
            return

        # Reset animation at the end of the path
        if self.index >= len(self.snake):
            self.index = 0
            # Clear all cell styles
            for val in self.snake:
                cell = document.getElementById(f"cell-{val}")
                if cell:
                    cell.innerText = str(val)
                    cell.style.backgroundColor = ""

        # Animate current cell
        val = self.snake[self.index]
        cell = document.getElementById(f"cell-{val}")
        if cell:
            cell.style.backgroundColor = "#cfc"
            cell.innerText = "🐍"

        # Clear previous cell
        if self.index > 0:
            prev = self.snake[self.index - 1]
            prev_cell = document.getElementById(f"cell-{prev}")
            if prev_cell:
                prev_cell.style.backgroundColor = ""
                prev_cell.innerText = str(prev)

        self.index += 1

        # Schedule next animation frame
        setTimeout(create_proxy(self._animate_step), self.animation_delay)

    def run(self):
        """
        Execute the main example logic: render the table and start the animation.

        This method:
        1. Renders the matrix table in the DOM
        2. Starts the snake traversal animation
        3. Continues animating in a loop until the page is navigated away

        The animation runs indefinitely, resetting when it reaches the end of the path.
        """
        print(f"🐍 Starting Snake Matrix Traversal ({self.rows}x{self.cols})...")

        # Render the table
        self._render_table()

        # Start animation
        print(f"🎬 Starting animation (delay: {self.animation_delay}ms)")
        self._animate_step()


# Entry point: Create instance and run the example
if __name__ == "__main__":
    example = SnakeMatrixExample()
    example.run()
