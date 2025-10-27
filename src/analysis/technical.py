"""
Technical Analysis Module
Indicators: EMA, RSI, MACD, ATR, ADX
"""
import pandas as pd
import numpy as np
from typing import Dict


class TechnicalAnalyzer:
    """Technical Analyzer for Price Action and Indicators"""
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if len(df) < period:
            return df['close'].rolling(window=len(df), min_periods=1).mean()
        return df['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan).fillna(0)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal = macd_line.ewm(span=9, adjust=False).mean()
        return {
            'value': macd_line,
            'signal': signal,
            'histogram': macd_line - signal
        }
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period, min_periods=1).mean()
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX for trend strength"""
        if len(df) < period + 1:
            return 25.0
        
        high = df['high']
        low = df['low']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = TechnicalAnalyzer.calculate_atr(df, 1)
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 25.0
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, short: int = 20, long: int = 50) -> str:
        """Detect market trend: BULLISH, BEARISH, or RANGING"""
        if len(df) < long:
            return "RANGING"
        
        short_ma = df['close'].rolling(short).mean()
        long_ma = df['close'].rolling(long).mean()
        
        if len(df) >= 10:
            price_slope = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        else:
            price_slope = 0
        
        bullish = short_ma.iloc[-1] > long_ma.iloc[-1] and price_slope > 0.001
        bearish = short_ma.iloc[-1] < long_ma.iloc[-1] and price_slope < -0.001
        
        if bullish:
            return "BULLISH"
        elif bearish:
            return "BEARISH"
        return "RANGING"
