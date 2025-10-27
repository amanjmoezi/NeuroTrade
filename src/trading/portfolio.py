"""
Portfolio Manager - Track positions and risk (MongoDB version)
"""
import logging
from typing import Dict
from src.database.connection import DatabaseManager
from src.database.repositories import PortfolioRepository, TradingHistoryRepository


class PortfolioManager:
    """Portfolio Management and Risk Tracking using MongoDB"""
    
    def __init__(self, user_id: int = 0):
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.portfolio_repo = PortfolioRepository(self.db_manager)
        self.history_repo = TradingHistoryRepository(self.db_manager)
        
        # Cache
        self.positions = []
        self.total_risk = 0.0
        self.winning_streak = 0
        self.losing_streak = 0
        self.recent_drawdown = 0.0
    
    async def initialize(self):
        """Initialize database connection and load portfolio"""
        await self.db_manager.connect()
        await self._load_portfolio()
    
    async def _load_portfolio(self):
        """Load portfolio from database"""
        try:
            portfolio = await self.portfolio_repo.get_user_portfolio(self.user_id)
            self.positions = portfolio.get("positions", [])
            self.total_risk = portfolio.get("total_risk", 0.0)
            self.winning_streak = portfolio.get("winning_streak", 0)
            self.losing_streak = portfolio.get("losing_streak", 0)
            self.recent_drawdown = portfolio.get("recent_drawdown", 0.0)
        except Exception as e:
            self.logger.error(f"Error loading portfolio: {e}")
    
    async def get_state(self) -> Dict:
        """Get current portfolio state"""
        await self._load_portfolio()
        return {
            "open_positions": len(self.positions),
            "total_risk_exposure": round(self.total_risk, 2),
            "winning_streak": self.winning_streak,
            "recent_drawdown": round(self.recent_drawdown, 2)
        }
    
    async def add_position(self, symbol: str, risk_percent: float, entry_price: float = 0.0, size: float = 0.0):
        """Add new position"""
        try:
            position = {
                "symbol": symbol,
                "risk": risk_percent,
                "entry_price": entry_price,
                "size": size
            }
            await self.portfolio_repo.add_position(self.user_id, position)
            self.positions.append(position)
            self.total_risk += risk_percent
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
    
    async def remove_position(self, symbol: str, is_win: bool, pnl: float = 0.0, exit_price: float = 0.0):
        """Remove position and update stats"""
        try:
            # Record trade in history
            position = next((p for p in self.positions if p['symbol'] == symbol), None)
            if position:
                trade = {
                    "user_id": self.user_id,
                    "symbol": symbol,
                    "entry_price": position.get("entry_price", 0.0),
                    "exit_price": exit_price,
                    "size": position.get("size", 0.0),
                    "pnl": pnl,
                    "is_win": is_win,
                    "risk": position.get("risk", 0.0)
                }
                await self.history_repo.add_trade(trade)
            
            # Remove from portfolio
            await self.portfolio_repo.remove_position(self.user_id, symbol, is_win)
            
            # Update local cache
            self.positions = [p for p in self.positions if p['symbol'] != symbol]
            if is_win:
                self.winning_streak += 1
                self.losing_streak = 0
            else:
                self.losing_streak += 1
                self.winning_streak = 0
            
            # Recalculate total risk
            self.total_risk = sum(p['risk'] for p in self.positions)
            
        except Exception as e:
            self.logger.error(f"Error removing position: {e}")
    
    async def update_drawdown(self, drawdown: float):
        """Update recent drawdown"""
        try:
            self.recent_drawdown = drawdown
            await self.portfolio_repo.update_portfolio(self.user_id, {
                "recent_drawdown": drawdown
            })
        except Exception as e:
            self.logger.error(f"Error updating drawdown: {e}")
    
    async def get_trading_stats(self) -> Dict:
        """Get trading statistics"""
        try:
            return await self.history_repo.get_trade_stats(self.user_id)
        except Exception as e:
            self.logger.error(f"Error getting trading stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup database connection"""
        await self.db_manager.disconnect()
