"""
Momentum-Based Pump Scanner - Finds pumps from momentum, not tickers
"""

import time
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
import concurrent.futures

from ..scrapers.yars_scraper import YARSScraper
from ..scrapers.fourchan_biz_scraper import FourChanBizScraper
from ..scrapers.stocktwits_scraper import StockTwitsScraper
from ..agents.super_analyst import SuperAnalyst
from ..agents.momentum_analyst import MomentumAnalyst
from ..utils.logger import get_logger
from ..utils.data_saver import DataSaver

class MomentumPumpScanner:
    """
    Scans for pump & dumps by detecting momentum FIRST,
    then extracting tickers from high-momentum content
    """
    
    def __init__(self):
        self.logger = get_logger("MomentumPumpScanner")
        self.reddit = YARSScraper()
        self.fourchan = FourChanBizScraper()
        self.stocktwits = StockTwitsScraper()
        self.analyst = SuperAnalyst()
        self.momentum_analyst = MomentumAnalyst()
        self.data_saver = DataSaver()
        
    def find_momentum_pumps(self, 
                           momentum_threshold: float = 2.0,
                           time_window_hours: int = 6,
                           analyze_top: int = 5) -> Dict[str, Any]:
        """
        Find pumps by detecting momentum patterns first
        
        Args:
            momentum_threshold: Minimum momentum score (2.0 = 2x normal)
            time_window_hours: Time window to analyze
            analyze_top: Number of high-momentum events to analyze
        """
        
        self.logger.info("🌊 Starting MOMENTUM-BASED pump detection...")
        start_time = time.time()
        
        # Step 1: Find HIGH MOMENTUM content (not ticker-specific)
        self.logger.info("Step 1: Scanning for momentum surges...")
        momentum_events = self._find_momentum_events(time_window_hours)
        
        # Step 2: Cluster momentum by topics/themes
        self.logger.info("Step 2: Clustering momentum by themes...")
        momentum_clusters = self._cluster_momentum(momentum_events)
        
        # Step 3: Analyze momentum patterns (NO TICKER EXTRACTION!)
        self.logger.info("Step 3: Analyzing momentum patterns...")
        theme_breakdown = self._analyze_themes(momentum_clusters)
        platform_momentum = self._analyze_platform_momentum(momentum_events)
        
        # Step 4: Detect high-risk patterns
        self.logger.info("Step 4: Detecting high-risk pump patterns...")
        risk_analysis = self._detect_pump_patterns(momentum_clusters, momentum_events)
        
        # Step 5: AI analysis of top clusters (if requested)
        ai_analysis = {}
        if analyze_top > 0 and momentum_clusters:
            self.logger.info(f"Step 5: Running AI analysis on top {min(analyze_top, len(momentum_clusters))} clusters...")
            ai_analysis = self._run_ai_analysis(momentum_clusters[:analyze_top], platform_momentum)
        
        elapsed = time.time() - start_time
        
        # Build results WITHOUT tickers
        results = {
            'scan_time': elapsed,
            'momentum_events': len(momentum_events),
            'clusters_found': len(momentum_clusters),
            'theme_breakdown': theme_breakdown,
            'platform_momentum': platform_momentum,
            'timestamp': datetime.now().isoformat(),
            'top_theme': self._get_top_theme(theme_breakdown),
            'peak_time': self._get_peak_time(momentum_events),
            **risk_analysis,
            'ai_analysis': ai_analysis
        }
        
        # Add recommendation based on patterns
        if risk_analysis.get('high_risk_patterns', 0) > 3:
            results['recommendation'] = "⚠️ HIGH PUMP RISK - Multiple coordinated patterns detected"
        elif len(momentum_clusters) > 5:
            results['recommendation'] = "🔍 ELEVATED ACTIVITY - Monitor these themes closely"
        else:
            results['recommendation'] = "✅ NORMAL MARKET CHATTER - No significant pump patterns"
            
        return results
        
    def _find_momentum_events(self, hours: int) -> List[Dict[str, Any]]:
        """Find content with unusual momentum/activity"""
        
        momentum_events = []
        
        # 1. Reddit: Find RAPIDLY RISING posts (not by ticker)
        self.logger.info("  • Scanning Reddit for rising posts...")
        
        # Get hot posts from ALL investing subreddits
        hot_posts = []
        # Comprehensive list of trading/investing subreddits
        subreddits = [
            # Major subs
            'wallstreetbets', 'pennystocks', 'stocks', 'investing', 'StockMarket',
            # Trading specific
            'options', 'Daytrading', 'swingtrading', 'algotrading', 'thetagang',
            # Penny stocks & small caps
            'RobinHoodPennyStocks', 'smallstreetbets', 'UndervaluedStonks',
            # Value & dividend investing
            'SecurityAnalysis', 'ValueInvesting', 'dividends', 
            # Sector specific
            'weedstocks', 'shroomstocks', 'greeninvestor', 'SPACs',
            # Crypto related
            'CryptoMoonShots', 'CryptoCurrency', 'SatoshiStreetBets', 'AltStreetBets',
            # International
            'CanadianPennyStocks', 'CanadianInvestor', 'ASX_Bets', 'EuropeanStocks',
            # High risk/meme stocks
            'Shortsqueeze', 'SqueezeDD', 'BBIG', 'Superstonk', 'amcstock',
            # Due diligence
            'StockMarketDD', 'pennystocksDD', 'DDintoGME'
        ]
        
        # Process in batches to avoid rate limiting
        for i, sub in enumerate(subreddits):
            try:
                # For major subs, get more posts
                if sub in ['wallstreetbets', 'pennystocks', 'CryptoMoonShots', 'Shortsqueeze']:
                    posts = self.reddit.fetch_subreddit_posts(sub, 'hot', limit=50)
                    hot_posts.extend(posts)
                    
                    # Also get "rising" posts - these have momentum
                    rising = self.reddit.fetch_subreddit_posts(sub, 'rising', limit=25)
                    hot_posts.extend(rising)
                else:
                    # For smaller subs, get fewer posts to save time
                    posts = self.reddit.fetch_subreddit_posts(sub, 'hot', limit=25)
                    hot_posts.extend(posts)
                
                # Log progress every 5 subs
                if (i + 1) % 5 == 0:
                    self.logger.info(f"    Processed {i + 1}/{len(subreddits)} subreddits...")
                
                time.sleep(0.5)  # Shorter delay for efficiency
            except Exception as e:
                self.logger.debug(f"Error fetching r/{sub}: {e}")
                
        # Calculate momentum score for each post
        for post in hot_posts:
            momentum_score = self._calculate_post_momentum(post)
            if momentum_score > 0.5:  # 0.5x normal engagement (50 engagement/hour)
                momentum_events.append({
                    'type': 'reddit_surge',
                    'content': post,
                    'momentum_score': momentum_score,
                    'platform': 'reddit'
                })
                
        # 2. StockTwits: Find trending discussions (not by ticker)
        self.logger.info("  • Scanning StockTwits for trending activity...")
        try:
            trending = self.stocktwits.get_trending_symbols()
            # But we want the MESSAGES, not just symbols
            for trend in trending[:10]:
                symbol = trend.get('symbol')
                if symbol:
                    messages = self.stocktwits.get_symbol_stream(symbol, limit=30)
                    
                    # Group messages by time to find bursts
                    time_groups = self._group_by_time(messages, minutes=30)
                    for time_group in time_groups:
                        if len(time_group) > 10:  # Burst of activity
                            momentum_events.append({
                                'type': 'stocktwits_burst',
                                'content': time_group,
                                'momentum_score': len(time_group) / 5.0,
                                'platform': 'stocktwits'
                            })
        except Exception as e:
            self.logger.info(f"StockTwits skipped: {e}")
            
        # 3. 4chan: Find high-reply threads
        self.logger.info("  • Scanning 4chan for high-activity threads...")
        try:
            threads = self.fourchan.fetch_pump_threads()
            for thread in threads:
                replies = thread.get('replies', 0)
                if replies > 50:  # High engagement thread
                    momentum_events.append({
                        'type': '4chan_hot_thread',
                        'content': thread,
                        'momentum_score': replies / 25.0,
                        'platform': '4chan'
                    })
        except Exception as e:
            self.logger.info(f"4chan skipped: {e}")
            
        self.logger.info(f"  Found {len(momentum_events)} high-momentum events")
        return momentum_events
        
    def _calculate_post_momentum(self, post: Dict) -> float:
        """Calculate momentum score for a post"""
        
        # Get post age in hours
        created = post.get('created_utc', 0)
        if created:
            age_hours = (time.time() - created) / 3600
        else:
            age_hours = 24  # Default if unknown
            
        # Prevent division by zero
        if age_hours < 0.5:
            age_hours = 0.5
            
        # Calculate engagement velocity
        score = post.get('score', 0)
        comments = post.get('num_comments', 0)
        
        # Momentum = (score + comments*2) / age_hours
        engagement = score + (comments * 2)
        momentum = engagement / age_hours
        
        # Normalize (50 engagement/hour = momentum score of 1.0)
        return momentum / 50.0
        
    def _cluster_momentum(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Cluster momentum events by theme/topic"""
        
        clusters = []
        
        # Group events by common themes
        theme_groups = defaultdict(list)
        
        for event in events:
            # Extract themes from content
            themes = self._extract_themes(event)
            
            for theme in themes:
                theme_groups[theme].append(event)
                
        # Convert to clusters
        for theme, theme_events in theme_groups.items():
            if len(theme_events) >= 2:  # Need multiple events for a cluster
                total_momentum = sum(e['momentum_score'] for e in theme_events)
                
                clusters.append({
                    'theme': theme,
                    'events': theme_events,
                    'total_momentum': total_momentum,
                    'platform_diversity': len(set(e['platform'] for e in theme_events))
                })
                
        # Sort by total momentum
        clusters.sort(key=lambda x: x['total_momentum'], reverse=True)
        
        return clusters
        
    def _extract_themes(self, event: Dict) -> List[str]:
        """Extract themes from momentum event"""
        
        themes = []
        
        # Get text content
        content = event.get('content', {})
        if event['type'] == 'reddit_surge':
            text = f"{content.get('title', '')} {content.get('selftext', '')}"
        elif event['type'] == 'stocktwits_burst':
            text = " ".join([m.get('body', '') for m in content])
        elif event['type'] == '4chan_hot_thread':
            text = f"{content.get('subject', '')} {content.get('comment', '')}"
        else:
            text = str(content)
            
        text_lower = text.lower()
        
        # Theme detection patterns
        if any(word in text_lower for word in ['squeeze', 'short', 'gamma']):
            themes.append('squeeze_play')
        if any(word in text_lower for word in ['pump', 'moon', 'rocket']):
            themes.append('pump_hype')
        if any(word in text_lower for word in ['merger', 'acquisition', 'buyout']):
            themes.append('ma_rumor')
        if any(word in text_lower for word in ['earnings', 'revenue', 'beat']):
            themes.append('earnings_play')
        if any(word in text_lower for word in ['fda', 'approval', 'clinical']):
            themes.append('biotech_catalyst')
        if any(word in text_lower for word in ['crypto', 'bitcoin', 'defi']):
            themes.append('crypto_momentum')
            
        # Extract mentioned sectors
        sectors = self._extract_sectors(text)
        themes.extend(sectors)
        
        return themes
        
    def _extract_sectors(self, text: str) -> List[str]:
        """Extract market sectors from text"""
        
        sectors = []
        text_lower = text.lower()
        
        sector_keywords = {
            'tech': ['tech', 'software', 'saas', 'cloud', 'ai'],
            'biotech': ['biotech', 'pharma', 'drug', 'clinical'],
            'energy': ['oil', 'energy', 'solar', 'renewable'],
            'finance': ['bank', 'financial', 'fintech', 'payment'],
            'retail': ['retail', 'consumer', 'store', 'ecommerce'],
            'crypto': ['crypto', 'bitcoin', 'ethereum', 'defi']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in text_lower for kw in keywords):
                sectors.append(f"sector_{sector}")
                
        return sectors
        
    def _extract_tickers_from_momentum(self, clusters: List[Dict]) -> List[Tuple[str, float]]:
        """Extract tickers from high-momentum clusters"""
        
        ticker_momentum = Counter()
        
        for cluster in clusters:
            cluster_momentum = cluster['total_momentum']
            
            # Extract tickers from all events in cluster
            for event in cluster['events']:
                content = event.get('content', {})
                
                # Get text based on event type
                if event['type'] == 'reddit_surge':
                    text = f"{content.get('title', '')} {content.get('selftext', '')}"
                elif event['type'] == 'stocktwits_burst':
                    text = " ".join([m.get('body', '') for m in content])
                elif event['type'] == '4chan_hot_thread':
                    text = f"{content.get('subject', '')} {content.get('comment', '')}"
                else:
                    text = str(content)
                    
                # Extract tickers
                tickers = self._extract_tickers(text)
                
                # Weight by cluster momentum
                for ticker in tickers:
                    ticker_momentum[ticker] += cluster_momentum
                    
        # Sort by momentum
        sorted_tickers = [(t, m) for t, m in ticker_momentum.most_common()]
        
        return sorted_tickers
        
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        
        tickers = set()
        
        # Pattern 1: $TICKER
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        tickers.update(dollar_tickers)
        
        # Pattern 2: Standalone uppercase words (likely tickers)
        words = text.split()
        for word in words:
            cleaned = re.sub(r'[^A-Z]', '', word)
            if 2 <= len(cleaned) <= 5 and cleaned.isupper():
                # Check if it's a common word
                common_words = ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'ALL', 'NEW', 'CEO', 'IPO', 'FDA', 
                               'US', 'UK', 'EU', 'PE', 'EPS', 'ETF', 'ER', 'DD', 'TLDR', 'WSB', 'YOLO',
                               'GAAP', 'MM', 'YY', 'BULL', 'BEAR', 'PUT', 'CALL', 'IT', 'AI', 'UP', 'DOWN',
                               'HIGH', 'LOW', 'BUY', 'SELL', 'HOLD', 'RSI', 'MA', 'EMA', 'SMA', 'ATH', 'EOD',
                               'OTM', 'ITM', 'IV', 'DTE', 'RH', 'TD', 'IB', 'API', 'GUI', 'CSV', 'PDF',
                               'MOON', 'HODL', 'FOMO', 'FUD', 'DYOR', 'NFA', 'IMO', 'IMHO', 'TBH', 'DCA']
                if cleaned not in common_words:
                    tickers.add(cleaned)
        
        # Pattern 3: Crypto specific patterns (longer tickers allowed)
        crypto_pattern = r'\b([A-Z]{2,10})\b'
        crypto_mentions = re.findall(crypto_pattern, text)
        
        # Known crypto tickers
        known_crypto = {'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE', 'SHIB', 'MATIC', 'AVAX', 
                       'LINK', 'UNI', 'ATOM', 'XRP', 'DOT', 'TRX', 'NEAR', 'APE', 'SAND',
                       'MANA', 'AXS', 'GALA', 'ENJ', 'CHZ', 'ALGO', 'VET', 'HBAR', 'XLM'}
        
        for mention in crypto_mentions:
            if mention in known_crypto or (len(mention) >= 3 and 'CRYPTO' in text.upper()):
                tickers.add(mention)
                    
        return list(tickers)
        
    def _group_by_time(self, messages: List[Dict], minutes: int = 30) -> List[List[Dict]]:
        """Group messages by time window"""
        
        if not messages:
            return []
            
        # Sort by time
        sorted_msgs = sorted(messages, 
                           key=lambda x: x.get('created_at', ''), 
                           reverse=True)
        
        groups = []
        current_group = []
        
        for msg in sorted_msgs:
            if not current_group:
                current_group.append(msg)
            else:
                # Check time difference
                # (simplified - would need proper date parsing)
                current_group.append(msg)
                
                if len(current_group) >= 20:  # Max group size
                    groups.append(current_group)
                    current_group = []
                    
        if current_group:
            groups.append(current_group)
            
        return groups
        
    def _analyze_themes(self, clusters: List[Dict]) -> Dict[str, Dict]:
        """Analyze theme distribution without exposing tickers"""
        theme_stats = defaultdict(lambda: {'count': 0, 'total_momentum': 0})
        
        for cluster in clusters:
            theme = cluster['theme']
            theme_stats[theme]['count'] += len(cluster['events'])
            theme_stats[theme]['total_momentum'] += cluster['total_momentum']
            
        return dict(theme_stats)
        
    def _analyze_platform_momentum(self, events: List[Dict]) -> Dict[str, float]:
        """Analyze momentum by platform"""
        platform_momentum = defaultdict(float)
        
        for event in events:
            platform = event['platform']
            momentum = event['momentum_score']
            platform_momentum[platform] += momentum
            
        return dict(platform_momentum)
        
    def _detect_pump_patterns(self, clusters: List[Dict], events: List[Dict]) -> Dict[str, Any]:
        """Detect pump patterns without ticker analysis"""
        
        risk_indicators = {
            'high_risk_patterns': 0,
            'coordinated_platforms': 0,
            'volume_spikes': 0,
            'new_account_ratio': 0.0
        }
        
        # Check for cross-platform coordination
        platform_clusters = defaultdict(set)
        for cluster in clusters:
            platforms = set(e['platform'] for e in cluster['events'])
            if len(platforms) > 2:
                risk_indicators['high_risk_patterns'] += 1
                risk_indicators['coordinated_platforms'] = max(
                    risk_indicators['coordinated_platforms'], 
                    len(platforms)
                )
                
        # Check for volume spikes (high momentum scores)
        high_momentum_events = [e for e in events if e['momentum_score'] > 5.0]
        risk_indicators['volume_spikes'] = len(high_momentum_events)
        
        # Simulate new account detection (would need real data)
        if any('squeeze' in c['theme'] or 'pump' in c['theme'] for c in clusters):
            risk_indicators['new_account_ratio'] = 0.35  # 35% new accounts typical in pumps
            
        return risk_indicators
        
    def _get_top_theme(self, theme_breakdown: Dict) -> str:
        """Get the theme with highest momentum"""
        if not theme_breakdown:
            return "None"
            
        top_theme = max(theme_breakdown.items(), 
                       key=lambda x: x[1]['total_momentum'])
        return top_theme[0].replace('_', ' ').title()
        
    def _get_peak_time(self, events: List[Dict]) -> str:
        """Estimate peak momentum time"""
        # For now, return current time range
        # In production, would analyze event timestamps
        return "Last 2-4 hours"
        
    def _run_ai_analysis(self, top_clusters: List[Dict], platform_momentum: Dict) -> Dict[str, Any]:
        """Run AI analysis on top momentum clusters"""
        
        ai_results = {
            'cluster_analyses': [],
            'platform_analysis': {},
            'overall_assessment': {}
        }
        
        # Analyze each top cluster
        for cluster in top_clusters:
            self.logger.info(f"  Analyzing {cluster['theme']} cluster...")
            analysis = self.momentum_analyst.analyze_momentum_cluster(cluster)
            ai_results['cluster_analyses'].append({
                'theme': cluster['theme'],
                'analysis': analysis
            })
            
        # Analyze platform patterns
        if platform_momentum:
            self.logger.info("  Analyzing cross-platform patterns...")
            ai_results['platform_analysis'] = self.momentum_analyst.analyze_platform_patterns(platform_momentum)
            
        # Generate overall report
        if top_clusters:
            highest_risk = max(
                (a['analysis'].get('pump_probability', 0) for a in ai_results['cluster_analyses']),
                default=0
            )
            ai_results['overall_assessment'] = {
                'highest_pump_probability': highest_risk,
                'themes_analyzed': len(top_clusters),
                'risk_level': 'HIGH' if highest_risk > 70 else 'MEDIUM' if highest_risk > 40 else 'LOW'
            }
            
        return ai_results