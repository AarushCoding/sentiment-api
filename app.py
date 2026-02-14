import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
import nltk

app = Flask(__name__)
CORS(app)

# Pre-download required data
nltk.download('punkt_tab')

@app.route('/')
def home():
    return jsonify({"status": "active", "model": "Sentiment-v1"})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text'}), 400
    
    blob = TextBlob(data['text'])
    score = blob.sentiment.polarity
    # Confidence is roughly based on subjectivity (how factual vs opinionated)
    confidence = abs(blob.sentiment.subjectivity) * 100
    
    vibe = "Neutral"
    if score > 0.1: vibe = "Positive"
    elif score < -0.1: vibe = "Negative"
    
    return jsonify({
        'vibe': vibe,
        'score': round(score, 2),
        'confidence': f"{round(confidence, 1)}%"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
