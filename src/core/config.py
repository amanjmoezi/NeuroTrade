"""
System Configuration Management
"""
import os
from dotenv import load_dotenv


class Config:
    """System Configuration Management"""
    
    def __init__(self):
        load_dotenv()
        
        # API Keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        
        # MongoDB Configuration
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "trading_bot")
        
        # Binance APIs (for market data)
        self.binance_api = "https://api.binance.com"
        self.binance_futures_api = "https://fapi.binance.com"
        self.binance_ws = "wss://stream.binance.com:9443/ws"
        
        # AI Settings
        self.ai_model = "deepseek/deepseek-chat-v3.1"
        self.temperature = 0.15
        self.top_p = 0.9
        self.ai_timeout = 120  # AI API timeout in seconds
        
        # Network Settings
        self.http_timeout = 30  # HTTP request timeout in seconds
        
        # Trading Settings
        self.default_symbol = "BTCUSDT"
        self.available_symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
            "DOTUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "XLMUSDT",
            "DOGEUSDT", "SOLUSDT", "MATICUSDT", "UNIUSDT", "AVAXUSDT"
        ]
        self.timeframes = ["15m", "1h", "4h", "1d"]
        self.winrate = 0
        
        # Portfolio State (simplified - can be extended with database)
        self.portfolio_state = {
            "open_positions": 0,
            "total_risk_exposure": 0.0,
            "winning_streak": 0,
            "recent_drawdown": 0.0
        }
