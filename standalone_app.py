#!/usr/bin/env python3
"""
Standalone Flask application for sentiment analysis.
Provides web interface and REST API without Slack integration.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from config import get_config
from gemini_client import GeminiClient, SentimentAnalysisRequest, GeminiAPIError


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    
    # Configure Flask
    app.config['SECRET_KEY'] = config.security.secret_key
    app.config['DEBUG'] = config.server.debug
    
    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize Gemini client
    gemini_client = GeminiClient(config.gemini)
    
    # Setup logging
    logger = logging.getLogger('standalone_app')
    
    @app.route('/')
    def index():
        """Serve the web interface."""
        return render_template_string(WEB_INTERFACE_TEMPLATE)
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'config': config.config_summary()
        })
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze_sentiment():
        """Analyze sentiment of a single message."""
        logger.info("Processing sentiment analysis request")
        
        try:
            # Validate request
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            # Validate required fields
            if 'text' not in data:
                return jsonify({'error': 'text field is required'}), 400
            
            text = data['text'].strip()
            if not text:
                return jsonify({'error': 'text cannot be empty'}), 400
            
            if len(text) > 10000:
                return jsonify({'error': 'text cannot exceed 10,000 characters'}), 400
            
            # Create analysis request
            analysis_request = SentimentAnalysisRequest(
                text=text,
                language=data.get('language', 'auto'),
                context=data.get('context'),
                channel_type='web'
            )
            
            # Perform analysis
            start_time = time.time()
            response = gemini_client.analyze_sentiment(analysis_request)
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Format response
            result = {
                'sentiment_score': response.sentiment_score,
                'sentiment_label': response.sentiment_label,
                'confidence': response.confidence,
                'explanation': response.explanation,
                'language_detected': response.language_detected,
                'processing_time_ms': round(processing_time_ms, 1),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info("Sentiment analysis completed")
            return jsonify(result)
            
        except GeminiAPIError as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return jsonify({
                'error': 'Sentiment analysis failed',
                'details': str(e)
            }), 500
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'details': str(e)
            }), 500
    
    @app.route('/api/batch', methods=['POST'])
    def batch_analyze():
        """Analyze sentiment of multiple messages."""
        logger.info("Processing batch sentiment analysis request")
        
        try:
            # Validate request
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            # Validate required fields
            if 'texts' not in data:
                return jsonify({'error': 'texts field is required'}), 400
            
            texts = data['texts']
            if not isinstance(texts, list):
                return jsonify({'error': 'texts must be an array'}), 400
            
            if len(texts) == 0:
                return jsonify({'error': 'texts array cannot be empty'}), 400
            
            if len(texts) > 50:
                return jsonify({'error': 'Cannot process more than 50 texts at once'}), 400
            
            # Process each text
            results = []
            successful = 0
            failed = 0
            
            start_time = time.time()
            
            for i, text_item in enumerate(texts):
                try:
                    # Validate text item
                    if isinstance(text_item, str):
                        text_data = {'text': text_item, 'id': str(i)}
                    elif isinstance(text_item, dict):
                        text_data = text_item
                    else:
                        results.append({
                            'id': str(i),
                            'error': 'Invalid text item format'
                        })
                        failed += 1
                        continue
                    
                    if 'text' not in text_data:
                        results.append({
                            'id': text_data.get('id', str(i)),
                            'error': 'text field is required'
                        })
                        failed += 1
                        continue
                    
                    text = text_data['text'].strip()
                    if not text:
                        results.append({
                            'id': text_data.get('id', str(i)),
                            'error': 'text cannot be empty'
                        })
                        failed += 1
                        continue
                    
                    if len(text) > 10000:
                        results.append({
                            'id': text_data.get('id', str(i)),
                            'error': 'text cannot exceed 10,000 characters'
                        })
                        failed += 1
                        continue
                    
                    # Create analysis request
                    analysis_request = SentimentAnalysisRequest(
                        text=text,
                        language=text_data.get('language', 'auto'),
                        context=text_data.get('context'),
                        channel_type='web'
                    )
                    
                    # Perform analysis
                    response = gemini_client.analyze_sentiment(analysis_request)
                    
                    # Format response
                    result = {
                        'id': text_data.get('id', str(i)),
                        'sentiment_score': response.sentiment_score,
                        'sentiment_label': response.sentiment_label,
                        'confidence': response.confidence,
                        'explanation': response.explanation,
                        'language_detected': response.language_detected,
                        'processing_time_ms': round(response.processing_time * 1000, 1)
                    }
                    
                    results.append(result)
                    successful += 1
                    
                except GeminiAPIError as e:
                    results.append({
                        'id': text_data.get('id', str(i)),
                        'error': f'Analysis failed: {str(e)}'
                    })
                    failed += 1
                    
                except Exception as e:
                    results.append({
                        'id': text_data.get('id', str(i)),
                        'error': f'Unexpected error: {str(e)}'
                    })
                    failed += 1
            
            total_time_ms = (time.time() - start_time) * 1000
            
            # Format batch response
            batch_result = {
                'results': results,
                'summary': {
                    'total': len(texts),
                    'successful': successful,
                    'failed': failed,
                    'total_processing_time_ms': round(total_time_ms, 1)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Batch analysis completed: {successful} successful, {failed} failed")
            return jsonify(batch_result)
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {str(e)}")
            return jsonify({
                'error': 'Batch analysis failed',
                'details': str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors."""
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


