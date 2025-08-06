"""
InvestorsHub Forum Scraper - Major penny stock discussion forum
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from datetime import datetime
import re
import time
from ..utils.logger import get_logger

class InvestorsHubScraper:
    """Scrapes InvestorsHub forums for pump & dump activity"""
    
    def __init__(self):
        self.logger = get_logger("InvestorsHubScraper")
        self.base_url = "https://investorshub.advfn.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_board_posts(self, ticker: str, pages: int = 3) -> List[Dict[str, Any]]:
        """Get posts from a stock's message board"""
        posts = []
        
        try:
            # Search for the board
            search_url = f"{self.base_url}/boards/board.aspx?board_id=0&search_term={ticker}"
            
            # Get board URL
            response = requests.get(search_url, headers=self.headers)
            if response.status_code != 200:
                return posts
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find board link
            board_link = None
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if f'/boards/read_msg.aspx?message_id=' in href:
                    board_link = href.split('?')[0].replace('read_msg.aspx', 'board.aspx')
                    break
                    
            if not board_link:
                # Try direct board URL
                board_url = f"{self.base_url}/boards/board.aspx?board_name={ticker}"
            else:
                board_url = f"{self.base_url}{board_link}"
                
            # Get posts from board
            for page in range(1, pages + 1):
                page_url = f"{board_url}?page={page}"
                
                response = requests.get(page_url, headers=self.headers)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find posts table - try multiple selectors
                posts_table = soup.find('table', {'id': 'ctl00_CP1_gv'}) or \
                             soup.find('table', {'class': 'messageboard'}) or \
                             soup.find('div', {'class': 'posts-list'}) or \
                             soup.find('table', attrs={'cellpadding': '2'})
                
                if not posts_table:
                    self.logger.debug(f"No posts table found on page {page_url}")
                    continue
                    
                rows = posts_table.find_all('tr')
                if len(rows) <= 1:  # Skip if only header or no rows
                    continue
                
                rows = rows[1:]  # Skip header
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 4:
                            continue
                            
                        # Extract post data
                        post_num = cells[0].get_text().strip()
                        subject = cells[1].get_text().strip()
                        author = cells[2].get_text().strip()
                        date_str = cells[3].get_text().strip()
                        
                        # Get post content
                        post_link = cells[1].find('a')
                        if post_link:
                            post_url = f"{self.base_url}{post_link['href']}"
                            content = self._get_post_content(post_url)
                        else:
                            content = subject
                            
                        posts.append({
                            'ticker': ticker,
                            'post_number': post_num,
                            'subject': subject,
                            'content': content,
                            'author': author,
                            'date': date_str,
                            'url': post_url if post_link else page_url,
                            'source': 'InvestorsHub'
                        })
                        
                    except Exception as e:
                        self.logger.debug(f"Error parsing post: {e}")
                        continue
                        
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            self.logger.error(f"Error scraping InvestorsHub for {ticker}: {e}")
            
        return posts
        
    def _get_post_content(self, url: str) -> str:
        """Get full post content"""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return ""
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find post content - try multiple selectors
            content_selectors = [
                {'div': {'class': 'KonaBody'}},
                {'td': {'class': 'msgtext'}},
                {'div': {'class': 'message-content'}},
                {'div': {'class': 'post-content'}},
                {'div': {'id': 'postcontent'}},
                {'td': {'class': 'alt1'}}
            ]
            
            for selector in content_selectors:
                for tag, attrs in selector.items():
                    content_elem = soup.find(tag, attrs)
                    if content_elem:
                        text = content_elem.get_text().strip()
                        if text and len(text) > 10:  # Valid content
                            return text
                
        except Exception as e:
            self.logger.debug(f"Error getting post content: {e}")
            
        return ""
        
    def get_hot_boards(self) -> List[Dict[str, Any]]:
        """Get most active boards (potential pumps)"""
        hot_boards = []
        
        try:
            url = f"{self.base_url}/boards/hot_boards.aspx"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return hot_boards
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find hot boards table - try multiple selectors
            table = soup.find('table', {'class': 'hottable'}) or \
                   soup.find('table', {'class': 'hot-boards'}) or \
                   soup.find('div', {'class': 'hot-boards-list'}) or \
                   soup.find('table', attrs={'border': '0'})
            
            if not table:
                self.logger.debug("No hot boards table found")
                return hot_boards
                
            rows = table.find_all('tr')
            if len(rows) <= 1:
                return hot_boards
            rows = rows[1:]  # Skip header
            
            for row in rows[:20]:  # Top 20
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                        
                    ticker_link = cells[0].find('a')
                    if not ticker_link:
                        continue
                        
                    ticker = ticker_link.get_text().strip()
                    posts_today = cells[1].get_text().strip()
                    
                    hot_boards.append({
                        'ticker': ticker,
                        'posts_today': int(posts_today.replace(',', '')),
                        'rank': len(hot_boards) + 1,
                        'source': 'InvestorsHub'
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error getting hot boards: {e}")
            
        return hot_boards
        
    def search_pump_keywords(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search for pump-related keywords across forums"""
        if keywords is None:
            keywords = [
                'moon', 'squeeze', 'rocket', 'explosion',
                'buyout', 'merger', 'breakout', 'alert'
            ]
            
        results = []
        
        for keyword in keywords:
            try:
                search_url = f"{self.base_url}/boards/search.aspx?searchstr={keyword}"
                response = requests.get(search_url, headers=self.headers)
                
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse search results
                search_results = soup.find_all('div', {'class': 'search-result'}) or \
                               soup.find_all('tr', {'class': 'windowbg'}) or \
                               soup.find_all('a', href=re.compile(r'read_msg\.aspx'))
                
                for result in search_results[:10]:  # Limit results
                    try:
                        if result.name == 'a':
                            title = result.get_text().strip()
                            url = f"{self.base_url}{result['href']}"
                        else:
                            link = result.find('a')
                            if link:
                                title = link.get_text().strip()
                                url = f"{self.base_url}{link['href']}"
                            else:
                                continue
                                
                        if title and url:
                            results.append({
                                'keyword': keyword,
                                'title': title,
                                'url': url,
                                'source': 'InvestorsHub'
                            })
                    except Exception:
                        continue
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error searching for {keyword}: {e}")
                
        return results