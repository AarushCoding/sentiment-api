import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
import nltk

app = Flask(__name__)
CORS(app)

# Ensure NLTK is ready
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

@app.route('/')
def home():
    return jsonify({"status": "active"})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text'}), 400
    
    blob = TextBlob(data['text'])
    score = round(blob.sentiment.polarity, 3)
    # Subjectivity is a good proxy for confidence in sentiment analysis
    conf_value = 100 - (abs(blob.sentiment.subjectivity - 0.5) * 100)
    
    vibe = "Neutral"
    if score > 0.1: vibe = "Positive"
    elif score < -0.1: vibe = "Negative"
    
    return jsonify({
        'vibe': vibe,
        'score': score,
        'confidence': f"{round(max(min(conf_value, 99.9), 50.1), 1)}%"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
