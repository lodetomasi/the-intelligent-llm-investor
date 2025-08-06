"""
Social Media Aggregator - Focuses on social platforms where pumps happen
"""

import concurrent.futures
from typing import Dict, List, Any
from datetime import datetime

from .yars_scraper import YARSScraper
from .stocktwits_scraper import StockTwitsScraper
from .twitter_scraper import TwitterScraper
from .discord_scraper import DiscordScraper
from .telegram_scraper import TelegramScraper
from .fourchan_biz_scraper import FourChanBizScraper
from .investorshub_scraper import InvestorsHubScraper
from .bitcointalk_scraper import BitcoinTalkScraper
from ..utils.logger import get_logger
from ..utils.data_saver import DataSaver
from ..utils.llm_formatter import LLMFormatter

class SocialMediaAggregator:
    """Aggregates data from social platforms where pump & dumps are coordinated"""
    
    def __init__(self):
        self.logger = get_logger("SocialMediaAggregator")
        self.data_saver = DataSaver()
        self.formatter = LLMFormatter()
        
        # Initialize all social scrapers
        self.reddit = YARSScraper()
        self.stocktwits = StockTwitsScraper()
        self.twitter = TwitterScraper()
        self.discord = DiscordScraper()
        self.telegram = TelegramScraper()
        self.fourchan = FourChanBizScraper()
        self.investorshub = InvestorsHubScraper()
        self.bitcointalk = BitcoinTalkScraper()
        
    def collect_pump_data(self, ticker: str, save_raw: bool = True) -> Dict[str, Any]:
        """
        Collect pump & dump data from all social sources
        Returns both raw data and LLM-formatted version
        """
        self.logger.info(f"Collecting social pump data for {ticker}")
        
        all_data = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'formatted_for_llm': '',
            'summary': {}
        }
        
        # Use ThreadPoolExecutor for parallel collection
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            
            # Submit all collection tasks
            futures['reddit'] = executor.submit(self._get_reddit_pump_data, ticker)
            futures['stocktwits'] = executor.submit(self._get_stocktwits_data, ticker)
            futures['twitter'] = executor.submit(self._get_twitter_pump_data, ticker)
            futures['fourchan'] = executor.submit(self._get_fourchan_data, ticker)
            futures['investorshub'] = executor.submit(self._get_investorshub_data, ticker)
            futures['discord'] = executor.submit(self._get_discord_pump_data, ticker)
            futures['telegram'] = executor.submit(self._get_telegram_pump_data, ticker)
            
            # For crypto, also check BitcoinTalk
            if self._is_crypto(ticker):
                futures['bitcointalk'] = executor.submit(self._get_bitcointalk_data, ticker)
                
            # Collect results
            for source, future in futures.items():
                try:
                    result = future.result(timeout=30)
                    if result:
                        all_data['sources'][source] = result
                        
                        # Save raw data if requested
                        if save_raw:
                            self.data_saver.save_scraped_data(ticker, source, result)
                            
                except Exception as e:
                    self.logger.error(f"Error collecting {source} data: {e}")
                    
        # Generate summary
        all_data['summary'] = self._generate_summary(all_data['sources'])
        
        # Format for LLM
        all_data['formatted_for_llm'] = self.formatter.format_social_data_for_llm(ticker, all_data)
        
        # Save complete dataset
        if save_raw:
            self.data_saver.save_pump_report(all_data)
            
        return all_data
        
    def _get_reddit_pump_data(self, ticker: str) -> Dict[str, Any]:
        """Get Reddit pump discussions"""
        try:
            # Search Reddit for ticker
            posts = self.reddit.search_reddit(f"${ticker} OR {ticker}", limit=100)
            
            # Also check pump-prone subreddits
            pump_subs = ['wallstreetbets', 'pennystocks', 'Shortsqueeze', 'SqueezePlays']
            for sub in pump_subs:
                sub_posts = self.reddit.fetch_subreddit_posts(sub, 'hot', limit=50)
                posts.extend(sub_posts)
                
            # Filter for ticker mentions
            relevant_posts = []
            for post in posts:
                text = f"{post.get('title', '')} {post.get('selftext', '')}".upper()
                if ticker.upper() in text or f"${ticker.upper()}" in text:
                    # Calculate pump indicators
                    post['pump_signals'] = self._calculate_reddit_pump_signals(post)
                    relevant_posts.append(post)
                    
            # Sort by engagement
            relevant_posts.sort(key=lambda x: x.get('score', 0) + x.get('num_comments', 0), reverse=True)
            
            return {
                'posts': relevant_posts[:30],
                'total_mentions': len(relevant_posts),
                'pump_score': self._calculate_overall_pump_score(relevant_posts)
            }
            
        except Exception as e:
            self.logger.error(f"Reddit error: {e}")
            return {}
            
    def _get_stocktwits_data(self, ticker: str) -> Dict[str, Any]:
        """Get StockTwits sentiment"""
        try:
            if not self.stocktwits:
                return {}
                
            messages = self.stocktwits.get_symbol_stream(ticker, limit=50)
            trending = self.stocktwits.get_trending_symbols()
            
            # Analyze sentiment distribution
            sentiment_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            pump_messages = []
            
            for msg in messages:
                sentiment = msg.get('sentiment', {}).get('class', 'neutral')
                sentiment_counts[sentiment] += 1
                
                # Check for pump language
                if self._is_pump_message(msg.get('body', '')):
                    pump_messages.append(msg)
                    
            return {
                'messages': messages[:30],
                'sentiment_distribution': sentiment_counts,
                'pump_messages': pump_messages,
                'is_trending': any(s['symbol'] == ticker for s in trending[:50]),
                'trending_rank': next((i+1 for i, s in enumerate(trending[:50]) if s['symbol'] == ticker), None)
            }
            
        except Exception as e:
            self.logger.error(f"StockTwits error: {e}")
            return {}
            
    def _get_twitter_pump_data(self, ticker: str) -> Dict[str, Any]:
        """Get Twitter pump discussions"""
        try:
            if not self.twitter:
                return {}
                
            # Search for pump-related tweets
            pump_queries = [
                f"${ticker} moon",
                f"${ticker} squeeze",
                f"${ticker} rocket",
                f"${ticker} buy now"
            ]
            
            all_tweets = []
            for query in pump_queries:
                tweets = self.twitter.run_search(query, limit=20)
                all_tweets.extend(tweets)
                
            # Check pump influencers
            pump_influencers = [
                'wallstreetbets', 'wsbmod', 'realwillmeade',
                'zerohedge', 'stoolpresidente'
            ]
            
            influencer_data = self.twitter.run_monitor(pump_influencers, hours_back=24)
            
            return {
                'tweets': all_tweets,
                'influencer_activity': influencer_data,
                'total_pump_tweets': len(all_tweets)
            }
            
        except Exception as e:
            self.logger.error(f"Twitter error: {e}")
            return {}
            
    def _get_fourchan_data(self, ticker: str) -> Dict[str, Any]:
        """Get 4chan /biz/ pump threads"""
        try:
            # Get ticker mentions
            ticker_mentions = self.fourchan.get_ticker_mentions()
            
            # Find pump threads
            pump_threads = self.fourchan.find_pump_threads()
            
            # Filter for our ticker
            ticker_threads = []
            for thread in pump_threads:
                if ticker.upper() in thread.get('tickers', []):
                    ticker_threads.append(thread)
                    
            return {
                'mention_count': ticker_mentions.get(ticker.upper(), 0),
                'pump_threads': ticker_threads,
                'pump_alerts': [a for a in self.fourchan.get_pump_alerts() if ticker.upper() in a.get('tickers', [])]
            }
            
        except Exception as e:
            self.logger.error(f"4chan error: {e}")
            return {}
            
    def _get_investorshub_data(self, ticker: str) -> Dict[str, Any]:
        """Get InvestorsHub forum data"""
        try:
            # Get board posts
            posts = self.investorshub.get_board_posts(ticker)
            
            # Check if it's a hot board
            hot_boards = self.investorshub.get_hot_boards()
            is_hot = any(b['ticker'].upper() == ticker.upper() for b in hot_boards)
            
            return {
                'posts': posts,
                'is_hot_board': is_hot,
                'post_count': len(posts)
            }
            
        except Exception as e:
            self.logger.error(f"InvestorsHub error: {e}")
            return {}
            
    def _get_discord_pump_data(self, ticker: str) -> Dict[str, Any]:
        """Get Discord pump group data"""
        try:
            if not self.discord:
                return {}
                
            # Monitor known pump servers
            messages = self.discord.monitor_servers(hours_back=6)
            
            # Filter for ticker
            ticker_messages = []
            for msg in messages:
                if ticker.upper() in msg.get('content', '').upper():
                    ticker_messages.append(msg)
                    
            return {
                'messages': ticker_messages,
                'pump_servers': self.discord.known_pump_servers if hasattr(self.discord, 'known_pump_servers') else []
            }
            
        except Exception as e:
            self.logger.error(f"Discord error: {e}")
            return {}
            
    def _get_telegram_pump_data(self, ticker: str) -> Dict[str, Any]:
        """Get Telegram pump group data"""
        try:
            if not self.telegram:
                return {}
                
            # Get messages from pump groups
            messages = self.telegram.get_pump_signals()
            
            # Filter for ticker
            ticker_signals = []
            for msg in messages:
                if ticker.upper() in msg.get('text', '').upper():
                    ticker_signals.append(msg)
                    
            return {
                'pump_signals': ticker_signals,
                'signal_count': len(ticker_signals)
            }
            
        except Exception as e:
            self.logger.error(f"Telegram error: {e}")
            return {}
            
    def _get_bitcointalk_data(self, ticker: str) -> Dict[str, Any]:
        """Get BitcoinTalk forum data for crypto"""
        try:
            # Search altcoin announcements
            announcements = self.bitcointalk.search_altcoin_announcements()
            
            # Get trending
            trending = self.bitcointalk.get_trending_altcoins()
            
            # Filter for ticker
            ticker_data = {
                'announcements': [a for a in announcements if ticker.upper() in a.get('title', '').upper()],
                'is_trending': any(t['ticker'] == ticker.upper() for t in trending)
            }
            
            return ticker_data
            
        except Exception as e:
            self.logger.error(f"BitcoinTalk error: {e}")
            return {}
            
    def _calculate_reddit_pump_signals(self, post: Dict[str, Any]) -> List[str]:
        """Calculate pump signals from Reddit post"""
        signals = []
        text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
        
        # New account
        if post.get('author_created_utc'):
            account_age = (datetime.now().timestamp() - post['author_created_utc']) / 86400
            if account_age < 30:
                signals.append("New account (<30 days)")
                
        # Pump keywords
        pump_keywords = ['squeeze', 'moon', 'rocket', 'buy now', 'don\'t miss', 'last chance']
        for keyword in pump_keywords:
            if keyword in text:
                signals.append(f"Pump keyword: {keyword}")
                
        # Awards (potential manipulation)
        if post.get('total_awards_received', 0) > 5:
            signals.append(f"Heavily awarded ({post['total_awards_received']} awards)")
            
        # Sudden activity
        if post.get('score', 0) > 100 and post.get('num_comments', 0) < 10:
            signals.append("High score, low engagement (bot activity?)")
            
        return signals
        
    def _is_pump_message(self, text: str) -> bool:
        """Check if message contains pump language"""
        text_lower = text.lower()
        pump_phrases = [
            'to the moon', 'rocket', 'squeeze', 'buy now',
            'don\'t miss', 'last chance', '10x', '100x',
            'millionaire', 'lambo', 'diamond hands'
        ]
        return any(phrase in text_lower for phrase in pump_phrases)
        
    def _calculate_overall_pump_score(self, posts: List[Dict[str, Any]]) -> int:
        """Calculate overall pump likelihood score"""
        if not posts:
            return 0
            
        score = 0
        
        # Volume of posts
        if len(posts) > 50:
            score += 3
        elif len(posts) > 20:
            score += 2
        elif len(posts) > 10:
            score += 1
            
        # Average pump signals per post
        total_signals = sum(len(p.get('pump_signals', [])) for p in posts)
        avg_signals = total_signals / len(posts) if posts else 0
        
        if avg_signals > 3:
            score += 3
        elif avg_signals > 2:
            score += 2
        elif avg_signals > 1:
            score += 1
            
        # Recent surge
        recent_posts = [p for p in posts if (datetime.now().timestamp() - p.get('created_utc', 0)) < 3600]
        if len(recent_posts) > len(posts) * 0.5:
            score += 2
            
        return min(score, 10)  # Cap at 10
        
    def _is_crypto(self, ticker: str) -> bool:
        """Check if ticker is cryptocurrency"""
        crypto_symbols = {
            'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE', 'SHIB',
            'MATIC', 'AVAX', 'LINK', 'UNI', 'XRP', 'LTC'
        }
        return ticker.upper() in crypto_symbols
        
    def _generate_summary(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of social media activity"""
        summary = {
            'total_social_mentions': 0,
            'active_platforms': [],
            'pump_indicators': [],
            'risk_level': 'LOW'
        }
        
        # Count mentions
        if 'reddit' in sources:
            summary['total_social_mentions'] += sources['reddit'].get('total_mentions', 0)
            
        if 'stocktwits' in sources:
            summary['total_social_mentions'] += len(sources['stocktwits'].get('messages', []))
            
        if 'twitter' in sources:
            summary['total_social_mentions'] += sources['twitter'].get('total_pump_tweets', 0)
            
        # Active platforms
        summary['active_platforms'] = [k for k, v in sources.items() if v]
        
        # Pump indicators
        if summary['total_social_mentions'] > 100:
            summary['pump_indicators'].append('High social volume')
            
        if 'stocktwits' in sources and sources['stocktwits'].get('is_trending'):
            summary['pump_indicators'].append('Trending on StockTwits')
            
        if 'fourchan' in sources and sources['fourchan'].get('pump_alerts'):
            summary['pump_indicators'].append('4chan pump alerts')
            
        # Risk assessment
        if len(summary['pump_indicators']) >= 3:
            summary['risk_level'] = 'HIGH'
        elif len(summary['pump_indicators']) >= 2:
            summary['risk_level'] = 'MEDIUM'
            
        return summary