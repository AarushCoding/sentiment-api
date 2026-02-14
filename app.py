import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
from bs4 import BeautifulSoup
import nltk

# 1. Initialize Flask and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 2. Ensure NLTK data is available for TextBlob
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('brown')
    nltk.download('punkt_tab')

@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 3. Amazon Scraper Logic
def scrape_amazon_reviews(url):
    if "/dp/" in url:
        try:
            asin = url.split("/dp/")[1].split("/")[0].split("?")[0]
            url = f"https://www.amazon.co.uk/product-reviews/{asin}/?reviewerType=all_reviews"
        except:
            pass

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200 or "captcha" in response.text.lower():
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        review_elements = soup.select('.review-text-content span, [data-hook="review-body"] span')
        reviews = [rev.get_text(strip=True) for rev in review_elements if len(rev.get_text()) > 15]
        return reviews if reviews else None
    except Exception as e:
        print(f"Scrape error: {e}")
        return None

# 4. Routes
@app.route('/')
def home():
    return jsonify({
        "status": "API Online", 
        "owner": "Aarush Naik",
        "endpoints": ["/analyze", "/analyze-amazon"]
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    analysis = TextBlob(data['text'])
    score = analysis.sentiment.polarity
    
    vibe = "Neutral"
    if score > 0.1: vibe = "Positive"
    elif score < -0.1: vibe = "Negative"
    
    return jsonify({'score': round(score, 3), 'vibe': vibe})

@app.route('/analyze-amazon', methods=['POST'])
def analyze_amazon():
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    reviews = scrape_amazon_reviews(data['url'])
    if not reviews:
        return jsonify({'error': 'Amazon blocked or no reviews found'}), 503

    processed = []
    for text in reviews:
        score = TextBlob(text).sentiment.polarity
        processed.append({
            'text': text[:200] + "..." if len(text) > 200 else text,
            'score': round(score, 3)
        })

    return jsonify({
        'total_reviews': len(processed),
        'results': sorted(processed, key=lambda x: x['score'], reverse=True)
    })

# 5. THE CRITICAL FIX FOR RENDER
if __name__ == "__main__":
    # Render sets a PORT environment variable. We MUST use it.
    port = int(os.environ.get("PORT", 10000))
    # Using 0.0.0.0 is mandatory to allow external traffic
    app.run(host='0.0.0.0', port=port)
