from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# This setup explicitly allows all methods and headers to prevent "Failed to fetch"
CORS(app, resources={r"/*": {"origins": "*"}})

def scrape_amazon_reviews(url):
    if "/dp/" in url:
        url = url.split("?")[0].replace("/dp/", "/product-reviews/") + "?reviewerType=all_reviews"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        review_elements = soup.select('[data-hook="review-body"]')
        return [rev.get_text(strip=True) for rev in review_elements]
    except:
        return None

@app.route('/')
def home():
    return "API Online"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({'error': 'No text'}), 400
    
    score = TextBlob(data['text']).sentiment.polarity
    vibe = "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
    return jsonify({'score': round(score, 3), 'vibe': vibe})

@app.route('/analyze-amazon', methods=['POST'])
def analyze_amazon():
    data = request.get_json(silent=True)
    url = data.get('url', '')
    
    reviews = scrape_amazon_reviews(url)
    if not reviews:
        return jsonify({'error': 'Amazon blocked us or link invalid'}), 503

    results = []
    for text in reviews:
        score = TextBlob(text).sentiment.polarity
        results.append({'text': text[:200] + "...", 'score': round(score, 3)})

    sorted_res = sorted(results, key=lambda x: x['score'], reverse=True)
    
    pos = [r for r in results if r['score'] > 0.1]
    neg = [r for r in results if r['score'] < -0.1]

    return jsonify({
        'tally': {'positive': len(pos), 'negative': len(neg), 'total': len(results)},
        'top_positive': sorted_res[:5],
        'top_negative': sorted_res[-5:][::-1]
    })

if __name__ == '__main__':
    app.run(debug=True)
