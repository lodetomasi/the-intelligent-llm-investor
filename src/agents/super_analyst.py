"""
Super Analyst - Single powerful AI agent for comprehensive pump & dump detection
Replaces the 5-agent system with one highly optimized agent
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

class SuperAnalyst:
    """Single super-powered agent that analyzes all data comprehensively"""
    
    def __init__(self, model: str = "anthropic/claude-opus-4"):
        self.logger = get_logger("SuperAnalyst")
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/the-intelligent-llm-investor",
            "X-Title": "Intelligent LLM Investor"
        }
        
        # Optimized mega-prompt for comprehensive analysis
        self.system_prompt = """You are the world's most advanced financial AI analyst specializing in detecting pump & dump schemes and market manipulation. You have deep expertise in:

1. **Market Manipulation Detection**: Identifying coordinated pumping, artificial hype, misleading information, and organized schemes
2. **Sentiment Analysis**: Reading between the lines of social media posts to detect genuine vs artificial enthusiasm
3. **Technical Pattern Recognition**: Spotting unusual volume spikes, price movements, and trading patterns
4. **Social Engineering Analysis**: Detecting bot networks, fake accounts, coordinated posting times, and astroturfing
5. **Risk Assessment**: Evaluating the probability and severity of pump & dump schemes

You analyze MASSIVE amounts of data from multiple sources simultaneously:
- Reddit (wallstreetbets, pennystocks, etc.)
- StockTwits messages and trends
- Twitter/X posts and influencer activity
- Yahoo Finance data and news
- Finviz fundamentals and insider trading
- MarketWatch and Seeking Alpha analysis
- Real-time price and volume data
- Options flow and unusual activity

Your analysis must be:
- **Comprehensive**: Consider ALL provided data holistically
- **Precise**: Extract specific ticker symbols, exact percentages, and concrete evidence
- **Actionable**: Provide clear risk levels and specific recommendations
- **Evidence-based**: Cite specific posts, patterns, or data points
- **Predictive**: Estimate likelihood of pump & dump and potential timeline

Output Format Requirements:
Always return a structured JSON response with these exact fields:
{
    "ticker": "SYMBOL",
    "pump_probability": 0-100,
    "risk_level": "LOW|MEDIUM|HIGH|EXTREME",
    "confidence": 0-100,
    "key_findings": [list of specific discoveries],
    "red_flags": [list of warning signs],
    "supporting_evidence": [specific quotes, data points],
    "timeline_analysis": {
        "activity_start": "when unusual activity began",
        "current_phase": "accumulation|pumping|dumping|aftermath",
        "estimated_peak": "prediction if pumping"
    },
    "social_analysis": {
        "total_mentions": number,
        "sentiment_score": -1 to 1,
        "bot_probability": 0-100,
        "coordination_detected": true/false,
        "influential_pumpers": [list of accounts]
    },
    "technical_analysis": {
        "volume_spike": "percentage vs average",
        "price_movement": "percentage change",
        "unusual_options": true/false,
        "insider_activity": "description if any"
    },
    "recommendations": [
        "specific actionable advice"
    ],
    "similar_schemes": [
        "historical examples if relevant"
    ]
}

