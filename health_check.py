"""
Completely isolated health check for Render deployment
This module has ZERO dependencies on the main app or database
"""

def create_health_check():
    """Create a health check function that returns a simple response"""
    def health_check():
        return "OK", 200
    return health_check

# This can be imported and used without any database access
if __name__ == "__main__":
    print("Health check module loaded successfully")
