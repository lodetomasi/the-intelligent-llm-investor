"""
4chan /biz/ Board Scraper - Crypto and stock pump discussions
"""

import requests
from typing import Dict, List, Any
from datetime import datetime
import re
import time
from ..utils.logger import get_logger

class FourChanBizScraper:
    """Scrapes 4chan /biz/ board for pump & dump schemes"""
    
    def __init__(self):
        self.logger = get_logger("FourChanBizScraper")
        self.base_url = "https://a.4cdn.org"
        self.board = "biz"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_catalog(self) -> List[Dict[str, Any]]:
        """Get all threads from /biz/ catalog"""
        threads = []
        
        try:
            url = f"{self.base_url}/{self.board}/catalog.json"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return threads
                
            data = response.json()
            
            # Parse all pages
            for page in data:
                for thread in page.get('threads', []):
                    thread_data = {
                        'thread_id': thread.get('no'),
                        'subject': thread.get('sub', ''),
                        'comment': thread.get('com', ''),
                        'replies': thread.get('replies', 0),
                        'images': thread.get('images', 0),
                        'time': thread.get('time', 0),
                        'last_modified': thread.get('last_modified', 0),
                        'source': '4chan /biz/'
                    }
                    
                    # Clean HTML from comment
                    thread_data['comment'] = self._clean_html(thread_data['comment'])
                    
                    # Extract tickers
                    thread_data['tickers'] = self._extract_tickers(
                        f"{thread_data['subject']} {thread_data['comment']}"
                    )
                    
                    # Calculate pump score
                    thread_data['pump_score'] = self._calculate_pump_score(thread_data)
                    
                    threads.append(thread_data)
                    
        except Exception as e:
            self.logger.error(f"Error getting catalog: {e}")
            
        return threads
        
    def get_thread_posts(self, thread_id: int) -> List[Dict[str, Any]]:
        """Get all posts from a specific thread"""
        posts = []
        
        try:
            url = f"{self.base_url}/{self.board}/thread/{thread_id}.json"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return posts
                
            data = response.json()
            
            for post in data.get('posts', []):
                post_data = {
                    'post_id': post.get('no'),
                    'thread_id': thread_id,
                    'comment': self._clean_html(post.get('com', '')),
                    'time': post.get('time', 0),
                    'name': post.get('name', 'Anonymous'),
                    'trip': post.get('trip', ''),
                    'source': '4chan /biz/'
                }
                
                # Extract mentioned tickers
                post_data['tickers'] = self._extract_tickers(post_data['comment'])
                
                posts.append(post_data)
                
        except Exception as e:
            self.logger.error(f"Error getting thread {thread_id}: {e}")
            
        return posts
        
    def find_pump_threads(self, min_replies: int = 10) -> List[Dict[str, Any]]:
        """Find threads discussing potential pumps"""
        catalog = self.get_catalog()
        pump_threads = []
        
        # Pump-related keywords
        pump_keywords = [
            'pump', 'moon', 'rocket', 'gem', '10x', '100x',
            'buy signal', 'accumulate', 'bottom', 'breakout',
            'squeeze', 'insider', 'whales accumulating'
        ]
        
        for thread in catalog:
            # Check if thread has enough activity
            if thread['replies'] < min_replies:
                continue
                
            # Check for pump keywords
            text = f"{thread['subject']} {thread['comment']}".lower()
            keyword_count = sum(1 for keyword in pump_keywords if keyword in text)
            
            # High pump score or multiple keywords
            if thread['pump_score'] >= 3 or keyword_count >= 2:
                # Get full thread posts for more context
                if thread['replies'] < 100:  # Limit to avoid huge threads
                    thread['posts'] = self.get_thread_posts(thread['thread_id'])
                    time.sleep(0.5)  # Rate limiting
                    
                pump_threads.append(thread)
                
        # Sort by activity and pump score
        pump_threads.sort(key=lambda x: (x['pump_score'], x['replies']), reverse=True)
        
        return pump_threads[:20]  # Top 20
        
    def get_ticker_mentions(self) -> Dict[str, int]:
        """Count ticker mentions across all threads"""
        catalog = self.get_catalog()
        ticker_counts = {}
        
        for thread in catalog:
            # Weight by thread activity
            weight = 1 + (thread['replies'] / 10)  # More replies = more weight
            
            for ticker in thread.get('tickers', []):
                if ticker not in ticker_counts:
                    ticker_counts[ticker] = 0
                ticker_counts[ticker] += weight
                
        # Sort by mention count
        sorted_tickers = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_tickers[:50])  # Top 50
        
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from 4chan text"""
        if not text:
            return ""
            
        # Remove <br> tags
        text = text.replace('<br>', ' ')
        text = text.replace('<br/>', ' ')
        text = text.replace('<br />', ' ')
        
        # Remove other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = text.replace('&gt;', '>')
        text = text.replace('&lt;', '<')
        text = text.replace('&amp;', '&')
        text = text.replace('&#039;', "'")
        text = text.replace('&quot;', '"')
        
        return text.strip()
        
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock/crypto tickers from text"""
        tickers = set()
        
        # Look for $TICKER pattern
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        tickers.update(dollar_tickers)
        
        # Common crypto tickers without $
        crypto_pattern = r'\b(BTC|ETH|LINK|UNI|MATIC|SOL|ADA|DOT|AVAX|ATOM|ALGO|FTM|NEAR|SAND|MANA|GALA|LRC|CRO|CRV|AAVE|SUSHI|YFI|COMP|MKR|SNX|UMA|BAL|INCH|DYDX)\b'
        crypto_tickers = re.findall(crypto_pattern, text, re.I)
        tickers.update(t.upper() for t in crypto_tickers)
        
        # Look for "buy TICKER" or "TICKER to the moon" patterns
        buy_pattern = r'buy\s+([A-Z]{2,5})\b'
        buy_tickers = re.findall(buy_pattern, text, re.I)
        tickers.update(t.upper() for t in buy_tickers)
        
        return list(tickers)
        
    def _calculate_pump_score(self, thread: Dict[str, Any]) -> int:
        """Calculate likelihood of pump discussion"""
        score = 0
        text = f"{thread['subject']} {thread['comment']}".lower()
        
        # Pump phrases (weighted)
        high_weight_phrases = [
            'coordinated pump', 'pump group', 'pump signal',
            'insider info', 'whales loading', 'about to explode'
        ]
        
        medium_weight_phrases = [
            'moon', 'rocket', 'gem', '10x', '100x', 'lambo',
            'accumulate', 'bottom is in', 'breakout imminent'
        ]
        
        low_weight_phrases = [
            'buy', 'bullish', 'going up', 'cheap', 'undervalued'
        ]
        
        # Count phrase occurrences
        for phrase in high_weight_phrases:
            if phrase in text:
                score += 3
                
        for phrase in medium_weight_phrases:
            if phrase in text:
                score += 2
                
        for phrase in low_weight_phrases:
            if phrase in text:
                score += 1
                
        # Activity bonus
        if thread['replies'] > 50:
            score += 2
        elif thread['replies'] > 20:
            score += 1
            
        # Multiple tickers mentioned (possible shill thread)
        if len(thread.get('tickers', [])) > 3:
            score += 1
            
        return score
        
    def get_pump_alerts(self) -> List[Dict[str, Any]]:
        """Get high-priority pump alerts"""
        pump_threads = self.find_pump_threads()
        alerts = []
        
        for thread in pump_threads:
            if thread['pump_score'] >= 5:  # High score threshold
                # Extract key info
                alert = {
                    'thread_id': thread['thread_id'],
                    'title': thread['subject'] or thread['comment'][:50] + '...',
                    'tickers': thread['tickers'],
                    'pump_score': thread['pump_score'],
                    'replies': thread['replies'],
                    'url': f"https://boards.4channel.org/biz/thread/{thread['thread_id']}",
                    'timestamp': datetime.fromtimestamp(thread['time']).isoformat(),
                    'source': '4chan /biz/'
                }
                
                # Add snippet
                alert['snippet'] = thread['comment'][:200]
                
                alerts.append(alert)
                
        return alerts