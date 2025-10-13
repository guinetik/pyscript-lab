"""
Fibonacci Sequence Generator

This module demonstrates generating and displaying a Fibonacci sequence using Python
running in the browser via PyScript.

The Fibonacci sequence is a series where each number is the sum of the two preceding ones,
usually starting with 0 and 1. The sequence appears in nature, art, and mathematics.

Author: PyScript L.A.B
"""

from pyscript import display
from typing import List


class FibonacciExample:
    """
    A class-based example that generates and displays Fibonacci sequences.

    This example demonstrates:
    - Recursive algorithm implementation
    - List comprehension
    - PyScript display functionality
    - Configurable sequence generation

    Attributes:
        count (int): The number of Fibonacci numbers to generate.
        use_memoization (bool): Whether to use memoization for performance.
        _memo (dict): Cache for memoized Fibonacci calculations.
    """

    def __init__(self, count: int = 10, use_memoization: bool = False):
        """
        Initialize the FibonacciExample with sequence parameters.

        Args:
            count (int, optional): Number of Fibonacci numbers to generate.
                                  Defaults to 10.
            use_memoization (bool, optional): Enable memoization for better performance
                                             with larger sequences. Defaults to False.

        Example:
            >>> example = FibonacciExample()
            >>> example = FibonacciExample(count=15, use_memoization=True)
        """
        self.count = count
        self.use_memoization = use_memoization
        self._memo = {}

    def fibonacci(self, n: int) -> int:
        """
        Calculate the nth Fibonacci number using simple recursion.

        This is the basic recursive implementation. For better performance with
        larger values, enable memoization in the constructor.

        Args:
            n (int): The position in the Fibonacci sequence (0-indexed).

        Returns:
            int: The nth Fibonacci number.

        Note:
            - fibonacci(0) returns 0
            - fibonacci(1) returns 1
            - fibonacci(n) returns fibonacci(n-1) + fibonacci(n-2) for n > 1
        """
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return self.fibonacci(n - 1) + self.fibonacci(n - 2)

    def fibonacci_memoized(self, n: int) -> int:
        """
        Calculate the nth Fibonacci number using memoization for better performance.

        This method caches previously calculated values to avoid redundant computation,
        making it much faster for larger sequences.

        Args:
            n (int): The position in the Fibonacci sequence (0-indexed).

        Returns:
            int: The nth Fibonacci number.
        """
        if n in self._memo:
            return self._memo[n]

        if n <= 0:
            result = 0
        elif n == 1:
            result = 1
        else:
            result = self.fibonacci_memoized(n - 1) + self.fibonacci_memoized(n - 2)

        self._memo[n] = result
        return result

    def generate_sequence(self) -> List[int]:
        """
        Generate a Fibonacci sequence of the configured length.

        Uses either the basic recursive method or the memoized version
        depending on the use_memoization setting.

        Returns:
            List[int]: A list containing the Fibonacci sequence.

        Example:
            >>> example = FibonacciExample(count=5)
            >>> example.generate_sequence()
            [0, 1, 1, 2, 3]
        """
        if self.use_memoization:
            return [self.fibonacci_memoized(i) for i in range(self.count)]
        else:
            return [self.fibonacci(i) for i in range(self.count)]

    def run(self) -> List[int]:
        """
        Execute the main example logic: generate and display the Fibonacci sequence.

        This method:
        1. Logs the start of sequence generation
        2. Generates the Fibonacci sequence
        3. Displays the result using PyScript's display()
        4. Logs the completion with the sequence

        Returns:
            List[int]: The generated Fibonacci sequence.
        """
        print("🐍 Generating Fibonacci sequence...")

        fibo = self.generate_sequence()

        display(fibo)
        print(f"🐍 Fibonacci sequence displayed: {fibo}")

        return fibo


# Entry point: Create instance and run the example
if __name__ == "__main__":
    example = FibonacciExample()
    example.run()
