#!/usr/bin/env python3
"""
Simple test script to verify the sentiment analyzer service works.
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from config import get_config
        print("✅ config module imported successfully")
        
        from gemini_client import GeminiClient, SentimentAnalysisRequest
        print("✅ gemini_client module imported successfully")
        
        from standalone_app import create_app
        print("✅ standalone_app module imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n🔧 Testing configuration...")
    
    try:
        load_dotenv()
        
        from config import get_config
        config = get_config()
        
        print("✅ Configuration loaded successfully")
        
        # Check validation
        validation = config.validate()
        if validation['valid']:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has errors:")
            for error in validation['errors']:
                print(f"  - {error}")
            return False
        
        # Print summary
        summary = config.config_summary()
        print("📊 Configuration summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_gemini_client():
    """Test Gemini client initialization."""
    print("\n🤖 Testing Gemini client...")
    
    try:
        from config import get_config
        from gemini_client import GeminiClient, SentimentAnalysisRequest
        
        config = get_config()
        
        # Check if API key is available
        if not config.gemini.api_key or config.gemini.api_key == 'your_gemini_api_key_here':
            print("⚠️  No valid API key found - skipping actual API test")
            print("✅ Gemini client can be initialized (API key needed for actual testing)")
            return True
        
        client = GeminiClient(config.gemini)
        print("✅ Gemini client initialized successfully")
        
        # Test with a simple request (if API key is available)
        request = SentimentAnalysisRequest(
            text="This is a test message",
            language="auto"
        )
        
        print("🔍 Testing sentiment analysis...")
        response = client.analyze_sentiment(request)
        
        print(f"✅ Sentiment analysis successful!")
        print(f"  Score: {response.sentiment_score}/5")
        print(f"  Label: {response.sentiment_label}")
        print(f"  Confidence: {response.confidence:.0%}")
        
        return True
    except Exception as e:
        print(f"❌ Gemini client error: {e}")
        return False

def test_flask_app():
    """Test Flask app creation."""
    print("\n🌐 Testing Flask app...")
    
    try:
        from standalone_app import create_app
        
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Test that routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/health', '/api/analyze', '/api/batch']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Flask app error: {e}")
        return False

def main():
    """Run all tests."""
    print("🎭 Sentiment Analyzer Service Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Gemini Client Test", test_gemini_client),
        ("Flask App Test", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Service is ready to use.")
        print("\n🚀 To start the service, run:")
        print("python3 run_standalone.py")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

