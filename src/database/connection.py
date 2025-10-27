"""
MongoDB Connection Manager
"""
import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure


class DatabaseManager:
    """MongoDB Connection Manager using Motor (async driver)"""
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGODB_DATABASE", "trading_bot")
    
    async def connect(self):
        """Connect to MongoDB"""
        if self._client is None:
            try:
                self._client = AsyncIOMotorClient(self.mongo_uri)
                # Test connection
                await self._client.admin.command('ping')
                self._db = self._client[self.db_name]
                self.logger.info(f"✅ Connected to MongoDB: {self.db_name}")
                
                # Create indexes
                await self._create_indexes()
                
            except ConnectionFailure as e:
                self.logger.error(f"❌ MongoDB connection failed: {e}")
                raise
    
    async def _create_indexes(self):
        """Create necessary indexes for collections"""
        try:
            # User settings indexes
            await self._db.user_settings.create_index("user_id", unique=True)
            
            # Alerts indexes
            await self._db.alerts.create_index([("user_id", 1), ("symbol", 1)])
            await self._db.alerts.create_index("created_at")
            
            # Portfolio indexes
            await self._db.portfolio.create_index("user_id")
            await self._db.portfolio.create_index([("user_id", 1), ("symbol", 1)])
            
            # Trading history indexes
            await self._db.trading_history.create_index([("user_id", 1), ("timestamp", -1)])
            await self._db.trading_history.create_index("symbol")
            await self._db.trading_history.create_index("timestamp")
            
            # Analysis history indexes
            await self._db.analysis_history.create_index([("user_id", 1), ("timestamp", -1)])
            await self._db.analysis_history.create_index("symbol")
            await self._db.analysis_history.create_index("timestamp")
            
            # Performance tracking indexes
            await self._db.performance.create_index([("user_id", 1), ("date", -1)])
            
            self.logger.info("✅ Database indexes created")
        except Exception as e:
            self.logger.warning(f"⚠️ Error creating indexes: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self.logger.info("🔌 Disconnected from MongoDB")
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self._client is not None and self._db is not None
    
    # Collection accessors
    @property
    def user_settings(self):
        """User settings collection"""
        return self.db.user_settings
    
    @property
    def alerts(self):
        """Price alerts collection"""
        return self.db.alerts
    
    @property
    def portfolio(self):
        """Portfolio positions collection"""
        return self.db.portfolio
    
    @property
    def trading_history(self):
        """Trading history collection"""
        return self.db.trading_history
    
    @property
    def analysis_history(self):
        """Analysis history collection"""
        return self.db.analysis_history
    
    @property
    def performance(self):
        """Performance tracking collection"""
        return self.db.performance