# Web interface template
WEB_INTERFACE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .content {
            padding: 40px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        textarea, select, input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        textarea:focus, select:focus, input:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result {
            margin-top: 30px;
            padding: 25px;
            border-radius: 15px;
            display: none;
        }
        
        .result.success {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-left: 5px solid #00d4aa;
        }
        
        .result.error {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-left: 5px solid #ff6b6b;
        }
        
        .sentiment-score {
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        
        .sentiment-label {
            font-size: 1.5em;
            text-align: center;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .detail-item {
            background: rgba(255,255,255,0.7);
            padding: 15px;
            border-radius: 10px;
        }
        
        .detail-label {
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .detail-value {
            font-size: 1.1em;
            color: #333;
        }
        
        .explanation {
            background: rgba(255,255,255,0.7);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4facfe;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .score-1 { color: #ff4757; }
        .score-2 { color: #ff6348; }
        .score-3 { color: #ffa502; }
        .score-4 { color: #2ed573; }
        .score-5 { color: #1dd1a1; }
        
        @media (max-width: 600px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .details {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Sentiment Analyzer</h1>
            <p>Analyze the emotional tone of any text with AI-powered precision</p>
        </div>
        
        <div class="content">
            <form id="sentimentForm">
                <div class="form-group">
                    <label for="text">Text to Analyze</label>
                    <textarea 
                        id="text" 
                        name="text" 
                        placeholder="Enter the text you want to analyze for sentiment..."
                        required
                    ></textarea>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="language">Language</label>
                        <select id="language" name="language">
                            <option value="auto">Auto-detect</option>
                            <option value="en">English</option>
                            <option value="ja">Japanese</option>
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                            <option value="de">German</option>
                            <option value="zh">Chinese</option>
                            <option value="ko">Korean</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="context">Context (Optional)</label>
                        <input 
                            type="text" 
                            id="context" 
                            name="context" 
                            placeholder="e.g., customer feedback, social media"
                        />
                    </div>
                </div>
                
                <button type="submit" class="btn" id="analyzeBtn">
                    Analyze Sentiment
                </button>
            </form>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Analyzing sentiment...</p>
            </div>
            
            <div id="result" class="result"></div>
        </div>
    </div>

    <script>
        document.getElementById('sentimentForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                text: formData.get('text'),
                language: formData.get('language'),
                context: formData.get('context') || undefined
            };
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = true;
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult(result);
                } else {
                    showError(result.error || 'Analysis failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('analyzeBtn').disabled = false;
            }
        });
        
        function showResult(result) {
            const resultDiv = document.getElementById('result');
            resultDiv.className = 'result success';
            resultDiv.innerHTML = `
                <div class="sentiment-score score-${result.sentiment_score}">${result.sentiment_score}/5</div>
                <div class="sentiment-label">${result.sentiment_label}</div>
                
                <div class="details">
                    <div class="detail-item">
                        <div class="detail-label">Confidence</div>
                        <div class="detail-value">${Math.round(result.confidence * 100)}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Language</div>
                        <div class="detail-value">${result.language_detected.toUpperCase()}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Processing Time</div>
                        <div class="detail-value">${result.processing_time_ms}ms</div>
                    </div>
                </div>
                
                <div class="explanation">
                    <div class="detail-label">Analysis Explanation</div>
                    <div class="detail-value">${result.explanation}</div>
                </div>
            `;
            resultDiv.style.display = 'block';
        }
        
        function showError(error) {
            const resultDiv = document.getElementById('result');
            resultDiv.className = 'result error';
            resultDiv.innerHTML = `
                <h3>❌ Analysis Failed</h3>
                <p>${error}</p>
            `;
            resultDiv.style.display = 'block';
        }
    </script>
</body>
</html>
"""


if __name__ == '__main__':
    app = create_app()
    config = get_config()
    
    print("🎭 Standalone Sentiment Analyzer")
    print("=" * 40)
    print(f"📍 Web interface: http://{config.server.host}:{config.server.port}")
    print(f"🔗 API endpoint: http://{config.server.host}:{config.server.port}/api/analyze")
    print(f"📊 Health check: http://{config.server.host}:{config.server.port}/health")
    print("✨ Press Ctrl+C to stop the service")
    
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )