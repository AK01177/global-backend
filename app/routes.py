from flask import Blueprint, request, jsonify, current_app
from app.search_engine import search_news
from app.geocode import get_location_name
from app.utils import summarize_news
import json
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'GlobeScope AI Backend is running!'})

@main.route('/api/news', methods=['POST'])
def get_news():
    """Get news for a specific location"""
    try:
        data = request.get_json()
        
        if not data or 'lat' not in data or 'lng' not in data:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        lat = data['lat']
        lng = data['lng']
        
        # Get location name from coordinates
        location_name = get_location_name(lat, lng)
        if not location_name:
            return jsonify({'error': 'Could not determine location'}), 400
        
        # Search for news
        news_articles = search_news(location_name)
        if not news_articles:
            return jsonify({'error': 'No news found for this location'}), 404
        
        # Summarize news using Gemini
        summary = summarize_news(news_articles, location_name)
        if not summary:
            return jsonify({'error': 'Failed to generate news summary'}), 500
        
        # Log the request
        log_request(lat, lng, location_name, summary)
        
        response = {
            'location': location_name,
            'coordinates': {'lat': lat, 'lng': lng},
            'summary': summary,
            'articles_count': len(news_articles),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in get_news: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def log_request(lat, lng, location, summary):
    """Log requests to chatlog.json"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'coordinates': {'lat': lat, 'lng': lng},
            'location': location,
            'summary': summary[:200] + '...' if len(summary) > 200 else summary
        }
        
        log_file = os.path.join('Data', 'chatlog.json')
        
        # Create Data directory if it doesn't exist
        os.makedirs('Data', exist_ok=True)
        
        # Read existing logs
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 100 entries
        if len(logs) > 100:
            logs = logs[-100:]
        
        # Write back to file
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        current_app.logger.error(f"Error logging request: {str(e)}")

@main.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent request logs"""
    try:
        log_file = os.path.join('Data', 'chatlog.json')
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
            return jsonify(logs)
        else:
            return jsonify([])
            
    except Exception as e:
        current_app.logger.error(f"Error reading logs: {str(e)}")
        return jsonify({'error': 'Failed to read logs'}), 500