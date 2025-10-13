"""
JavaScript-Python Interoperability Example

This module demonstrates bidirectional communication between JavaScript and Python in PyScript.
It shows how JavaScript can call Python functions and how Python can manipulate the DOM.

This example creates an interactive greeting system that responds to user input with
personalized messages based on their name and age.

Author: Guinetik
"""

import json
import random
from typing import Optional, Dict, List
from pyscript import document
from js import console


class InteropGreeter:
    """
    A class-based example demonstrating JavaScript-Python interoperability in PyScript.

    This class provides an interactive greeting system that:
    - Validates user input from JavaScript
    - Generates personalized responses based on age groups
    - Manipulates DOM elements to display results
    - Demonstrates Python's ability to interact with browser APIs

    The greeter categorizes users into different developer experience levels
    based on their age and provides humorous, personalized responses.

    Attributes:
        output_element_id (str): ID of the DOM element where output is displayed.
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

    def __init__(self, output_element_id: str = "chart"):
        """
        Initialize the InteropGreeter with configuration.

        Args:
            output_element_id (str, optional): ID of the HTML element for output display.
                                              Defaults to "chart".

        Example:
            >>> greeter = InteropGreeter()
            >>> greeter = InteropGreeter(output_element_id="output")
        """
        self.output_element_id = output_element_id
        self.greeting_variants = [
            "Hello", "Hi", "Hey", "Greetings", "Welcome",
            "What's up", "Howdy", "Yo", "Hola", "Salutations"
        ]

        # Initialize the output element with a welcome message
        self._initialize_display()

    def _initialize_display(self):
        """
        Initialize the output display with a welcome message.

        Sets up the initial state of the output element when the script loads.
        """
        chart = document.getElementById(self.output_element_id)
        if chart:
            chart.innerHTML = """
                <div class="text-center p-4">
                    <p class="text-2xl mb-2">🐍 Python is Ready!</p>
                    <p class="text-gray-600">Fill out the form to see JavaScript calling Python in action</p>
                </div>
            """
            console.log("✅ InteropGreeter initialized and ready")

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
            List[str]: A list of HTML-formatted response strings.
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
                'error': "<p class='text-red-600'>❌ <i>Name</i> is required!</p>"
            }

        if age is None or age == "":
            return {
                'valid': False,
                'error': "<p class='text-red-600'>❌ <i>Age</i> is required!</p>"
            }

        try:
            age_int = int(age)
            if age_int < 0:
                return {
                    'valid': False,
                    'error': "<p class='text-red-600'>❌ Age can't be negative! Time travel not supported yet.</p>"
                }
            if age_int > 150:
                return {
                    'valid': False,
                    'error': "<p class='text-red-600'>❌ Age seems a bit high! Are you a vampire? 🧛</p>"
                }
        except ValueError:
            return {
                'valid': False,
                'error': "<p class='text-red-600'>❌ Age must be a valid number!</p>"
            }

        return {'valid': True, 'error': None}

    def _generate_response_html(self, name: str, age: int) -> str:
        """
        Generate the complete HTML response for a valid greeting.

        Args:
            name (str): The user's name.
            age (int): The user's age.

        Returns:
            str: HTML-formatted response string.
        """
        greeting = self._get_greeting()
        category = self._categorize_age(age)
        age_responses = self._get_age_specific_responses(age, category)

        # Build the response HTML
        html_parts = [
            f"<div class='p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg'>",
            f"<p class='text-2xl font-bold mb-3'>{greeting}, <span class='text-blue-600'>{name}</span>! 👋</p>",
            f"<p class='text-gray-600 mb-2'>Age: {age} | Category: <span class='font-semibold capitalize'>{category}</span></p>",
            "<div class='mt-4 space-y-2'>"
        ]

        # Add age-specific responses
        for response in age_responses:
            html_parts.append(f"<p class='text-lg'>{response}</p>")

        # Add fun facts
        years_coding = max(0, age - 18) if age >= 18 else 0
        if years_coding > 0:
            html_parts.append(
                f"<p class='text-sm text-gray-500 mt-3'>🎂 Potential coding years: ~{years_coding}</p>"
            )

        # Add footer
        html_parts.extend([
            "</div>",
            "<p class='text-xs text-gray-400 mt-4 italic'>💬 Just kidding around! All developers are awesome! 🚀</p>",
            "</div>"
        ])

        return "".join(html_parts)

    def run(self, name: Optional[str], age: Optional[int]) -> None:
        """
        Main entry point called from JavaScript to generate a greeting.

        This method:
        1. Validates the input parameters
        2. Generates an appropriate response
        3. Updates the DOM with the result
        4. Logs the interaction to the console

        Args:
            name (Optional[str]): The user's name from the form input.
            age (Optional[int]): The user's age from the form input.

        Example (called from JavaScript):
            >>> run('Alice', 28)
            # Displays personalized greeting in the output element

        Note:
            This function is exposed to JavaScript and called via PyScript's
            interoperability features. See the Svelte component for the JS side.
        """
        console.log(f"🐍 Python function called with: name='{name}', age={age}")

        # Get the output element
        chart = document.getElementById(self.output_element_id)
        if not chart:
            console.error(f"❌ Output element '#{self.output_element_id}' not found!")
            return

        # Validate input
        validation = self._validate_input(name, age)
        if not validation['valid']:
            chart.innerHTML = validation['error']
            console.warn(f"⚠️ Validation failed: {validation['error']}")
            return

        # Generate and display response
        response_html = self._generate_response_html(name, int(age))
        chart.innerHTML = response_html

        console.log(f"✅ Greeting generated successfully for {name}, age {age}")


# Create a global instance of the greeter
_greeter_instance = InteropGreeter()


def run(name: Optional[str], age: Optional[int]) -> None:
    """
    Global function that exposes the greeter to JavaScript.

    This function acts as a bridge between JavaScript and the InteropGreeter class.
    It's called directly from JavaScript code via PyScript.

    Args:
        name (Optional[str]): The user's name.
        age (Optional[int]): The user's age.

    Example (from JavaScript):
        run('Bob', 35)
    """
    _greeter_instance.run(name, age)


# Log initialization
console.log("🐍 Interop module loaded successfully")
