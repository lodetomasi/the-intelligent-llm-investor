"""
Twitter/X Scraper using twscrape - Real data only
Based on vladkens/twscrape
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from ..utils.logger import get_logger

# We'll use twscrape library
try:
    from twscrape import API, gather
    from twscrape.logger import set_log_level
    TWSCRAPE_AVAILABLE = True
except ImportError:
    TWSCRAPE_AVAILABLE = False
    
class TwitterScraper:
    """Scrapes Twitter/X for crypto pump signals"""
    
    def __init__(self):
        self.logger = get_logger("TwitterScraper")
        
        if not TWSCRAPE_AVAILABLE:
            self.logger.warning("twscrape not installed. Install with: pip install twscrape")
            self.api = None
        else:
            # Initialize API
            self.api = API()
            set_log_level("WARNING")  # Reduce verbosity
            
    async def search_tweets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search tweets with query
        
        Args:
            query: Search query (e.g., 'bitcoin pump', '$BTC moon')
            limit: Number of tweets to fetch
            
        Returns:
            List of tweets
        """
        if not self.api:
            self.logger.error("Twitter API not available")
            return []
            
        try:
            tweets = []
            
            # Search tweets
            async for tweet in self.api.search(query, limit=limit):
                tweets.append({
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'created_at': tweet.date.isoformat(),
                    'user': tweet.user.username,
                    'user_followers': tweet.user.followersCount,
                    'likes': tweet.likeCount,
                    'retweets': tweet.retweetCount,
                    'replies': tweet.replyCount,
                    'views': tweet.viewCount,
                    'hashtags': [tag.text for tag in tweet.hashtags] if tweet.hashtags else [],
                    'cashtags': [tag.text for tag in tweet.cashtags] if tweet.cashtags else [],
                    'source': 'twitter',
                    'url': tweet.url
                })
                
            self.logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
            return []
            
    async def get_user_tweets(self, username: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get tweets from specific user
        
        Args:
            username: Twitter username (without @)
            limit: Number of tweets
            
        Returns:
            List of tweets
        """
        if not self.api:
            return []
            
        try:
            tweets = []
            
            # Get user ID first
            user = await self.api.user_by_login(username)
            if not user:
                self.logger.error(f"User {username} not found")
                return []
                
            # Get user tweets
            async for tweet in self.api.user_tweets(user.id, limit=limit):
                tweets.append({
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'created_at': tweet.date.isoformat(),
                    'user': username,
                    'likes': tweet.likeCount,
                    'retweets': tweet.retweetCount,
                    'cashtags': [tag.text for tag in tweet.cashtags] if tweet.cashtags else [],
                    'source': 'twitter'
                })
                
            self.logger.info(f"Got {len(tweets)} tweets from @{username}")
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error getting user tweets: {e}")
            return []
            
    async def monitor_crypto_influencers(self, influencers: List[str], hours_back: int = 6) -> Dict[str, Any]:
        """
        Monitor crypto influencers for pump signals
        
        Args:
            influencers: List of usernames to monitor
            hours_back: How many hours to look back
            
        Returns:
            Analysis of influencer activity
        """
        all_tweets = []
        pump_signals = []
        
        since = datetime.now() - timedelta(hours=hours_back)
        
        for username in influencers:
            tweets = await self.get_user_tweets(username, limit=20)
            
            # Filter recent tweets
            recent_tweets = [
                t for t in tweets 
                if datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')) > since
            ]
            
            all_tweets.extend(recent_tweets)
            
            # Check for pump signals
            for tweet in recent_tweets:
                text_lower = tweet['text'].lower()
                pump_keywords = ['moon', 'pump', 'explode', 'rocket', '🚀', '🌙', 'buy now', '100x', '10x']
                
                if any(keyword in text_lower for keyword in pump_keywords):
                    pump_signals.append({
                        'user': username,
                        'text': tweet['text'][:200],
                        'engagement': tweet['likes'] + tweet['retweets'],
                        'cashtags': tweet['cashtags']
                    })
                    
        return {
            'total_tweets': len(all_tweets),
            'pump_signals': pump_signals,
            'active_influencers': len(set(t['user'] for t in all_tweets)),
            'most_mentioned_tickers': self._extract_top_tickers(all_tweets)
        }
        
    def _extract_top_tickers(self, tweets: List[Dict], top_n: int = 5) -> List[tuple]:
        """Extract most mentioned tickers"""
        ticker_counts = {}
        
        for tweet in tweets:
            # From cashtags
            for tag in tweet.get('cashtags', []):
                ticker_counts[tag] = ticker_counts.get(tag, 0) + 1
                
            # From text with $
            import re
            text = tweet.get('text', '')
            dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
            for ticker in dollar_tickers:
                ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
                
        # Sort by count
        sorted_tickers = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tickers[:top_n]
        
    def run_search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Synchronous wrapper for search"""
        if not TWSCRAPE_AVAILABLE:
            self.logger.error("Please install twscrape: pip install twscrape")
            return []
            
        return asyncio.run(self.search_tweets(query, limit))
        
    def run_monitor(self, influencers: List[str], hours_back: int = 6) -> Dict[str, Any]:
        """Synchronous wrapper for monitoring"""
        if not TWSCRAPE_AVAILABLE:
            return {'error': 'twscrape not installed'}
            
        return asyncio.run(self.monitor_crypto_influencers(influencers, hours_back))