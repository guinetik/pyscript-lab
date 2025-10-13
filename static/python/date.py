"""
Date and Time Display Example

This module demonstrates how to get and format the current date and time using Python's
datetime module running in the browser via PyScript.

Author: PyScript L.A.B
"""

from pyscript import display
from datetime import datetime


class DateTimeExample:
    """
    A class-based example that demonstrates Python's datetime functionality in PyScript.

    This example shows how to:
    - Get the current date and time
    - Format datetime objects for display
    - Use PyScript's display() function to render output

    Attributes:
        format_string (str): The format string used for datetime formatting.
                            Default: "%m/%d/%Y, %H:%M:%S"
    """

    def __init__(self, format_string: str = "%m/%d/%Y, %H:%M:%S"):
        """
        Initialize the DateTimeExample with a custom format string.

        Args:
            format_string (str, optional): The format string for datetime.strftime().
                                          Defaults to "%m/%d/%Y, %H:%M:%S".

        Example:
            >>> example = DateTimeExample()
            >>> example = DateTimeExample("%Y-%m-%d %H:%M:%S")
        """
        self.format_string = format_string

    def get_current_datetime(self) -> datetime:
        """
        Get the current date and time.

        Returns:
            datetime: The current datetime object.
        """
        return datetime.now()

    def format_datetime(self, dt: datetime) -> str:
        """
        Format a datetime object according to the instance's format string.

        Args:
            dt (datetime): The datetime object to format.

        Returns:
            str: The formatted datetime string.
        """
        return dt.strftime(self.format_string)

    def run(self) -> str:
        """
        Execute the main example logic: get current time, format it, and display it.

        This method:
        1. Logs the start of the operation
        2. Gets the current datetime
        3. Formats it according to the format string
        4. Displays the result using PyScript's display()
        5. Logs the completion

        Returns:
            str: The formatted datetime string that was displayed.
        """
        print("🐍 Generating current timestamp...")

        now = self.get_current_datetime()
        formatted = self.format_datetime(now)

        display(formatted)
        print(f"🐍 Timestamp displayed: {formatted}")

        return formatted


# Entry point: Create instance and run the example
if __name__ == "__main__":
    example = DateTimeExample()
    example.run()
