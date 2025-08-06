# Changelog

All notable changes to The Intelligent LLM Investor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-08-06

### 🚀 Complete Rewrite: Momentum-Based Detection

This release completely transforms the system from ticker-based to momentum-based pump detection.

#### Added
- **Momentum-Based Detection System** (`momentum_pump_finder.py`)
  - Finds pumps by detecting unusual activity patterns first
  - No ticker input required - discovers pumps organically
  - Analyzes engagement velocity across platforms
  - Groups events by themes (squeeze_play, pump_hype, earnings_play, etc.)
  
- **AI Asset Extraction** (`momentum_analyst.py`)
  - Automatically extracts company/crypto names from discussions
  - Identifies specific assets being pumped without ticker symbols
  - Provides mention counts and context
  - Enhanced prompts for better pattern recognition
  
- **Expanded Platform Coverage**
  - Increased from 8 to 36+ subreddits
  - Added high-risk subs: Shortsqueeze, SqueezeDD, BBIG, amcstock
  - Crypto-specific: CryptoMoonShots, SatoshiStreetBets, AltStreetBets
  - International: CanadianPennyStocks, ASX_Bets, EuropeanStocks
  - Sector-specific: weedstocks, shroomstocks, greeninvestor

- **Smart Configuration System**
  - Dynamic subreddit targeting by risk level
  - Configurable momentum thresholds
  - Smart detection modes with pattern analysis
  - Customizable search strategies

#### Changed
- **Core Architecture Overhaul**
  - Switched from ticker-monitoring to momentum-detection
  - AI analyzes themes and patterns, not individual stocks
  - Results show momentum clusters instead of ticker lists
  
- **Output Format Revolution**
  - Shows momentum themes with visual indicators
  - Platform activity heatmaps
  - AI-extracted asset names with mention counts
  - Risk assessment based on coordination patterns
  - No ticker display unless high-risk detected

- **Improved AI Analysis**
  - Better coordination detection (cross-platform patterns)
  - Enhanced red flag identification
  - Asset name extraction from context
  - Pump type classification (penny_stock, squeeze_play, crypto_pump)

#### Removed
- `automatic_pump_finder.py` (replaced by momentum-based system)
- `improve_data_collection.py` (obsolete utility)
- Old ticker-based detection logic
- Hardcoded ticker lists and watchlists
- Dead code from multi-agent system

#### Fixed
- AI JSON parsing errors with better error handling
- False positive ticker extraction (US, EPS, GAAP, etc.)
- 4chan scraper method name inconsistencies
- Import errors across modules
- Reddit rate limiting with better delays

## [1.0.0] - 2025-08-06

### 🎉 Initial Release

#### Added
- **Automatic Pump & Dump Detection** - No ticker input required, automatically finds trending stocks
- **Super Analyst AI** - Single powerful LLM agent replacing the previous 5-agent system
- **Multi-Platform Social Media Scraping**:
  - Reddit (via YARS - no API required)
  - StockTwits (with API fallback to web scraping)
  - 4chan /biz/
  - InvestorsHub
  - BitcoinTalk
  - Twitter/X (placeholder - requires twscrape)
  - Discord (placeholder - requires discord.py)
  - Telegram (placeholder - requires telethon)
- **Comprehensive Data Collection** - Parallel scraping from all sources
- **AI-Powered Analysis** with:
  - Pump probability scoring (0-100%)
  - Risk level assessment (LOW/MEDIUM/HIGH/EXTREME)
  - Timeline analysis (accumulation/pumping/dumping phases)
  - Social metrics (bot probability, coordination detection)
  - Evidence-based recommendations
- **Data Persistence** - Saves all scraped data and LLM responses
- **LLM-Optimized Formatting** - Uses tiktoken for efficient token usage
- **Configurable Settings** via config.yaml
- **Professional Documentation** with architecture diagrams

#### Security
- API keys managed via environment variables
- No hardcoded credentials
- Comprehensive .gitignore for sensitive data

#### Technical Stack
- Python 3.8+ support
- OpenRouter API integration for LLM access
- BeautifulSoup4 for web scraping
- Asyncio support for Discord/Telegram
- Comprehensive logging system

---

## Upgrade Guide

### From 1.x to 2.0

The system now uses momentum-based detection. Key changes:

1. **New Entry Point**
   ```bash
   # Old
   python automatic_pump_finder.py
   
   # New  
   python momentum_pump_finder.py
   ```

2. **Different Approach**
   - No ticker lists needed
   - Finds pumps from momentum patterns
   - Shows themes instead of tickers
   - AI extracts asset names

3. **New Parameters**
   ```bash
   python momentum_pump_finder.py --threshold 1.0 --hours 6 --analyze 3
   ```
   - `--threshold`: Momentum sensitivity (lower = more sensitive)
   - `--hours`: Time window for analysis
   - `--analyze`: Number of clusters for AI analysis

4. **Configuration Changes**
   - Extended subreddit lists in config.yaml
   - New smart detection modes
   - Momentum-based thresholds

---

*This project is for educational and research purposes only. Not financial advice.*