from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob

app = Flask(__name__)

# Use "*" temporarily to rule out domain/subdomain typos
# This allows the OPTIONS request to pass regardless of the origin
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Sentiment API is Online. Please use the /analyze endpoint via POST."

# Add 'OPTIONS' to methods to handle preflight checks manually if needed
@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    # Handle the Preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    text = data.get('text', '')
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    
    if score > 0.1:
        vibe = "Positive"
    elif score < -0.1:
        vibe = "Negative"
    else:
        vibe = "Neutral"
        
    return jsonify({
        'score': round(score, 3),
        'vibe': vibe
    })

if __name__ == '__main__':
    app.run(debug=True)
