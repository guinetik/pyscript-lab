"""
JavaScript-Python Interoperability Example

This module demonstrates bidirectional communication between JavaScript and Python in PyScript.
It shows how JavaScript can call Python functions and how Python sends data back to JavaScript
for rendering.

IMPORTANT: This module follows the data-only communication pattern:
- Python computes and processes data
- Python sends plain data structures via window callbacks
- JavaScript/Svelte handles all DOM rendering

This example creates an interactive greeting system that responds to user input with
personalized messages based on their name and age.

Author: Guinetik
"""

import json
import random
from typing import Optional, Dict, List
from js import window, console, Object
from pyodide.ffi import to_js


class InteropGreeter:
    """
    A class-based example demonstrating JavaScript-Python interoperability in PyScript.

    This class provides an interactive greeting system that:
    - Validates user input from JavaScript
    - Generates personalized responses based on age groups
    - Sends data back to JavaScript via window callbacks (NO innerHTML)
    - Demonstrates Python's ability to process data for browser display

    The greeter categorizes users into different developer experience levels
    based on their age and provides humorous, personalized responses.

    Attributes:
        greeting_variants (List[str]): Different greeting styles to randomize responses.
    """

    # Age brackets for different developer categories
    AGE_BRACKETS = {
        'student': (0, 17),
        'junior': (18, 24),
        'mid': (25, 32),
        'senior': (33, 39),
        'veteran': (40, 55),
        'legend': (56, 100)
    }

    def __init__(self):
        """
        Initialize the InteropGreeter with configuration.
        """
        self.greeting_variants = [
            "Hello", "Hi", "Hey", "Greetings", "Welcome",
            "What's up", "Howdy", "Yo", "Hola", "Salutations"
        ]

        # Signal that Python is ready
        self._signal_ready()

    def _signal_ready(self):
        """
        Signal to JavaScript that Python is initialized and ready.

        Sends data via window callback instead of manipulating DOM.
        """
        data = {
            'ready': True,
            'message': 'Python is Ready!',
            'subtitle': 'Fill out the form to see JavaScript calling Python in action'
        }
        # Convert Python dict to JavaScript object to avoid proxy destruction
        window.onInteropReady(to_js(data, dict_converter=Object.fromEntries))
        print("✅ InteropGreeter initialized and ready")

    def _get_greeting(self) -> str:
        """
        Get a random greeting phrase.

        Returns:
            str: A randomly selected greeting from the greeting variants.
        """
        return random.choice(self.greeting_variants)

    def _categorize_age(self, age: int) -> str:
        """
        Categorize a person's age into a developer experience bracket.

        Args:
            age (int): The person's age.

        Returns:
            str: The age bracket category ('student', 'junior', 'mid', etc.).
        """
        for category, (min_age, max_age) in self.AGE_BRACKETS.items():
            if min_age <= age <= max_age:
                return category
        return 'legend'  # Default for ages outside defined ranges

    def _get_age_specific_responses(self, age: int, category: str) -> List[str]:
        """
        Generate age-specific responses with personality and humor.

        Args:
            age (int): The person's age.
            category (str): The age bracket category.

        Returns:
            List[str]: A list of response strings (plain text, no HTML).
        """
        responses = {
            'student': [
                "🎓 Welcome, future coder! The tech world awaits you!",
                "📚 Still in school? Great! You're learning Python before it was cool!",
                "🌟 Young and ambitious! The next tech unicorn founder perhaps?",
                "💡 Script kiddie in training! We all started somewhere 😊"
            ],
            'junior': [
                "🚀 Junior dev energy! You're in the exciting phase of your career!",
                "💻 Fresh out of bootcamp or college? Welcome to the real world!",
                "🎯 Junior years are the best - everything is new and exciting!",
                "🔥 That sweet spot between student and experienced dev!"
            ],
            'mid': [
                "⚡ Mid-level developer! The backbone of every tech team!",
                "🎨 You've seen some things... mostly Stack Overflow pages 😄",
                "🏗️ Building cool stuff and still Googling syntax? Perfect!",
                "💪 The goldilocks zone of development - not too junior, not too senior!"
            ],
            'senior': [
                "👨‍💻 Senior dev spotted! Time to review everyone's PRs!",
                "🧙‍♂️ With great seniority comes great responsibility (and meetings).",
                "📊 Senior enough to know what you're doing, young enough to remember how to code!",
                "🎓 Ah, the mentoring years. How many juniors have you saved from production disasters?"
            ],
            'veteran': [
                "🦕 Dinosaur sighting! But the cool kind that adapted and survived!",
                "📜 You've probably written code in languages that no longer exist.",
                "🏛️ Old school meets new school. Respect! 🙏",
                "⚔️ Veteran of the browser wars, the mobile revolution, and probably punch cards!",
                "🎖️ Still coding after all these years? You're either passionate or crazy. Probably both!"
            ],
            'legend': [
                "👴 LEGENDARY STATUS! You've seen the entire evolution of computing!",
                "🏆 Living history! Please tell us about the good old days!",
                "🌟 Age is just a number, but yours suggests you invented the internet!",
                "💎 Coding since before the web? You're a rare gem!",
                "🎩 Sir/Madam, your wisdom is invaluable. Also, how are you still debugging at this age?! 😄"
            ]
        }

        # Get responses for the category, with fallback
        category_responses = responses.get(category, responses['legend'])

        # Return a random response from the category
        return [random.choice(category_responses)]

    def _validate_input(self, name: Optional[str], age: Optional[int]) -> Dict[str, any]:
        """
        Validate user input and return validation results.

        Args:
            name (Optional[str]): The user's name.
            age (Optional[int]): The user's age.

        Returns:
            Dict[str, any]: Dictionary with 'valid' (bool) and 'error' (str) keys.
        """
        if not name or name.strip() == "":
            return {
                'valid': False,
                'message': 'Name is required!'
            }

        if age is None or age == "":
            return {
                'valid': False,
                'message': 'Age is required!'
            }

        try:
            age_int = int(age)
            if age_int < 0:
                return {
                    'valid': False,
                    'message': "Age can't be negative! Time travel not supported yet."
                }
            if age_int > 150:
                return {
                    'valid': False,
                    'message': "Age seems a bit high! Are you a vampire? 🧛"
                }
        except ValueError:
            return {
                'valid': False,
                'message': 'Age must be a valid number!'
            }

        return {'valid': True, 'message': None}

    def _generate_response_data(self, name: str, age: int) -> Dict:
        """
        Generate the complete response data for a valid greeting.

        This returns a plain data structure (no HTML) that JavaScript will render.

        Args:
            name (str): The user's name.
            age (int): The user's age.

        Returns:
            Dict: Data structure containing all greeting information.
        """
        greeting = self._get_greeting()
        category = self._categorize_age(age)
        age_responses = self._get_age_specific_responses(age, category)

        # Calculate potential coding years
        years_coding = max(0, age - 18) if age >= 18 else 0

        # Return plain data structure
        return {
            'greeting': greeting,
            'name': name,
            'age': age,
            'category': category,
            'responses': age_responses,
            'years_coding': years_coding,
            'disclaimer': "Just kidding around! All developers are awesome! 🚀"
        }

    def run(self, name: Optional[str], age: Optional[int]) -> None:
        """
        Main entry point called from JavaScript to generate a greeting.

        This method:
        1. Validates the input parameters
        2. Generates an appropriate response
        3. Sends data to JavaScript via window callbacks
        4. Logs the interaction to the console

        NO DOM MANIPULATION - only sends data!

        Args:
            name (Optional[str]): The user's name from the form input.
            age (Optional[int]): The user's age from the form input.

        Example (called from JavaScript):
            >>> runGreeting('Alice', 28)
            # Sends data via window.onGreetingResult()
        """
        print(f"🐍 Python function called with: name='{name}', age={age}")

        # Validate input
        validation = self._validate_input(name, age)
        if not validation['valid']:
            # Send validation error to JavaScript
            # Convert Python dict to JavaScript object to avoid proxy destruction
            error_data = {'message': validation['message']}
            window.onValidationError(to_js(error_data, dict_converter=Object.fromEntries))
            console.warn(f"⚠️ Validation failed: {validation['message']}")
            return

        # Generate response data
        response_data = self._generate_response_data(name, int(age))

        # Send data to JavaScript for rendering
        # Convert Python dict to JavaScript object to avoid proxy destruction
        window.onGreetingResult(to_js(response_data, dict_converter=Object.fromEntries))

        print(f"✅ Greeting data generated successfully for {name}, age {age}")


# Create a global instance of the greeter
_greeter_instance = InteropGreeter()


def runGreeting(name: Optional[str], age: Optional[int]) -> None:
    """
    Global function that exposes the greeter to JavaScript.

    This function acts as a bridge between JavaScript and the InteropGreeter class.
    It's called directly from JavaScript code via PyScript.

    Args:
        name (Optional[str]): The user's name.
        age (Optional[int]): The user's age.

    Example (from JavaScript):
        window.runGreeting('Bob', 35)
    """
    _greeter_instance.run(name, age)


# Expose the function to window object so JavaScript can call it
window.runGreeting = runGreeting

# Log initialization
print("🐍 Interop module loaded successfully")
console.log("🐍 Interop module loaded - window.runGreeting is available")
