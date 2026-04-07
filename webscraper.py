import requests
from bs4 import BeautifulSoup
import logging
import urllib.parse
import os
import sys
from flask import Blueprint, request, jsonify

# CRITICAL: Fix for Render/Gunicorn path resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Configure logging
logger = logging.getLogger(__name__)

# 1. Define the Blueprint that app.py is looking for
scraper_bp = Blueprint('webscraper', __name__)

class WebScraper:
    def __init__(self):
        """
        Mimic a real browser to avoid blocks.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def search(self, query):
        """
        Executes a search via Google and extracts top results.
        """
        try:
            logger.info(f"Scanning web for: {query}")
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract snippets from Google results
            # Note: Google's CSS classes change frequently; these are standard for current results
            for g in soup.find_all('div', class_='g')[:4]:
                anchors = g.find_all('a')
                if anchors:
                    link = anchors[0]['href']
                    title = g.find('h3').text if g.find('h3') else "No Title"
                    snippet = g.find('div', class_='VwiC3b') 
                    snippet_text = snippet.text if snippet else "No preview available."
                    
                    results.append(f"Title: {title}\nLink: {link}\nSummary: {snippet_text}\n")
            
            if not results:
                return "No high-confidence search results found."
                
            return "\n-----------------\n".join(results)
            
        except Exception as e:
            logger.error(f"Search Failure: {e}")
            return f"Error scanning web: {str(e)}"

# 2. Global Instance: For internal imports (chat_manager.py)
web_searcher = WebScraper()

# 3. Blueprint Routes: For API access
@scraper_bp.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"success": False, "error": "No query provided"}), 400
    
    query = data['query']
    results = web_searcher.search(query)
    return jsonify({
        "success": True,
        "query": query,
        "results": results
    })