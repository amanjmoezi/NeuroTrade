# 🤖 ICT Trading Telegram Bot

An advanced cryptocurrency trading bot powered by **ICT (Inner Circle Trader)** concepts and AI analysis. This bot provides real-time market analysis, trading signals, price alerts, and beautiful visualizations directly in Telegram.

## ✨ Features

### 📊 Core Features
- **🧠 Smart Coin Analysis** - AI-powered automatic selection of best trading opportunities
- **Real-time ICT Analysis** - Market Structure Shifts (MSS), Fair Value Gaps (FVG), Order Blocks
- **Smart Money Concepts** - Liquidity zones (SSL/BSL), institutional data
- **AI-Powered Signals** - Entry/exit levels with risk-reward ratios
- **Multi-Timeframe Analysis** - 15m, 1h, 4h, 1d timeframes
- **Beautiful Charts** - Price charts with indicators and zones
- **Price Alerts** - Get notified when price reaches your targets
- **User Settings** - Customizable preferences per user (exchange, timeframe, leverage, risk, etc.)
- **Multi-Exchange Support** - Toobit, LBank, Binance with per-user selection
- **MongoDB Integration** - Persistent user settings and data storage

### 🧠 Smart Analysis Features (Advanced)
- **Multi-Criteria Scoring** - Trend quality, volume profile, volatility health, momentum, market structure, liquidity
- **Range Detection** - Automatically filters out coins stuck in range/consolidation
- **Volume Health Check** - Ensures sufficient liquidity and consistent volume
- **Volatility Analysis** - Filters extreme volatility and identifies healthy price action
- **Trend Quality Assessment** - Evaluates trend strength, consistency, and RSI levels
- **Market Structure Analysis** - Detects Higher Highs/Lower Lows patterns
- **Real-time Progress Updates** - Live transparent reporting during analysis
- **Rejection Reporting** - Shows which coins were filtered out and why
- **Automatic Coin Selection** - Analyzes multiple coins and picks the best opportunity

### 🎯 Trading Features
- Market structure detection (Bullish/Bearish MSS)
- Fair Value Gap identification
- Order Block detection
- Liquidity zone mapping
- Volume analysis with CVD
- RSI, MACD, EMA indicators
- Funding rates and Open Interest

### 🔔 Alert System
- Set price alerts for any symbol
- Automatic notifications when triggered
- Multiple alerts per user
- Above/below condition support

### 📈 Supported Symbols
BTC, ETH, BNB, ADA, XRP, DOT, LINK, LTC, BCH, XLM, DOGE, SOL, MATIC, UNI, AVAX and more!

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Telegram account
- OpenAI API key (or compatible API)
- Telegram Bot Token

### Installation

1. **Clone the repository**
```bash
cd /home/amanj/Desktop/tarder
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create or edit `.env` file:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ADMIN_IDS=your_telegram_user_id
```

### Getting Your Credentials

#### 1. Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token provided
5. Add it to `.env` as `TELEGRAM_BOT_TOKEN`

#### 2. Your Telegram User ID
1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start the bot
3. It will send you your user ID
4. Add it to `.env` as `TELEGRAM_ADMIN_IDS`

#### 3. OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add it to `.env` as `OPENAI_API_KEY`

## 🎮 Usage

### Run the Telegram Bot (Default)
```bash
python main.py
```

The bot will start and you'll see:
```
🤖 ICT Trading Bot Started!
================================================================================
✅ Bot is running... Press Ctrl+C to stop
================================================================================
```

### Run CLI Analysis Mode
```bash
python main.py --cli --symbol BTCUSDT
```

### Using the Bot in Telegram

1. **Start the bot** - Search for your bot username in Telegram and click Start
2. **Quick Analysis** - Use `/quick` for instant BTC & ETH analysis
3. **Analyze Symbol** - Use `/analyze BTC` or just type `BTC`
4. **Set Alerts** - Use `/setalert BTC 50000` to get notified
5. **View Settings** - Use `/settings` to customize preferences

## 📱 Bot Commands

### Analysis Commands
- `/start` - Welcome message and bot introduction
- `/help` - Complete command guide
- `/smartanalyze` - 🧠 **NEW!** Smart analysis - automatically finds best coin
- `/smartanalyze 3` - Analyze and show top 3 coins
- `/smartanalyze 5 BTC ETH SOL` - Analyze specific coins
- `/analyze [SYMBOL]` - Full ICT analysis with chart
- `/quick` - Quick analysis of BTC & ETH
- `/status` - System status and statistics

### Alert Commands
- `/alerts` - View all your active alerts
- `/setalert [SYMBOL] [PRICE]` - Set a price alert
  - Example: `/setalert BTC 50000`

### Settings Commands
- `/settings` - View and manage your preferences
  - Select exchange (Toobit, LBank, Binance)
  - Set default timeframe (15m, 1h, 4h, 1d)
  - Configure leverage (5x, 10x, 20x, 50x, 100x)
  - Set risk per trade (1%, 2%, 3%, 5%, 10%)
  - Toggle notifications on/off
  - Change language (فارسی/English)
  - Manage favorite symbols
- `/exchange` - Quick exchange selection
- `/positions` - View open positions from your selected exchange
  - Example: `/positions` (uses your selected exchange)
  - Example: `/positions toobit` (specific exchange)

### Quick Buttons
Use the keyboard buttons for easy access:
- 📊 Quick Analysis
- 🔍 Analyze Symbol
- ⚡ My Alerts
- ⚙️ Settings

## 🏗️ Architecture

