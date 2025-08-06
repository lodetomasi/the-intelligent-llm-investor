"""
Configuration Management
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
TESTS_DIR = PROJECT_ROOT / "tests"

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model assignments for multi-agent system
MODEL_ASSIGNMENTS = {
    'SentimentAnalyst': 'mistralai/mixtral-8x22b-instruct',
    'PatternDetector': 'anthropic/claude-opus-4',
    'RiskAssessor': 'meta-llama/llama-3.3-70b-instruct',
    'CoordinationDetective': 'deepseek/deepseek-r1-0528',
    'MarketCorrelator': 'google/gemini-2.5-pro'
}

# Scraping configuration
REDDIT_SUBREDDITS = [
    'wallstreetbets', 'pennystocks', 'Shortsqueeze',
    'stocks', 'StockMarket', 'RobinHoodPennyStocks',
    'Superstonk', 'smallstreetbets', 'DeepFuckingValue',
    'SPACs', 'ValueInvesting', 'options',
    'CryptoCurrency', 'CryptoMoonShots', 'SatoshiStreetBets'
]

# Detection parameters
DEFAULT_HOURS_BACK = 6
DEFAULT_MIN_MENTIONS = 10
DEFAULT_TOP_CANDIDATES = 5

__all__ = [
    'PROJECT_ROOT', 'CONFIG_DIR', 'TESTS_DIR',
    'OPENROUTER_API_KEY', 'MODEL_ASSIGNMENTS',
    'REDDIT_SUBREDDITS', 'DEFAULT_HOURS_BACK',
    'DEFAULT_MIN_MENTIONS', 'DEFAULT_TOP_CANDIDATES'
]