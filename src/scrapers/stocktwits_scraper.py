"""
StockTwits Scraper - Real data only, no mocks
"""

import requests
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from ..utils.logger import get_logger

class StockTwitsScraper:
    """Scrapes StockTwits for stock sentiment and pump signals"""
    
    def __init__(self):
        self.logger = get_logger("StockTwitsScraper")
        self.base_url = "https://api.stocktwits.com/api/2/streams"
        
        # Headers to appear as browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://stocktwits.com/',
            'Origin': 'https://stocktwits.com'
        }
        
    def get_symbol_stream(self, symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get message stream for a specific symbol
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            limit: Number of messages to fetch
            
        Returns:
            List of messages
        """
        try:
            # StockTwits public API endpoint
            url = f"{self.base_url}/symbol/{symbol}.json"
            params = {
                'limit': min(limit, 30)  # API limit
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data or not isinstance(data, dict):
                        self.logger.warning(f"Invalid JSON response for {symbol}")
                        return []
                    
                    messages = data.get('messages', [])
                    if not messages:
                        self.logger.debug(f"No messages in response for {symbol}")
                        return []
                    
                    # Convert to our format
                    posts = []
                    for msg in messages:
                        if not msg or not isinstance(msg, dict):
                            continue
                            
                        # Safe extraction with null checks
                        user_data = msg.get('user') or {}
                        likes_data = msg.get('likes') or {}
                        entities_data = msg.get('entities') or {}
                        sentiment_data = entities_data.get('sentiment') or {}
                        symbols_data = msg.get('symbols') or []
                        
                        post = {
                            'id': msg.get('id') or 'unknown',
                            'body': msg.get('body') or '',
                            'created_at': msg.get('created_at') or '',
                            'user': user_data.get('username') or 'unknown',
                            'user_followers': user_data.get('followers') or 0,
                            'likes': likes_data.get('total') or 0,
                            'sentiment': sentiment_data.get('basic'),
                            'symbols': [s.get('symbol') for s in symbols_data if s and s.get('symbol')],
                            'source': 'stocktwits',
                            'url': f"https://stocktwits.com/{user_data.get('username', 'unknown')}/message/{msg.get('id', 'unknown')}"
                        }
                        posts.append(post)
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error parsing StockTwits response: {e}")
                    return []
                    
                self.logger.info(f"Fetched {len(posts)} messages for ${symbol} from StockTwits")
                return posts
                
            elif response.status_code == 429:
                self.logger.warning("StockTwits rate limit hit")
                return []
            elif response.status_code == 404:
                self.logger.warning(f"StockTwits API endpoint not found for {symbol}. Trying alternative approach...")
                # Try web scraping as fallback
                return self._scrape_symbol_page(symbol)
            else:
                self.logger.error(f"StockTwits API error: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching StockTwits data: {e}")
            return []
            
    def get_trending_symbols(self) -> List[Dict[str, Any]]:
        """
        Get trending symbols on StockTwits
        
        Returns:
            List of trending symbols with metrics
        """
        try:
            url = f"{self.base_url}/trending.json"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data or not isinstance(data, dict):
                        self.logger.warning("Invalid JSON response for trending")
                        return []
                    
                    symbols = data.get('symbols', [])
                    if not symbols:
                        self.logger.debug("No symbols in trending response")
                        return []
                    
                    trending = []
                    for sym in symbols:
                        if not sym or not isinstance(sym, dict):
                            continue
                            
                        trending.append({
                            'symbol': sym.get('symbol') or 'UNKNOWN',
                            'title': sym.get('title') or '',
                            'watchlist_count': sym.get('watchlist_count') or 0,
                            'trending_score': sym.get('trending_score') or 0
                        })
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error parsing trending response: {e}")
                    return []
                    
                self.logger.info(f"Found {len(trending)} trending symbols on StockTwits")
                return trending
                
            elif response.status_code == 404:
                self.logger.warning("StockTwits trending endpoint changed. Trying web scraping...")
                return self._scrape_trending_page()
            else:
                self.logger.error(f"Failed to get trending: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching trending symbols: {e}")
            return []
            
    def search_cashtag(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Search for messages containing a cashtag
        
        Args:
            query: Search term (e.g., 'pump', 'squeeze')
            limit: Number of results
            
        Returns:
            List of messages
        """
        try:
            # Use general stream search
            url = f"{self.base_url}/all.json"
            params = {
                'filter': 'top',
                'limit': min(limit, 30)
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                # Filter for query term
                filtered = []
                for msg in messages:
                    body = msg.get('body', '').lower()
                    if query.lower() in body:
                        post = {
                            'id': msg.get('id'),
                            'body': msg.get('body', ''),
                            'created_at': msg.get('created_at'),
                            'user': msg.get('user', {}).get('username', 'unknown'),
                            'likes': msg.get('likes', {}).get('total', 0),
                            'symbols': [s.get('symbol') for s in msg.get('symbols', [])],
                            'source': 'stocktwits'
                        }
                        filtered.append(post)
                        
                self.logger.info(f"Found {len(filtered)} messages containing '{query}'")
                return filtered
                
            else:
                self.logger.error(f"Search failed: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching StockTwits: {e}")
            return []
            
    def analyze_pump_signals(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze messages for pump & dump signals
        
        Args:
            messages: List of StockTwits messages
            
        Returns:
            Analysis results
        """
        pump_keywords = [
            'moon', 'rocket', 'squeeze', 'explode', 'pump',
            'buy now', 'last chance', 'going up', 'huge gains',
            '🚀', '🌙', '💎', '🙌', 'diamond hands', 'hodl',
            'short squeeze', 'gamma squeeze', 'to the moon'
        ]
        
        urgency_words = [
            'now', 'today', 'hurry', 'quick', 'fast',
            'don\'t miss', 'last chance', 'final'
        ]
        
        total_messages = len(messages)
        pump_messages = 0
        urgency_messages = 0
        bullish_count = 0
        bearish_count = 0
        
        suspicious_users = []
        
        for msg in messages:
            body_lower = msg.get('body', '').lower()
            
            # Check pump keywords
            if any(keyword in body_lower for keyword in pump_keywords):
                pump_messages += 1
                
            # Check urgency
            if any(word in body_lower for word in urgency_words):
                urgency_messages += 1
                
            # Sentiment
            sentiment = msg.get('sentiment')
            if sentiment == 'Bullish':
                bullish_count += 1
            elif sentiment == 'Bearish':
                bearish_count += 1
                
            # Check suspicious users (low followers, new accounts)
            if msg.get('user_followers', 0) < 10:
                suspicious_users.append(msg.get('user'))
                
        pump_ratio = pump_messages / total_messages if total_messages > 0 else 0
        urgency_ratio = urgency_messages / total_messages if total_messages > 0 else 0
        
        sentiment_score = (bullish_count - bearish_count) / total_messages if total_messages > 0 else 0
        
        return {
            'total_messages': total_messages,
            'pump_messages': pump_messages,
            'pump_ratio': pump_ratio,
            'urgency_ratio': urgency_ratio,
            'sentiment_score': sentiment_score,
            'bullish_ratio': bullish_count / total_messages if total_messages > 0 else 0,
            'bearish_ratio': bearish_count / total_messages if total_messages > 0 else 0,
            'suspicious_users': len(set(suspicious_users)),
            'risk_indicators': {
                'high_pump_language': pump_ratio > 0.3,
                'urgency_tactics': urgency_ratio > 0.2,
                'extreme_bullish': sentiment_score > 0.7,
                'suspicious_accounts': len(set(suspicious_users)) > total_messages * 0.2
            }
        }
    
    def _scrape_symbol_page(self, symbol: str) -> List[Dict[str, Any]]:
        """Fallback web scraping when API fails"""
        try:
            url = f"https://stocktwits.com/symbol/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for message containers
            messages = []
            message_divs = soup.find_all('div', class_=re.compile(r'message.*')) or \
                          soup.find_all('article') or \
                          soup.find_all('div', attrs={'data-testid': re.compile(r'message.*')})
            
            for div in message_divs[:10]:  # Limit to 10 messages
                try:
                    text_elem = div.find('p') or div.find('span', class_='st-body')
                    if text_elem:
                        text = text_elem.get_text().strip()
                        if text:
                            messages.append({
                                'id': f"scraped_{len(messages)}",
                                'body': text[:200],
                                'created_at': datetime.now().isoformat(),
                                'user': 'unknown',
                                'user_followers': 0,
                                'likes': 0,
                                'sentiment': None,
                                'symbols': [symbol],
                                'source': 'stocktwits_scraped'
                            })
                except Exception:
                    continue
            
            self.logger.info(f"Scraped {len(messages)} messages for ${symbol}")
            return messages
            
        except Exception as e:
            self.logger.error(f"Web scraping failed for {symbol}: {e}")
            return []
    
    def _scrape_trending_page(self) -> List[Dict[str, Any]]:
        """Fallback trending scraper"""
        try:
            url = "https://stocktwits.com/rankings/trending"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            trending = []
            # Look for trending symbol links
            symbol_links = soup.find_all('a', href=re.compile(r'/symbol/[A-Z]+')) or \
                          soup.find_all('span', class_=re.compile(r'symbol.*'))
            
            for link in symbol_links[:10]:
                try:
                    if link.name == 'a':
                        symbol = link.get('href').split('/')[-1]
                        title = link.get_text().strip()
                    else:
                        symbol = link.get_text().strip().replace('$', '')
                        title = symbol
                    
                    if symbol and symbol.isalpha() and len(symbol) <= 5:
                        trending.append({
                            'symbol': symbol,
                            'title': title,
                            'watchlist_count': 0,
                            'trending_score': 100 - len(trending)  # Approximate score
                        })
                except Exception:
                    continue
            
            self.logger.info(f"Scraped {len(trending)} trending symbols")
            return trending
            
        except Exception as e:
            self.logger.error(f"Trending scraping failed: {e}")
            return []