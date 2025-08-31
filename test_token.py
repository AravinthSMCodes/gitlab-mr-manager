#!/usr/bin/env python3
"""
Script to test GitLab tokens and show user information
"""

import os
import requests
import json

def test_gitlab_token(token, gitlab_url="https://git.csez.zohocorpin.com"):
    """Test a GitLab token and return user information"""
    headers = {
        'PRIVATE-TOKEN': token
    }
    
    try:
        response = requests.get(f"{gitlab_url}/api/v4/user", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return {
                'success': True,
                'name': user_data.get('name', 'Unknown'),
                'username': user_data.get('username', 'Unknown'),
                'email': user_data.get('email', 'Unknown'),
                'bot': user_data.get('bot', False)
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("🔧 GitLab Token Tester")
    print("=" * 50)
    
    # Test current token
    current_token = os.getenv('GITLAB_TOKEN', 'NczS48B1EvysG2_jZtZ3')
    print(f"Current token: {current_token[:10]}...")
    
    result = test_gitlab_token(current_token)
    if result['success']:
        print(f"✅ Current user: {result['name']} (@{result['username']})")
        if result['bot']:
            print("🤖 This is a bot account")
        else:
            print("👤 This is a regular user account")
    else:
        print(f"❌ Error: {result['error']}")
    
    print("\n" + "=" * 50)
    print("To change the bot name, you can:")
    print("1. Create a new Personal Access Token from your GitLab account")
    print("2. Update the GITLAB_TOKEN environment variable")
    print("3. Or create a new bot account with a better name")
    print("\nExample:")
    print("export GITLAB_TOKEN='your_new_token_here'")
    print("python3 test_token.py")

if __name__ == "__main__":
    main()
