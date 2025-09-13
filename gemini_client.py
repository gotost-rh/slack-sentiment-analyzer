#!/usr/bin/env python3
"""
Google Gemini AI client for sentiment analysis.
Handles API communication, prompt engineering, and response parsing.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
import requests

from config import GeminiConfig


class GeminiAPIError(Exception):
    """Raised when Gemini API returns an error."""
    pass


@dataclass
class SentimentAnalysisRequest:
    """Request data for sentiment analysis."""
    text: str
    language: str = 'auto'
    context: Optional[str] = None
    channel_type: str = 'web'


@dataclass
class SentimentResponse:
    """Response data from sentiment analysis."""
    sentiment_score: int
    sentiment_label: str
    confidence: float
    explanation: str
    language_detected: str
    processing_time: float


class GeminiClient:
    """Client for Google Gemini AI sentiment analysis."""
    
    def __init__(self, config: GeminiConfig):
        """Initialize the Gemini client."""
        self.config = config
        self.logger = logging.getLogger('gemini_client.GeminiClient')
        self.session = requests.Session()
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model_name}:generateContent?key={config.api_key}"
    
    def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentResponse:
        """Analyze sentiment of the given text."""
        start_time = time.time()
        
        self.logger.info("Starting sentiment analysis")
        
        try:
            # Create the prompt
            prompt = self._create_sentiment_prompt(request)
            
            # Make API request with retry logic
            response_data = self._make_api_request(prompt)
            
            # Parse the response
            sentiment_response = self._parse_api_response(response_data, request.language)
            
            # Add processing time
            processing_time = time.time() - start_time
            sentiment_response.processing_time = processing_time
            
            self.logger.info("Sentiment analysis completed")
            return sentiment_response
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {str(e)}")
            raise
    
    def _create_sentiment_prompt(self, request: SentimentAnalysisRequest) -> str:
        """Create a culturally-aware prompt for sentiment analysis."""
        
        # Language-specific cultural context
        language_instructions = {
            'ja': """
Consider Japanese cultural context:
- Indirect communication styles (honne vs tatemae)
- Honorific language and politeness levels
- Context-dependent meaning
- Emotional restraint in expression
            """,
            'ko': """
Consider Korean cultural context:
- Hierarchical communication patterns
- Honorific language systems
- Indirect expression of emotions
            """,
            'zh': """
Consider Chinese cultural context:
- Concept of face (mianzi) in communication
- Indirect communication styles
- Contextual meaning interpretation
            """,
            'en': """
Consider English communication patterns:
- Direct communication style
- Sarcasm and irony detection
- Professional vs casual contexts
            """
        }
        
        # Determine language for cultural context
        detected_lang = request.language if request.language != 'auto' else 'en'
        cultural_context = language_instructions.get(detected_lang, language_instructions['en'])
        
        prompt = f"""You are a sentiment analysis expert. Analyze the sentiment of the following text and respond with ONLY a valid JSON object.

Text: "{request.text}"
Language: {request.language}
Context: {request.context or 'General communication'}

{cultural_context}

Sentiment Scale:
1 = Very Negative (anger, hostility, severe criticism)
2 = Negative (disappointment, mild criticism, concern)  
3 = Neutral (factual, informational, balanced)
4 = Positive (satisfaction, approval, mild enthusiasm)
5 = Very Positive (excitement, joy, strong approval, celebration)

