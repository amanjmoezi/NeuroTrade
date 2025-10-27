"""
Market Data Aggregator - Combines all data sources
"""
import asyncio
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List
from src.core.config import Config
from src.data.providers import BinanceDataProvider
from src.analysis.technical import TechnicalAnalyzer
from src.analysis.ict import ICTAnalyzer
from src.analysis.regime import RegimeDetector


class MarketDataAggregator:
    """Market Data Collection - ICT Format"""
    
    def __init__(self, provider: BinanceDataProvider, config: Config):
        self.provider = provider
        self.config = config
        self.tech = TechnicalAnalyzer()
        self.ict = ICTAnalyzer()
        self.regime = RegimeDetector()
    
    async def aggregate_ict_data(self, symbol: str) -> Dict:
        """Collect All Data in ICT Format with comprehensive error handling"""
        print(f"🔹 Fetching ICT-compatible data for {symbol}")
        
        try:
            # Fetch all timeframes with error handling
            limits = {"15m": 500, "1h": 500, "4h": 500, "1d": 500}
            tasks = [self.provider.fetch_ohlcv(symbol, tf, limits[tf]) for tf in self.config.timeframes]
            
            try:
                dfs_list = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions in results
                errors = []
                for i, result in enumerate(dfs_list):
                    if isinstance(result, Exception):
                        tf = self.config.timeframes[i]
                        error_detail = f"{tf}: {type(result).__name__} - {str(result)}"
                        errors.append(error_detail)
                        print(f"🔴 Error fetching {tf}: {error_detail}")
                
                if errors:
                    error_msg = f"خطا در دریافت داده‌های قیمت: {'; '.join(errors)}"
                    print(f"🔴 {error_msg}")
                    return {
                        "error": error_msg,
                        "error_type": "PRICE_DATA_ERROR",
                        "user_message": f"❌ خطا در دریافت داده‌های قیمت {symbol}. لطفاً نماد را بررسی کنید."
                    }
                
            except Exception as e:
                error_msg = f"خطا در دریافت داده‌های قیمت: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "PRICE_DATA_ERROR",
                    "user_message": f"❌ خطا در دریافت داده‌های قیمت {symbol}. لطفاً نماد را بررسی کنید."
                }
            
            dfs = dict(zip(self.config.timeframes, dfs_list))
            
            # Validate that we have data
            missing_timeframes = [tf for tf, df in dfs.items() if df is None or len(df) < 50]
            if missing_timeframes:
                error_msg = f"داده کافی برای تایم‌فریم‌های {', '.join(missing_timeframes)} وجود ندارد"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "INSUFFICIENT_DATA",
                    "user_message": f"❌ داده کافی برای تحلیل {symbol} وجود ندارد. لطفاً نماد دیگری انتخاب کنید."
                }
            
            # Fetch current price and institutional data
            try:
                current_price, funding, oi = await asyncio.gather(
                    self.provider.get_current_price(symbol),
                    self.provider.get_funding_rate(symbol),
                    self.provider.get_open_interest(symbol)
                )
            except Exception as e:
                error_msg = f"خطا در دریافت داده‌های بازار: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "MARKET_DATA_ERROR",
                    "user_message": f"❌ خطا در دریافت اطلاعات بازار {symbol}. لطفاً دوباره تلاش کنید."
                }
            
            # Validate price data
            if not current_price or current_price <= 0:
                error_msg = f"قیمت نامعتبر برای {symbol}: {current_price}"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "INVALID_PRICE",
                    "user_message": f"❌ قیمت {symbol} نامعتبر است. لطفاً نماد را بررسی کنید."
                }
            
            # Calculate ATR for distance measurements
            try:
                atr_1h = self.tech.calculate_atr(dfs['1h']).iloc[-1]
            except Exception as e:
                error_msg = f"خطا در محاسبه ATR: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "CALCULATION_ERROR",
                    "user_message": "❌ خطا در محاسبات تکنیکال. لطفاً دوباره تلاش کنید."
                }
            
            # Calculate order flow and market regime
            try:
                order_flow = self.regime.calculate_order_flow(dfs['15m'])
                market_regime = self.regime.detect_market_regime(dfs['1h'], atr_1h)
            except Exception as e:
                error_msg = f"خطا در تحلیل رژیم بازار: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
                print(f"⚠️ {error_msg}")
                # Use default values instead of failing
                order_flow = {
                    "bid_ask_imbalance": 0.5,
                    "aggressive_buy_ratio": 0.5,
                    "order_book_depth": {"bid_depth_5": 0, "ask_depth_5": 0}
                }
                market_regime = {
                    "volatility_state": "NORMAL",
                    "trend_strength": 0.5,
                    "regime_type": "RANGING",
                    "regime_confidence": 0.5
                }
            
            # Build ICT-compatible structure
            try:
                data = {
                    "market_data": {
                        "symbol": symbol,
                        "timeframe": "15m",
                        "current_price": current_price,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "ohlcv": self._build_ohlcv(dfs)
                    },
                    "market_structure": self._build_market_structure(dfs),
                    "liquidity": self._build_liquidity(dfs['4h'], atr_1h),
                    "zones": self._build_zones(dfs['15m'], dfs['4h']),
                    "indicators": self._build_indicators(dfs['1h']),
                    "volume": self._build_volume(dfs['1h']),
                    "institutional": {
                        "open_interest": oi,
                        "oi_change_24h": round(oi * 0.02, 2),
                        "funding_rate": funding
                    },
                    "order_flow": order_flow,
                    "market_regime": market_regime,
                    "portfolio_state": self.config.portfolio_state
                }
                
                print(f"✅ ICT data for {symbol} collected")
                return data
                
            except Exception as e:
                error_msg = f"خطا در ساخت داده‌های تحلیل: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
                print(f"🔴 {error_msg}")
                return {
                    "error": error_msg,
                    "error_type": "DATA_BUILD_ERROR",
                    "user_message": "❌ خطا در پردازش داده‌های تحلیل. لطفاً دوباره تلاش کنید."
                }
        
        except Exception as e:
            error_msg = f"خطای غیرمنتظره در جمع‌آوری داده: {type(e).__name__} - {str(e) or 'خطای ناشناخته'}"
            print(f"🔴 {error_msg}")
            return {
                "error": error_msg,
                "error_type": "UNEXPECTED_ERROR",
                "user_message": "❌ خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید."
            }
    
    def _build_ohlcv(self, dfs: Dict) -> List:
        """Build OHLCV array"""
        df = dfs['15m']
        candles = []
        for _, row in df.iterrows():
            candles.append({
                'timestamp': int(row['timestamp'].timestamp() * 1000),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        return candles
    
    def _build_market_structure(self, dfs: Dict) -> Dict:
        """Build Market Structure with MSS"""
        htf_trend = self.tech.detect_trend(dfs['4h'])
        ltf_trend = self.tech.detect_trend(dfs['1h'], 10, 20)
        
        # Detect MSS on 4H
        mss = self.ict.detect_mss(dfs['4h'], "4h")
        
        # Find swing points
        df_4h = dfs['4h'].tail(50)
        highs = [{"price": float(p), "time": t.isoformat()} 
                 for p, t in zip(df_4h.nlargest(3, 'high')['high'], 
                                df_4h.nlargest(3, 'high')['timestamp'])]
        lows = [{"price": float(p), "time": t.isoformat()} 
                for p, t in zip(df_4h.nsmallest(3, 'low')['low'], 
                               df_4h.nsmallest(3, 'low')['timestamp'])]
        
        return {
            "htf_trend": htf_trend,
            "ltf_trend": ltf_trend,
            "last_mss": {
                "type": mss.type if mss else "NONE",
                "price": mss.price if mss else 0,
                "timestamp": mss.timestamp if mss else ""
            },
            "swing_points": {
                "highs": highs,
                "lows": lows
            }
        }
    
    def _build_liquidity(self, df: pd.DataFrame, atr: float) -> Dict:
        """Build Liquidity Zones"""
        liq = self.ict.detect_liquidity(df, atr)
        
        return {
            "ssl": [{"price": z.price, "strength": z.strength, "distance_atr": z.distance_atr} 
                    for z in liq['ssl']],
            "bsl": [{"price": z.price, "strength": z.strength, "distance_atr": z.distance_atr} 
                    for z in liq['bsl']]
        }
    
    def _build_zones(self, df_15m: pd.DataFrame, df_4h: pd.DataFrame) -> Dict:
        """Build FVG and Order Blocks"""
        fvgs = self.ict.detect_fvg(df_15m)
        obs = self.ict.detect_order_blocks(df_4h)
        
        return {
            "fvgs": [{"type": f.type, "top": f.top, "bottom": f.bottom, "mitigated": f.mitigated} 
                     for f in fvgs],
            "order_blocks": [{"type": ob.type, "top": ob.top, "bottom": ob.bottom, "strength": ob.strength} 
                            for ob in obs]
        }
    
    def _build_indicators(self, df: pd.DataFrame) -> Dict:
        """Build Indicators"""
        ema_50 = self.tech.calculate_ema(df, 50).iloc[-1] if len(df) >= 50 else 0
        ema_200 = self.tech.calculate_ema(df, 200).iloc[-1] if len(df) >= 200 else 0
        rsi = self.tech.calculate_rsi(df).iloc[-1]
        macd = self.tech.calculate_macd(df)
        atr = self.tech.calculate_atr(df).iloc[-1]
        
        return {
            "ema": {
                "50": float(ema_50),
                "200": float(ema_200)
            },
            "rsi": float(rsi),
            "macd": {
                "value": float(macd['value'].iloc[-1]),
                "signal": float(macd['signal'].iloc[-1]),
                "histogram": float(macd['histogram'].iloc[-1])
            },
            "atr": float(atr)
        }
    
    def _build_volume(self, df: pd.DataFrame) -> Dict:
        """Build Volume Data"""
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].tail(20).mean()
        delta = current_vol - avg_vol
        cvd = self.ict.calculate_cvd(df)
        
        return {
            "current": float(current_vol),
            "avg_20": float(avg_vol),
            "delta": float(delta),
            "cvd": float(cvd)
        }