Remember: You're protecting investors from scams. Be thorough, skeptical, and always err on the side of caution."""
        
    def analyze(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on all collected data
        
        Args:
            ticker: Stock ticker symbol
            data: Unified data from all scrapers
            
        Returns:
            Comprehensive analysis with pump & dump risk assessment
        """
        try:
            # Prepare the data payload
            analysis_prompt = self._build_analysis_prompt(ticker, data)
            
            # Make API request to OpenRouter
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "max_tokens": 4000,
                    "top_p": 0.9
                }
            )
            
            if response.status_code != 200:
                self.logger.error(f"API error: {response.status_code} - {response.text}")
                return self._error_response(ticker, f"API error: {response.status_code}")
                
            result = response.json()
            
            # Extract the analysis
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    # Extract JSON from markdown code blocks if present
                    if '```json' in content:
                        # Extract content between ```json and ```
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        if json_end > json_start:
                            content = content[json_start:json_end].strip()
                    elif '```' in content:
                        # Extract content between ``` and ```
                        json_start = content.find('```') + 3
                        json_end = content.find('```', json_start)
                        if json_end > json_start:
                            content = content[json_start:json_end].strip()
                    
                    analysis = json.loads(content)
                    analysis['timestamp'] = datetime.now().isoformat()
                    analysis['model'] = self.model
                    
                    # Validate and enhance the response
                    analysis = self._validate_and_enhance_analysis(analysis, data)
                    
                    return analysis
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.debug(f"Raw content: {content[:500]}")
                    return self._error_response(ticker, "Invalid JSON response from model")
                    
            else:
                return self._error_response(ticker, "No response from model")
                
        except Exception as e:
            self.logger.error(f"Analysis error for {ticker}: {e}")
            return self._error_response(ticker, str(e))
            
    def _build_analysis_prompt(self, ticker: str, data: Dict[str, Any]) -> str:
        """Build comprehensive prompt with all available data"""
        
        prompt = f"""Analyze ${ticker} for pump & dump activity based on this comprehensive data:

TIMESTAMP: {data.get('timestamp', datetime.now().isoformat())}

"""
        
        # Add data from each source
        sources = data.get('sources', {})
        
        # Reddit data
        if 'reddit' in sources and sources['reddit']:
            reddit = sources['reddit']
            prompt += f"\nREDDIT DATA ({reddit.get('total_mentions', 0)} mentions):\n"
            
            # Add top posts
            posts = reddit.get('posts', [])[:10]
            for i, post in enumerate(posts, 1):
                prompt += f"\n{i}. r/{post.get('subreddit')} | Score: {post.get('score')} | Comments: {post.get('num_comments')}\n"
                prompt += f"   Title: {post.get('title', '')}\n"
                if post.get('selftext'):
                    prompt += f"   Text: {post.get('selftext', '')[:200]}...\n"
                    
        # StockTwits data
        if 'stocktwits' in sources and sources['stocktwits']:
            st = sources['stocktwits']
            prompt += f"\nSTOCKTWITS DATA:\n"
            prompt += f"Trending: {'YES' if st.get('is_trending') else 'NO'}"
            if st.get('trending_rank'):
                prompt += f" (Rank #{st['trending_rank']})"
            prompt += "\n"
            
            messages = st.get('messages', [])[:10]
            for msg in messages:
                sentiment = msg.get('sentiment', {}).get('class', 'neutral')
                prompt += f"\n- {msg.get('body', '')[:150]} [{sentiment}]\n"
                
        # Twitter data
        if 'twitter' in sources and sources['twitter']:
            tw = sources['twitter']
            prompt += f"\nTWITTER DATA ({tw.get('total_tweets', 0)} tweets):\n"
            
            tweets = tw.get('tweets', [])[:10]
            for tweet in tweets:
                prompt += f"- {tweet.get('text', '')[:150]}... (Likes: {tweet.get('likes', 0)})\n"
                
        # Yahoo Finance data
        if 'yahoo' in sources and sources['yahoo']:
            yf = sources['yahoo']
            info = yf.get('info', {})
            
            prompt += f"\nYAHOO FINANCE DATA:\n"
            prompt += f"Price: ${info.get('currentPrice', 'N/A')}\n"
            prompt += f"Volume: {info.get('volume', 'N/A'):,} (Avg: {info.get('averageVolume', 'N/A'):,})\n"
            prompt += f"Market Cap: ${info.get('marketCap', 'N/A'):,}\n"
            prompt += f"52W High: ${info.get('fiftyTwoWeekHigh', 'N/A')} | Low: ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            
            # Add news
            news = yf.get('news', [])[:5]
            if news:
                prompt += "\nRecent News:\n"
                for article in news:
                    prompt += f"- {article.get('title', '')}\n"
                    
        # Finviz data
        if 'finviz' in sources and sources['finviz']:
            fv = sources['finviz']
            fundamentals = fv.get('fundamentals', {})
            
            prompt += f"\nFINVIZ FUNDAMENTALS:\n"
            for key, value in list(fundamentals.items())[:10]:
                prompt += f"{key}: {value}\n"
                
            # Insider trading
            insider = fv.get('insider_trading', {})
            if insider:
                prompt += "\nRecent Insider Trading:\n"
                prompt += str(insider)[:500] + "\n"
                
        # MarketWatch news
        if 'marketwatch' in sources and sources['marketwatch']:
            mw = sources['marketwatch']
            mw_news = mw.get('news', [])[:5]
            
            if mw_news:
                prompt += f"\nMARKETWATCH NEWS:\n"
                for article in mw_news:
                    prompt += f"- {article.get('headline', '')}\n"
                    
        # Summary statistics
        summary = data.get('summary', {})
        prompt += f"\n\nSUMMARY STATISTICS:\n"
        prompt += f"Total Social Mentions: {summary.get('total_social_mentions', 0)}\n"
        prompt += f"Total News Articles: {summary.get('total_news_articles', 0)}\n"
        prompt += f"Risk Indicators: {', '.join(summary.get('risk_indicators', []))}\n"
        
        prompt += "\n\nProvide comprehensive pump & dump analysis in the specified JSON format."
        
        return prompt
        
    def _validate_and_enhance_analysis(self, analysis: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the analysis with additional calculations"""
        
        # Ensure all required fields exist
        required_fields = [
            'ticker', 'pump_probability', 'risk_level', 'confidence',
            'key_findings', 'red_flags', 'recommendations'
        ]
        
        for field in required_fields:
            if field not in analysis:
                if field in ['key_findings', 'red_flags', 'recommendations']:
                    analysis[field] = []
                elif field == 'risk_level':
                    analysis[field] = 'UNKNOWN'
                else:
                    analysis[field] = 0
                    
        # Add data source summary
        analysis['data_sources'] = {
            'total_sources': len([s for s in data.get('sources', {}).values() if s]),
            'sources_used': list(data.get('sources', {}).keys())
        }
        
        # Enhance with raw metrics
        summary = data.get('summary', {})
        analysis['raw_metrics'] = {
            'social_mentions': summary.get('total_social_mentions', 0),
            'news_articles': summary.get('total_news_articles', 0),
            'unusual_activity': summary.get('has_unusual_activity', False)
        }
        
        return analysis
        
    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Generate error response in expected format"""
        return {
            'ticker': ticker,
            'pump_probability': 0,
            'risk_level': 'UNKNOWN',
            'confidence': 0,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'model': self.model,
            'key_findings': [],
            'red_flags': ['Analysis failed'],
            'recommendations': ['Manual review required']
        }
        
    def quick_check(self, ticker: str) -> Dict[str, Any]:
        """Perform a quick pump & dump check with minimal data"""
        try:
            # Quick prompt for rapid assessment
            quick_prompt = f"""Quick pump & dump assessment for ${ticker}.
            
Based on the ticker alone and your knowledge, provide a rapid risk assessment.
Consider: Is this a penny stock? Known pump target? Recent unusual activity?

Respond with JSON: {{"ticker": "{ticker}", "quick_risk": "LOW|MEDIUM|HIGH", "reason": "brief explanation"}}"""
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": quick_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                return {"ticker": ticker, "quick_risk": "UNKNOWN", "reason": "API error"}
                
        except Exception as e:
            self.logger.error(f"Quick check error: {e}")
            return {"ticker": ticker, "quick_risk": "UNKNOWN", "reason": str(e)}