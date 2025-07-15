from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

def create_app():
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Enable CORS for all domains and routes
    CORS(app, origins="*")
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app