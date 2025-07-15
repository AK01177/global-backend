import requests
from flask import current_app
import os

def get_location_name(latitude, longitude):
    """
    Convert latitude and longitude to location name using reverse geocoding
    Uses OpenStreetMap Nominatim API (free) as primary method
    """
    try:
        # Try OpenStreetMap Nominatim first (free)
        location = get_location_nominatim(latitude, longitude)
        if location:
            return location
        
        # Fallback to Google Geocoding if available
        google_location = get_location_google(latitude, longitude)
        if google_location:
            return google_location
        
        # Final fallback - simple coordinate-based location
        return f"Location at {latitude:.4f}, {longitude:.4f}"
        
    except Exception as e:
        current_app.logger.error(f"Error in get_location_name: {str(e)}")
        return f"Location at {latitude:.4f}, {longitude:.4f}"

def get_location_nominatim(latitude, longitude):
    """
    Use OpenStreetMap Nominatim API for reverse geocoding (free)
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'accept-language': 'en'
        }
        
        headers = {
            'User-Agent': 'GlobeScope-AI/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'display_name' in data:
            # Extract meaningful location components
            address = data.get('address', {})
            
            # Build location name with priority: city, state/province, country
            location_parts = []
            
            # Add city/town/village
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('hamlet') or
                   address.get('municipality'))
            
            if city:
                location_parts.append(city)
            
            # Add state/province
            state = (address.get('state') or 
                    address.get('province') or
                    address.get('region'))
            
            if state and state not in location_parts:
                location_parts.append(state)
            
            # Add country
            country = address.get('country')
            if country and country not in location_parts:
                location_parts.append(country)
            
            if location_parts:
                return ', '.join(location_parts)
            else:
                return data['display_name'].split(',')[0]
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error in Nominatim geocoding: {str(e)}")
        return None

def get_location_google(latitude, longitude):
    """
    Use Google Geocoding API for reverse geocoding
    Requires GOOGLE_MAPS_API_KEY in environment variables
    """
    try:
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return None
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': api_key,
            'language': 'en'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            
            # Extract components
            components = result.get('address_components', [])
            
            location_parts = []
            
            # Find city, state, country
            city = None
            state = None
            country = None
            
            for component in components:
                types = component.get('types', [])
                
                if 'locality' in types or 'administrative_area_level_2' in types:
                    city = component['long_name']
                elif 'administrative_area_level_1' in types:
                    state = component['long_name']
                elif 'country' in types:
                    country = component['long_name']
            
            # Build location name
            if city:
                location_parts.append(city)
            if state:
                location_parts.append(state)
            if country:
                location_parts.append(country)
            
            if location_parts:
                return ', '.join(location_parts)
            else:
                return result.get('formatted_address', '').split(',')[0]
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error in Google geocoding: {str(e)}")
        return None

def get_country_from_coordinates(latitude, longitude):
    """
    Get country name from coordinates
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'accept-language': 'en'
        }
        
        headers = {
            'User-Agent': 'GlobeScope-AI/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'address' in data:
            return data['address'].get('country', 'Unknown')
        
        return 'Unknown'
        
    except Exception as e:
        current_app.logger.error(f"Error getting country: {str(e)}")
        return 'Unknown'