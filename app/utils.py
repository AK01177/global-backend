import google.generativeai as genai
from flask import current_app
import os
import json
import time
import random

def configure_gemini():
    """Configure Gemini API with API key"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
        
    except Exception as e:
        current_app.logger.error(f"Error configuring Gemini: {str(e)}")
        return None

def summarize_news(articles, location_name, max_retries=3):
    """
    Summarize news articles using Gemini 1.5 Flash
    """
    try:
        model = configure_gemini()
        if not model:
            return "AI summarization service unavailable"
        
        # Prepare articles text
        articles_text = ""
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
            articles_text += f"\n--- Article {i} ---\n"
            articles_text += f"URL: {article.get('url', 'Unknown')}\n"
            articles_text += f"Content: {article.get('content', 'No content')}\n"
        
        # Create prompt
        prompt = f"""
        You are a professional news summarizer. Please provide a comprehensive and engaging summary of the latest news from {location_name} based on the following articles:

        {articles_text}

        Instructions:
        1. Create a well-structured summary that captures the most important news events
        2. Focus on recent developments, current events, and significant happenings
        3. Organize the information logically with clear sections if multiple topics are covered
        4. Use a professional but engaging tone
        5. Include specific details, dates, and key figures when available
        6. If there are multiple unrelated stories, organize them under appropriate headings
        7. Aim for 200-400 words
        8. End with a brief note about the general situation or outlook for the region

        Please provide only the summary without any meta-commentary about the task.
        """
        
        # Generate summary with retries
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                
                if response and response.text:
                    summary = response.text.strip()
                    
                    # Basic validation
                    if len(summary) > 50:  # Minimum length check
                        return summary
                    else:
                        current_app.logger.warning(f"Summary too short on attempt {attempt + 1}")
                
                # Add delay before retry
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                current_app.logger.error(f"Gemini API error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
                else:
                    # Final fallback
                    return create_fallback_summary(articles, location_name)
        
        return create_fallback_summary(articles, location_name)
        
    except Exception as e:
        current_app.logger.error(f"Error in summarize_news: {str(e)}")
        return create_fallback_summary(articles, location_name)

def create_fallback_summary(articles, location_name):
    """
    Create a basic summary when AI is unavailable
    """
    try:
        if not articles:
            return f"No recent news articles found for {location_name}. This could be due to limited coverage or search limitations."
        
        summary = f"Latest News from {location_name}:\n\n"
        
        for i, article in enumerate(articles[:3], 1):
            content = article.get('content', '')
            if content:
                # Extract first sentence or first 100 characters
                first_sentence = content.split('.')[0][:150]
                summary += f"{i}. {first_sentence}...\n\n"
        
        summary += f"Found {len(articles)} news articles related to {location_name}. "
        summary += "For more detailed information, please check the original news sources."
        
        return summary
        
    except Exception as e:
        current_app.logger.error(f"Error creating fallback summary: {str(e)}")
        return f"Unable to generate news summary for {location_name} at this time."

def validate_coordinates(lat, lng):
    """
    Validate latitude and longitude coordinates
    """
    try:
        lat = float(lat)
        lng = float(lng)
        
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        
        if not (-180 <= lng <= 180):
            return False, "Longitude must be between -180 and 180"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

def format_response(location, coordinates, summary, articles_count):
    """
    Format API response consistently
    """
    return {
        'location': location,
        'coordinates': coordinates,
        'summary': summary,
        'articles_count': articles_count,
        'timestamp': time.time(),
        'status': 'success'
    }

def sanitize_location_name(location):
    """
    Sanitize location name for search queries
    """
    if not location:
        return ""
    
    # Remove special characters that might interfere with search
    import re
    sanitized = re.sub(r'[^\w\s,.-]', '', location)
    
    # Remove extra whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip()

def estimate_api_usage():
    """
    Estimate daily API usage for rate limiting
    """
    try:
        log_file = os.path.join('Data', 'chatlog.json')
        
        if not os.path.exists(log_file):
            return 0
        
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        # Count requests from today
        from datetime import datetime, timedelta
        today = datetime.now().date()
        today_requests = 0
        
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp']).date()
                if log_date == today:
                    today_requests += 1
            except:
                continue
        
        return today_requests
        
    except Exception as e:
        current_app.logger.error(f"Error estimating API usage: {str(e)}")
        return 0

def check_rate_limit():
    """
    Check if we're approaching API rate limits
    """
    daily_usage = estimate_api_usage()
    
    # Gemini 1.5 Flash has 1500 requests per day
    if daily_usage >= 1400:
        return False, "Daily API limit nearly reached"
    
    return True, None