"""
ICT Trading System - Modular Architecture v3.0
"""
__version__ = "3.0.0"
__author__ = "ICT Trading Team"

# Import main components for easy access
from .core import Config
from .trading import TradingSystem
from .bot import CommandHandlers

__all__ = ['Config', 'TradingSystem', 'CommandHandlers']
