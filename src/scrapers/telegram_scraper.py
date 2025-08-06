"""
Telegram Scraper using Telethon - Real data only
Based on unnohwn/telegram-scraper approach
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re
from ..utils.logger import get_logger

# Try to import telethon
try:
    from telethon import TelegramClient
    from telethon.tl.types import PeerChannel
    from telethon.errors import SessionPasswordNeededError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

class TelegramScraper:
    """Scrapes Telegram channels for pump & dump signals"""
    
    def __init__(self, api_id: Optional[int] = None, api_hash: Optional[str] = None):
        self.logger = get_logger("TelegramScraper")
        
        if not TELETHON_AVAILABLE:
            self.logger.warning("telethon not installed. Install with: pip install telethon")
            self.client = None
            return
            
        # You need to get these from https://my.telegram.org
        self.api_id = api_id
        self.api_hash = api_hash
        
        if not api_id or not api_hash:
            self.logger.warning("Telegram API credentials not provided. Get them from https://my.telegram.org")
            self.client = None
        else:
            self.client = TelegramClient('session', api_id, api_hash)
            
    def get_pump_signals(self) -> List[Dict[str, Any]]:
        """Placeholder for get_pump_signals - returns empty list"""
        self.logger.debug("get_pump_signals called but not implemented")
        return []
            
    async def connect(self, phone: Optional[str] = None):
        """Connect to Telegram"""
        if not self.client:
            return False
            
        try:
            await self.client.start(phone)
            self.logger.info("Connected to Telegram")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
            
    async def get_channel_messages(self, channel_name: str, limit: int = 100, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get messages from a Telegram channel
        
        Args:
            channel_name: Channel username or link
            limit: Number of messages to fetch
            hours_back: How many hours to look back
            
        Returns:
            List of messages
        """
        if not self.client:
            return []
            
        try:
            # Get channel entity
            channel = await self.client.get_entity(channel_name)
            
            # Calculate time limit
            time_limit = datetime.now() - timedelta(hours=hours_back)
            
            messages = []
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.date.replace(tzinfo=None) < time_limit:
                    break
                    
                # Extract message data
                msg_data = {
                    'id': message.id,
                    'text': message.text or '',
                    'date': message.date.isoformat(),
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                    'replies': message.replies.replies if message.replies else 0,
                    'channel': channel_name,
                    'source': 'telegram',
                    'has_media': bool(message.media),
                    'entities': []
                }
                
                # Extract entities (mentions, hashtags, etc)
                if message.entities:
                    for entity in message.entities:
                        if hasattr(entity, 'url'):
                            msg_data['entities'].append({
                                'type': 'url',
                                'value': entity.url
                            })
                            
                messages.append(msg_data)
                
            self.logger.info(f"Fetched {len(messages)} messages from {channel_name}")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error fetching channel messages: {e}")
            return []
            
    async def monitor_pump_channels(self, channels: List[str], hours_back: int = 6) -> Dict[str, Any]:
        """
        Monitor multiple pump & dump channels
        
        Args:
            channels: List of channel names to monitor
            hours_back: Hours to look back
            
        Returns:
            Analysis of pump signals
        """
        all_messages = []
        pump_alerts = []
        ticker_mentions = {}
        
        for channel in channels:
            messages = await self.get_channel_messages(channel, limit=50, hours_back=hours_back)
            all_messages.extend(messages)
            
            # Analyze messages for pump signals
            for msg in messages:
                text = msg['text'].lower()
                
                # Extract tickers
                tickers = self._extract_tickers(msg['text'])
                for ticker in tickers:
                    ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1
                
                # Check for pump keywords
                pump_keywords = [
                    'pump', 'moon', 'explode', '🚀', '🌙', 
                    'buy now', 'huge gains', '100x', '10x',
                    'next target', 'breakout', 'accumulate'
                ]
                
                if any(keyword in text for keyword in pump_keywords):
                    pump_alerts.append({
                        'channel': channel,
                        'text': msg['text'][:200],
                        'date': msg['date'],
                        'views': msg['views'],
                        'tickers': tickers
                    })
                    
        # Sort tickers by mention count
        top_tickers = sorted(ticker_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_messages': len(all_messages),
            'pump_alerts': pump_alerts,
            'channels_monitored': len(channels),
            'top_tickers': top_tickers,
            'high_activity_channels': self._identify_high_activity(all_messages, channels)
        }
        
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract crypto tickers from text"""
        tickers = set()
        
        # Match $TICKER format
        dollar_tickers = re.findall(r'\$([A-Z]{2,5})\b', text.upper())
        tickers.update(dollar_tickers)
        
        # Match common crypto mentions
        crypto_pattern = r'\b(BTC|ETH|BNB|ADA|SOL|DOT|DOGE|SHIB|MATIC|AVAX|LINK|UNI|ATOM|XRP|LTC)\b'
        crypto_tickers = re.findall(crypto_pattern, text.upper())
        tickers.update(crypto_tickers)
        
        return list(tickers)
        
    def _identify_high_activity(self, messages: List[Dict], channels: List[str]) -> List[Dict]:
        """Identify channels with suspicious activity spikes"""
        channel_activity = {}
        
        for msg in messages:
            channel = msg['channel']
            if channel not in channel_activity:
                channel_activity[channel] = {
                    'messages': 0,
                    'total_views': 0,
                    'recent_messages': []
                }
                
            channel_activity[channel]['messages'] += 1
            channel_activity[channel]['total_views'] += msg['views']
            
            # Track recent message timing
            msg_time = datetime.fromisoformat(msg['date'].replace('Z', '+00:00'))
            channel_activity[channel]['recent_messages'].append(msg_time)
            
        # Calculate activity metrics
        high_activity = []
        for channel, data in channel_activity.items():
            if data['messages'] > 10:  # High message volume
                # Check for burst patterns
                times = sorted(data['recent_messages'])
                if len(times) > 5:
                    # Calculate messages per hour
                    time_span = (times[-1] - times[0]).total_seconds() / 3600
                    if time_span > 0:
                        msgs_per_hour = data['messages'] / time_span
                        
                        if msgs_per_hour > 10:  # Suspicious rate
                            high_activity.append({
                                'channel': channel,
                                'messages_per_hour': msgs_per_hour,
                                'total_messages': data['messages'],
                                'avg_views': data['total_views'] / data['messages']
                            })
                            
        return sorted(high_activity, key=lambda x: x['messages_per_hour'], reverse=True)
        
    def run_monitor(self, channels: List[str], hours_back: int = 6) -> Dict[str, Any]:
        """Synchronous wrapper for monitoring"""
        if not TELETHON_AVAILABLE:
            return {'error': 'telethon not installed'}
            
        async def _run():
            if not self.client or not self.client.is_connected():
                await self.connect()
            return await self.monitor_pump_channels(channels, hours_back)
            
        return asyncio.run(_run())