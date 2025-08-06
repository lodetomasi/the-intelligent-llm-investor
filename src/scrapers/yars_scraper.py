"""
YARS-based Reddit Scraper - Works without API keys
Based on: https://github.com/datavorous/yars
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

class YARSScraper:
    """Reddit scraper using YARS approach - no API needed"""
    
    def __init__(self):
        self.logger = get_logger("YARSScraper")
        self.session = requests.Session()
        
        # Headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(self.headers)
        
    def search_reddit(self, query: str, limit: int = 25) -> List[Dict]:
        """
        Search Reddit for posts containing query
        
        Args:
            query: Search query (e.g., stock ticker)
            limit: Maximum number of results
            
        Returns:
            List of post data
        """
        posts = []
        
        # Reddit's JSON endpoint for search
        url = f"https://www.reddit.com/search.json"
        params = {
            'q': query,
            'limit': limit,
            'sort': 'relevance',
            't': 'day'  # Last 24 hours
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract posts from response
            for item in data.get('data', {}).get('children', []):
                post_data = item.get('data', {})
                
                posts.append({
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data.get('author', '[deleted]'),
                    'subreddit': post_data.get('subreddit'),
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                    'url': post_data.get('url', ''),
                    'is_self': post_data.get('is_self', True)
                })
                
            self.logger.info(f"Found {len(posts)} posts for query: {query}")
            
        except Exception as e:
            self.logger.error(f"Error searching Reddit: {e}")
            
        return posts
        
    def fetch_subreddit_posts(self, subreddit: str, 
                            category: str = 'hot',
                            time_filter: str = 'day',
                            limit: int = 25) -> List[Dict]:
        """
        Fetch posts from a subreddit
        
        Args:
            subreddit: Name of subreddit
            category: hot, new, top, rising
            time_filter: hour, day, week, month, year, all
            limit: Maximum posts to fetch
            
        Returns:
            List of posts
        """
        posts = []
        
        # Build URL based on category
        if category == 'top':
            url = f"https://www.reddit.com/r/{subreddit}/top.json"
            params = {'t': time_filter, 'limit': limit}
        else:
            url = f"https://www.reddit.com/r/{subreddit}/{category}.json"
            params = {'limit': limit}
            
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract posts
            for item in data.get('data', {}).get('children', []):
                post_data = item.get('data', {})
                
                posts.append({
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data.get('author', '[deleted]'),
                    'subreddit': subreddit,
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                    'url': post_data.get('url', ''),
                    'is_self': post_data.get('is_self', True),
                    'link_flair_text': post_data.get('link_flair_text', ''),
                    'total_awards_received': post_data.get('total_awards_received', 0)
                })
                
            self.logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            
        except Exception as e:
            self.logger.error(f"Error fetching from r/{subreddit}: {e}")
            
        return posts
        
    def scrape_post_comments(self, permalink: str, limit: int = 50) -> List[Dict]:
        """
        Scrape comments from a post
        
        Args:
            permalink: Post permalink
            limit: Maximum comments to fetch
            
        Returns:
            List of comments
        """
        comments = []
        
        # Clean permalink
        if permalink.startswith('https://reddit.com'):
            permalink = permalink.replace('https://reddit.com', '')
        elif permalink.startswith('https://www.reddit.com'):
            permalink = permalink.replace('https://www.reddit.com', '')
            
        # Add .json to get JSON response
        url = f"https://www.reddit.com{permalink}.json"
        params = {'limit': limit}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Comments are in the second element
            if len(data) > 1:
                comment_data = data[1].get('data', {}).get('children', [])
                
                for item in comment_data:
                    if item.get('kind') == 't1':  # t1 = comment
                        comment = item.get('data', {})
                        
                        comments.append({
                            'id': comment.get('id'),
                            'body': comment.get('body', ''),
                            'author': comment.get('author', '[deleted]'),
                            'score': comment.get('score', 0),
                            'created_utc': comment.get('created_utc', 0),
                            'edited': comment.get('edited', False),
                            'parent_id': comment.get('parent_id', ''),
                            'permalink': f"https://reddit.com{comment.get('permalink', '')}"
                        })
                        
            self.logger.info(f"Scraped {len(comments)} comments from post")
            
        except Exception as e:
            self.logger.error(f"Error scraping comments: {e}")
            
        return comments
        
    def search_subreddit(self, subreddit: str, query: str, 
                        time_filter: str = 'day',
                        limit: int = 25) -> List[Dict]:
        """
        Search within a specific subreddit
        
        Args:
            subreddit: Subreddit name
            query: Search query
            time_filter: Time range
            limit: Maximum results
            
        Returns:
            List of posts
        """
        posts = []
        
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            'q': query,
            'restrict_sr': 'on',  # Restrict to this subreddit
            'sort': 'relevance',
            't': time_filter,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract posts
            for item in data.get('data', {}).get('children', []):
                post_data = item.get('data', {})
                
                posts.append({
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data.get('author', '[deleted]'),
                    'subreddit': subreddit,
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                    'url': post_data.get('url', ''),
                    'is_self': post_data.get('is_self', True)
                })
                
            self.logger.info(f"Found {len(posts)} posts in r/{subreddit} for: {query}")
            
        except Exception as e:
            self.logger.error(f"Error searching r/{subreddit}: {e}")
            
        return posts
        
    def get_user_posts(self, username: str, limit: int = 25) -> List[Dict]:
        """
        Get recent posts by a user
        
        Args:
            username: Reddit username
            limit: Maximum posts
            
        Returns:
            List of user's posts
        """
        posts = []
        
        url = f"https://www.reddit.com/user/{username}/submitted.json"
        params = {'limit': limit}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('data', {}).get('children', []):
                post_data = item.get('data', {})
                
                posts.append({
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'author': username,
                    'subreddit': post_data.get('subreddit'),
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'permalink': f"https://reddit.com{post_data.get('permalink', '')}"
                })
                
            self.logger.info(f"Fetched {len(posts)} posts from user: {username}")
            
        except Exception as e:
            self.logger.error(f"Error fetching user posts: {e}")
            
        return posts