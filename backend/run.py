"""
Run script for the Flask application
This script sets up the Python path correctly
"""
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Now import and run the app
from app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

