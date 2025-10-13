"""
Simple Sentiment Analysis with Active Learning
Demonstrates text classification using scikit-learn in PyScript
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from pyscript import document
from js import console, window, alert
from pyodide.http import open_url
import numpy as np
import pandas as pd

# Training data will be loaded from CSV
training_texts = []
training_labels = []

# Sentiment label mapping
sentiment_to_label = {
    'positive': 1,
    'negative': 0,
    'neutral': 2
}

# Global variables
vectorizer = None
classifier = None
X_train = None
y_train = None

# Store last prediction for feedback
last_prediction_data = {
    'text': None,
    'prediction': None,
    'features': None
}

print("🤖 Initializing Sentiment Analysis Model...")
console.log("🤖 Initializing Sentiment Analysis Model...")

def load_training_data():
    """Load training data from CSV"""
    global training_texts, training_labels

    try:
        print("📂 Loading training data from CSV...")
        console.log("📂 Loading training data from CSV...")

        # Load CSV file using open_url for PyScript
        df = pd.read_csv(open_url('/data/sentiment_training.csv'))

        print(f"✅ Loaded {len(df)} training examples from CSV")
        console.log(f"✅ Loaded {len(df)} training examples from CSV")

        # Extract texts and labels
        training_texts = df['text'].tolist()
        training_labels = [sentiment_to_label[sentiment.lower()] for sentiment in df['sentiment']]

        print(f"📊 Dataset breakdown:")
        print(f"   Positive: {training_labels.count(1)}")
        print(f"   Negative: {training_labels.count(0)}")
        print(f"   Neutral: {training_labels.count(2)}")

        console.log(f"📊 Dataset breakdown:")
        console.log(f"   Positive: {training_labels.count(1)}")
        console.log(f"   Negative: {training_labels.count(0)}")
        console.log(f"   Neutral: {training_labels.count(2)}")

        return True

    except Exception as e:
        print(f"❌ Error loading CSV: {str(e)}")
        console.error(f"❌ Error loading CSV: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        console.error(error_trace)
        return False

def train_model():
    """Train the sentiment classifier"""
    global vectorizer, classifier, X_train, y_train

    print("📚 Training sentiment classifier...")
    console.log("📚 Training sentiment classifier...")

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    X_train = vectorizer.fit_transform(training_texts)
    y_train = np.array(training_labels)

    # Train logistic regression classifier
    classifier = LogisticRegression(max_iter=1000, random_state=42)
    classifier.fit(X_train, y_train)

    # Calculate accuracy (just for display)
    accuracy = classifier.score(X_train, y_train)

    print(f"✅ Model trained! Training accuracy: {accuracy * 100:.1f}%")
    console.log(f"✅ Model trained! Training accuracy: {accuracy * 100:.1f}%")
    print(f"📊 Training examples: {len(training_texts)}")
    console.log(f"📊 Training examples: {len(training_texts)}")

    return accuracy

def predict_sentiment(text):
    """Predict sentiment of input text"""
    try:
        if not text or text.strip() == "":
            alert("Please enter some text to analyze!")
            return

        print(f"🔍 Analyzing: {text}")
        console.log(f"🔍 Analyzing: {text}")

        # Transform text
        features = vectorizer.transform([text])

        # Get prediction
        prediction = classifier.predict(features)[0]
        probabilities = classifier.predict_proba(features)[0]
        confidence = probabilities[prediction] * 100

        # Store for potential correction
        last_prediction_data['text'] = text
        last_prediction_data['prediction'] = prediction
        last_prediction_data['features'] = features

        # Map labels
        sentiment_map = {0: "Negative", 1: "Positive", 2: "Neutral"}
        emoji_map = {0: "😞", 1: "😊", 2: "😐"}
        color_map = {0: "red", 1: "green", 2: "yellow"}

        sentiment = sentiment_map[prediction]
        emoji = emoji_map[prediction]
        color = color_map[prediction]

        print(f"✅ Prediction: {sentiment} ({confidence:.1f}% confidence)")
        console.log(f"✅ Prediction: {sentiment} ({confidence:.1f}% confidence)")

        # Display all probabilities
        print("📊 All predictions:")
        for i, label in sentiment_map.items():
            prob = probabilities[i] * 100
            print(f"   {label}: {prob:.1f}%")

        # Display result
        result_div = document.getElementById("result")
        if result_div:
            result_div.innerHTML = f"""
            <div class="rounded-lg bg-{color}-50 p-6 mb-4 border-2 border-{color}-200">
                <div class="text-center mb-4">
                    <div class="text-6xl mb-2">{emoji}</div>
                    <h3 class="text-3xl font-bold text-{color}-700 mb-2">{sentiment}</h3>
                    <p class="text-lg text-gray-600">{confidence:.1f}% confident</p>
                </div>

                <div class="mt-4">
                    <h4 class="font-semibold text-sm text-gray-700 mb-2">All Scores:</h4>
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-sm">😊 Positive</span>
                            <div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
                                <div class="bg-green-500 h-2 rounded-full" style="width: {probabilities[1] * 100}%"></div>
                            </div>
                            <span class="text-sm font-medium">{probabilities[1] * 100:.1f}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-sm">😐 Neutral</span>
                            <div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
                                <div class="bg-yellow-500 h-2 rounded-full" style="width: {probabilities[2] * 100}%"></div>
                            </div>
                            <span class="text-sm font-medium">{probabilities[2] * 100:.1f}%</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <span class="text-sm">😞 Negative</span>
                            <div class="flex-1 mx-3 bg-gray-200 rounded-full h-2">
                                <div class="bg-red-500 h-2 rounded-full" style="width: {probabilities[0] * 100}%"></div>
                            </div>
                            <span class="text-sm font-medium">{probabilities[0] * 100:.1f}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="rounded-lg bg-blue-50 p-4 border-2 border-blue-200" id="feedback-box">
                <h4 class="font-bold mb-2 text-center text-blue-900">Was this prediction correct?</h4>
                <p class="text-xs text-center text-gray-600 mb-3">Help improve the model!</p>
                <div class="flex gap-2" id="yes-no-buttons">
                    <button
                        onclick="window.handleCorrectPrediction()"
                        class="flex-1 rounded bg-green-400 px-4 py-3 text-white hover:bg-green-500 font-bold text-lg">
                        ✓ YES
                    </button>
                    <button
                        onclick="window.showCorrectionInput()"
                        class="flex-1 rounded bg-red-400 px-4 py-3 text-white hover:bg-red-500 font-bold text-lg">
                        ✗ NO
                    </button>
                </div>
                <div id="correction-form" style="display: none;">
                    <div class="mb-3">
                        <label class="text-sm font-medium block mb-1">What's the correct sentiment?</label>
                        <select
                            id="correct-sentiment-input"
                            class="w-full px-3 py-2 border rounded">
                            <option value="1">😊 Positive</option>
                            <option value="2">😐 Neutral</option>
                            <option value="0">😞 Negative</option>
                        </select>
                    </div>
                    <div class="flex gap-2">
                        <button
                            onclick="window.retrainWithCorrection()"
                            class="flex-1 rounded bg-orange-400 px-3 py-2 text-white hover:bg-orange-500 font-medium">
                            🎓 Retrain Model
                        </button>
                        <button
                            onclick="window.resetTraining()"
                            class="flex-1 rounded bg-gray-400 px-3 py-2 text-white hover:bg-gray-500 font-medium">
                            🔄 Reset Training
                        </button>
                    </div>
                </div>
            </div>

            <p class="text-xs text-center text-gray-500 mt-4">
                Training examples: {len(training_texts)} | Model: TF-IDF + Logistic Regression
            </p>
            """

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        console.error(error_trace)

        result_div = document.getElementById("result")
        if result_div:
            result_div.innerHTML = f"""
            <div class="rounded-lg bg-red-100 p-4 text-center border-2 border-red-300">
                <p class="text-2xl font-bold mb-2 text-red-600">Error!</p>
                <p class="text-sm text-red-700">{str(e)}</p>
            </div>
            """

def show_correction_input():
    """Show the correction input form"""
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

def handle_correct_prediction():
    """Handle positive feedback - prediction was correct"""
    global training_texts, training_labels, X_train, y_train, classifier

    try:
        if last_prediction_data['text'] is None:
            alert("No prediction to reinforce!")
            return

        correct_sentiment = last_prediction_data['prediction']
        text = last_prediction_data['text']

        print(f"✅ Reinforcing correct prediction: {correct_sentiment}")
        console.log(f"✅ Reinforcing correct prediction: {correct_sentiment}")

        # Add to training data
        training_texts.append(text)
        training_labels.append(int(correct_sentiment))

        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")
        console.log(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")

        # Retrain
        X_train = vectorizer.fit_transform(training_texts)
        y_train = np.array(training_labels)
        classifier.fit(X_train, y_train)

        accuracy = classifier.score(X_train, y_train)
        print(f"✅ Model reinforced! New accuracy: {accuracy * 100:.1f}%")
        console.log(f"✅ Model reinforced! New accuracy: {accuracy * 100:.1f}%")

        sentiment_map = {0: "Negative", 1: "Positive", 2: "Neutral"}

        # Update display
        result_div = document.getElementById("result")
        if result_div:
            result_div.innerHTML = f"""
            <div class="rounded-lg bg-green-100 p-4 text-center border-2 border-green-400">
                <p class="text-3xl mb-2">✅</p>
                <p class="font-bold mb-1 text-green-900">Great! Model Learned!</p>
                <p class="text-sm text-gray-700">Your feedback has been added to reinforce the model</p>
                <p class="text-xs text-gray-600 mt-2">Training examples: {len(training_texts)}</p>
                <button onclick="window.clearAndReset()"
                        class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500">
                    Analyze Another Text
                </button>
            </div>
            """

        # Clear stored data
        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        alert(f"Error reinforcing model: {str(e)}")

def retrain_with_correction():
    """Retrain with user correction"""
    global training_texts, training_labels, X_train, y_train, classifier

    try:
        correct_input = document.getElementById("correct-sentiment-input")
        if not correct_input:
            alert("Error: correction input not found")
            return

        correct_sentiment = int(correct_input.value)
        text = last_prediction_data['text']

        if text is None:
            alert("No prediction to correct!")
            return

        print(f"🎓 Retraining with correction: {last_prediction_data['prediction']} → {correct_sentiment}")
        console.log(f"🎓 Retraining with correction: {last_prediction_data['prediction']} → {correct_sentiment}")

        # Add corrected example
        training_texts.append(text)
        training_labels.append(correct_sentiment)

        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")
        console.log(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")

        # Retrain
        X_train = vectorizer.fit_transform(training_texts)
        y_train = np.array(training_labels)
        classifier.fit(X_train, y_train)

        accuracy = classifier.score(X_train, y_train)
        print(f"✅ Model retrained! New accuracy: {accuracy * 100:.1f}%")
        console.log(f"✅ Model retrained! New accuracy: {accuracy * 100:.1f}%")

        sentiment_map = {0: "Negative", 1: "Positive", 2: "Neutral"}

        # Update display
        result_div = document.getElementById("result")
        if result_div:
            result_div.innerHTML = f"""
            <div class="rounded-lg bg-green-100 p-4 text-center border-2 border-green-400">
                <p class="text-3xl mb-2">✅</p>
                <p class="font-bold mb-1 text-green-900">Model Retrained!</p>
                <p class="text-sm text-gray-700">Added your correction as <strong>{sentiment_map[correct_sentiment]}</strong></p>
                <p class="text-xs text-gray-600 mt-2">Training examples: {len(training_texts)}</p>
                <button onclick="window.clearAndReset()"
                        class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500">
                    Analyze Another Text
                </button>
            </div>
            """

        # Clear stored data
        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        alert(f"Error retraining: {str(e)}")

def reset_training():
    """Reset to original training data"""
    global training_texts, training_labels

    try:
        print("🔄 Resetting to original training data...")
        console.log("🔄 Resetting to original training data...")

        # Reload from CSV
        if not load_training_data():
            alert("Error reloading training data from CSV")
            return

        # Retrain
        accuracy = train_model()

        print(f"✅ Training reset! Examples: {len(training_texts)}")
        console.log(f"✅ Training reset! Examples: {len(training_texts)}")

        result_div = document.getElementById("result")
        if result_div:
            result_div.innerHTML = f"""
            <div class="rounded-lg bg-blue-100 p-4 text-center border-2 border-blue-400">
                <p class="text-3xl mb-2">🔄</p>
                <p class="font-bold mb-1 text-blue-900">Training Reset!</p>
                <p class="text-sm text-gray-700">Model restored to original training data</p>
                <p class="text-xs text-gray-600 mt-2">Training examples: {len(training_texts)}</p>
                <button onclick="window.clearAndReset()"
                        class="mt-3 rounded bg-blue-400 px-3 py-2 text-sm text-white hover:bg-blue-500">
                    Analyze Text
                </button>
            </div>
            """

        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        alert(f"Error resetting: {str(e)}")

def clear_and_reset():
    """Clear input and reset display"""
    text_input = document.getElementById("text-input")
    if text_input:
        text_input.value = ""

    result_div = document.getElementById("result")
    if result_div:
        result_div.innerHTML = f"""
        <div class="rounded-lg bg-blue-100 p-4 text-center border-2 border-blue-300">
            <p class="text-3xl mb-2">🤖</p>
            <p class="font-bold mb-1">Sentiment Analyzer Ready!</p>
            <p class="text-sm text-gray-600">Enter text above and click Analyze</p>
            <p class="text-xs text-gray-500 mt-2">Training examples: {len(training_texts)}</p>
        </div>
        """

# Load training data and train the model on page load
if load_training_data():
    accuracy = train_model()
else:
    accuracy = 0
    print("❌ Failed to load training data")
    console.error("❌ Failed to load training data")

# Expose functions to JavaScript
window.predictSentiment = predict_sentiment
window.handleCorrectPrediction = handle_correct_prediction
window.showCorrectionInput = show_correction_input
window.retrainWithCorrection = retrain_with_correction
window.resetTraining = reset_training
window.clearAndReset = clear_and_reset

# Show ready message
result_div = document.getElementById("result")
if result_div:
    result_div.innerHTML = f"""
    <div class="rounded-lg bg-blue-100 p-4 text-center border-2 border-blue-300">
        <p class="text-3xl mb-2">🤖</p>
        <p class="font-bold mb-1">Sentiment Analyzer Ready!</p>
        <p class="text-sm text-gray-600">Enter text above and click Analyze</p>
        <p class="text-xs text-gray-500 mt-2">Training examples: {len(training_texts)} | Accuracy: {accuracy * 100:.1f}%</p>
    </div>
    """.format(accuracy * 100, len(training_texts))
