from flask import Flask, request, jsonify
from flask_cors import CORS
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

# Allow your frontend to talk to the backend
CORS(app, resources={r"/*": {"origins": "*"}})

def scrape_amazon_reviews(url):
    """
    Attempts to scrape visible reviews from an Amazon.co.uk product page.
    Note: Amazon aggressively blocks scrapers.
    """
    # 1. Transform standard product links to the "All Reviews" page for easier scraping
    if "/dp/" in url:
        url = url.split("?")[0].replace("/dp/", "/product-reviews/") + "?reviewerType=all_reviews"
    
    # 2. Modern browser headers to mimic a real visitor
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # If Amazon blocks us with a 503 or CAPTCHA, return None
        if response.status_code != 200:
            print(f"Amazon returned status: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Amazon's review body selector
        review_elements = soup.select('[data-hook="review-body"]')
        
        if not review_elements:
            print("No review elements found. Might be a CAPTCHA page.")
            return None

        # Clean the text (remove "Read more", "Verified Purchase", etc.)
        reviews = [rev.get_text(strip=True) for rev in review_elements]
        return reviews

    except Exception as e:
        print(f"Scraper error: {e}")
        return None

@app.route('/')
def home():
    return "Sentiment API Online. Use /analyze or /analyze-amazon."

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a single snippet of text (Manual Input)"""
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
        
    text = data.get('text', '')
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    
    vibe = "Neutral"
    if score > 0.1: vibe = "Positive"
    elif score < -0.1: vibe = "Negative"
        
    return jsonify({
        'score': round(score, 3),
        'vibe': vibe
    })

@app.route('/analyze-amazon', methods=['POST'])
def analyze_amazon():
    """Scrape an Amazon URL and perform bulk sentiment analysis"""
    data = request.get_json(silent=True)
    url = data.get('url', '')
    
    if not url or "amazon.co.uk" not in url.lower():
        return jsonify({'error': 'Invalid Amazon.co.uk URL'}), 400

    raw_reviews = scrape_amazon_reviews(url)
    
    if not raw_reviews:
        return jsonify({'error': 'Amazon blocked the request or no reviews found. Try again in a minute.'}), 503

    results = []
    pos_count = 0
    neg_count = 0

    for text in raw_reviews:
        blob = TextBlob(text)
        score = blob.sentiment.polarity
        
        sentiment_type = "Neutral"
        if score > 0.1:
            sentiment_type = "Positive"
            pos_count += 1
        elif score < -0.1:
            sentiment_type = "Negative"
            neg_count += 1
            
        results.append({
            'text': text[:250] + ("..." if len(text) > 250 else ""), # Truncate for UI
            'score': round(score, 3),
            'type': sentiment_type
        })

    # Sort reviews by sentiment score
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'tally': {
            'positive': pos_count,
            'negative': neg_count,
            'total': len(raw_results)
        },
        'top_positive': sorted_results[:5],
        'top_negative': sorted_results[-5:][::-1] # Bottom 5, but most negative first
    })

if __name__ == '__main__':
    app.run(debug=True)
