from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob

app = Flask(__name__)

# Explicitly allow your frontend domain
CORS(app, resources={r"/*": {"origins": ["https://sentiment.aarushnaik.co.uk", "https://aarushnaik.co.uk"]}})

@app.route('/')
def home():
    return "Sentiment API is Online. Please use the /analyze endpoint via POST."
    
@app.route('/analyze', methods=['POST'])
def analyze():
    # Adding a simple check to ensure JSON was actually sent
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
