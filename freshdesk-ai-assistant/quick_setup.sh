#!/bin/bash

# Quick setup script for the Freshdesk AI Assistant

echo "Setting up Freshdesk AI Assistant..."

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize the database
echo "Initializing database..."
python -c "from database.models import init_db; init_db()"

echo "Setup complete!"
echo "To run the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: python app.py"
echo "3. Open your browser and navigate to: http://localhost:8001"
