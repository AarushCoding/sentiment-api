from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# robust CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def scrape_amazon_reviews(url):
    # Convert standard product link to the dedicated reviews page
    if "/dp/" in url:
        try:
            parts = url.split("/dp/")[1].split("/")
            asin = parts[0].split("?")[0]
            url = f"https://www.amazon.co.uk/product-reviews/{asin}/?reviewerType=all_reviews"
        except:
            pass

    session = requests.Session()
    
    # Precise headers to mimic a high-end desktop browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive"
    }

    try:
        # Hit the homepage first to establish a session/cookie context
        session.get("https://www.amazon.co.uk", headers=headers, timeout=5)
        
        # Small delay to mimic human behavior
        time.sleep(1)
        
        response = session.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None

        # Check if the page is a "Sorry, we're just checking you're a human" CAPTCHA page
        if "api-services-support@amazon.com" in response.text or "captcha" in response.text.lower():
            print("Amazon triggered a CAPTCHA challenge.")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectors for the review text
        review_elements = soup.select('.review-text-content span, [data-hook="review-body"] span')
        
        # Filter out very short strings (like "Read more")
        reviews = [rev.get_text(strip=True) for rev in review_elements if len(rev.get_text()) > 15]
        
        return reviews if reviews else None
    except Exception as e:
        print(f"Error during scrape: {e}")
        return None

@app.route('/')
def home():
    return jsonify({"status": "API Online", "endpoints": ["/analyze", "/analyze-amazon"]})

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
    
    return jsonify({
        'score': round(score, 3),
        'vibe': vibe
    })

@app.route('/analyze-amazon', methods=['POST'])
def analyze_amazon():
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    url = data.get('url', '')
    reviews = scrape_amazon_reviews(url)
    
    if not reviews:
        return jsonify({'error': 'Amazon blocked the request or the link is invalid.'}), 503

    processed = []
    for text in reviews:
        score = TextBlob(text).sentiment.polarity
        processed.append({
            'text': text[:250] + "..." if len(text) > 250 else text,
            'score': round(score, 3)
        })

    # Sort results by score (descending)
    sorted_results = sorted(processed, key=lambda x: x['score'], reverse=True)
    
    pos_tally = len([r for r in processed if r['score'] > 0.1])
    neg_tally = len([r for r in processed if r['score'] < -0.1])

    return jsonify({
        'tally': {
            'positive': pos_tally,
            'negative': neg_tally,
            'total': len(processed)
        },
        'top_positive': sorted_results[:5],
        'top_negative': sorted_results[-5:][::-1]
    })

if __name__ == '__main__':
    app.run(debug=True)
