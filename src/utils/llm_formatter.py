"""
LLM Formatter - Optimizes data for LLM consumption
Implements best practices for feeding data to LLMs
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import tiktoken
import re
from ..utils.logger import get_logger

class LLMFormatter:
    """Formats and optimizes data for LLM analysis"""
    
    def __init__(self, max_tokens: int = 100000):
        self.logger = get_logger("LLMFormatter")
        self.max_tokens = max_tokens
        
        # Initialize tokenizer (using cl100k_base for Claude/GPT-4)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoder = None
            self.logger.warning("Tokenizer not available, using character count estimation")
            
    def format_social_data_for_llm(self, ticker: str, data: Dict[str, Any]) -> str:
        """
        Format social media data optimally for LLM analysis
        Focuses on pump & dump detection patterns
        """
        
        formatted = f"=== PUMP & DUMP ANALYSIS FOR ${ticker} ===\n"
        formatted += f"Analysis Time: {datetime.now().isoformat()}\n\n"
        
        # Add summary statistics first (LLMs benefit from context)
        summary = data.get('summary', {})
        formatted += "SUMMARY STATISTICS:\n"
        formatted += f"- Total Social Mentions: {summary.get('total_social_mentions', 0)}\n"
        formatted += f"- News Articles: {summary.get('total_news_articles', 0)}\n"
        formatted += f"- Risk Indicators: {', '.join(summary.get('risk_indicators', []))}\n\n"
        
        sources = data.get('sources', {})
        
        # Format social media data (most important for pump & dump)
        formatted += self._format_social_media_section(sources)
        
        # Format forum data
        formatted += self._format_forum_section(sources)
        
        # Format market data (brief, for context)
        formatted += self._format_market_data_section(sources)
        
        # Trim if too long
        formatted = self._trim_to_token_limit(formatted)
        
        return formatted
        
    def _format_social_media_section(self, sources: Dict[str, Any]) -> str:
        """Format social media posts for pump detection"""
        section = "\n=== SOCIAL MEDIA ACTIVITY ===\n\n"
        
        # Reddit
        if 'reddit' in sources and sources['reddit']:
            reddit = sources['reddit']
            section += f"REDDIT ({reddit.get('total_mentions', 0)} mentions):\n"
            
            posts = reddit.get('posts', [])[:15]  # Top 15 posts
            for i, post in enumerate(posts, 1):
                # Include key metadata for pump detection
                section += f"\n[{i}] r/{post.get('subreddit')} | "
                section += f"Score: {post.get('score')} | "
                section += f"Comments: {post.get('num_comments')} | "
                section += f"Time: {self._format_timestamp(post.get('created_utc'))}\n"
                
                # Title is crucial for pump detection
                section += f"Title: {post.get('title', '')}\n"
                
                # Include snippet of content
                content = post.get('selftext', '')[:200]
                if content:
                    section += f"Content: {content}...\n"
                    
                # Look for pump indicators
                pump_signals = self._extract_pump_signals(
                    f"{post.get('title', '')} {post.get('selftext', '')}"
                )
                if pump_signals:
                    section += f"🚨 Pump Signals: {', '.join(pump_signals)}\n"
                    
        # StockTwits
        if 'stocktwits' in sources and sources['stocktwits']:
            st = sources['stocktwits']
            section += f"\n\nSTOCKTWITS"
            if st.get('is_trending'):
                section += f" [TRENDING #{st.get('trending_rank')}]"
            section += ":\n"
            
            messages = st.get('messages', [])[:10]
            for msg in messages:
                sentiment = msg.get('sentiment', {}).get('class', 'neutral')
                section += f"\n- [{sentiment.upper()}] {msg.get('body', '')}\n"
                section += f"  User: {msg.get('user', {}).get('username', 'unknown')} | "
                section += f"  Likes: {msg.get('likes', {}).get('total', 0)}\n"
                
        # 4chan /biz/
        if 'fourchan' in sources and sources['fourchan']:
            fc = sources['fourchan']
            section += f"\n\n4CHAN /BIZ/:\n"
            
            threads = fc.get('pump_threads', [])[:5]
            for thread in threads:
                section += f"\n- Thread: {thread.get('title', thread.get('comment', '')[:50])}...\n"
                section += f"  Replies: {thread.get('replies')} | "
                section += f"  Pump Score: {thread.get('pump_score')}/10\n"
                
                # Key quotes from thread
                if 'posts' in thread:
                    section += "  Key Posts:\n"
                    for post in thread['posts'][:3]:
                        section += f"    > {post['comment'][:100]}...\n"
                        
        return section
        
    def _format_forum_section(self, sources: Dict[str, Any]) -> str:
        """Format forum data for pump detection"""
        section = "\n=== FORUM ACTIVITY ===\n\n"
        
        # InvestorsHub
        if 'investorshub' in sources and sources['investorshub']:
            ih = sources['investorshub']
            section += "INVESTORSHUB:\n"
            
            posts = ih.get('posts', [])[:10]
            for post in posts:
                section += f"\n- {post.get('subject', '')}\n"
                section += f"  Author: {post.get('author')} | "
                section += f"  Date: {post.get('date')}\n"
                section += f"  {post.get('content', '')[:150]}...\n"
                
        # BitcoinTalk
        if 'bitcointalk' in sources and sources['bitcointalk']:
            bt = sources['bitcointalk']
            section += "\nBITCOINTALK:\n"
            
            topics = bt.get('topics', [])[:5]
            for topic in topics:
                section += f"\n- {topic.get('title', '')}\n"
                section += f"  Replies: {topic.get('replies')} | "
                section += f"  Views: {topic.get('views')} | "
                section += f"  Pump Score: {topic.get('pump_score')}\n"
                
        return section
        
    def _format_market_data_section(self, sources: Dict[str, Any]) -> str:
        """Format market data briefly"""
        section = "\n=== MARKET DATA ===\n\n"
        
        # Yahoo Finance
        if 'yahoo' in sources and sources['yahoo']:
            yf = sources['yahoo']
            info = yf.get('info', {})
            
            section += "YAHOO FINANCE:\n"
            section += f"- Price: ${info.get('currentPrice', 'N/A')}\n"
            section += f"- Volume: {info.get('volume', 'N/A'):,} "
            section += f"(Avg: {info.get('averageVolume', 'N/A'):,})\n"
            
            # Volume spike is key pump indicator
            if info.get('volume') and info.get('averageVolume'):
                vol_ratio = info['volume'] / info['averageVolume']
                if vol_ratio > 3:
                    section += f"- 🚨 VOLUME SPIKE: {vol_ratio:.1f}x average!\n"
                    
            # Recent news
            news = yf.get('news', [])[:3]
            if news:
                section += "- Recent News:\n"
                for article in news:
                    section += f"  • {article.get('title', '')}\n"
                    
        return section
        
    def _extract_pump_signals(self, text: str) -> List[str]:
        """Extract pump & dump signals from text"""
        signals = []
        text_lower = text.lower()
        
        # Direct pump mentions
        if 'pump' in text_lower:
            signals.append("Direct pump mention")
            
        # Urgency indicators
        urgency_phrases = ['now or never', 'last chance', 'don\'t miss', 'hurry']
        if any(phrase in text_lower for phrase in urgency_phrases):
            signals.append("Urgency language")
            
        # Unrealistic promises
        if re.search(r'\d+x|moon|lambo|millionaire', text_lower):
            signals.append("Unrealistic gains promised")
            
        # Coordination signals
        if re.search(r'telegram|discord|group|coordinate', text_lower):
            signals.append("Group coordination mentioned")
            
        # New account pushing
        if 'first post' in text_lower or 'new here' in text_lower:
            signals.append("New account promoting")
            
        return signals
        
    def _format_timestamp(self, timestamp: Any) -> str:
        """Format timestamp for readability"""
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M")
            return str(timestamp)
        except:
            return str(timestamp)
            
    def _trim_to_token_limit(self, text: str) -> str:
        """Trim text to fit within token limit"""
        if self.encoder:
            tokens = self.encoder.encode(text)
            if len(tokens) > self.max_tokens:
                # Decode only the allowed number of tokens
                trimmed_tokens = tokens[:self.max_tokens]
                return self.encoder.decode(trimmed_tokens) + "\n\n[TRIMMED DUE TO LENGTH]"
        else:
            # Fallback: estimate 4 characters per token
            char_limit = self.max_tokens * 4
            if len(text) > char_limit:
                return text[:char_limit] + "\n\n[TRIMMED DUE TO LENGTH]"
                
        return text
        
    def create_pump_detection_prompt(self, formatted_data: str) -> str:
        """Create optimized prompt for pump & dump detection"""
        prompt = """Analyze the following social media and market data for pump & dump scheme indicators.

