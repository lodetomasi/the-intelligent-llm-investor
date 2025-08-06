"""
Smart Pump Detection Strategy - More intelligent and less hardcoded
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set, Counter
from collections import Counter
import re

class SmartPumpDetector:
    """Intelligent pump detection using configurable strategies"""
    
    def __init__(self):
        # Load configuration
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.pump_config = self.config.get('pump_detection', {})
        self.smart_mode = self.pump_config.get('smart_mode', {})
        
    def get_detection_strategy(self) -> Dict[str, any]:
        """Get intelligent detection strategy based on config"""
        
        if self.smart_mode.get('enabled', True):
            return {
                'mode': 'smart',
                'analyze_trending': self.smart_mode.get('analyze_trending', True),
                'spike_detection': self.smart_mode.get('spike_detection', True),
                'cross_platform': self.smart_mode.get('cross_platform_validation', True),
                'strategies': self._get_smart_strategies()
            }
        else:
            return {
                'mode': 'keyword',
                'queries': self._get_keyword_queries()
            }
    
    def _get_smart_strategies(self) -> List[Dict]:
        """Get smart detection strategies"""
        strategies = []
        
        # Strategy 1: Analyze trending posts without keyword bias
        strategies.append({
            'name': 'trending_analysis',
            'action': 'fetch_hot_posts',
            'params': {
                'subreddits': self._get_target_subreddits(),
                'limit': 50,
                'analyze_velocity': True  # Look for rapid upvote velocity
            }
        })
        
        # Strategy 2: Detect mention spikes
        strategies.append({
            'name': 'spike_detection',
            'action': 'compare_mention_frequency',
            'params': {
                'timeframes': ['1h', '6h', '24h'],
                'spike_threshold': 3.0  # 3x normal volume
            }
        })
        
        # Strategy 3: Cross-platform validation
        strategies.append({
            'name': 'cross_platform',
            'action': 'validate_across_platforms',
            'params': {
                'min_platforms': 2,
                'platforms': ['reddit', 'stocktwits', '4chan', 'twitter']
            }
        })
        
        # Strategy 4: Pattern recognition without keywords
        strategies.append({
            'name': 'pattern_analysis',
            'action': 'detect_patterns',
            'params': {
                'patterns': [
                    'sudden_user_influx',  # Many new users posting
                    'repetitive_messaging',  # Same message patterns
                    'time_clustering',  # Posts clustered in time
                    'low_karma_surge'  # Many low-karma accounts
                ]
            }
        })
        
        return strategies
    
    def _get_keyword_queries(self) -> List[str]:
        """Get keyword queries from config"""
        search_strategies = self.pump_config.get('search_strategies', {})
        
        # Combine all keyword categories
        all_keywords = []
        for category, keywords in search_strategies.items():
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
                
        return all_keywords[:10]  # Limit to top 10
    
    def _get_target_subreddits(self) -> List[str]:
        """Get target subreddits from config"""
        target_subs = self.pump_config.get('target_subreddits', {})
        
        # Prioritize high-risk subreddits
        subreddits = []
        subreddits.extend(target_subs.get('high_risk', []))
        subreddits.extend(target_subs.get('medium_risk', []))
        subreddits.extend(target_subs.get('crypto', []))
        
        return subreddits
    
    def analyze_without_keywords(self, posts: List[Dict]) -> Dict[str, float]:
        """Analyze posts for pump signals without relying on keywords"""
        
        signals = {
            'user_anomaly_score': 0.0,
            'temporal_clustering': 0.0,
            'engagement_spike': 0.0,
            'cross_posting': 0.0,
            'new_account_ratio': 0.0
        }
        
        if not posts:
            return signals
            
        # 1. User anomaly detection
        user_post_counts = Counter()
        user_ages = []
        for post in posts:
            author = post.get('author', 'unknown')
            user_post_counts[author] += 1
            
            # Check account age if available
            if 'author_created' in post:
                user_ages.append(post['author_created'])
                
        # High concentration of posts from few users
        if len(user_post_counts) > 0:
            top_5_users = sum(count for _, count in user_post_counts.most_common(5))
            signals['user_anomaly_score'] = top_5_users / len(posts)
            
        # 2. Temporal clustering (posts clustered in short time window)
        if len(posts) > 10:
            timestamps = sorted([p.get('created_utc', 0) for p in posts if p.get('created_utc')])
            if timestamps:
                time_span = timestamps[-1] - timestamps[0]
                if time_span > 0:
                    posts_per_hour = len(posts) / (time_span / 3600)
                    # Normal is ~1-2 posts per hour, 10+ is suspicious
                    signals['temporal_clustering'] = min(posts_per_hour / 10, 1.0)
                    
        # 3. Engagement spike (unusually high upvotes/comments)
        scores = [p.get('score', 0) for p in posts]
        if scores:
            avg_score = sum(scores) / len(scores)
            high_score_posts = sum(1 for s in scores if s > avg_score * 3)
            signals['engagement_spike'] = high_score_posts / len(posts)
            
        # 4. Cross-posting detection
        titles = [p.get('title', '').lower() for p in posts]
        duplicate_titles = len(titles) - len(set(titles))
        if titles:
            signals['cross_posting'] = duplicate_titles / len(titles)
            
        # 5. New account ratio
        if user_ages:
            new_accounts = sum(1 for age in user_ages if age < 30)  # Less than 30 days
            signals['new_account_ratio'] = new_accounts / len(user_ages)
            
        return signals
    
    def calculate_pump_probability(self, signals: Dict[str, float]) -> float:
        """Calculate overall pump probability from signals"""
        
        # Weighted average of signals
        weights = {
            'user_anomaly_score': 0.25,
            'temporal_clustering': 0.20,
            'engagement_spike': 0.15,
            'cross_posting': 0.20,
            'new_account_ratio': 0.20
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for signal, value in signals.items():
            if signal in weights:
                total_score += value * weights[signal]
                total_weight += weights[signal]
                
        if total_weight > 0:
            return total_score / total_weight
        return 0.0