"""
Social Pump Scanner - Automatically finds pump & dump candidates from social media
No ticker input required - finds them automatically!
"""

import time
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import concurrent.futures

from ..scrapers.social_media_aggregator import SocialMediaAggregator
from ..scrapers.yars_scraper import YARSScraper
from ..scrapers.fourchan_biz_scraper import FourChanBizScraper
from ..scrapers.investorshub_scraper import InvestorsHubScraper
from ..scrapers.bitcointalk_scraper import BitcoinTalkScraper
from ..scrapers.stocktwits_scraper import StockTwitsScraper
from ..agents.super_analyst import SuperAnalyst
from ..utils.logger import get_logger
from ..utils.data_saver import DataSaver
from ..utils.llm_formatter import LLMFormatter

class SocialPumpScanner:
    """Automatically finds pump & dump candidates from social media activity"""
    
    def __init__(self):
        self.logger = get_logger("SocialPumpScanner")
        self.aggregator = SocialMediaAggregator()
        self.analyst = SuperAnalyst()
        self.data_saver = DataSaver()
        self.formatter = LLMFormatter()
        
        # Individual scrapers for finding candidates
        self.reddit = YARSScraper()
        self.fourchan = FourChanBizScraper()
        self.investorshub = InvestorsHubScraper()
        self.bitcointalk = BitcoinTalkScraper()
        self.stocktwits = StockTwitsScraper()
        
    def find_pump_candidates(self, 
                           min_mentions: int = 10,
                           top_n: int = 10,
                           analyze_top: int = 5) -> Dict[str, Any]:
        """
        Automatically find pump & dump candidates without ticker input
        
        Returns:
            Dictionary with top pump candidates and analysis
        """
        self.logger.info("🔍 Starting automatic pump & dump detection...")
        start_time = time.time()
        
        # Step 1: Find trending tickers from all social sources
        self.logger.info("Step 1: Finding trending tickers across social media...")
        trending_tickers = self._find_trending_tickers()
        self.logger.info(f"Found {len(trending_tickers)} potential tickers")
        
        # Step 2: Filter by activity level
        active_tickers = {
            ticker: count for ticker, count in trending_tickers.items() 
            if count >= min_mentions
        }
        self.logger.info(f"Filtered to {len(active_tickers)} active tickers (>={min_mentions} mentions)")
        
        # Step 3: Collect detailed data for top candidates
        top_tickers = sorted(active_tickers.items(), key=lambda x: x[1], reverse=True)[:top_n]
        self.logger.info(f"Collecting detailed data for top {len(top_tickers)} candidates...")
        
        candidate_data = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            for ticker, mention_count in top_tickers:
                futures[ticker] = executor.submit(
                    self.aggregator.collect_pump_data, 
                    ticker,
                    save_raw=True
                )
                
            for ticker, future in futures.items():
                try:
                    data = future.result(timeout=60)
                    candidate_data[ticker] = data
                except Exception as e:
                    self.logger.error(f"Error collecting data for {ticker}: {e}")
                    
        # Step 4: Run AI analysis on top candidates
        self.logger.info(f"Running AI analysis on top {analyze_top} candidates...")
        analyzed_results = []
        
        for ticker, _ in top_tickers[:analyze_top]:
            if ticker in candidate_data:
                self.logger.info(f"Analyzing ${ticker}...")
                
                try:
                    # Use formatted data for LLM
                    formatted_data = candidate_data[ticker].get('formatted_for_llm', '')
                    
                    # Create pump detection prompt
                    prompt = self.formatter.create_pump_detection_prompt(formatted_data)
                    
                    # Run analysis
                    analysis = self.analyst.analyze(ticker, candidate_data[ticker])
                    
                    # Save LLM response
                    self.data_saver.save_llm_analysis(ticker, analysis)
                    
                    # Add to results
                    analyzed_results.append({
                        **analysis,
                        'mention_count': active_tickers[ticker],
                        'data_sources': list(candidate_data[ticker].get('sources', {}).keys())
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing {ticker}: {e}")
                    
        # Sort by pump probability
        analyzed_results.sort(key=lambda x: x.get('pump_probability', 0), reverse=True)
        
        # Step 5: Compile final report
        report = {
            'timestamp': datetime.now().isoformat(),
            'scan_duration_seconds': time.time() - start_time,
            'total_tickers_found': len(trending_tickers),
            'active_tickers': len(active_tickers),
            'top_pump_candidates': analyzed_results,
            'ticker_rankings': [
                {
                    'ticker': ticker,
                    'total_mentions': count,
                    'rank': i + 1
                }
                for i, (ticker, count) in enumerate(top_tickers)
            ],
            'high_risk_alerts': [
                r for r in analyzed_results 
                if r.get('risk_level') in ['HIGH', 'EXTREME']
            ],
            'platform_summary': self._get_platform_summary(candidate_data)
        }
        
        # Save complete report
        self.data_saver.save_pump_report(report)
        
        return report
        
    def _find_trending_tickers(self) -> Dict[str, int]:
        """Find all trending tickers across social platforms"""
        all_tickers = Counter()
        
        # Reddit - search for pump keywords
        self.logger.info("  • Scanning Reddit for pump activity...")
        reddit_tickers = self._scan_reddit_for_pumps()
        all_tickers.update(reddit_tickers)
        
        # 4chan /biz/
        self.logger.info("  • Scanning 4chan /biz/...")
        fourchan_tickers = self.fourchan.get_ticker_mentions()
        all_tickers.update(fourchan_tickers)
        
        # InvestorsHub hot boards
        self.logger.info("  • Scanning InvestorsHub hot boards...")
        hot_boards = self.investorshub.get_hot_boards()
        for board in hot_boards:
            ticker = board.get('ticker', '').upper()
            if ticker:
                all_tickers[ticker] += board.get('posts_today', 0) // 10  # Weight by activity
                
        # StockTwits trending
        if self.stocktwits:
            self.logger.info("  • Getting StockTwits trending...")
            try:
                trending = self.stocktwits.get_trending_symbols()
                for symbol in trending[:30]:
                    ticker = symbol.get('symbol', '').upper()
                    if ticker:
                        all_tickers[ticker] += 20  # High weight for trending
            except:
                pass
                
        # BitcoinTalk for crypto
        self.logger.info("  • Scanning BitcoinTalk for crypto pumps...")
        crypto_trending = self.bitcointalk.get_trending_altcoins()
        for crypto in crypto_trending:
            ticker = crypto.get('ticker', '').upper()
            if ticker:
                all_tickers[ticker] += crypto.get('activity', 0) // 5
                
        return dict(all_tickers)
        
    def _scan_reddit_for_pumps(self) -> Counter:
        """Scan Reddit for pump activity using smart detection"""
        ticker_counts = Counter()
        
        # Load configuration
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        pump_config = config.get('pump_detection', {})
        smart_mode = pump_config.get('smart_mode', {})
        
        # Get search queries from config
        search_strategies = pump_config.get('search_strategies', {})
        pump_queries = []
        
        # Smart mode: prioritize different query types
        if smart_mode.get('enabled', True):
            # Mix different types of queries for better detection
            pump_queries.extend(search_strategies.get('explicit_pump_terms', [])[:2])
            pump_queries.extend(search_strategies.get('momentum_terms', [])[:3])
            pump_queries.extend(search_strategies.get('volume_terms', [])[:2])
        else:
            # Traditional mode: use all keywords
            for category in search_strategies.values():
                if isinstance(category, list):
                    pump_queries.extend(category)
        
        # Get subreddits from config
        target_subs = pump_config.get('target_subreddits', {})
        pump_subs = []
        pump_subs.extend(target_subs.get('high_risk', []))
        pump_subs.extend(target_subs.get('medium_risk', [])[:3])
        
        # Search for pump keywords
        for query in pump_queries[:5]:  # Limit to avoid rate limiting
            try:
                posts = self.reddit.search_reddit(query, limit=25)
                
                # Extract tickers
                for post in posts:
                    tickers = self._extract_tickers_from_text(
                        f"{post.get('title', '')} {post.get('selftext', '')}"
                    )
                    for ticker in tickers:
                        ticker_counts[ticker] += 1
                        
                time.sleep(1)  # Rate limiting
            except Exception as e:
                self.logger.debug(f"Error searching '{query}': {e}")
                
        # Check hot posts in pump subreddits
        for sub in pump_subs[:3]:  # Top 3 to avoid rate limiting
            try:
                posts = self.reddit.fetch_subreddit_posts(sub, 'hot', limit=25)
                
                # Smart detection: analyze post patterns
                if smart_mode.get('enabled', True) and smart_mode.get('analyze_trending', True):
                    # Analyze posts for pump patterns without keyword bias
                    from .smart_pump_detector import SmartPumpDetector
                    detector = SmartPumpDetector()
                    
                    # Group posts by ticker
                    ticker_posts = {}
                    for post in posts:
                        tickers = self._extract_tickers_from_text(
                            f"{post.get('title', '')} {post.get('selftext', '')}"
                        )
                        for ticker in tickers:
                            if ticker not in ticker_posts:
                                ticker_posts[ticker] = []
                            ticker_posts[ticker].append(post)
                    
                    # Analyze each ticker's posts
                    for ticker, t_posts in ticker_posts.items():
                        if len(t_posts) >= 3:  # Need multiple posts for pattern analysis
                            signals = detector.analyze_without_keywords(t_posts)
                            pump_prob = detector.calculate_pump_probability(signals)
                            
                            # Weight by pump probability
                            weight = 1 + int(pump_prob * 5)  # 1-6 weight based on probability
                            ticker_counts[ticker] += weight * len(t_posts)
                else:
                    # Traditional keyword-based detection
                    for post in posts:
                        tickers = self._extract_tickers_from_text(
                            f"{post.get('title', '')} {post.get('selftext', '')}"
                        )
                        
                        # Weight by engagement
                        weight = 1
                        if post.get('score', 0) > 100:
                            weight = 2
                        if post.get('score', 0) > 1000:
                            weight = 3
                            
                        for ticker in tickers:
                            ticker_counts[ticker] += weight
                        
                time.sleep(1)
            except Exception as e:
                self.logger.debug(f"Error scanning r/{sub}: {e}")
                
        return ticker_counts
        
    def _extract_tickers_from_text(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        import re
        
        tickers = set()
        
        # $TICKER pattern
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        tickers.update(dollar_tickers)
        
        # Common stocks mentioned without $
        text_upper = text.upper()
        common_tickers = [
            'GME', 'AMC', 'BBBY', 'BB', 'NOK', 'PLTR', 'TSLA', 
            'AAPL', 'NVDA', 'AMD', 'MSFT', 'META', 'GOOGL',
            'SPY', 'QQQ', 'SNDL', 'TLRY', 'ACB', 'CLOV',
            'WISH', 'SOFI', 'HOOD', 'RIVN', 'LCID'
        ]
        
        for ticker in common_tickers:
            if f' {ticker} ' in f' {text_upper} ':
                tickers.add(ticker)
                
        # Crypto tickers
        crypto_pattern = r'\b(BTC|ETH|DOGE|SHIB|ADA|SOL|MATIC|AVAX|LINK|UNI)\b'
        crypto_tickers = re.findall(crypto_pattern, text, re.I)
        tickers.update(t.upper() for t in crypto_tickers)
        
        # Remove common false positives
        exclude = {'I', 'A', 'DD', 'CEO', 'USA', 'EU', 'UK', 'LOL', 'WTF', 'IMO'}
        tickers = {t for t in tickers if t not in exclude and len(t) >= 2}
        
        return list(tickers)
        
    def _get_platform_summary(self, candidate_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Summarize activity by platform"""
        platform_stats = defaultdict(lambda: {'tickers': 0, 'total_posts': 0})
        
        for ticker, data in candidate_data.items():
            sources = data.get('sources', {})
            
            for platform, platform_data in sources.items():
                if platform_data:
                    platform_stats[platform]['tickers'] += 1
                    
                    # Count posts/messages
                    if platform == 'reddit':
                        platform_stats[platform]['total_posts'] += len(platform_data.get('posts', []))
                    elif platform == 'stocktwits':
                        platform_stats[platform]['total_posts'] += len(platform_data.get('messages', []))
                    elif platform == 'fourchan':
                        platform_stats[platform]['total_posts'] += len(platform_data.get('pump_threads', []))
                        
        return dict(platform_stats)
        
    def monitor_live_pumps(self, check_interval_minutes: int = 15):
        """
        Continuously monitor for new pump & dump activity
        
        Args:
            check_interval_minutes: How often to check for new pumps
        """
        self.logger.info("🔴 Starting live pump monitoring...")
        
        while True:
            try:
                # Run pump detection
                results = self.find_pump_candidates(
                    min_mentions=5,  # Lower threshold for live monitoring
                    top_n=5,
                    analyze_top=3
                )
                
                # Alert on high-risk pumps
                if results['high_risk_alerts']:
                    self.logger.warning("⚠️ HIGH RISK PUMP DETECTED!")
                    for alert in results['high_risk_alerts']:
                        self.logger.warning(
                            f"  ${alert['ticker']}: {alert['pump_probability']}% probability | "
                            f"Risk: {alert['risk_level']}"
                        )
                        
                # Show summary
                self.logger.info(f"Scan complete: {len(results['top_pump_candidates'])} candidates found")
                
                # Wait before next scan
                self.logger.info(f"Next scan in {check_interval_minutes} minutes...")
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring: {e}")
                time.sleep(60)  # Wait 1 minute on error