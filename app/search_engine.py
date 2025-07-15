import requests
from googlesearch import search
import time
from flask import current_app
import random

def search_news(location_name, max_results=10):
    """
    Search for news articles about a specific location
    Uses Google search with news-specific queries
    """
    try:
        # Create search queries for news
        queries = [
            f"{location_name} news today",
            f"{location_name} latest news",
            f"{location_name} current events",
            f"breaking news {location_name}",
            f"{location_name} recent developments"
        ]
        
        articles = []
        
        for query in queries:
            try:
                # Use googlesearch library with news domain preference
                search_results = search(
                    query,
                    num=max_results // len(queries) + 1,
                    stop=max_results // len(queries) + 1,
                    pause=2,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                
                for url in search_results:
                    # Filter for news websites
                    if is_news_website(url):
                        article_content = scrape_article_content(url)
                        if article_content:
                            articles.append({
                                'url': url,
                                'content': article_content,
                                'query': query
                            })
                            
                    if len(articles) >= max_results:
                        break
                
                # Add delay between queries
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                current_app.logger.error(f"Error searching for query '{query}': {str(e)}")
                continue
                
            if len(articles) >= max_results:
                break
        
        return articles[:max_results]
        
    except Exception as e:
        current_app.logger.error(f"Error in search_news: {str(e)}")
        return []

def is_news_website(url):
    """Check if URL is from a news website"""
    news_domains = [
        'bbc.com', 'cnn.com', 'reuters.com', 'ap.org', 'npr.org',
        'theguardian.com', 'nytimes.com', 'washingtonpost.com',
        'bloomberg.com', 'wsj.com', 'forbes.com', 'time.com',
        'newsweek.com', 'usatoday.com', 'abcnews.go.com',
        'cbsnews.com', 'nbcnews.com', 'foxnews.com', 'skynews.com',
        'news.google.com', 'yahoo.com/news', 'msn.com',
        'indianexpress.com', 'timesofindia.indiatimes.com', 'hindustantimes.com',
        'ndtv.com', 'republicworld.com', 'news18.com', 'zeenews.india.com',
        'aljazeera.com', 'dw.com', 'france24.com', 'euronews.com'
    ]
    
    return any(domain in url.lower() for domain in news_domains)

def scrape_article_content(url):
    """
    Scrape article content from URL
    Returns first few paragraphs of the article
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple text extraction (you might want to use BeautifulSoup for better parsing)
        content = response.text
        
        # Extract title and some content (basic approach)
        if '<title>' in content and '</title>' in content:
            title_start = content.find('<title>') + 7
            title_end = content.find('</title>')
            title = content[title_start:title_end].strip()
        else:
            title = "No title found"
        
        # Try to extract some paragraph content
        paragraphs = []
        if '<p>' in content:
            import re
            p_matches = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
            for p in p_matches[:3]:  # Get first 3 paragraphs
                # Remove HTML tags
                clean_p = re.sub(r'<[^>]+>', '', p).strip()
                if len(clean_p) > 50:  # Only include substantial paragraphs
                    paragraphs.append(clean_p)
        
        if paragraphs:
            return f"Title: {title}\n\n" + "\n\n".join(paragraphs)
        else:
            return f"Title: {title}\n\nContent extraction failed for this article."
        
    except Exception as e:
        current_app.logger.error(f"Error scraping article {url}: {str(e)}")
        return None

def search_with_custom_api(location_name):
    """
    Alternative search method using Google Custom Search API
    Requires GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in environment
    """
    try:
        import os
        api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        cx = os.getenv('GOOGLE_SEARCH_CX')
        
        if not api_key or not cx:
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cx,
            'q': f"{location_name} news",
            'num': 10,
            'sort': 'date'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json()
        articles = []
        
        for item in results.get('items', []):
            articles.append({
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'content': item.get('snippet', '')
            })
        
        return articles
        
    except Exception as e:
        current_app.logger.error(f"Error in custom search: {str(e)}")
        return []