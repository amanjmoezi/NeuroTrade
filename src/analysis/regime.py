"""
Market Regime Detection and Order Flow Analysis
"""
import pandas as pd
from typing import Dict
from .technical import TechnicalAnalyzer


class RegimeDetector:
    """Market Regime and Order Flow Detector"""
    
    @staticmethod
    def detect_market_regime(df: pd.DataFrame, atr: float) -> Dict:
        """Detect market regime: TRENDING, RANGING, VOLATILE, TRANSITIONAL"""
        if len(df) < 30:
            return {
                "type": "TRANSITIONAL",
                "confidence": 0.5,
                "volatility_state": "NORMAL",
                "trend_strength": 0.5
            }
        
        # Calculate ADX for trend strength
        adx = TechnicalAnalyzer.calculate_adx(df)
        
        # Calculate price range ratio
        high_20 = df['high'].tail(20).max()
        low_20 = df['low'].tail(20).min()
        price_range_ratio = (high_20 - low_20) / atr if atr > 0 else 10
        
        # Calculate ATR percentile (simplified)
        atr_series = TechnicalAnalyzer.calculate_atr(df, 14)
        atr_30d = atr_series.tail(min(30, len(atr_series)))
        atr_percentile = (atr_30d < atr).sum() / len(atr_30d) * 100 if len(atr_30d) > 0 else 50
        
        # Determine volatility state
        if atr_percentile < 30:
            volatility_state = "LOW"
        elif atr_percentile > 90:
            volatility_state = "EXTREME"
        elif atr_percentile > 70:
            volatility_state = "HIGH"
        else:
            volatility_state = "NORMAL"
        
        # Determine regime type
        if adx > 25 and price_range_ratio > 15:
            regime_type = "TRENDING"
            confidence = min(adx / 50, 1.0)
        elif adx < 20 and price_range_ratio < 10:
            regime_type = "RANGING"
            confidence = (25 - adx) / 25
        elif atr_percentile > 80:
            regime_type = "VOLATILE"
            confidence = atr_percentile / 100
        else:
            regime_type = "TRANSITIONAL"
            confidence = 0.5
        
        return {
            "type": regime_type,
            "confidence": round(confidence, 2),
            "volatility_state": volatility_state,
            "trend_strength": round(adx / 50, 2)
        }
    
    @staticmethod
    def calculate_order_flow(df: pd.DataFrame) -> Dict:
        """Calculate simplified order flow metrics"""
        if len(df) < 20:
            return {
                "bid_ask_imbalance": 0.5,
                "large_orders": [],
                "aggressive_buy_ratio": 0.5,
                "order_book_depth": {"bid_depth_5": 0, "ask_depth_5": 0}
            }
        
        # Simplified bid-ask imbalance based on candle closes
        recent = df.tail(20)
        bullish_candles = (recent['close'] > recent['open']).sum()
        bid_ask_imbalance = bullish_candles / len(recent)
        
        # Detect large orders (volume spikes)
        avg_volume = recent['volume'].mean()
        large_orders = []
        for idx, row in recent.tail(5).iterrows():
            if row['volume'] > avg_volume * 2:
                side = "BUY" if row['close'] > row['open'] else "SELL"
                large_orders.append({
                    "side": side,
                    "size": float(row['volume']),
                    "price": float(row['close'])
                })
        
        # Aggressive buy ratio
        aggressive_buy_ratio = bid_ask_imbalance
        
        # Simplified order book depth (based on volume)
        total_volume = recent['volume'].sum()
        bid_volume = recent[recent['close'] > recent['open']]['volume'].sum()
        ask_volume = total_volume - bid_volume
        
        return {
            "bid_ask_imbalance": round(bid_ask_imbalance, 2),
            "large_orders": large_orders[-3:],  # Last 3 large orders
            "aggressive_buy_ratio": round(aggressive_buy_ratio, 2),
            "order_book_depth": {
                "bid_depth_5": float(bid_volume),
                "ask_depth_5": float(ask_volume)
            }
        }
