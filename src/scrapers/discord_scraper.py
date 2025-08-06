"""
Discord Scraper for pump & dump detection - Real data only
Based on justusip/crypto-pnd-bot approach
"""

import asyncio
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..utils.logger import get_logger

# Try to import discord.py
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

class DiscordScraper:
    """Monitors Discord servers for pump & dump signals"""
    
    def __init__(self, token: Optional[str] = None):
        self.logger = get_logger("DiscordScraper")
        
        if not DISCORD_AVAILABLE:
            self.logger.warning("discord.py not installed. Install with: pip install discord.py")
            self.bot = None
            return
            
        self.token = token
        if not token:
            self.logger.warning("Discord bot token not provided")
            self.bot = None
        else:
            # Set up bot with minimal intents
            intents = discord.Intents.default()
            intents.message_content = True
            intents.messages = True
            self.bot = commands.Bot(command_prefix='!', intents=intents)
            
        self.messages_cache = []
        self.pump_signals = []
        
        # Regex patterns for crypto detection
        self.ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?:\s|$)')
        self.contract_pattern = re.compile(r'0x[a-fA-F0-9]{40}')  # Ethereum addresses
        
    def monitor_servers(self, hours_back: int = 6) -> List[Dict[str, Any]]:
        """Placeholder for monitor_servers - returns empty list"""
        self.logger.debug("monitor_servers called but not implemented")
        return []
        
    async def monitor_channel(self, channel_id: int, hours_back: int = 6) -> List[Dict[str, Any]]:
        """
        Monitor a specific Discord channel
        
        Args:
            channel_id: Discord channel ID
            hours_back: Hours to look back
            
        Returns:
            List of messages with pump signals
        """
        if not self.bot:
            return []
            
        messages = []
        
        @self.bot.event
        async def on_ready():
            self.logger.info(f"Discord bot connected as {self.bot.user}")
            
            try:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    self.logger.error(f"Channel {channel_id} not found")
                    return
                    
                # Calculate time limit
                time_limit = datetime.now() - timedelta(hours=hours_back)
                
                # Fetch messages
                async for message in channel.history(limit=200, after=time_limit):
                    msg_data = self._process_message(message)
                    if msg_data:
                        messages.append(msg_data)
                        
                self.logger.info(f"Fetched {len(messages)} messages from channel")
                
            except Exception as e:
                self.logger.error(f"Error fetching messages: {e}")
            finally:
                await self.bot.close()
                
        try:
            await self.bot.start(self.token)
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
            
        return messages
        
    def _process_message(self, message) -> Optional[Dict[str, Any]]:
        """Process a Discord message for pump signals"""
        if message.author.bot:
            return None
            
        text = message.content
        
        # Extract tickers
        tickers = self._extract_tickers(text)
        contracts = self.contract_pattern.findall(text)
        
        # Check for pump indicators
        pump_score = self._calculate_pump_score(text)
        
        msg_data = {
            'id': str(message.id),
            'text': text[:500],  # Truncate long messages
            'author': str(message.author),
            'author_id': str(message.author.id),
            'channel': str(message.channel),
            'timestamp': message.created_at.isoformat(),
            'tickers': tickers,
            'contracts': contracts,
            'pump_score': pump_score,
            'reactions': len(message.reactions),
            'mentions': len(message.mentions),
            'source': 'discord'
        }
        
        # Flag high pump probability
        if pump_score > 0.7 or len(tickers) > 0:
            msg_data['is_pump_signal'] = True
            
        return msg_data
        
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract crypto tickers from text"""
        tickers = set()
        
        # Find $TICKER format
        matches = self.ticker_pattern.findall(text.upper())
        for match in matches:
            ticker = match[0] or match[1]
            if ticker and 2 <= len(ticker) <= 5:
                tickers.add(ticker)
                
        # Common crypto keywords
        crypto_keywords = [
            'BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE',
            'SHIB', 'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI'
        ]
        
        for keyword in crypto_keywords:
            if keyword in text.upper():
                tickers.add(keyword)
                
        return list(tickers)
        
    def _calculate_pump_score(self, text: str) -> float:
        """Calculate probability this is a pump message"""
        text_lower = text.lower()
        score = 0.0
        
        # Pump keywords (weighted)
        pump_indicators = {
            # High confidence indicators
            'pump': 0.3,
            'pumping': 0.3,
            'buy now': 0.25,
            'moon': 0.2,
            '🚀': 0.2,
            '🌙': 0.2,
            'explode': 0.2,
            'launching': 0.2,
            
            # Medium confidence
            'gem': 0.15,
            '100x': 0.15,
            '10x': 0.1,
            'gains': 0.1,
            'profit': 0.1,
            'breakout': 0.1,
            
            # Low confidence
            'dyor': 0.05,
            'nfa': 0.05,
            'potential': 0.05
        }
        
        for keyword, weight in pump_indicators.items():
            if keyword in text_lower:
                score += weight
                
        # Check for urgency
        urgency_words = ['now', 'quick', 'fast', 'hurry', 'asap', 'immediately']
        urgency_count = sum(1 for word in urgency_words if word in text_lower)
        score += urgency_count * 0.1
        
        # Contract address increases score
        if self.contract_pattern.search(text):
            score += 0.2
            
        # Multiple exclamation marks
        if text.count('!') > 2:
            score += 0.1
            
        # Cap at 1.0
        return min(score, 1.0)
        
    async def live_monitor(self, channel_ids: List[int], callback=None):
        """
        Live monitoring of channels
        
        Args:
            channel_ids: List of channel IDs to monitor
            callback: Function to call when pump detected
        """
        if not self.bot:
            return
            
        @self.bot.event
        async def on_ready():
            self.logger.info(f"Live monitoring started for {len(channel_ids)} channels")
            
        @self.bot.event
        async def on_message(message):
            if message.channel.id not in channel_ids:
                return
                
            msg_data = self._process_message(message)
            if msg_data and msg_data.get('is_pump_signal'):
                self.logger.warning(f"Pump signal detected: {msg_data['tickers']} - Score: {msg_data['pump_score']:.2f}")
                
                if callback:
                    await callback(msg_data)
                    
        try:
            await self.bot.start(self.token)
        except Exception as e:
            self.logger.error(f"Live monitoring failed: {e}")
            
    def run_monitor(self, channel_id: int, hours_back: int = 6) -> List[Dict[str, Any]]:
        """Synchronous wrapper for monitoring"""
        if not DISCORD_AVAILABLE:
            self.logger.error("discord.py not installed")
            return []
            
        return asyncio.run(self.monitor_channel(channel_id, hours_back))