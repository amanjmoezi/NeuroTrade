"""
ICT (Inner Circle Trader) Analysis Module
Concepts: MSS, FVG, Order Blocks, Liquidity Zones
"""
import pandas as pd
from typing import Dict, List, Optional
from src.core.models import MSS, FVG, OrderBlock, LiquidityZone


class ICTAnalyzer:
    """ICT/Smart Money Concepts Analyzer"""
    
    def __init__(self):
        pass
    
    def detect_mss(self, df: pd.DataFrame, timeframe: str) -> Optional[MSS]:
        """Detect Most Recent Market Structure Shift"""
        if len(df) < 20:
            return None
        
        recent_data = df.tail(20)
        highs = recent_data['high'].tolist()
        lows = recent_data['low'].tolist()
        
        # Bullish MSS: Break above recent swing high
        for i in range(len(highs)-3, 0, -1):
            if highs[-1] > highs[i]:
                return MSS(
                    type="BULLISH_MSS",
                    price=highs[i],
                    timestamp=recent_data.iloc[i]['timestamp'].isoformat(),
                    timeframe=timeframe
                )
        
        # Bearish MSS: Break below recent swing low
        for i in range(len(lows)-3, 0, -1):
            if lows[-1] < lows[i]:
                return MSS(
                    type="BEARISH_MSS",
                    price=lows[i],
                    timestamp=recent_data.iloc[i]['timestamp'].isoformat(),
                    timeframe=timeframe
                )
        
        return None
    
    def detect_liquidity(self, df: pd.DataFrame, atr: float) -> Dict[str, List[LiquidityZone]]:
        """Detect Sell Side Liquidity (SSL) and Buy Side Liquidity (BSL)"""
        ssl = []  # Sell Side (Equal Highs)
        bsl = []  # Buy Side (Equal Lows)
        
        lookback = min(100, len(df))
        recent = df.tail(lookback)
        
        # Detect Equal Highs (SSL)
        high_levels = []
        for i in range(1, len(recent)-1):
            if abs(recent['high'].iloc[i] - recent['high'].iloc[i-1]) < recent['high'].iloc[i] * 0.002:
                high_levels.append(recent['high'].iloc[i])
        
        if high_levels:
            high_levels.sort()
            clusters = self._cluster_levels(high_levels, 0.002)
            for cluster in clusters[-3:]:
                avg = sum(cluster) / len(cluster)
                distance = abs(df['close'].iloc[-1] - avg) / atr if atr > 0 else 0
                ssl.append(LiquidityZone(
                    type="SSL",
                    price=avg,
                    strength="HIGH" if len(cluster) >= 3 else "MED",
                    distance_atr=round(distance, 2)
                ))
        
        # Detect Equal Lows (BSL)
        low_levels = []
        for i in range(1, len(recent)-1):
            if abs(recent['low'].iloc[i] - recent['low'].iloc[i-1]) < recent['low'].iloc[i] * 0.002:
                low_levels.append(recent['low'].iloc[i])
        
        if low_levels:
            low_levels.sort()
            clusters = self._cluster_levels(low_levels, 0.002)
            for cluster in clusters[-3:]:
                avg = sum(cluster) / len(cluster)
                distance = abs(df['close'].iloc[-1] - avg) / atr if atr > 0 else 0
                bsl.append(LiquidityZone(
                    type="BSL",
                    price=avg,
                    strength="HIGH" if len(cluster) >= 3 else "MED",
                    distance_atr=round(distance, 2)
                ))
        
        return {"ssl": ssl, "bsl": bsl}
    
    def _cluster_levels(self, levels: List[float], tolerance: float) -> List[List[float]]:
        """Cluster similar price levels"""
        if not levels:
            return []
        
        clusters = []
        current = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current[-1]) < current[-1] * tolerance:
                current.append(level)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [level]
        
        if len(current) >= 2:
            clusters.append(current)
        
        return clusters
    
    def detect_fvg(self, df: pd.DataFrame) -> List[FVG]:
        """Detect Fair Value Gaps"""
        fvgs = []
        
        for i in range(2, len(df)):
            # Bullish FVG
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                fvgs.append(FVG(
                    type="BULL",
                    top=df['low'].iloc[i],
                    bottom=df['high'].iloc[i-2],
                    mitigated=False,
                    timestamp=df['timestamp'].iloc[i].isoformat()
                ))
            
            # Bearish FVG
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                fvgs.append(FVG(
                    type="BEAR",
                    top=df['low'].iloc[i-2],
                    bottom=df['high'].iloc[i],
                    mitigated=False,
                    timestamp=df['timestamp'].iloc[i].isoformat()
                ))
        
        return fvgs[-5:]
    
    def detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """Detect Order Blocks"""
        obs = []
        
        for i in range(2, len(df)):
            body = abs(df['close'].iloc[i] - df['open'].iloc[i])
            prev_range = df['high'].iloc[i-1] - df['low'].iloc[i-1]
            
            if prev_range <= 0:
                continue
            
            if body > prev_range * 1.2:
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    obs.append(OrderBlock(
                        type="BULL",
                        top=df['high'].iloc[i],
                        bottom=df['low'].iloc[i],
                        strength="MEDIUM",
                        timestamp=df['timestamp'].iloc[i].isoformat()
                    ))
                else:
                    obs.append(OrderBlock(
                        type="BEAR",
                        top=df['high'].iloc[i],
                        bottom=df['low'].iloc[i],
                        strength="MEDIUM",
                        timestamp=df['timestamp'].iloc[i].isoformat()
                    ))
        
        return obs[-5:]
    
    def calculate_cvd(self, df: pd.DataFrame) -> float:
        """Calculate Cumulative Volume Delta (Simplified)"""
        delta = 0
        for i in range(len(df)):
            if df['close'].iloc[i] > df['open'].iloc[i]:
                delta += df['volume'].iloc[i]
            else:
                delta -= df['volume'].iloc[i]
        return delta
