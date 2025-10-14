"""
Digit Recognition using scikit-learn K-Nearest Neighbors

This module provides an interactive digit recognition system that runs entirely
in the browser using PyScript. It demonstrates:
- Training a K-Nearest Neighbors classifier on the sklearn digits dataset
- Preprocessing user-drawn digits from an HTML canvas
- Making predictions with confidence scores
- Interactive retraining with user feedback

The system allows users to draw digits, get predictions, and correct the model
when it makes mistakes, providing a hands-on introduction to machine learning.

Author: Guinetik
"""

import base64
import io
import numpy as np
from sklearn import datasets
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from PIL import Image
from pyscript import document
from js import console, window, alert, Object
from pyodide.ffi import to_js
from typing import Tuple, Optional, Dict


class DigitRecognizer:
    """
    Interactive digit recognition system using K-Nearest Neighbors.

    This class encapsulates a complete digit recognition pipeline including:
    - Model training and evaluation
    - Image preprocessing from canvas drawings
    - Prediction with confidence scoring
    - Interactive retraining with user feedback
    - Visualization of model predictions and training data

    The recognizer uses the scikit-learn digits dataset (8x8 grayscale images)
    and a K-Nearest Neighbors classifier optimized for handwritten digit recognition.

    Attributes:
        classifier (KNeighborsClassifier): The trained KNN model.
        X_train (np.ndarray): Training feature data.
        y_train (np.ndarray): Training labels.
        X_test (np.ndarray): Test feature data.
        y_test (np.ndarray): Test labels.
        X_full (np.ndarray): Full dataset features (for examples).
        y_full (np.ndarray): Full dataset labels (for examples).
        accuracy (float): Current model accuracy on test set.
        last_prediction_data (Dict): Cached last prediction for retraining.
    """

    # Model hyperparameters
    N_NEIGHBORS = 5  # Number of neighbors to consider
    WEIGHT_METHOD = 'distance'  # Weight by inverse distance
    TEST_SIZE = 0.2  # 20% of data for testing
    RANDOM_STATE = 42  # For reproducibility

    # Image preprocessing constants
    TARGET_SIZE = 8  # sklearn digits are 8x8
    PIXEL_RANGE = 16.0  # sklearn digits use 0-16 scale
    THRESHOLD_RATIO = 0.10  # 10% of max for bounding box detection
    MIN_THRESHOLD = 20  # Minimum threshold value
    BORDER_RATIO = 0.20  # 20% border padding
    INTENSITY_TARGET_MAX = 13.0  # Target max intensity after scaling
    INTENSITY_PERCENTILE = 95  # Use 95th percentile for scaling

    def __init__(self):
        """
        Initialize the DigitRecognizer and train the initial model.

        Loads the sklearn digits dataset, splits it into train/test sets,
        trains a K-Nearest Neighbors classifier, and prepares the UI.
        """
        print("🔢 Initializing DigitRecognizer...")
        print("🔢 Initializing DigitRecognizer...")

        # Load dataset
        digits = datasets.load_digits()
        self.X_full = digits.data
        self.y_full = digits.target

        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X_full, self.y_full,
            test_size=self.TEST_SIZE,
            random_state=self.RANDOM_STATE
        )

        # Cache for last prediction (enables retraining)
        self.last_prediction_data: Dict[str, Optional[np.ndarray]] = {
            'image': None,
            'prediction': None
        }

        # Train initial model
        self._train_model()

        # Initialize UI
        self._initialize_ui()

        print("✅ DigitRecognizer ready!")
        print("✅ DigitRecognizer ready!")

    def _train_model(self):
        """
        Train (or retrain) the K-Nearest Neighbors classifier.

        Uses distance-weighted voting where closer neighbors have more influence.
        Calculates and logs the model accuracy on the test set.
        """
        print(f"🤖 Training K-Nearest Neighbors classifier (k={self.N_NEIGHBORS})...")
        print(f"🤖 Training K-Nearest Neighbors classifier (k={self.N_NEIGHBORS})...")

        self.classifier = KNeighborsClassifier(
            n_neighbors=self.N_NEIGHBORS,
            weights=self.WEIGHT_METHOD
        )
        self.classifier.fit(self.X_train, self.y_train)

        # Calculate accuracy
        self.accuracy = self.classifier.score(self.X_test, self.y_test)

        print(f"✅ Model trained! Accuracy: {self.accuracy * 100:.2f}%")
        print(f"✅ Model trained! Accuracy: {self.accuracy * 100:.2f}%")

    def _initialize_ui(self):
        """
        Set up the initial user interface state.

        Updates Svelte stores with initial model state and ready message.
        """
        # Update model state
        model_data = to_js({
            'accuracy': self.accuracy * 100,
            'trainingExamples': len(self.X_train)
        })
        window.updateModelState(model_data)

        # Update UI state to ready
        window.updateUIState('ready', 'Draw a digit and click Predict')

    def _preprocess_image(self, image_base64: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess canvas image to match sklearn digits format (8x8 grayscale).

        The preprocessing pipeline:
        1. Decode base64 image to PIL Image
        2. Convert to grayscale and invert colors
        3. Find bounding box of digit (remove whitespace)
        4. Crop to bounding box
        5. Make square and center the digit
        6. Add 20% border padding (matches training data)
        7. Resize to 8x8 using high-quality LANCZOS resampling
        8. Normalize to 0-16 range (sklearn digits format)
        9. Apply intensity scaling to match training data distribution

        Args:
            image_base64 (str): Base64 encoded image from HTML canvas.

        Returns:
            Tuple[np.ndarray, np.ndarray]: (flattened_array, 8x8_array)
                - flattened_array: 64-element array for prediction
                - 8x8_array: 2D array for visualization

        Raises:
            ValueError: If image is empty or cannot be processed.
        """
        # Remove data URL prefix if present
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        # Decode and open image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to grayscale and invert (white digit on black background)
        image = image.convert('L')
        img_array = np.array(image)
        img_array = 255 - img_array  # Invert

        print(f"📐 Original image shape: {img_array.shape}")
        print(f"📐 Original image shape: {img_array.shape}")

        # Find bounding box using adaptive thresholding
        threshold = max(self.MIN_THRESHOLD, img_array.max() * self.THRESHOLD_RATIO)
        print(f"🎯 Using threshold: {threshold:.1f} (max pixel: {img_array.max()})")
        print(f"🎯 Using threshold: {threshold:.1f} (max pixel: {img_array.max()})")

        rows = np.any(img_array > threshold, axis=1)
        cols = np.any(img_array > threshold, axis=0)

        if not rows.any() or not cols.any():
            print("⚠️ No digit detected - canvas might be empty")
            empty = np.zeros((self.TARGET_SIZE, self.TARGET_SIZE))
            return empty.flatten(), empty

        # Crop to bounding box
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        cropped = img_array[rmin:rmax+1, cmin:cmax+1]

        print(f"✂️ Cropping to bounding box: rows {rmin}-{rmax}, cols {cmin}-{cmax}")
        print(f"✂️ Cropping to bounding box: rows {rmin}-{rmax}, cols {cmin}-{cmax}")

        # Make square by adding padding
        cropped_img = Image.fromarray(cropped.astype('uint8'))
        width, height = cropped_img.size
        size = max(width, height)

        square_img = Image.new('L', (size, size), color=0)
        paste_x = (size - width) // 2
        paste_y = (size - height) // 2
        square_img.paste(cropped_img, (paste_x, paste_y))

        print(f"📦 Squared and centered: {size}×{size}")
        print(f"📦 Squared and centered: {size}×{size}")

        # Add border padding (matches training data)
        border = max(4, int(size * self.BORDER_RATIO))
        padded_size = size + 2 * border
        padded_img = Image.new('L', (padded_size, padded_size), color=0)
        padded_img.paste(square_img, (border, border))

        print(f"📦 Added {int(self.BORDER_RATIO * 100)}% border: {border}px, final size: {padded_size}×{padded_size}")
        print(f"📦 Added {int(self.BORDER_RATIO * 100)}% border: {border}px, final size: {padded_size}×{padded_size}")

        # Resize to 8x8 using high-quality resampling
        final_img = padded_img.resize((self.TARGET_SIZE, self.TARGET_SIZE), Image.Resampling.LANCZOS)
        image_array = np.array(final_img)

        # Normalize to 0-16 range
        image_array = (image_array / 255.0 * self.PIXEL_RANGE)

        print(f"🔍 Before intensity correction - min: {image_array.min():.2f}, max: {image_array.max():.2f}, mean: {image_array.mean():.2f}")
        print(f"🔍 Before intensity correction - min: {image_array.min():.2f}, max: {image_array.max():.2f}, mean: {image_array.mean():.2f}")

        # Apply intensity scaling to match training data
        if image_array.max() > 0:
            current_max = np.percentile(image_array, self.INTENSITY_PERCENTILE)
            if current_max > 0:
                scale_factor = self.INTENSITY_TARGET_MAX / current_max
                image_array = np.clip(image_array * scale_factor, 0, self.PIXEL_RANGE)
                print(f"⚡ Applied intensity scaling factor: {scale_factor:.2f}")
                print(f"⚡ Applied intensity scaling factor: {scale_factor:.2f}")

        # Log final array for debugging
        print("🔍 Final 8x8 array:")
        print("🔍 Final 8x8 array:")
        for row in image_array:
            row_str = " ".join([f"{val:4.1f}" for val in row])
            print(f"   {row_str}")
            print(f"   {row_str}")

        print(f"🔍 Final stats - min: {image_array.min():.2f}, max: {image_array.max():.2f}, mean: {image_array.mean():.2f}")
        print(f"🔍 Final stats - min: {image_array.min():.2f}, max: {image_array.max():.2f}, mean: {image_array.mean():.2f}")
        print(f"🔍 Training data stats - min: {self.X_full.min():.2f}, max: {self.X_full.max():.2f}, mean: {self.X_full.mean():.2f}")
        print(f"🔍 Training data stats - min: {self.X_full.min():.2f}, max: {self.X_full.max():.2f}, mean: {self.X_full.mean():.2f}")

        return image_array.flatten(), image_array

    def _create_visualization_html(self, image_2d: np.ndarray) -> str:
        """
        Create HTML visualization of the 8x8 processed image.

        Args:
            image_2d (np.ndarray): 8x8 array of pixel values (0-16 range).

        Returns:
            str: HTML string showing the 8x8 grid with grayscale colors.
        """
        viz_html = "<div class='grid grid-cols-8 gap-0 mx-auto' style='width: 160px;'>"
        for val in image_2d.flatten():
            intensity = int((val / self.PIXEL_RANGE) * 255)
            viz_html += f"<div style='width: 20px; height: 20px; background: rgb({intensity},{intensity},{intensity});'></div>"
        viz_html += "</div>"
        return viz_html

    def _create_prediction_ui(self, prediction: int, confidence: float,
                             probabilities: np.ndarray, image_2d: np.ndarray):
        """
        Update the UI with prediction results via Svelte stores.

        Args:
            prediction (int): Predicted digit (0-9).
            confidence (float): Confidence percentage (0-100).
            probabilities (np.ndarray): Probability distribution for all digits.
            image_2d (np.ndarray): 8x8 array of the processed image.
        """
        # Convert numpy arrays to Python lists for JSON serialization
        probabilities_list = probabilities.tolist()
        image_2d_list = image_2d.tolist()
        image_flat_list = image_2d.flatten().tolist()

        # Update prediction result store - convert to JS object
        prediction_data = to_js({
            'prediction': int(prediction),
            'confidence': float(confidence),
            'probabilities': probabilities_list,
            'imageData': image_flat_list,
            'imageData2D': image_2d_list
        })
        print(f"🟡 [PY] Calling window.updatePredictionResult with prediction={prediction}, confidence={confidence}")
        print(f"🟡 [PY] Calling window.updatePredictionResult with prediction={prediction}, confidence={confidence}")
        window.updatePredictionResult(prediction_data)

        # Update model state - convert to JS object
        model_data = to_js({
            'accuracy': self.accuracy * 100,
            'trainingExamples': len(self.X_train)
        })
        print(f"🟡 [PY] Calling window.updateModelState")
        print(f"🟡 [PY] Calling window.updateModelState")
        window.updateModelState(model_data)

    def predict_digit(self, image_base64: str):
        """
        Predict the digit drawn on the canvas.

        This is the main entry point for predictions, called from JavaScript.
        Processes the image, makes a prediction, and updates the UI with results.

        Args:
            image_base64 (str): Base64 encoded image from HTML canvas.
        """
        try:
            print("🟡 [PY] predict_digit() called")
            print("🟡 [PY] predict_digit() called")
            print("🎨 Processing image...")
            print("🎨 Processing image...")

            # Preprocess image
            processed_flat, processed_2d = self._preprocess_image(image_base64)

            # Cache for potential retraining
            self.last_prediction_data['image'] = processed_flat.copy()

            # Make prediction
            processed_image = processed_flat.reshape(1, -1)
            prediction = self.classifier.predict(processed_image)[0]
            self.last_prediction_data['prediction'] = prediction

            # Get confidence scores
            probabilities = self.classifier.predict_proba(processed_image)[0]
            confidence = probabilities[prediction] * 100

            print(f"✅ Predicted: {prediction} (confidence: {confidence:.1f}%)")
            print(f"✅ Predicted: {prediction} (confidence: {confidence:.1f}%)")

            # Log all predictions
            print("📊 All predictions:")
            for i, prob in enumerate(probabilities):
                if prob > 0.01:
                    print(f"   Digit {i}: {prob*100:.1f}%")

            # Update UI via Svelte stores
            self._create_prediction_ui(prediction, confidence, probabilities, processed_2d)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            console.error(f"❌ Error: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)
            console.error(error_trace)

            # Update UI to error state
            window.updateUIState('error', str(e))

    def show_correction_input(self):
        """Show the correction input form when user indicates prediction was wrong."""
        try:
            yes_no_buttons = document.getElementById("yes-no-buttons")
            if yes_no_buttons:
                yes_no_buttons.style.display = "none"

            correction_form = document.getElementById("correction-form")
            if correction_form:
                correction_form.style.display = "block"

        except Exception as e:
            print(f"❌ Error showing correction form: {str(e)}")
            console.error(f"❌ Error showing correction form: {str(e)}")

    def handle_correct_prediction(self):
        """
        Retrain the model with the correct prediction to reinforce it.

        Adds the current drawing to the training set with its predicted label,
        effectively reinforcing the model's correct behavior.
        """
        try:
            if self.last_prediction_data['image'] is None or self.last_prediction_data['prediction'] is None:
                alert("No prediction to reinforce. Draw a digit first!")
                return

            correct_digit = self.last_prediction_data['prediction']

            print(f"✅ Reinforcing correct prediction: {correct_digit}")
            print(f"✅ Reinforcing correct prediction: {correct_digit}")

            # Add to training data
            self.X_train = np.vstack([self.X_train, self.last_prediction_data['image'].reshape(1, -1)])
            self.y_train = np.append(self.y_train, correct_digit)

            print(f"📊 Training set size increased to: {len(self.X_train)}")
            print(f"📊 Training set size increased to: {len(self.X_train)}")

            # Retrain
            self._train_model()

            # Update UI via stores - convert to JS objects
            model_data = to_js({
                'accuracy': self.accuracy * 100,
                'trainingExamples': len(self.X_train)
            })
            window.updateModelState(model_data)
            window.updateUIState('reinforced', f'Your drawing of {correct_digit} was added to reinforce the model')
            window.updatePredictionResult(None)  # Clear prediction

            # Clear cache
            self.last_prediction_data['image'] = None
            self.last_prediction_data['prediction'] = None

        except Exception as e:
            print(f"❌ Reinforcement error: {str(e)}")
            console.error(f"❌ Reinforcement error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            console.error(traceback.format_exc())
            alert(f"Error reinforcing model: {str(e)}")

    def retrain_with_correction(self):
        """
        Retrain the model with a user-corrected example.

        Allows the user to provide the correct label when the model makes
        a mistake, adding the corrected example to the training set.
        """
        try:
            # Get user input
            correct_input = document.getElementById("correct-digit-input")
            if not correct_input or not correct_input.value:
                alert("Please enter the correct digit (0-9)")
                return

            correct_digit = int(correct_input.value)
            if correct_digit < 0 or correct_digit > 9:
                alert("Please enter a digit between 0 and 9")
                return

            if self.last_prediction_data['image'] is None:
                alert("No prediction to correct. Draw a digit first!")
                return

            print(f"🎓 Retraining with correction: {self.last_prediction_data['prediction']} → {correct_digit}")
            print(f"🎓 Retraining with correction: {self.last_prediction_data['prediction']} → {correct_digit}")

            # Add corrected example to training data
            self.X_train = np.vstack([self.X_train, self.last_prediction_data['image'].reshape(1, -1)])
            self.y_train = np.append(self.y_train, correct_digit)

            print(f"📊 Training set size increased to: {len(self.X_train)}")
            print(f"📊 Training set size increased to: {len(self.X_train)}")

            # Retrain
            self._train_model()

            # Update UI via stores - convert to JS objects
            model_data = to_js({
                'accuracy': self.accuracy * 100,
                'trainingExamples': len(self.X_train)
            })
            window.updateModelState(model_data)
            window.updateUIState('retrained', f'Added your drawing as a {correct_digit} to the training set')
            window.updatePredictionResult(None)  # Clear prediction

            # Clear cache
            self.last_prediction_data['image'] = None
            self.last_prediction_data['prediction'] = None

        except Exception as e:
            print(f"❌ Retrain error: {str(e)}")
            console.error(f"❌ Retrain error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            console.error(traceback.format_exc())
            alert(f"Error retraining: {str(e)}")

    def reset_training(self):
        """
        Reset the model to the original training dataset.

        Discards all user-added examples and retrains on the original sklearn
        digits dataset, effectively resetting the model to its initial state.
        """
        try:
            print("🔄 Resetting training data to original dataset...")
            print("🔄 Resetting training data to original dataset...")

            # Reset to original split
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                self.X_full, self.y_full,
                test_size=self.TEST_SIZE,
                random_state=self.RANDOM_STATE
            )

            print(f"📊 Training set reset to original size: {len(self.X_train)}")
            print(f"📊 Training set reset to original size: {len(self.X_train)}")

            # Retrain
            self._train_model()

            # Update UI via stores - convert to JS objects
            model_data = to_js({
                'accuracy': self.accuracy * 100,
                'trainingExamples': len(self.X_train)
            })
            window.updateModelState(model_data)
            window.updateUIState('reset', 'Model restored to original training dataset')
            window.updatePredictionResult(None)  # Clear prediction

            # Clear cache
            self.last_prediction_data['image'] = None
            self.last_prediction_data['prediction'] = None

        except Exception as e:
            print(f"❌ Reset error: {str(e)}")
            console.error(f"❌ Reset error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            console.error(traceback.format_exc())
            alert(f"Error resetting training: {str(e)}")

    def show_training_examples(self):
        """Show training examples of 4s and 9s for comparison."""
        training_div = document.getElementById("training-examples")
        if not training_div:
            return

        # Get indices of 4s and 9s
        fours_idx = [i for i, label in enumerate(self.y_full) if label == 4]
        nines_idx = [i for i, label in enumerate(self.y_full) if label == 9]

        output = """
        <div class="rounded-lg bg-purple-50 p-4 mb-4">
            <h3 class="font-bold text-center mb-3">Training Data Examples</h3>
            <p class="text-sm text-center mb-4">Here's what the model was trained on:</p>
        """

        # Show 4s
        output += "<div class='mb-4'><h4 class='font-bold text-center mb-2'>Training 4s:</h4><div class='flex justify-center gap-2 flex-wrap'>"
        for idx in fours_idx[:5]:
            digit_data = self.X_full[idx].reshape(8, 8)
            viz = "<div class='grid grid-cols-8 gap-0' style='width: 80px;'>"
            for val in digit_data.flatten():
                intensity = int((val / self.PIXEL_RANGE) * 255)
                viz += f"<div style='width: 10px; height: 10px; background: rgb({intensity},{intensity},{intensity});'></div>"
            viz += "</div>"
            output += viz
        output += "</div></div>"

        # Show 9s
        output += "<div class='mb-4'><h4 class='font-bold text-center mb-2'>Training 9s:</h4><div class='flex justify-center gap-2 flex-wrap'>"
        for idx in nines_idx[:5]:
            digit_data = self.X_full[idx].reshape(8, 8)
            viz = "<div class='grid grid-cols-8 gap-0' style='width: 80px;'>"
            for val in digit_data.flatten():
                intensity = int((val / self.PIXEL_RANGE) * 255)
                viz += f"<div style='width: 10px; height: 10px; background: rgb({intensity},{intensity},{intensity});'></div>"
            viz += "</div>"
            output += viz
        output += "</div></div>"

        output += """
            <button onclick="window.hideTrainingExamples()"
                    class="w-full mt-2 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500">
                Hide Examples
            </button>
        </div>
        """

        training_div.innerHTML = output

    def hide_training_examples(self):
        """Hide the training examples display."""
        training_div = document.getElementById("training-examples")
        if training_div:
            training_div.innerHTML = ""

    def clear_and_reset(self):
        """Clear the canvas and reset the display to initial state."""
        # Clear canvas
        canvas = document.getElementById("drawCanvas")
        if canvas:
            ctx = canvas.getContext("2d")
            ctx.fillStyle = "white"
            ctx.fillRect(0, 0, canvas.width, canvas.height)

        # Reset displays via stores
        self._initialize_ui()
        window.updatePredictionResult(None)  # Clear prediction


# Create global instance
_recognizer = DigitRecognizer()

# Expose methods to JavaScript
window.showTrainingExamples = _recognizer.show_training_examples
window.hideTrainingExamples = _recognizer.hide_training_examples
window.retrainWithCorrection = _recognizer.retrain_with_correction
window.resetTraining = _recognizer.reset_training
window.handleCorrectPrediction = _recognizer.handle_correct_prediction
window.showCorrectionInput = _recognizer.show_correction_input
window.clearAndReset = _recognizer.clear_and_reset

# Make predict_digit accessible from window (for runCode to find it)
def predict_digit(image_base64: str):
    """Global function to predict digit (called from JavaScript)."""
    print("🟡 [PY] Global predict_digit() called")
    print("🟡 [PY] Global predict_digit() called")
    _recognizer.predict_digit(image_base64)

# Expose to window
window.predict_digit = predict_digit
