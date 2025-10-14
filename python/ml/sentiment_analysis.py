"""
Sentiment Analysis with Active Learning

Interactive text classification using scikit-learn in PyScript.
Demonstrates proper class-based architecture with event-driven initialization.

Author: Guinetik
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from js import console, window, Object
from pyodide.http import open_url
from pyodide.ffi import to_js
import numpy as np
import pandas as pd
from lib.pyscript_manager import PyScriptManager


class SentimentAnalyzer:
    """
    Sentiment analysis classifier with active learning.

    Features:
    - TF-IDF feature extraction
    - Logistic regression classification
    - Active learning with user feedback
    - Three sentiment classes: positive, negative, neutral
    """

    # Sentiment label mapping
    SENTIMENT_TO_LABEL = {
        'positive': 1,
        'negative': 0,
        'neutral': 2
    }

    LABEL_TO_SENTIMENT = {0: 'negative', 1: 'positive', 2: 'neutral'}

    def __init__(self):
        """Initialize the sentiment analyzer."""
        print("🤖 Initializing Sentiment Analysis Model...")

        # Training data
        self.training_texts = []
        self.training_labels = []

        # ML components
        self.vectorizer = None
        self.classifier = None
        self.X_train = None
        self.y_train = None

        # Store last prediction for feedback
        self.last_prediction_data = {
            'text': None,
            'prediction': None,
            'features': None
        }

    def load_training_data(self):
        """Load training data from CSV."""
        try:
            print("📂 Loading training data from CSV...")

            # Load CSV file using open_url for PyScript
            df = pd.read_csv(open_url('/data/sentiment_training.csv'))

            print(f"✅ Loaded {len(df)} training examples from CSV")

            # Extract texts and labels
            self.training_texts = df['text'].tolist()
            self.training_labels = [
                self.SENTIMENT_TO_LABEL[sentiment.lower()]
                for sentiment in df['sentiment']
            ]

            print(f"📊 Dataset breakdown:")
            print(f"   Positive: {self.training_labels.count(1)}")
            print(f"   Negative: {self.training_labels.count(0)}")
            print(f"   Neutral: {self.training_labels.count(2)}")

            return True

        except Exception as e:
            print(f"❌ Error loading CSV: {str(e)}")
            console.error(f"❌ Error loading CSV: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)
            console.error(error_trace)
            return False

    def train_model(self):
        """Train the sentiment classifier."""
        print("📚 Training sentiment classifier...")

        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.X_train = self.vectorizer.fit_transform(self.training_texts)
        self.y_train = np.array(self.training_labels)

        # Train logistic regression classifier
        self.classifier = LogisticRegression(max_iter=1000, random_state=42)
        self.classifier.fit(self.X_train, self.y_train)

        # Calculate accuracy
        accuracy = self.classifier.score(self.X_train, self.y_train)

        print(f"✅ Model trained! Training accuracy: {accuracy * 100:.1f}%")
        print(f"📊 Training examples: {len(self.training_texts)}")

        return accuracy

    def get_model_stats(self):
        """Get current model statistics."""
        accuracy = 0
        if self.classifier and self.X_train is not None and self.y_train is not None:
            accuracy = self.classifier.score(self.X_train, self.y_train)

        return {
            'training_count': len(self.training_texts),
            'accuracy': accuracy,
            'positive_count': self.training_labels.count(1),
            'negative_count': self.training_labels.count(0),
            'neutral_count': self.training_labels.count(2)
        }

    def predict_sentiment(self, text):
        """
        Predict sentiment of input text.
        Sends data to JavaScript via callbacks.
        """
        try:
            if not text or text.strip() == "":
                if hasattr(window, 'onSentimentError'):
                    window.onSentimentError("Please enter some text to analyze!")
                return

            print(f"🔍 Analyzing: {text[:50]}...")

            # Transform text
            features = self.vectorizer.transform([text])

            # Get prediction
            prediction = self.classifier.predict(features)[0]
            probabilities = self.classifier.predict_proba(features)[0]

            # Store for potential correction
            self.last_prediction_data['text'] = text
            self.last_prediction_data['prediction'] = int(prediction)
            self.last_prediction_data['features'] = features

            # Prepare result data
            result = {
                'text': text,
                'sentiment': self.LABEL_TO_SENTIMENT[prediction],
                'label': int(prediction),
                'confidence': float(probabilities[prediction]),
                'probabilities': {
                    'positive': float(probabilities[1]),
                    'negative': float(probabilities[0]),
                    'neutral': float(probabilities[2])
                }
            }

            print(f"✅ Prediction: {result['sentiment']} ({result['confidence']*100:.1f}% confidence)")

            # Call JavaScript callback with result data
            if hasattr(window, 'onSentimentPrediction'):
                js_result = to_js(result, dict_converter=Object.fromEntries)
                window.onSentimentPrediction(js_result)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            console.error(f"❌ Error: {str(e)}")
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)
            console.error(error_trace)

            if hasattr(window, 'onSentimentError'):
                window.onSentimentError(str(e))

    def handle_correct_prediction(self):
        """Handle positive feedback - prediction was correct."""
        try:
            if self.last_prediction_data['text'] is None:
                if hasattr(window, 'onSentimentError'):
                    window.onSentimentError("No prediction to reinforce!")
                return

            correct_sentiment = self.last_prediction_data['prediction']
            text = self.last_prediction_data['text']

            print(f"✅ Reinforcing correct prediction: {self.LABEL_TO_SENTIMENT[correct_sentiment]}")

            # Add to training data
            self.training_texts.append(text)
            self.training_labels.append(int(correct_sentiment))

            print(f"📊 Training set size: {len(self.training_texts) - 1} → {len(self.training_texts)}")

            # Retrain
            self.X_train = self.vectorizer.fit_transform(self.training_texts)
            self.y_train = np.array(self.training_labels)
            self.classifier.fit(self.X_train, self.y_train)

            accuracy = self.classifier.score(self.X_train, self.y_train)
            print(f"✅ Model reinforced! New accuracy: {accuracy * 100:.1f}%")

            # Clear stored data
            self.last_prediction_data['text'] = None
            self.last_prediction_data['prediction'] = None

            # Call JavaScript callback with updated stats
            if hasattr(window, 'onModelUpdated'):
                update_data = {
                    'action': 'reinforced',
                    'sentiment': self.LABEL_TO_SENTIMENT[correct_sentiment],
                    'stats': self.get_model_stats()
                }
                js_update = to_js(update_data, dict_converter=Object.fromEntries)
                window.onModelUpdated(js_update)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            console.error(f"❌ Error: {str(e)}")
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError(f"Error reinforcing model: {str(e)}")

    def retrain_with_correction(self, correct_label):
        """Retrain with user correction."""
        try:
            correct_sentiment = int(correct_label)
            text = self.last_prediction_data['text']

            if text is None:
                if hasattr(window, 'onSentimentError'):
                    window.onSentimentError("No prediction to correct!")
                return

            old_prediction = self.last_prediction_data['prediction']
            print(f"🎓 Retraining: {self.LABEL_TO_SENTIMENT[old_prediction]} → {self.LABEL_TO_SENTIMENT[correct_sentiment]}")

            # Add corrected example
            self.training_texts.append(text)
            self.training_labels.append(correct_sentiment)

            print(f"📊 Training set size: {len(self.training_texts) - 1} → {len(self.training_texts)}")

            # Retrain
            self.X_train = self.vectorizer.fit_transform(self.training_texts)
            self.y_train = np.array(self.training_labels)
            self.classifier.fit(self.X_train, self.y_train)

            accuracy = self.classifier.score(self.X_train, self.y_train)
            print(f"✅ Model retrained! New accuracy: {accuracy * 100:.1f}%")

            # Clear stored data
            self.last_prediction_data['text'] = None
            self.last_prediction_data['prediction'] = None

            # Call JavaScript callback with updated stats
            if hasattr(window, 'onModelUpdated'):
                update_data = {
                    'action': 'retrained',
                    'old_sentiment': self.LABEL_TO_SENTIMENT[old_prediction],
                    'new_sentiment': self.LABEL_TO_SENTIMENT[correct_sentiment],
                    'stats': self.get_model_stats()
                }
                js_update = to_js(update_data, dict_converter=Object.fromEntries)
                window.onModelUpdated(js_update)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            console.error(f"❌ Error: {str(e)}")
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError(f"Error retraining: {str(e)}")

    def reset_training(self):
        """Reset to original training data."""
        try:
            print("🔄 Resetting to original training data...")

            # Reload from CSV
            if not self.load_training_data():
                if hasattr(window, 'onSentimentError'):
                    window.onSentimentError("Error reloading training data from CSV")
                return

            # Retrain
            accuracy = self.train_model()

            print(f"✅ Training reset! Examples: {len(self.training_texts)}")

            # Clear stored prediction
            self.last_prediction_data['text'] = None
            self.last_prediction_data['prediction'] = None

            # Call JavaScript callback
            if hasattr(window, 'onModelUpdated'):
                update_data = {
                    'action': 'reset',
                    'stats': self.get_model_stats()
                }
                js_update = to_js(update_data, dict_converter=Object.fromEntries)
                window.onModelUpdated(js_update)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            console.error(f"❌ Error: {str(e)}")
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError(f"Error resetting: {str(e)}")


# Create global instance and initialize
print("🟡 Creating SentimentAnalyzer instance...")
_analyzer = SentimentAnalyzer()

# Load training data and train model
try:
    if _analyzer.load_training_data():
        accuracy = _analyzer.train_model()

        # Notify JavaScript that model is ready
        print("🔔 Model ready, preparing to signal JavaScript...")

        # Get initial stats
        stats = _analyzer.get_model_stats()
        print(f"📊 Initial stats: {stats}")

        # Signal ready via PyScriptManager with exported functions
        manager = PyScriptManager("sentiment_analysis")
        manager.signal_ready(extra_exports={
            'predictSentiment': _analyzer.predict_sentiment,
            'handleCorrectPrediction': _analyzer.handle_correct_prediction,
            'retrainWithCorrection': _analyzer.retrain_with_correction,
            'resetTraining': _analyzer.reset_training,
            'getModelStats': _analyzer.get_model_stats
        })

        # Call onModelReady callback after signaling
        if hasattr(window, 'onModelReady'):
            js_stats = to_js(stats, dict_converter=Object.fromEntries)
            window.onModelReady(js_stats)
            print("✅ Model ready callback completed")

        print("✅ Sentiment Analysis module ready and signaled to JavaScript")
    else:
        console.error("❌ Failed to load training data")
        if hasattr(window, 'onSentimentError'):
            window.onSentimentError("Failed to load training data")

except Exception as e:
    print(f"❌ Error during initialization: {str(e)}")
    console.error(f"❌ Error during initialization: {str(e)}")
    import traceback
    error_trace = traceback.format_exc()
    print(error_trace)
    console.error(error_trace)
    if hasattr(window, 'onSentimentError'):
        window.onSentimentError(f"Initialization error: {str(e)}")