Focus on:
1. Coordinated posting patterns (multiple accounts, similar timing)
2. Unrealistic price predictions and urgency language
3. New accounts or low-credibility sources pushing the stock
4. Unusual volume or activity spikes
5. Lack of fundamental catalysts for the hype

Provide your analysis in this EXACT JSON format:
{
    "pump_probability": [0-100 integer],
    "risk_level": "[LOW|MEDIUM|HIGH|EXTREME]",
    "confidence": [0-100 integer],
    "coordination_evidence": {
        "detected": [true/false],
        "patterns": ["list of specific patterns found"]
    },
    "suspicious_accounts": ["list of suspicious usernames/sources"],
    "pump_timeline": {
        "stage": "[accumulation|promotion|pump|dump|aftermath]",
        "estimated_start": "when activity began",
        "peak_prediction": "if pumping, when peak likely"
    },
    "key_findings": ["list of specific discoveries"],
    "red_flags": ["list of warning signs"],
    "supporting_quotes": ["exact quotes showing pump behavior"],
    "recommendations": ["specific actionable advice"]
}

DATA TO ANALYZE:
"""
        return prompt + formatted_data
        
    def format_batch_for_comparison(self, tickers: List[str], 
                                   data_dict: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple tickers for comparative analysis"""
        formatted = "=== COMPARATIVE PUMP & DUMP ANALYSIS ===\n\n"
        formatted += f"Comparing {len(tickers)} tickers: {', '.join(f'${t}' for t in tickers)}\n\n"
        
        for ticker in tickers:
            if ticker in data_dict:
                ticker_data = data_dict[ticker]
                summary = ticker_data.get('summary', {})
                
                formatted += f"\n{'='*40}\n"
                formatted += f"${ticker}:\n"
                formatted += f"- Social Mentions: {summary.get('total_social_mentions', 0)}\n"
                formatted += f"- Primary Sources: {', '.join(list(ticker_data.get('sources', {}).keys())[:3])}\n"
                
                # Add top pump signals
                sources = ticker_data.get('sources', {})
                
                # Check Reddit
                if 'reddit' in sources:
                    top_post = sources['reddit'].get('posts', [{}])[0]
                    if top_post:
                        formatted += f"- Top Reddit: {top_post.get('title', 'N/A')[:60]}...\n"
                        
        return self._trim_to_token_limit(formatted)