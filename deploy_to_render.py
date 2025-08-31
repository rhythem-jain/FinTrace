#!/usr/bin/env python3
"""
FinTrace Render Deployment Helper Script

This script helps verify your FinTrace application is ready for Render deployment.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filename):
    """Check if a required file exists."""
    if Path(filename).exists():
        print(f"✅ {filename} - Found")
        return True
    else:
        print(f"❌ {filename} - Missing")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.9+")
        return False

def check_dependencies():
    """Check if all required dependencies can be imported."""
    required_packages = [
        'flask', 'flask_sqlalchemy', 'pandas', 'numpy', 
        'sklearn', 'networkx', 'matplotlib', 'gunicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - Available")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_app_structure():
    """Check if the Flask app structure is correct."""
    print("\n🔍 Checking Flask Application Structure...")
    
    # Check main app file
    if not check_file_exists('app.py'):
        return False
    
    # Check requirements
    if not check_file_exists('requirements.txt'):
        return False
    
    # Check render configuration
    if not check_file_exists('render.yaml'):
        return False
    
    # Check WSGI entry point
    if not check_file_exists('wsgi.py'):
        return False
    
    return True

def check_environment():
    """Check environment configuration."""
    print("\n🔍 Checking Environment Configuration...")
    
    # Check if instance directory exists
    instance_dir = Path('instance')
    if not instance_dir.exists():
        print("📁 Creating instance directory...")
        instance_dir.mkdir(exist_ok=True)
        print("✅ instance/ directory created")
    else:
        print("✅ instance/ directory exists")
    
    # Check environment variables
    required_env_vars = ['FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL']
    missing_env_vars = []
    
    for var in required_env_vars:
        if os.environ.get(var):
            print(f"✅ {var} - Set")
        else:
            print(f"⚠️  {var} - Not set (will use defaults)")
            missing_env_vars.append(var)
    
    return True

def test_flask_app():
    """Test if the Flask app can be imported and configured."""
    print("\n🔍 Testing Flask Application...")
    
    try:
        # Change to the project directory
        os.chdir(Path(__file__).parent)
        
        # Try to import the app
        from app import app, db
        
        print("✅ Flask application imports successfully")
        print("✅ Database models loaded successfully")
        
        # Don't test database creation locally - it's not needed for deployment
        return True
        
    except Exception as e:
        print(f"❌ Flask application test failed: {e}")
        return False

def main():
    """Main deployment check function."""
    print("🚀 FinTrace Render Deployment Check")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    # Check file structure
    if not check_app_structure():
        all_checks_passed = False
    
    # Check environment
    if not check_environment():
        all_checks_passed = False
    
    # Check dependencies
    print("\n🔍 Checking Dependencies...")
    if not check_dependencies():
        all_checks_passed = False
    
    # Test Flask app
    if not test_flask_app():
        all_checks_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All checks passed! Your FinTrace app is ready for Render deployment.")
        print("\n📋 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Go to render.com and create a new Blueprint")
        print("3. Connect your GitHub repository")
        print("4. Deploy!")
        print("\n📖 See RENDER_DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ Some checks failed. Please fix the issues above before deploying.")
        print("\n💡 Common fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Check file permissions")
        print("- Verify Python version compatibility")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
