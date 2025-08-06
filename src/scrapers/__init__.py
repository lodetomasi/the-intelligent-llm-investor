"""
Scraper modules for various platforms - Real data only
"""

from .yars_scraper import YARSScraper
from .stocktwits_scraper import StockTwitsScraper
from .twitter_scraper import TwitterScraper
from .telegram_scraper import TelegramScraper
from .discord_scraper import DiscordScraper
from .fourchan_biz_scraper import FourChanBizScraper
from .investorshub_scraper import InvestorsHubScraper
from .bitcointalk_scraper import BitcoinTalkScraper
from .social_media_aggregator import SocialMediaAggregator

__all__ = [
    'YARSScraper',
    'StockTwitsScraper',
    'TwitterScraper',
    'TelegramScraper',
    'DiscordScraper',
    'FourChanBizScraper',
    'InvestorsHubScraper',
    'BitcoinTalkScraper',
    'SocialMediaAggregator'
]