Respond with ONLY this JSON format (no markdown, no explanation outside JSON):
{{
    "sentiment_score": [integer 1-5],
    "sentiment_label": "[Very Negative|Negative|Neutral|Positive|Very Positive]",
    "confidence": [float 0.0-1.0],
    "language_detected": "[2-letter language code]",
    "explanation": "[brief explanation in English]"
}}"""
        
        return prompt
    
    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Make API request to Gemini with retry logic."""
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for consistent responses
                "topP": 0.9,
                "topK": 20,  # Reduced for more focused responses
                "maxOutputTokens": 1024,  # Increased to handle thinking tokens
                "stopSequences": [],  # Don't stop early
                "candidateCount": 1
            }
        }
        
        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                    self.logger.info(f"Retrying API request in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', '60'))
                    if attempt < self.config.max_retries - 1:
                        self.logger.warning(f"Rate limited, waiting {retry_after}s")
                        time.sleep(retry_after)
                        continue
                    else:
                        raise GeminiAPIError("Rate limit exceeded")
                
                if response.status_code != 200:
                    error_text = response.text
                    raise GeminiAPIError(f"API returned status {response.status_code}: {error_text}")
                
                response_data = response.json()
                
                # Debug logging (only if debug level)
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Raw API response: {json.dumps(response_data, indent=2)}")
                
                # Check for valid response structure
                if 'candidates' not in response_data or not response_data['candidates']:
                    raise GeminiAPIError("No candidates in response")
                
                candidate = response_data['candidates'][0]
                
                if 'content' not in candidate:
                    raise GeminiAPIError("No content in response candidate")
                
                if 'parts' not in candidate['content']:
                    # This happens when MAX_TOKENS is hit during thinking phase
                    if candidate.get('finishReason') == 'MAX_TOKENS':
                        raise GeminiAPIError("Response truncated due to token limit - increase maxOutputTokens")
                    else:
                        raise GeminiAPIError("No parts in response content")
                
                if not candidate['content']['parts']:
                    raise GeminiAPIError("Empty parts array in response")
                
                response_text = candidate['content']['parts'][0].get('text', '')
                if not response_text:
                    raise GeminiAPIError("Empty response text")
                
                # Debug logging for response text
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Response text: {response_text[:500]}...")
                
                return response_text
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == self.config.max_retries - 1:
                    raise GeminiAPIError(f"API request failed after {self.config.max_retries} attempts: {str(e)}")
                self.logger.warning(f"API error on attempt {attempt + 1}: {str(e)}")
                continue
            except GeminiAPIError as e:
                if attempt == self.config.max_retries - 1:
                    raise GeminiAPIError(f"API request failed after {self.config.max_retries} attempts: {str(e)}")
                self.logger.warning(f"API error on attempt {attempt + 1}: {str(e)}")
                continue
        
        raise GeminiAPIError("Max retries exceeded")
    
    def _parse_api_response(self, response_text: str, expected_language: str) -> SentimentResponse:
        """Parse and validate the API response."""
        
        # Clean the response text
        cleaned_text = self._clean_response_text(response_text)
        
        # Try to parse as JSON
        try:
            response_data = json.loads(cleaned_text)
            return self._create_sentiment_response(response_data)
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error: {e}. Raw text: {cleaned_text[:200]}...")
        
        # Try to extract JSON from mixed content
        json_match = re.search(r'\{[^{}]*"sentiment_score"[^{}]*\}', cleaned_text, re.DOTALL)
        if json_match:
            try:
                response_data = json.loads(json_match.group())
                return self._create_sentiment_response(response_data)
            except json.JSONDecodeError:
                pass
        
        # Try to fix truncated JSON
        if self._is_truncated_json(cleaned_text):
            fixed_json = self._fix_truncated_json(cleaned_text)
            try:
                response_data = json.loads(fixed_json)
                return self._create_sentiment_response(response_data)
            except json.JSONDecodeError:
                pass
        
        # Fallback: infer sentiment from text
        return self._infer_sentiment_from_text(cleaned_text, expected_language)
    
    def _clean_response_text(self, text: str) -> str:
        """Clean response text for JSON parsing."""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove extra whitespace
        text = text.strip()
        
        return text
    
    def _is_truncated_json(self, text: str) -> bool:
        """Check if JSON appears to be truncated."""
        text = text.strip()
        return (
            text.startswith('{') and 
            not text.endswith('}') and 
            '"sentiment_score"' in text
        )
    
    def _fix_truncated_json(self, text: str) -> str:
        """Attempt to fix truncated JSON."""
        text = text.strip()
        
        # If it ends with an incomplete value, try to complete it
        if text.endswith('":'):
            text += ' 0.95'
        elif text.endswith(': '):
            text += '0.95'
        elif text.endswith(','):
            text = text[:-1]
        
        # Ensure it ends with closing brace
        if not text.endswith('}'):
            text += '}'
        
        return text
    
    def _create_sentiment_response(self, data: Dict[str, Any]) -> SentimentResponse:
        """Create SentimentResponse from parsed JSON data."""
        
        # Validate required fields
        if 'sentiment_score' not in data:
            raise GeminiAPIError("Missing sentiment_score in response")
        
        sentiment_score = int(data['sentiment_score'])
        if sentiment_score < 1 or sentiment_score > 5:
            raise GeminiAPIError(f"Invalid sentiment_score: {sentiment_score}")
        
        # Map score to label if not provided
        score_to_label = {
            1: "Very Negative",
            2: "Negative", 
            3: "Neutral",
            4: "Positive",
            5: "Very Positive"
        }
        
        sentiment_label = data.get('sentiment_label', score_to_label[sentiment_score])
        confidence = float(data.get('confidence', 0.95))
        explanation = data.get('explanation', 'Sentiment analysis completed')
        language_detected = data.get('language_detected', 'en')
        
        return SentimentResponse(
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            explanation=explanation,
            language_detected=language_detected,
            processing_time=0.0  # Will be set by caller
        )
    
    def _infer_sentiment_from_text(self, text: str, expected_language: str) -> SentimentResponse:
        """Fallback method to infer sentiment from response text."""
        
        text_lower = text.lower()
        
        # Simple keyword-based inference
        if any(word in text_lower for word in ['very positive', 'excellent', 'amazing', 'fantastic']):
            sentiment_score = 5
        elif any(word in text_lower for word in ['positive', 'good', 'great', 'happy']):
            sentiment_score = 4
        elif any(word in text_lower for word in ['neutral', 'factual', 'informational']):
            sentiment_score = 3
        elif any(word in text_lower for word in ['negative', 'bad', 'poor', 'disappointing']):
            sentiment_score = 2
        elif any(word in text_lower for word in ['very negative', 'terrible', 'awful', 'hate']):
            sentiment_score = 1
        else:
            sentiment_score = 3  # Default to neutral
        
        score_to_label = {
            1: "Very Negative",
            2: "Negative",
            3: "Neutral", 
            4: "Positive",
            5: "Very Positive"
        }
        
        return SentimentResponse(
            sentiment_score=sentiment_score,
            sentiment_label=score_to_label[sentiment_score],
            confidence=0.7,  # Lower confidence for inferred results
            explanation="Sentiment inferred from response text",
            language_detected=expected_language if expected_language != 'auto' else 'en',
            processing_time=0.0
        )


if __name__ == "__main__":
    # Test the Gemini client
    from config import get_config
    
    try:
        config = get_config()
        client = GeminiClient(config.gemini)
        
        # Test request
        request = SentimentAnalysisRequest(
            text="I absolutely love this new feature! It's amazing!",
            language="auto",
            context="user feedback"
        )
        
        response = client.analyze_sentiment(request)
        
        print("Sentiment Analysis Result:")
        print(f"Score: {response.sentiment_score}/5")
        print(f"Label: {response.sentiment_label}")
        print(f"Confidence: {response.confidence:.0%}")
        print(f"Language: {response.language_detected}")
        print(f"Explanation: {response.explanation}")
        print(f"Processing Time: {response.processing_time:.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")