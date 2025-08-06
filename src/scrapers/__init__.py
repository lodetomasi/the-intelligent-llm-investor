"""
Scraper modules for various platforms - Real data only
"""

from .yars_scraper import YARSScraper
from .multi_source_scraper import MultiSourceScraper

# Financial data scrapers
try:
    from .yahoo_finance_scraper import YahooFinanceScraper
except ImportError:
    YahooFinanceScraper = None
    
try:
    from .finviz_scraper import FinvizScraper
except ImportError:
    FinvizScraper = None
    
try:
    from .marketwatch_scraper import MarketWatchScraper
except ImportError:
    MarketWatchScraper = None
    
try:
    from .seeking_alpha_scraper import SeekingAlphaScraper
except ImportError:
    SeekingAlphaScraper = None
    
try:
    from .crypto_scraper import CryptoScraper
except ImportError:
    CryptoScraper = None

# Social media scrapers
try:
    from .stocktwits_scraper import StockTwitsScraper
except ImportError:
    StockTwitsScraper = None
    
try:
    from .twitter_scraper import TwitterScraper
except ImportError:
    TwitterScraper = None
    
try:
    from .telegram_scraper import TelegramScraper
except ImportError:
    TelegramScraper = None
    
try:
    from .discord_scraper import DiscordScraper
except ImportError:
    DiscordScraper = None

# Unified aggregator
try:
    from .unified_data_aggregator import UnifiedDataAggregator
except ImportError:
    UnifiedDataAggregator = None

__all__ = [
    'YARSScraper',
    'MultiSourceScraper',
    'YahooFinanceScraper',
    'FinvizScraper',
    'MarketWatchScraper',
    'SeekingAlphaScraper',
    'CryptoScraper',
    'StockTwitsScraper',
    'TwitterScraper',
    'TelegramScraper',
    'DiscordScraper',
    'UnifiedDataAggregator'
]