### Project Structure
```
tarder/
├── main.py              # Main entry point & trading system
├── bot.py               # Telegram bot implementation
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── README.md           # This file
├── data/               # Data storage
│   ├── output/         # Analysis results
│   └── bot_state.json  # Bot state & alerts
└── init/
    └── systemPrompt.txt # AI system prompt
```

### Key Components

#### `main.py` - Trading System
- **Config** - System configuration
- **BinanceDataProvider** - Fetches market data from Binance
- **TechnicalAnalyzer** - Calculates indicators (RSI, MACD, EMA, ATR)
- **ICTAnalyzer** - Detects ICT structures (MSS, FVG, Order Blocks, Liquidity)
- **MarketDataAggregator** - Aggregates all market data
- **AITradingAdvisor** - Gets AI-powered trading signals
- **TradingSystem** - Main orchestrator

#### `bot.py` - Telegram Bot
- **TradingBot** - Main bot class
- **BotStateManager** - Manages user settings and alerts
- **ChartGenerator** - Creates beautiful price charts
- **Command Handlers** - Handles all bot commands
- **Alert System** - Background task for price monitoring

## 🎨 Features Showcase

### 1. Real-time Analysis
Get comprehensive ICT analysis with:
- Current price and trend direction
- Trading signal (BUY/SELL/WAIT)
- Confidence level
- Entry, targets, and stop loss
- Market structure insights
- Technical indicators

### 2. Beautiful Charts
Automatically generated charts showing:
- Price action with candlesticks
- Fair Value Gaps (green/red zones)
- Entry and target levels
- Stop loss levels
- Volume bars

### 3. Price Alerts
Set unlimited price alerts:
- Above or below conditions
- Automatic detection
- Instant Telegram notifications
- Auto-removal after trigger

### 4. User Settings
Customize your experience:
- Toggle notifications
- Manage favorite symbols
- Personalized preferences

## 🔧 Configuration

### Trading Settings
Edit `main.py` Config class:
```python
self.default_symbol = "BTCUSDT"
self.timeframes = ["15m", "1h", "4h", "1d"]
self.ai_model = "deepseek/deepseek-chat-v3.1"
self.temperature = 0.15
```

### Bot Settings
Edit `bot.py` for customization:
- Alert check interval (default: 60 seconds)
- Chart settings (colors, size, DPI)
- Default user preferences

## 🐛 Troubleshooting

### Bot doesn't start
- Check if `TELEGRAM_BOT_TOKEN` is set in `.env`
- Verify the token is valid
- Ensure all dependencies are installed

### Analysis fails
- Check if `OPENAI_API_KEY` is set correctly
- Verify internet connection
- Check if Binance API is accessible

### Charts not generating
- Ensure matplotlib is installed
- Check if `data/` directory exists
- Verify sufficient disk space

### Alerts not working
- Check if bot has been running continuously
- Verify alert was set correctly with `/alerts`
- Check bot logs for errors

## 📊 Example Usage

### Analyze Bitcoin
```
You: /analyze BTC
Bot: 🔄 Analyzing BTCUSDT...
     [Sends chart with analysis]
     
     🟢 BTCUSDT - ICT Analysis
     💰 Price: $46,500.00
     📊 Trend: BULLISH (HTF) | BULLISH (LTF)
     
     🎯 Signal: BUY
     📈 Confidence: 75%
     ⚡ Bias: BULLISH
     
     Entry: $46,200.00
     Targets: $47,500.00 | $48,800.00 | $50,000.00
     Stop Loss: $45,000.00
     R:R: 1:2.5
```

### Set Price Alert
```
You: /setalert ETH 3000
Bot: ✅ Alert set!
     
     Symbol: ETHUSDT
     Target: $3,000.00
     Current: $2,850.00
     Condition: above
     
     I'll notify you! 🔔
```

## 🚀 Advanced Features

### Background Tasks
- **Alert Monitoring** - Checks prices every 60 seconds
- **Auto-cleanup** - Removes triggered alerts
- **State Persistence** - Saves user data automatically

### Modular Design
- Easy to extend with new commands
- Pluggable analyzers
- Customizable chart styles
- Flexible alert conditions

## 📝 Development

### Adding New Commands
```python
async def my_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello!")

# Register in run() method
self.app.add_handler(CommandHandler("mycommand", self.my_command))
```

### Adding New Indicators
Edit `TechnicalAnalyzer` class in `main.py`:
```python
@staticmethod
def calculate_my_indicator(df: pd.DataFrame) -> pd.Series:
    # Your calculation here
    return result
```

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

This project is for educational purposes. Use at your own risk.

## ⚠️ Disclaimer

**IMPORTANT**: This bot is for educational and informational purposes only. It is NOT financial advice. 

- Cryptocurrency trading carries significant risk
- Past performance does not guarantee future results
- Always do your own research (DYOR)
- Never invest more than you can afford to lose
- The developers are not responsible for any trading losses

## 🎓 Learning Resources

### ICT Concepts
- Market Structure Shifts (MSS)
- Fair Value Gaps (FVG)
- Order Blocks (OB)
- Liquidity Zones (SSL/BSL)
- Smart Money Concepts

### Technical Analysis
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
- ATR (Average True Range)

## 💡 Tips

1. **Start with /quick** - Get familiar with the analysis format
2. **Set realistic alerts** - Don't set too many at once
3. **Check /status** - Verify system is running properly
4. **Use favorites** - Add your most-traded symbols
5. **Enable notifications** - Never miss important alerts

## 🌟 Support

If you find this bot helpful:
- ⭐ Star the repository
- 🐛 Report bugs
- 💡 Suggest features
- 📖 Improve documentation

## 📞 Contact

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Happy Trading! 🚀📈**

*Remember: Trade responsibly and always manage your risk!*
