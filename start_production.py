#!/usr/bin/env python3
"""
Production startup script for FinTrace
Alternative to gunicorn for environments where gunicorn might not be available
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set production environment variables
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Get host from environment or use default
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting FinTrace in production mode on {host}:{port}")
    print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"🔧 Debug mode: {os.environ.get('FLASK_DEBUG', '0')}")
    
    # Run the app
    app.run(host=host, port=port, debug=False)
