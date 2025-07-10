#!/usr/bin/env python3
"""
Simple test script for Indonesian Mental Health Support Bot
Tests basic functionality and API endpoints
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_openai_api_key():
    """Test if OpenAI API key is available"""
    print("🔑 Testing OpenAI API Key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found in environment variables")
        print("💡 Please set OPENAI_API_KEY environment variable")
        return False
    
    if api_key.startswith('sk-'):
        print("✅ OpenAI API key format looks correct")
        return True
    else:
        print("⚠️ OpenAI API key format might be incorrect")
        return False

def test_local_imports():
    """Test if required modules can be imported"""
    print("\n📦 Testing Local Imports...")
    
    try:
        from infer import IndonesianMentalHealthBot
        print("✅ IndonesianMentalHealthBot imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import IndonesianMentalHealthBot: {e}")
        return False

def test_bot_initialization():
    """Test bot initialization"""
    print("\n🧠 Testing Bot Initialization...")
    
    try:
        from infer import IndonesianMentalHealthBot
        bot = IndonesianMentalHealthBot()
        print("✅ Bot initialized successfully")
        
        # Test system prompt
        if hasattr(bot, 'system_prompt') and bot.system_prompt:
            print("✅ System prompt configured")
        else:
            print("⚠️ System prompt not configured")
        
        # Test conversation storage
        if hasattr(bot, 'conversations'):
            print("✅ Conversation storage initialized")
        else:
            print("⚠️ Conversation storage not initialized")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return False

def test_server_health():
    """Test if server is running and healthy"""
    print("\n🌐 Testing Server Health...")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running and healthy")
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Bot Initialized: {data.get('bot_initialized', 'Unknown')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        print("💡 Start the server with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_crisis_resources():
    """Test crisis resources endpoint"""
    print("\n📞 Testing Crisis Resources...")
    
    try:
        response = requests.get('http://localhost:8000/crisis-resources', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Crisis resources endpoint working")
            
            # Check if required sections exist
            if 'mental_health_hotlines' in data:
                print("✅ Mental health hotlines available")
            
            if 'emergency_services' in data:
                print("✅ Emergency services available")
            
            if 'online_resources' in data:
                print("✅ Online resources available")
            
            return True
        else:
            print(f"❌ Crisis resources endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing crisis resources: {e}")
        return False

def test_therapy_tips():
    """Test therapy tips endpoint"""
    print("\n💡 Testing Therapy Tips...")
    
    try:
        response = requests.get('http://localhost:8000/therapy-tips', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Therapy tips endpoint working")
            
            # Check if required sections exist
            if 'daily_practices' in data:
                print("✅ Daily practices available")
            
            if 'coping_strategies' in data:
                print("✅ Coping strategies available")
            
            if 'family_support' in data:
                print("✅ Family support tips available")
            
            if 'spiritual_guidance' in data:
                print("✅ Spiritual guidance available")
            
            return True
        else:
            print(f"❌ Therapy tips endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing therapy tips: {e}")
        return False

def test_web_interface():
    """Test if web interface is accessible"""
    print("\n🌐 Testing Web Interface...")
    
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            html_content = response.text
            
            # Check for key elements
            if 'Kak Indira' in html_content:
                print("✅ Web interface title found")
            else:
                print("⚠️ Web interface title not found")
            
            if 'Konselor Kesehatan Mental' in html_content:
                print("✅ Mental health counselor description found")
            else:
                print("⚠️ Mental health counselor description not found")
            
            if 'IndonesianMentalHealthBot' in html_content:
                print("✅ JavaScript class found")
            else:
                print("⚠️ JavaScript class not found")
            
            return True
        else:
            print(f"❌ Web interface returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False

def test_text_therapy_response():
    """Test text-based therapy response"""
    print("\n💬 Testing Text Therapy Response...")
    
    try:
        test_message = {
            "text": "Saya merasa cemas dan stres akhir-akhir ini. Bisakah Anda membantu saya?",
            "session_id": "test_session_001"
        }
        
        response = requests.post(
            'http://localhost:8000/get-therapy-response',
            json=test_message,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Text therapy response working")
            
            if 'response' in data and data['response']:
                print("✅ AI response generated")
                print(f"   Response length: {len(data['response'])} characters")
                
                # Check if response is in Indonesian
                if any(word in data['response'].lower() for word in ['saya', 'anda', 'kamu', 'merasa', 'membantu']):
                    print("✅ Response appears to be in Indonesian")
                else:
                    print("⚠️ Response language uncertain")
            else:
                print("⚠️ No response generated")
            
            if 'session_id' in data:
                print("✅ Session ID maintained")
            
            return True
        else:
            print(f"❌ Text therapy response returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing text therapy response: {e}")
        return False

def main():
    """Run all tests"""
    print("🧠 Indonesian Mental Health Support Bot - Test Suite")
    print("="*60)
    
    tests = [
        ("OpenAI API Key", test_openai_api_key),
        ("Local Imports", test_local_imports),
        ("Bot Initialization", test_bot_initialization),
        ("Server Health", test_server_health),
        ("Crisis Resources", test_crisis_resources),
        ("Therapy Tips", test_therapy_tips),
        ("Web Interface", test_web_interface),
        ("Text Therapy Response", test_text_therapy_response),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"🎯 TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Bot is ready for use.")
        print("💚 You can now start using the Indonesian Mental Health Support Bot")
        print("🌐 Access the web interface at: http://localhost:8000")
    else:
        print(f"\n⚠️ {failed} tests failed. Please check the issues above.")
        print("💡 Make sure to:")
        print("   1. Set your OpenAI API key: export OPENAI_API_KEY=your_key")
        print("   2. Install all dependencies: pip install -r requirements.txt")
        print("   3. Start the server: python app.py")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 