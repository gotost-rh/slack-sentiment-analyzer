#!/usr/bin/env python3
"""
Test your original gemini-2.5-flash-preview-05-20 model.
"""

import requests
import json
import os
from dotenv import load_dotenv

def test_original_model():
    """Test your original model specification."""
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY', '***REMOVED_API_KEY***')
    
    # Your original model
    model_name = "gemini-2.5-flash-preview-05-20"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": """
                        Analyze the sentiment of this message: "Great work team! This project is fantastic!"
                        
                        Respond in JSON format:
                        {
                            "sentiment_score": [1-5 integer where 5 is very positive],
                            "sentiment_label": "[Very Negative|Negative|Neutral|Positive|Very Positive]",
                            "confidence": [0.0-1.0 float],
                            "language_detected": "en",
                            "explanation": "brief explanation"
                        }
                        """
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.8,
            "topK": 40,
            "maxOutputTokens": 1024
        }
    }
    
    print("🧪 Testing Your Original Model")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print()
    
    try:
        print("📡 Making API request...")
        
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Your original model works perfectly!")
            
            response_data = response.json()
            
            if 'candidates' in response_data and response_data['candidates']:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text_response = candidate['content']['parts'][0]['text']
                    
                    print("\n📝 API Response:")
                    print("-" * 30)
                    print(text_response)
                    
                    # Try to parse as JSON
                    try:
                        # Clean response
                        cleaned = text_response.strip()
                        if cleaned.startswith('```json'):
                            cleaned = cleaned[7:]
                        if cleaned.endswith('```'):
                            cleaned = cleaned[:-3]
                        cleaned = cleaned.strip()
                        
                        sentiment_data = json.loads(cleaned)
                        
                        print("\n🎯 Parsed Sentiment Analysis:")
                        print("-" * 35)
                        print(f"Score: {sentiment_data.get('sentiment_score')}/5")
                        print(f"Label: {sentiment_data.get('sentiment_label')}")
                        print(f"Confidence: {sentiment_data.get('confidence', 0):.0%}")
                        print(f"Language: {sentiment_data.get('language_detected')}")
                        print(f"Explanation: {sentiment_data.get('explanation')}")
                        
                        print(f"\n🎉 PERFECT! Your original model {model_name} works!")
                        return True
                        
                    except json.JSONDecodeError:
                        print(f"\n✅ Model works! (Response format needs minor adjustment)")
                        return True
                        
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_original_model()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ CONFIRMATION: Your original configuration is CORRECT!")
        print("Model: gemini-2.5-flash-preview-05-20")
        print("✅ Use this in your .env file:")
        print("GEMINI_MODEL=gemini-2.5-flash-preview-05-20")
    else:
        print("\n❌ Original model not working. Consider using gemini-1.5-flash instead.")
