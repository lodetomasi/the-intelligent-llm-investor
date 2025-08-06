"""
Multi-Agent System for Stock Sentiment Analysis
"""

from .sentiment_analyst import SentimentAnalyst
from .pattern_detector import PatternDetector
from .risk_assessor import RiskAssessor
from .coordination_detective import CoordinationDetective
from .market_correlator import MarketCorrelator

__all__ = [
    'SentimentAnalyst',
    'PatternDetector', 
    'RiskAssessor',
    'CoordinationDetective',
    'MarketCorrelator'
]