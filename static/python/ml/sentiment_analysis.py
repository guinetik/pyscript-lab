"""
Simple Sentiment Analysis with Active Learning
Demonstrates text classification using scikit-learn in PyScript

Pure Python implementation - no HTML generation.
Communicates with Svelte via callbacks.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from pyscript import window
from js import console, Object
from pyodide.http import open_url
from pyodide.ffi import to_js
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

label_to_sentiment = {0: 'negative', 1: 'positive', 2: 'neutral'}

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
print("🤖 Initializing Sentiment Analysis Model...")

def load_training_data():
    """Load training data from CSV"""
    global training_texts, training_labels

    try:
        print("📂 Loading training data from CSV...")
        print("📂 Loading training data from CSV...")

        # Load CSV file using open_url for PyScript
        df = pd.read_csv(open_url('/data/sentiment_training.csv'))

        print(f"✅ Loaded {len(df)} training examples from CSV")
        print(f"✅ Loaded {len(df)} training examples from CSV")

        # Extract texts and labels
        training_texts = df['text'].tolist()
        training_labels = [sentiment_to_label[sentiment.lower()] for sentiment in df['sentiment']]

        print(f"📊 Dataset breakdown:")
        print(f"   Positive: {training_labels.count(1)}")
        print(f"   Negative: {training_labels.count(0)}")
        print(f"   Neutral: {training_labels.count(2)}")

        print(f"📊 Dataset breakdown:")
        print(f"   Positive: {training_labels.count(1)}")
        print(f"   Negative: {training_labels.count(0)}")
        print(f"   Neutral: {training_labels.count(2)}")

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
    print("📚 Training sentiment classifier...")

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    X_train = vectorizer.fit_transform(training_texts)
    y_train = np.array(training_labels)

    # Train logistic regression classifier
    classifier = LogisticRegression(max_iter=1000, random_state=42)
    classifier.fit(X_train, y_train)

    # Calculate accuracy
    accuracy = classifier.score(X_train, y_train)

    print(f"✅ Model trained! Training accuracy: {accuracy * 100:.1f}%")
    print(f"✅ Model trained! Training accuracy: {accuracy * 100:.1f}%")
    print(f"📊 Training examples: {len(training_texts)}")
    print(f"📊 Training examples: {len(training_texts)}")

    return accuracy

def get_model_stats():
    """Get current model statistics"""
    accuracy = 0
    if classifier and X_train is not None and y_train is not None:
        accuracy = classifier.score(X_train, y_train)

    return {
        'training_count': len(training_texts),
        'accuracy': accuracy,
        'positive_count': training_labels.count(1),
        'negative_count': training_labels.count(0),
        'neutral_count': training_labels.count(2)
    }

def predict_sentiment(text):
    """
    Predict sentiment of input text.
    Calls Svelte callback with prediction data.
    """
    try:
        if not text or text.strip() == "":
            # Call Svelte error callback
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError("Please enter some text to analyze!")
            return

        print(f"🔍 Analyzing: {text}")
        print(f"🔍 Analyzing: {text}")

        # Transform text
        features = vectorizer.transform([text])

        # Get prediction
        prediction = classifier.predict(features)[0]
        probabilities = classifier.predict_proba(features)[0]

        # Store for potential correction
        last_prediction_data['text'] = text
        last_prediction_data['prediction'] = int(prediction)
        last_prediction_data['features'] = features

        # Prepare result data
        result = {
            'text': text,
            'sentiment': label_to_sentiment[prediction],
            'label': int(prediction),
            'confidence': float(probabilities[prediction]),
            'probabilities': {
                'positive': float(probabilities[1]),
                'negative': float(probabilities[0]),
                'neutral': float(probabilities[2])
            }
        }

        print(f"✅ Prediction: {result['sentiment']} ({result['confidence']*100:.1f}% confidence)")
        print(f"✅ Prediction: {result['sentiment']} ({result['confidence']*100:.1f}% confidence)")

        # Call Svelte callback with result data - convert to JS object
        if hasattr(window, 'onSentimentPrediction'):
            # Convert Python dict to JavaScript object with nested dict support
            js_result = to_js(result, dict_converter=Object.fromEntries)
            window.onSentimentPrediction(js_result)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        console.error(error_trace)

        # Call Svelte error callback
        if hasattr(window, 'onSentimentError'):
            window.onSentimentError(str(e))

def handle_correct_prediction():
    """Handle positive feedback - prediction was correct"""
    global training_texts, training_labels, X_train, y_train, classifier

    try:
        if last_prediction_data['text'] is None:
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError("No prediction to reinforce!")
            return

        correct_sentiment = last_prediction_data['prediction']
        text = last_prediction_data['text']

        print(f"✅ Reinforcing correct prediction: {label_to_sentiment[correct_sentiment]}")
        print(f"✅ Reinforcing correct prediction: {label_to_sentiment[correct_sentiment]}")

        # Add to training data
        training_texts.append(text)
        training_labels.append(int(correct_sentiment))

        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")
        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")

        # Retrain
        X_train = vectorizer.fit_transform(training_texts)
        y_train = np.array(training_labels)
        classifier.fit(X_train, y_train)

        accuracy = classifier.score(X_train, y_train)
        print(f"✅ Model reinforced! New accuracy: {accuracy * 100:.1f}%")
        print(f"✅ Model reinforced! New accuracy: {accuracy * 100:.1f}%")

        # Clear stored data
        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

        # Call Svelte callback with updated stats - convert to JS object
        if hasattr(window, 'onModelUpdated'):
            update_data = {
                'action': 'reinforced',
                'sentiment': label_to_sentiment[correct_sentiment],
                'stats': get_model_stats()
            }
            js_update = to_js(update_data, dict_converter=Object.fromEntries)
            window.onModelUpdated(js_update)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        if hasattr(window, 'onSentimentError'):
            window.onSentimentError(f"Error reinforcing model: {str(e)}")

def retrain_with_correction(correct_label):
    """Retrain with user correction"""
    global training_texts, training_labels, X_train, y_train, classifier

    try:
        correct_sentiment = int(correct_label)
        text = last_prediction_data['text']

        if text is None:
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError("No prediction to correct!")
            return

        old_prediction = last_prediction_data['prediction']
        print(f"🎓 Retraining with correction: {label_to_sentiment[old_prediction]} → {label_to_sentiment[correct_sentiment]}")
        print(f"🎓 Retraining with correction: {label_to_sentiment[old_prediction]} → {label_to_sentiment[correct_sentiment]}")

        # Add corrected example
        training_texts.append(text)
        training_labels.append(correct_sentiment)

        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")
        print(f"📊 Training set size: {len(training_texts) - 1} → {len(training_texts)}")

        # Retrain
        X_train = vectorizer.fit_transform(training_texts)
        y_train = np.array(training_labels)
        classifier.fit(X_train, y_train)

        accuracy = classifier.score(X_train, y_train)
        print(f"✅ Model retrained! New accuracy: {accuracy * 100:.1f}%")
        print(f"✅ Model retrained! New accuracy: {accuracy * 100:.1f}%")

        # Clear stored data
        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

        # Call Svelte callback with updated stats - convert to JS object
        if hasattr(window, 'onModelUpdated'):
            update_data = {
                'action': 'retrained',
                'old_sentiment': label_to_sentiment[old_prediction],
                'new_sentiment': label_to_sentiment[correct_sentiment],
                'stats': get_model_stats()
            }
            js_update = to_js(update_data, dict_converter=Object.fromEntries)
            window.onModelUpdated(js_update)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        if hasattr(window, 'onSentimentError'):
            window.onSentimentError(f"Error retraining: {str(e)}")

def reset_training():
    """Reset to original training data"""
    global training_texts, training_labels

    try:
        print("🔄 Resetting to original training data...")
        print("🔄 Resetting to original training data...")

        # Reload from CSV
        if not load_training_data():
            if hasattr(window, 'onSentimentError'):
                window.onSentimentError("Error reloading training data from CSV")
            return

        # Retrain
        accuracy = train_model()

        print(f"✅ Training reset! Examples: {len(training_texts)}")
        print(f"✅ Training reset! Examples: {len(training_texts)}")

        # Clear stored prediction
        last_prediction_data['text'] = None
        last_prediction_data['prediction'] = None

        # Call Svelte callback - convert to JS object
        if hasattr(window, 'onModelUpdated'):
            update_data = {
                'action': 'reset',
                'stats': get_model_stats()
            }
            js_update = to_js(update_data, dict_converter=Object.fromEntries)
            window.onModelUpdated(js_update)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        console.error(f"❌ Error: {str(e)}")
        if hasattr(window, 'onSentimentError'):
            window.onSentimentError(f"Error resetting: {str(e)}")

# Load training data and train the model on page load
try:
    if load_training_data():
        accuracy = train_model()
        # Notify Svelte that model is ready - convert to JS object
        print("🔔 Calling onModelReady callback...")
        print("🔔 Calling onModelReady callback...")

        if hasattr(window, 'onModelReady'):
            stats = get_model_stats()
            print(f"🔔 Stats: {stats}")
            print(f"🔔 Stats: {stats}")

            js_stats = to_js(stats, dict_converter=Object.fromEntries)
            print(f"🔔 Converted stats: {js_stats}")
            print(f"🔔 Converted stats type: {type(js_stats)}")

            window.onModelReady(js_stats)
            print("🔔 onModelReady callback completed")
            print("🔔 onModelReady callback completed")
        else:
            console.error("❌ window.onModelReady not found!")
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

# Expose functions to JavaScript
window.predictSentiment = predict_sentiment
window.handleCorrectPrediction = handle_correct_prediction
window.retrainWithCorrection = retrain_with_correction
window.resetTraining = reset_training
window.getModelStats = get_model_stats

print("✅ Sentiment Analysis module loaded")
