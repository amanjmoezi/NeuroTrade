"""
Data Models for Trading System
"""
from dataclasses import dataclass


@dataclass
class MSS:
    """Market Structure Shift"""
    type: str  # "BULLISH_MSS" or "BEARISH_MSS"
    price: float
    timestamp: str
    timeframe: str


@dataclass
class LiquidityZone:
    """Liquidity Zone (SSL/BSL)"""
    type: str  # "SSL" or "BSL"
    price: float
    strength: str  # "HIGH", "MED", "LOW"
    distance_atr: float


@dataclass
class FVG:
    """Fair Value Gap"""
    type: str  # "BULL" or "BEAR"
    top: float
    bottom: float
    mitigated: bool
    timestamp: str


@dataclass
class OrderBlock:
    """Order Block"""
    type: str  # "BULL" or "BEAR"
    top: float
    bottom: float
    strength: str
    timestamp: str
