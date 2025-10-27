"""
Database Repositories - Data access layer for MongoDB collections
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional
from .connection import DatabaseManager


class UserRepository:
    """Repository for user settings"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """Get user settings by user_id"""
        return await self.db.user_settings.find_one({"user_id": user_id})
    
    async def create_user_settings(self, user_id: int, settings: Dict) -> Dict:
        """Create new user settings"""
        doc = {
            "user_id": user_id,
            "notifications": settings.get("notifications", True),
            "favorite_symbols": settings.get("favorite_symbols", ["BTCUSDT", "ETHUSDT"]),
            "default_timeframe": settings.get("default_timeframe", "1h"),
            "default_leverage": settings.get("default_leverage", 10),
            "risk_per_trade": settings.get("risk_per_trade", 2.0),
            "language": settings.get("language", "fa"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await self.db.user_settings.insert_one(doc)
        return doc
    
    async def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Update user settings"""
        settings["updated_at"] = datetime.now(timezone.utc)
        result = await self.db.user_settings.update_one(
            {"user_id": user_id},
            {"$set": settings}
        )
        return result.modified_count > 0
    
    async def get_or_create_user_settings(self, user_id: int) -> Dict:
        """Get user settings or create if not exists"""
        settings = await self.get_user_settings(user_id)
        if not settings:
            settings = await self.create_user_settings(user_id, {})
        return settings


