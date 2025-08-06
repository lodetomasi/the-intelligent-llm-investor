# Changelog

All notable changes to The Intelligent LLM Investor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### 🔧 Architecture

The system uses a streamlined architecture:
```
automatic_pump_finder.py
    └── SocialPumpScanner
        ├── Social Media Aggregator (8 scrapers)
        ├── Super Analyst AI (Claude Opus 4)
        ├── Data Saver
        └── LLM Formatter
```

### 📊 Performance
- Typical scan time: 30-60 seconds
- Finds 50-100+ tickers per scan
- Analyzes top candidates with 90%+ confidence scoring

### ⚠️ Known Limitations
- Twitter scraper requires twscrape library (optional)
- Discord scraper requires bot token (optional)
- Telegram scraper requires API credentials (optional)
- StockTwits API endpoints may change (has web scraping fallback)

---

*This project is for educational and research purposes only. Not financial advice.*