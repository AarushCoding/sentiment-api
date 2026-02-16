import os
import pickle
from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob

app = Flask(__name__)
CORS(app)

model = None
vectorizer = None

try:
    with open('spam_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
except Exception as e:
    print(f"Spam model load error: {e}")

@app.route('/')
def home():
    return jsonify({"status": "active", "systems": ["sentiment", "spam"]})

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text'}), 400
    blob = TextBlob(data['text'])
    score = round(blob.sentiment.polarity, 3)
    conf_value = 100 - (abs(blob.sentiment.subjectivity - 0.5) * 100)
    vibe = "Neutral"
    if score > 0.1: vibe = "Positive"
    elif score < -0.1: vibe = "Negative"
    return jsonify({
        'vibe': vibe,
        'score': score,
        'confidence': f"{round(max(min(conf_value, 99.9), 50.1), 1)}%"
    })

@app.route('/spam', methods=['POST'])
def analyze_spam():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text'}), 400
    if model is None or vectorizer is None:
        return jsonify({'error': 'Spam model missing'}), 500
    vec = vectorizer.transform([data['text']])
    prediction = model.predict(vec)[0]
    probs = model.predict_proba(vec)[0]
    label = "Spam" if prediction == 1 else "Ham"
    conf = probs[1] if prediction == 1 else probs[0]
    return jsonify({
        'label': label,
        'confidence': f"{round(conf * 100, 1)}%"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
