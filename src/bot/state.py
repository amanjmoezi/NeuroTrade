"""
Bot State Manager - User settings and alerts (MongoDB version)
"""
import logging
from typing import Dict, List
from dataclasses import dataclass
from src.database.connection import DatabaseManager
from src.database.repositories import UserRepository, AlertRepository


@dataclass
class UserSettings:
    user_id: int
    notifications: bool = True
    favorite_symbols: List[str] = None
    default_timeframe: str = "1h"  # Default timeframe for analysis
    default_leverage: int = 10  # Default leverage
    risk_per_trade: float = 2.0  # Risk percentage per trade
    language: str = "fa"  # Language preference (fa/en)
    
    def __post_init__(self):
        if self.favorite_symbols is None:
            self.favorite_symbols = ["BTCUSDT", "ETHUSDT"]


@dataclass
class PriceAlert:
    user_id: int
    symbol: str
    target_price: float
    condition: str
    created_at: str
    _id: str = None


class BotStateManager:
    """Manage bot state, user settings, and alerts using MongoDB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.user_repo = UserRepository(self.db_manager)
        self.alert_repo = AlertRepository(self.db_manager)
        
        # Cache for quick access
        self.user_settings_cache: Dict[int, UserSettings] = {}
        self.price_alerts_cache: List[PriceAlert] = []
    
    async def initialize(self):
        """Initialize database connection"""
        await self.db_manager.connect()
        await self._load_alerts_cache()
    
    async def _load_alerts_cache(self):
        """Load all alerts into cache for quick checking"""
        try:
            alerts_data = await self.alert_repo.get_all_active_alerts()
            self.price_alerts_cache = [
                PriceAlert(
                    user_id=a["user_id"],
                    symbol=a["symbol"],
                    target_price=a["target_price"],
                    condition=a["condition"],
                    created_at=a["created_at"].isoformat() if hasattr(a["created_at"], 'isoformat') else str(a["created_at"]),
                    _id=str(a["_id"])
                )
                for a in alerts_data
            ]
        except Exception as e:
            self.logger.error(f"Error loading alerts cache: {e}")
    
    async def get_user_settings(self, user_id: int) -> UserSettings:
        """Get user settings"""
        # Check cache first
        if user_id in self.user_settings_cache:
            return self.user_settings_cache[user_id]
        
        # Load from database
        try:
            settings_data = await self.user_repo.get_or_create_user_settings(user_id)
            settings = UserSettings(
                user_id=settings_data["user_id"],
                notifications=settings_data.get("notifications", True),
                favorite_symbols=settings_data.get("favorite_symbols", ["BTCUSDT", "ETHUSDT"]),
                default_timeframe=settings_data.get("default_timeframe", "1h"),
                default_leverage=settings_data.get("default_leverage", 10),
                risk_per_trade=settings_data.get("risk_per_trade", 2.0),
                language=settings_data.get("language", "fa")
            )
            self.user_settings_cache[user_id] = settings
            return settings
        except Exception as e:
            self.logger.error(f"Error getting user settings: {e}")
            # Return default settings
            return UserSettings(user_id=user_id)
    
    async def update_user_settings(self, user_id: int, settings: UserSettings):
        """Update user settings"""
        try:
            settings_dict = {
                "notifications": settings.notifications,
                "favorite_symbols": settings.favorite_symbols,
                "default_timeframe": settings.default_timeframe,
                "default_leverage": settings.default_leverage,
                "risk_per_trade": settings.risk_per_trade,
                "language": settings.language
            }
            await self.user_repo.update_user_settings(user_id, settings_dict)
            self.user_settings_cache[user_id] = settings
        except Exception as e:
            self.logger.error(f"Error updating user settings: {e}")
    
    async def add_alert(self, alert: PriceAlert):
        """Add price alert"""
        try:
            alert_dict = {
                "user_id": alert.user_id,
                "symbol": alert.symbol,
                "target_price": alert.target_price,
                "condition": alert.condition,
                "created_at": alert.created_at
            }
            alert_id = await self.alert_repo.create_alert(alert_dict)
            alert._id = alert_id
            self.price_alerts_cache.append(alert)
        except Exception as e:
            self.logger.error(f"Error adding alert: {e}")
    
    async def remove_alert(self, alert: PriceAlert):
        """Remove price alert"""
        try:
            if alert._id:
                await self.alert_repo.delete_alert(alert._id)
            self.price_alerts_cache = [a for a in self.price_alerts_cache if a._id != alert._id]
        except Exception as e:
            self.logger.error(f"Error removing alert: {e}")
    
    async def get_user_alerts(self, user_id: int) -> List[PriceAlert]:
        """Get user's alerts"""
        try:
            alerts_data = await self.alert_repo.get_user_alerts(user_id)
            return [
                PriceAlert(
                    user_id=a["user_id"],
                    symbol=a["symbol"],
                    target_price=a["target_price"],
                    condition=a["condition"],
                    created_at=a["created_at"].isoformat() if hasattr(a["created_at"], 'isoformat') else str(a["created_at"]),
                    _id=str(a["_id"])
                )
                for a in alerts_data
            ]
        except Exception as e:
            self.logger.error(f"Error getting user alerts: {e}")
            return []
    
    @property
    def price_alerts(self) -> List[PriceAlert]:
        """Get all cached alerts"""
        return self.price_alerts_cache
    
    async def cleanup(self):
        """Cleanup database connection"""
        await self.db_manager.disconnect()
