#!/usr/bin/env python3
"""
Redis Setup Script for GitLab MR Manager
This script helps set up Redis for caching functionality.
"""

import subprocess
import sys
import os

def check_redis_installed():
    """Check if Redis is installed"""
    try:
        result = subprocess.run(['redis-server', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_redis_macos():
    """Install Redis on macOS using Homebrew"""
    print("Installing Redis on macOS...")
    try:
        subprocess.run(['brew', 'install', 'redis'], check=True)
        print("✅ Redis installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Redis. Please install Homebrew first.")
        return False
    except FileNotFoundError:
        print("❌ Homebrew not found. Please install Homebrew first:")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        return False

def install_redis_ubuntu():
    """Install Redis on Ubuntu/Debian"""
    print("Installing Redis on Ubuntu/Debian...")
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'], check=True)
        print("✅ Redis installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Redis.")
        return False

def start_redis_service():
    """Start Redis service"""
    print("Starting Redis service...")
    try:
        # Try to start Redis service
        subprocess.run(['brew', 'services', 'start', 'redis'], 
                      capture_output=True, text=True)
        print("✅ Redis service started!")
        return True
    except FileNotFoundError:
        # Try systemctl for Linux
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                          capture_output=True, text=True)
            print("✅ Redis service started!")
            return True
        except FileNotFoundError:
            print("⚠️  Could not start Redis service automatically.")
            print("   Please start Redis manually:")
            print("   - macOS: brew services start redis")
            print("   - Linux: sudo systemctl start redis-server")
            return False

def test_redis_connection():
    """Test Redis connection"""
    print("Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful!")
        return True
    except ImportError:
        print("❌ Redis Python package not installed.")
        print("   Run: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Redis Setup for GitLab MR Manager")
    print("=" * 40)
    
    # Check if Redis is installed
    if check_redis_installed():
        print("✅ Redis is already installed!")
    else:
        print("❌ Redis is not installed.")
        
        # Detect OS and install Redis
        if sys.platform == "darwin":  # macOS
            if not install_redis_macos():
                return
        elif sys.platform.startswith("linux"):  # Linux
            if not install_redis_ubuntu():
                return
        else:
            print("❌ Unsupported operating system.")
            print("   Please install Redis manually for your OS.")
            return
    
    # Start Redis service
    start_redis_service()
    
    # Test connection
    if test_redis_connection():
        print("\n🎉 Redis setup completed successfully!")
        print("\nYour GitLab MR Manager application is ready to use Redis caching.")
        print("The following endpoints will now be cached for 24 hours:")
        print("  - /api/labels")
        print("  - /api/reviewers") 
        print("  - /api/authors")
        print("\nCache management endpoints:")
        print("  - GET /api/cache/status - Check cache status")
        print("  - POST /api/cache/clear - Clear all cache")
        print("  - POST /api/cache/clear/<type> - Clear specific cache (labels/reviewers/authors)")
    else:
        print("\n❌ Redis setup incomplete. Please check the errors above.")

if __name__ == "__main__":
    main()
