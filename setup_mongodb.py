#!/usr/bin/env python3
"""
MongoDB Setup Script for GitLab MR Manager
Automates MongoDB installation and setup
"""

import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_mongodb_installed():
    """Check if MongoDB is already installed"""
    try:
        result = subprocess.run(['mongod', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB is already installed")
            print(f"Version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    return False

def install_mongodb_macos():
    """Install MongoDB on macOS"""
    print("🍎 Installing MongoDB on macOS...")
    
    # Try different installation methods
    methods = [
        ("brew tap mongodb/brew && brew install mongodb-community", "Homebrew MongoDB Community"),
        ("brew install mongodb", "Homebrew MongoDB"),
        ("brew install --cask mongodb-compass", "MongoDB Compass (GUI)")
    ]
    
    for command, description in methods:
        print(f"🔄 Trying {description}...")
        if run_command(command, f"Installing {description}"):
            return True
    
    print("❌ All installation methods failed")
    print("💡 Manual installation required:")
    print("   1. Download MongoDB from: https://www.mongodb.com/try/download/community")
    print("   2. Follow installation instructions for macOS")
    return False

def install_mongodb_ubuntu():
    """Install MongoDB on Ubuntu/Debian"""
    print("🐧 Installing MongoDB on Ubuntu/Debian...")
    
    commands = [
        ("sudo apt-get update", "Updating package list"),
        ("sudo apt-get install -y gnupg curl", "Installing prerequisites"),
        ("curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor", "Adding MongoDB GPG key"),
        ("echo 'deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list", "Adding MongoDB repository"),
        ("sudo apt-get update", "Updating package list"),
        ("sudo apt-get install -y mongodb-org", "Installing MongoDB"),
        ("sudo systemctl start mongod", "Starting MongoDB service"),
        ("sudo systemctl enable mongod", "Enabling MongoDB service")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def start_mongodb_service():
    """Start MongoDB service"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        commands = [
            ("brew services start mongodb-community", "Starting MongoDB Community"),
            ("brew services start mongodb", "Starting MongoDB"),
        ]
        
        for command, description in commands:
            if run_command(command, description):
                return True
        
        print("⚠️  Could not start MongoDB service automatically")
        print("💡 Please start MongoDB manually:")
        print("   mongod --config /usr/local/etc/mongod.conf")
        return False
        
    elif system == "linux":
        return run_command("sudo systemctl start mongod", "Starting MongoDB service")
    
    return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🧪 Testing MongoDB connection...")
    
    try:
        # Try to connect using mongosh or mongo
        test_commands = [
            "mongosh --eval 'db.runCommand({ping: 1})'",
            "mongo --eval 'db.runCommand({ping: 1})'"
        ]
        
        for command in test_commands:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("✅ MongoDB connection test successful")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        print("❌ MongoDB connection test failed")
        return False
        
    except Exception as e:
        print(f"❌ Error testing MongoDB connection: {e}")
        return False

def setup_mongodb_atlas():
    """Setup instructions for MongoDB Atlas (cloud)"""
    print("☁️  MongoDB Atlas Setup Instructions:")
    print("=" * 50)
    print("1. Go to https://www.mongodb.com/atlas")
    print("2. Create a free account")
    print("3. Create a new cluster")
    print("4. Get your connection string")
    print("5. Update your .env file with:")
    print("   export MONGO_URI='mongodb+srv://username:password@cluster.mongodb.net/'")
    print("   export MONGO_USER='your_username'")
    print("   export MONGO_PASSWORD='your_password'")
    print("=" * 50)

def main():
    """Main setup function"""
    print("🚀 MongoDB Setup for GitLab MR Manager")
    print("=" * 50)
    
    # Check if already installed
    if check_mongodb_installed():
        if start_mongodb_service():
            if test_mongodb_connection():
                print("🎉 MongoDB is ready to use!")
                return True
    
    # Detect operating system
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("🍎 Detected macOS")
        if install_mongodb_macos():
            if start_mongodb_service():
                if test_mongodb_connection():
                    print("🎉 MongoDB setup completed successfully!")
                    return True
    elif system == "linux":
        print("🐧 Detected Linux")
        if install_mongodb_ubuntu():
            if test_mongodb_connection():
                print("🎉 MongoDB setup completed successfully!")
                return True
    else:
        print(f"❌ Unsupported operating system: {system}")
        print("💡 Please install MongoDB manually:")
        print("   https://www.mongodb.com/try/download/community")
    
    print("\n❌ MongoDB setup failed")
    print("💡 Alternative: Use MongoDB Atlas (cloud)")
    setup_mongodb_atlas()
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
