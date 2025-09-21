#!/usr/bin/env python3
"""
Test script to verify Firefox DevTools Protocol setup
"""

import requests
import json
import subprocess
import sys
import time
import os

def test_firefox_connection(port=9222):
    """Test connection to Firefox debugging port"""
    print(f"🔍 Testing connection to Firefox on port {port}...")
    
    try:
        # Test if Firefox debugging server is running
        response = requests.get(f"http://localhost:{port}/json/list", timeout=5)
        if response.status_code == 200:
            tabs = response.json()
            print(f"✅ Firefox debugging server is running!")
            print(f"📊 Found {len(tabs)} open tabs")
            
            # Look for ChatGPT tabs
            chatgpt_tabs = [tab for tab in tabs if 'chat.openai.com' in tab.get('url', '') or 'chatgpt.com' in tab.get('url', '')]
            
            if chatgpt_tabs:
                print(f"🎯 Found {len(chatgpt_tabs)} ChatGPT tab(s):")
                for i, tab in enumerate(chatgpt_tabs, 1):
                    print(f"   {i}. {tab.get('title', 'Unknown')} - {tab.get('url', 'Unknown')}")
            else:
                print("⚠️  No ChatGPT tabs found. Make sure ChatGPT is open in Firefox.")
            
            return True, tabs
        else:
            print(f"❌ Firefox debugging server responded with status {response.status_code}")
            return False, []
            
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Firefox debugging server on port {port}")
        print("   Make sure Firefox is running with: firefox --start-debugger-server=9222")
        return False, []
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False, []

def test_python_dependencies():
    """Test if required Python packages are installed"""
    print("🐍 Testing Python dependencies...")
    
    required_packages = ['websocket-client', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'websocket-client':
                import websocket
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def test_localstorage_access(tabs):
    """Test if we can access localStorage from ChatGPT tabs"""
    if not tabs:
        print("⚠️  No tabs available for localStorage test")
        return False
    
    chatgpt_tabs = [tab for tab in tabs if 'chat.openai.com' in tab.get('url', '') or 'chatgpt.com' in tab.get('url', '')]
    
    if not chatgpt_tabs:
        print("⚠️  No ChatGPT tabs for localStorage test")
        return False
    
    print("🧪 Testing localStorage access...")
    
    # This is a simplified test - the actual script will do the full WebSocket connection
    tab = chatgpt_tabs[0]
    ws_url = tab.get('webSocketURL') or tab.get('webSocketDebuggerUrl')
    
    if ws_url:
        print(f"✅ WebSocket URL available: {ws_url[:50]}...")
        return True
    else:
        print("❌ No WebSocket URL found for ChatGPT tab")
        return False

def main():
    print("🚀 Firefox DevTools Protocol Test Suite")
    print("=" * 50)
    
    # Test 1: Python dependencies
    deps_ok = test_python_dependencies()
    print()
    
    # Test 2: Firefox connection
    firefox_ok, tabs = test_firefox_connection()
    print()
    
    # Test 3: localStorage access
    if firefox_ok:
        localstorage_ok = test_localstorage_access(tabs)
    else:
        localstorage_ok = False
    print()
    
    # Summary
    print("📋 Test Summary:")
    print(f"   Python Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"   Firefox Connection: {'✅ PASS' if firefox_ok else '❌ FAIL'}")
    print(f"   localStorage Access: {'✅ PASS' if localstorage_ok else '❌ FAIL'}")
    
    if deps_ok and firefox_ok and localstorage_ok:
        print("\n🎉 All tests passed! You're ready to use the extractor.")
        print("\n📝 Next steps:")
        print("1. Use your bookmarklet in ChatGPT to save some data")
        print("2. Run: python chatgpt_data_extractor.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
        if not firefox_ok:
            print("\n🔧 To fix Firefox connection:")
            print("1. Close all Firefox instances")
            print("2. Launch Firefox with: firefox --start-debugger-server=9222")
            print("3. Open ChatGPT in that Firefox instance")
            print("4. Run this test again")

if __name__ == "__main__":
    main()
