"""
Trading System - Main orchestrator
"""
import os
import re
import json
from datetime import datetime, timezone
from typing import Dict, List
from src.core.config import Config
from src.data.providers import BinanceDataProvider
from src.data.aggregator import MarketDataAggregator
from src.ai.advisor import AITradingAdvisor
from src.ai.smart_selector import SmartCoinSelector


class TradingSystem:
    """Main Trading System"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize Binance provider
        self.provider = BinanceDataProvider(config)
        self.aggregator = MarketDataAggregator(self.provider, config)
        self.ai = AITradingAdvisor(config)
        self.smart_selector = SmartCoinSelector(config, self.provider)
    
    async def analyze(self, symbol: str = None) -> Dict:
        """Analyze and Get ICT Signal"""
        symbol = symbol or self.config.default_symbol
        print(f"🔍 Starting ICT analysis for {symbol}")
        
        try:
            market_data = await self.aggregator.aggregate_ict_data(symbol)
            
            # Save market data
            self._save_data(market_data, symbol, "market")
            
            # Get AI signal
            signal = await self.ai.get_signal(market_data)
            
            # Save signal
            self._save_data(signal, symbol, "signal")
            
            result = {
                "market_data": market_data,
                "signal": signal,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            print("✅ Analysis complete")
            return result
            
        except Exception as e:
            print(f"🔴 Analysis error: {e}")
            raise
    
    def _save_data(self, data: Dict, symbol: str, data_type: str):
        """Save Data to File"""
        os.makedirs("data/output", exist_ok=True)
        
        # Find existing files with the same pattern
        pattern = rf"^\d+_{data_type}_{symbol}\.json$"
        existing = [f for f in os.listdir("data/output") if re.match(pattern, f)]
        
        # Extract numbers and find the highest
        if existing:
            numbers = [int(re.match(r"^(\d+)_", f).group(1)) for f in existing]
            num = max(numbers) + 1
        else:
            num = 1
        
        filename = f"data/output/{num:02d}_{data_type}_{symbol}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved to {filename}")
    
    async def smart_analyze(self, top_n: int = 5, custom_symbols: List[str] = None) -> Dict:
        """
        تحلیل هوشمند و انتخاب بهترین ارزها
        
        Args:
            top_n: تعداد ارزهای برتر برای انتخاب
            custom_symbols: لیست سفارشی ارزها (اختیاری)
        
        Returns:
            دیکشنری شامل بهترین ارزها، لاگ تحلیل و سیگنال ترید
        """
        print("🧠 Starting Smart Coin Analysis...")
        
        try:
            # پیدا کردن بهترین ارزها
            top_coins = await self.smart_selector.find_best_coins(top_n, custom_symbols)
            
            if not top_coins:
                raise Exception("No valid coins found in analysis")
            
            # انتخاب بهترین ارز
            best_coin = top_coins[0]
            best_symbol = best_coin['symbol']
            
            print(f"🏆 Best coin selected: {best_symbol} (Score: {best_coin['final_score']:.2%})")
            
            # تحلیل کامل ICT برای بهترین ارز
            market_data = await self.aggregator.aggregate_ict_data(best_symbol)
            
            # دریافت سیگنال AI
            signal = await self.ai.get_signal(market_data)
            
            # ترکیب نتایج
            result = {
                "smart_analysis": {
                    "top_coins": top_coins,
                    "selected_coin": best_coin,
                    "analysis_log": self.smart_selector.get_analysis_log(),
                    "report": self.smart_selector.format_analysis_report(top_coins)
                },
                "market_data": market_data,
                "signal": signal,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # ذخیره نتایج
            self._save_data(result, best_symbol, "smart_analysis")
            
            print("✅ Smart analysis complete!")
            return result
            
        except Exception as e:
            print(f"🔴 Smart analysis error: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.provider.close()
        await self.smart_selector.close()
