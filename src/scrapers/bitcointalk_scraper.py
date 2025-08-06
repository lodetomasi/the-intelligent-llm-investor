"""
BitcoinTalk Forum Scraper - Major crypto discussion forum
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from datetime import datetime
import re
import time
from ..utils.logger import get_logger

class BitcoinTalkScraper:
    """Scrapes BitcoinTalk forums for crypto pump activity"""
    
    def __init__(self):
        self.logger = get_logger("BitcoinTalkScraper")
        self.base_url = "https://bitcointalk.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        
        # Key boards for pump activity
        self.pump_boards = {
            'altcoin_ann': 159,  # Altcoin Announcements
            'altcoin_discussion': 67,  # Altcoin Discussion
            'speculation': 57,  # Speculation
            'bounties': 238,  # Bounties (often pump related)
            'tokens': 240  # Tokens
        }
        
    def get_board_topics(self, board_id: int, pages: int = 2) -> List[Dict[str, Any]]:
        """Get topics from a specific board"""
        topics = []
        
        try:
            for page in range(0, pages * 40, 40):  # 40 topics per page
                url = f"{self.base_url}/index.php?board={board_id}.{page}"
                
                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find topic table - try multiple selectors
                topic_table = soup.find('table', {'class': 'bordercolor'}) or \
                             soup.find('div', {'id': 'messageindex'}) or \
                             soup.find('table', {'cellpadding': '4'}) or \
                             soup.find('form', {'name': 'quickModForm'})
                
                if not topic_table:
                    self.logger.debug(f"No topic table found on page {url}")
                    continue
                
                # Find all topic rows - different approaches
                if topic_table.name == 'div':
                    rows = topic_table.find_all('div', {'class': 'topic'})
                else:
                    rows = topic_table.find_all('tr')
                    
                # Find all topic rows
                for row in rows:
                    try:
                        # Skip non-topic rows - multiple checks
                        if row.name == 'div':
                            topic_link = row.find('a', href=re.compile(r'topic=\d+'))
                        else:
                            # Skip header rows and non-content rows
                            if row.find('th') or not row.find('td'):
                                continue
                            # Look for topic link
                            topic_link = row.find('a', href=re.compile(r'topic=\d+'))
                            
                        if not topic_link:
                            continue
                            
                        title = topic_link.get_text().strip()
                        href = topic_link['href']
                        topic_id = re.search(r'topic=(\d+)', href).group(1)
                        
                        # Get stats
                        stats_cells = row.find_all('td', {'class': 'windowbg'})
                        if len(stats_cells) >= 2:
                            replies = stats_cells[0].get_text().strip()
                            views = stats_cells[1].get_text().strip()
                        else:
                            replies = views = '0'
                            
                        # Check for pump indicators in title
                        pump_score = self._calculate_pump_score(title)
                        
                        topics.append({
                            'topic_id': topic_id,
                            'title': title,
                            'url': f"{self.base_url}/index.php?{href}",
                            'replies': int(replies.replace(',', '')) if replies.isdigit() else 0,
                            'views': int(views.replace(',', '')) if views.isdigit() else 0,
                            'board_id': board_id,
                            'pump_score': pump_score,
                            'source': 'BitcoinTalk'
                        })
                        
                    except Exception as e:
                        continue
                        
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            self.logger.error(f"Error scraping board {board_id}: {e}")
            
        return topics
        
    def get_topic_posts(self, topic_id: str, pages: int = 2) -> List[Dict[str, Any]]:
        """Get posts from a specific topic"""
        posts = []
        
        try:
            for page in range(0, pages * 20, 20):  # 20 posts per page
                url = f"{self.base_url}/index.php?topic={topic_id}.{page}"
                
                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all posts - try multiple selectors
                post_selectors = [
                    soup.find_all('div', {'class': 'post'}),
                    soup.find_all('div', {'class': 'windowbg'}),
                    soup.find_all('div', {'class': 'windowbg2'}),
                    soup.find_all('table', {'class': 'bordercolor'})
                ]
                
                post_divs = []
                for posts in post_selectors:
                    if posts:
                        post_divs = posts
                        break
                
                if not post_divs:
                    self.logger.debug(f"No posts found on topic {topic_id} page {page}")
                    continue
                
                for post_div in post_divs:
                    try:
                        # Get post content - try multiple selectors
                        content_selectors = [
                            post_div.find('div', {'class': 'inner'}),
                            post_div.find('div', {'class': 'post'}),
                            post_div.find('td', {'class': 'windowbg'}),
                            post_div.find('td', {'class': 'windowbg2'}),
                            post_div.find('div', attrs={'style': re.compile('padding')})
                        ]
                        
                        content = ""
                        for content_elem in content_selectors:
                            if content_elem:
                                text = content_elem.get_text().strip()
                                if text and len(text) > 10:
                                    content = text
                                    break
                        
                        if not content:
                            continue
                        
                        # Get author info - try multiple approaches
                        author = 'Unknown'
                        author_selectors = [
                            post_div.find('b'),
                            post_div.find('a', {'class': 'subject'}),
                            post_div.find_previous('td', {'class': 'poster_info'}),
                            post_div.find('span', {'class': 'poster_name'})
                        ]
                        
                        for author_elem in author_selectors:
                            if author_elem:
                                if author_elem.name == 'td':
                                    name_elem = author_elem.find('b')
                                    if name_elem:
                                        author = name_elem.get_text().strip()
                                        break
                                else:
                                    author_text = author_elem.get_text().strip()
                                    if author_text and len(author_text) < 50:
                                        author = author_text
                                        break
                            
                        # Calculate pump indicators
                        pump_score = self._calculate_pump_score(content)
                        
                        posts.append({
                            'topic_id': topic_id,
                            'content': content[:1000],  # Limit content size
                            'author': author,
                            'pump_score': pump_score,
                            'source': 'BitcoinTalk'
                        })
                        
                    except Exception as e:
                        continue
                        
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            self.logger.error(f"Error getting posts for topic {topic_id}: {e}")
            
        return posts
        
    def search_altcoin_announcements(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Search altcoin announcements for new potential pumps"""
        self.logger.info("Searching altcoin announcements...")
        
        # Get topics from altcoin announcements board
        topics = self.get_board_topics(self.pump_boards['altcoin_ann'], pages=3)
        
        # Filter for potential pumps
        pump_candidates = []
        
        for topic in topics[:limit]:
            if topic['pump_score'] > 2:  # High pump indicator score
                pump_candidates.append(topic)
            elif 'ANN' in topic['title'] and topic['replies'] < 50:  # New announcements
                pump_candidates.append(topic)
                
        return pump_candidates
        
    def _calculate_pump_score(self, text: str) -> int:
        """Calculate pump likelihood score based on keywords"""
        text_lower = text.lower()
        score = 0
        
        # Pump keywords
        pump_keywords = [
            'moon', 'rocket', '🚀', '💎', 'gem', 'x10', 'x100',
            'millionaire', 'lambo', 'early', 'don\'t miss',
            'huge potential', 'next bitcoin', 'explosive',
            'buy now', 'last chance', 'going parabolic'
        ]
        
        for keyword in pump_keywords:
            if keyword in text_lower:
                score += 1
                
        # Extra points for multiple rocket emojis
        score += text.count('🚀') - 1
        
        return score
        
    def get_trending_altcoins(self) -> List[Dict[str, Any]]:
        """Get trending altcoins based on activity"""
        trending = []
        
        # Check multiple boards
        for board_name, board_id in self.pump_boards.items():
            topics = self.get_board_topics(board_id, pages=1)
            
            # Find most active topics
            active_topics = sorted(topics, key=lambda x: x['replies'], reverse=True)[:5]
            
            for topic in active_topics:
                # Extract coin name/ticker from title
                ticker = self._extract_ticker(topic['title'])
                if ticker:
                    trending.append({
                        'ticker': ticker,
                        'title': topic['title'],
                        'activity': topic['replies'],
                        'board': board_name,
                        'url': topic['url'],
                        'pump_score': topic['pump_score']
                    })
                    
        return trending
        
    def _extract_ticker(self, title: str) -> str:
        """Extract ticker symbol from title"""
        # Look for patterns like [TICKER] or (TICKER)
        match = re.search(r'[\[\(]([A-Z]{2,10})[\]\)]', title)
        if match:
            return match.group(1)
            
        # Look for common patterns
        match = re.search(r'\$([A-Z]{2,10})\b', title)
        if match:
            return match.group(1)
            
        return ""