class AlertRepository:
    """Repository for price alerts"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_alert(self, alert: Dict) -> str:
        """Create new price alert"""
        alert["created_at"] = datetime.now(timezone.utc)
        result = await self.db.alerts.insert_one(alert)
        return str(result.inserted_id)
    
    async def get_user_alerts(self, user_id: int) -> List[Dict]:
        """Get all alerts for a user"""
        cursor = self.db.alerts.find({"user_id": user_id})
        return await cursor.to_list(length=100)
    
    async def get_all_active_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        cursor = self.db.alerts.find({})
        return await cursor.to_list(length=1000)
    
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        from bson import ObjectId
        result = await self.db.alerts.delete_one({"_id": ObjectId(alert_id)})
        return result.deleted_count > 0
    
    async def delete_user_alerts(self, user_id: int, symbol: str = None) -> int:
        """Delete user alerts, optionally filtered by symbol"""
        query = {"user_id": user_id}
        if symbol:
            query["symbol"] = symbol
        result = await self.db.alerts.delete_many(query)
        return result.deleted_count


class PortfolioRepository:
    """Repository for portfolio positions"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_user_portfolio(self, user_id: int) -> Dict:
        """Get user's portfolio state"""
        return await self.db.portfolio.find_one({"user_id": user_id}) or {
            "user_id": user_id,
            "positions": [],
            "total_risk": 0.0,
            "winning_streak": 0,
            "losing_streak": 0,
            "recent_drawdown": 0.0
        }
    
    async def update_portfolio(self, user_id: int, portfolio_data: Dict) -> bool:
        """Update portfolio state"""
        portfolio_data["updated_at"] = datetime.now(timezone.utc)
        result = await self.db.portfolio.update_one(
            {"user_id": user_id},
            {"$set": portfolio_data},
            upsert=True
        )
        return result.acknowledged
    
    async def add_position(self, user_id: int, position: Dict) -> bool:
        """Add a new position to portfolio"""
        position["opened_at"] = datetime.now(timezone.utc)
        result = await self.db.portfolio.update_one(
            {"user_id": user_id},
            {
                "$push": {"positions": position},
                "$inc": {"total_risk": position.get("risk", 0.0)},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        return result.acknowledged
    
    async def remove_position(self, user_id: int, symbol: str, is_win: bool) -> bool:
        """Remove a position from portfolio"""
        portfolio = await self.get_user_portfolio(user_id)
        positions = portfolio.get("positions", [])
        
        # Find and remove position
        position_to_remove = None
        for pos in positions:
            if pos["symbol"] == symbol:
                position_to_remove = pos
                break
        
        if not position_to_remove:
            return False
        
        # Update streaks
        update_data = {
            "$pull": {"positions": {"symbol": symbol}},
            "$inc": {"total_risk": -position_to_remove.get("risk", 0.0)},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
        
        if is_win:
            update_data["$inc"]["winning_streak"] = 1
            update_data["$set"]["losing_streak"] = 0
        else:
            update_data["$inc"]["losing_streak"] = 1
            update_data["$set"]["winning_streak"] = 0
        
        result = await self.db.portfolio.update_one(
            {"user_id": user_id},
            update_data
        )
        return result.acknowledged


class TradingHistoryRepository:
    """Repository for trading history"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def add_trade(self, trade: Dict) -> str:
        """Add a trade to history"""
        trade["timestamp"] = datetime.now(timezone.utc)
        result = await self.db.trading_history.insert_one(trade)
        return str(result.inserted_id)
    
    async def get_user_trades(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's trading history"""
        cursor = self.db.trading_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_trades_by_symbol(self, user_id: int, symbol: str, limit: int = 20) -> List[Dict]:
        """Get trades for a specific symbol"""
        cursor = self.db.trading_history.find(
            {"user_id": user_id, "symbol": symbol}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_trade_stats(self, user_id: int) -> Dict:
        """Get trading statistics for a user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_trades": {"$sum": 1},
                "winning_trades": {
                    "$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}
                },
                "total_pnl": {"$sum": "$pnl"},
                "avg_pnl": {"$avg": "$pnl"}
            }}
        ]
        result = await self.db.trading_history.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {}


class AnalysisHistoryRepository:
    """Repository for analysis history"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def add_analysis(self, analysis: Dict) -> str:
        """Add an analysis to history"""
        analysis["timestamp"] = datetime.now(timezone.utc)
        result = await self.db.analysis_history.insert_one(analysis)
        return str(result.inserted_id)
    
    async def get_user_analyses(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's analysis history"""
        cursor = self.db.analysis_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_analyses_by_symbol(self, user_id: int, symbol: str, limit: int = 20) -> List[Dict]:
        """Get analyses for a specific symbol"""
        cursor = self.db.analysis_history.find(
            {"user_id": user_id, "symbol": symbol}
        ).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_analysis_stats(self, user_id: int) -> Dict:
        """Get analysis statistics for a user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_analyses": {"$sum": 1},
                "buy_signals": {
                    "$sum": {"$cond": [{"$in": ["$signal_type", ["BUY", "LONG"]]}, 1, 0]}
                },
                "sell_signals": {
                    "$sum": {"$cond": [{"$in": ["$signal_type", ["SELL", "SHORT"]]}, 1, 0]}
                },
                "hold_signals": {
                    "$sum": {"$cond": [{"$in": ["$signal_type", ["HOLD", "NO_TRADE"]]}, 1, 0]}
                },
                "avg_confidence": {"$avg": "$confidence"}
            }}
        ]
        result = await self.db.analysis_history.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {}


class PerformanceRepository:
    """Repository for performance tracking"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def record_daily_performance(self, user_id: int, performance: Dict) -> str:
        """Record daily performance metrics"""
        doc = {
            "user_id": user_id,
            "date": datetime.now(timezone.utc).date().isoformat(),
            "timestamp": datetime.now(timezone.utc),
            **performance
        }
        result = await self.db.performance.update_one(
            {"user_id": user_id, "date": doc["date"]},
            {"$set": doc},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    async def get_performance_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get performance history for specified days"""
        cursor = self.db.performance.find(
            {"user_id": user_id}
        ).sort("date", -1).limit(days)
        return await cursor.to_list(length=days)
    
    async def get_performance_summary(self, user_id: int) -> Dict:
        """Get overall performance summary"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_days": {"$sum": 1},
                "total_pnl": {"$sum": "$daily_pnl"},
                "avg_daily_pnl": {"$avg": "$daily_pnl"},
                "best_day": {"$max": "$daily_pnl"},
                "worst_day": {"$min": "$daily_pnl"}
            }}
        ]
        result = await self.db.performance.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {}
