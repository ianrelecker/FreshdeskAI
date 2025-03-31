#!/usr/bin/env python3
import os
import sys
import json
import logging
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Check Python version compatibility
if sys.version_info >= (3, 13):
    print("Warning: Python 3.13 may have compatibility issues with SQLAlchemy.")
    print("Proceeding anyway for testing purposes, but expect errors.")

from flask import Flask, render_template, flash, redirect, url_for
from markupsafe import Markup

from database.models import init_db
from web.routes import bp as main_bp
from utils.scheduler import setup_ticket_processing_jobs
from utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='static')
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Configure Flask
    app.config['SECRET_KEY'] = config['app'].get('secret_key', 'dev-key-change-this')
    app.config['DEBUG'] = config['app'].get('debug', False)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Initialize the database
    init_db()
    
    # Set up Jinja2 template filters
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format='%Y-%m-%d %H:%M %Z'):
        """Format a datetime object in PST timezone."""
        from pytz import timezone
        
        if value is None:
            return ''
        
        # Convert string to datetime if needed
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        
        # Convert to PST timezone
        pacific = timezone('US/Pacific')
        if value.tzinfo is None:
            # Assume UTC if no timezone info
            from pytz import utc
            value = utc.localize(value)
        
        # Convert to Pacific time
        value = value.astimezone(pacific)
        
        # Format with timezone abbreviation
        return value.strftime(format)
    
    @app.template_filter('status_color')
    def status_color_filter(status):
        """Map ticket status to a Bootstrap color class."""
        status_map = {
            'open': 'primary',
            'pending': 'warning',
            'resolved': 'success',
            'closed': 'secondary'
        }
        return status_map.get(status.lower() if status else '', 'info')
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        if not text:
            return ''
        return Markup(text.replace('\n', '<br>'))
    
    @app.template_filter('from_json')
    def from_json_filter(text):
        """Parse a JSON string into a Python object."""
        if not text:
            return []
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @app.context_processor
    def utility_processor():
        """Add utility functions to the template context."""
        def now(format_string=None):
            """Get the current datetime in PST timezone."""
            from pytz import timezone
            
            # Get current time in PST
            pacific = timezone('US/Pacific')
            current_time = datetime.now(pacific)
            
            if format_string:
                return current_time.strftime(format_string)
            return current_time
        
        return dict(now=now)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_code=500, error_message='Internal server error'), 500
    
    return app

def start_scheduler():
    """Start the background scheduler for ticket processing."""
    try:
        setup_ticket_processing_jobs()
        logger.info("Background scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {str(e)}")

if __name__ == '__main__':
    # Create the Flask app
    app = create_app()
    
    # Start the background scheduler
    start_scheduler()
    
    # Run the app
    app.run(host='0.0.0.0', port=8004)
