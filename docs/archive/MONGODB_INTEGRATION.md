# یکپارچه‌سازی MongoDB با پروژه Trading Bot

## 📋 خلاصه تغییرات

پروژه به طور کامل به MongoDB متصل شده است. تمام قسمت‌هایی که نیاز به ذخیره‌سازی داده داشتند، اکنون از MongoDB استفاده می‌کنند.

## 🗂️ فایل‌های جدید

### 1. ماژول Database (`src/database/`)

```
src/database/
├── __init__.py              # Export DatabaseManager
├── connection.py            # مدیریت اتصال MongoDB
└── repositories.py          # Repository pattern برای دسترسی به داده
```

#### `connection.py` - DatabaseManager
- **Singleton pattern** برای اتصال یکتا به MongoDB
- **Async support** با استفاده از Motor driver
- **Auto-indexing** برای بهینه‌سازی queries
- **Connection pooling** برای performance بهتر

#### `repositories.py` - Data Access Layer
شامل 5 Repository:
- `UserRepository` - مدیریت تنظیمات کاربران
- `AlertRepository` - مدیریت هشدارهای قیمت
- `PortfolioRepository` - مدیریت پورتفولیو
- `TradingHistoryRepository` - ذخیره تاریخچه معاملات
- `PerformanceRepository` - ردیابی عملکرد

### 2. فایل‌های تست و مستندات

- `test_mongodb.py` - اسکریپت تست اتصال MongoDB
- `MONGODB_SETUP.md` - راهنمای کامل نصب و راه‌اندازی
- `MONGODB_INTEGRATION.md` - این فایل

## 🔄 فایل‌های تغییر یافته

### 1. `requirements.txt`
```diff
+ # Database
+ motor==3.3.2
+ pymongo==4.6.1
```

### 2. `src/core/config.py`
```python
# MongoDB Configuration
self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
self.mongodb_database = os.getenv("MONGODB_DATABASE", "trading_bot")
```

### 3. `src/bot/state.py` - BotStateManager
**قبل:** استفاده از فایل JSON (`data/bot_state.json`)
**بعد:** استفاده از MongoDB

تغییرات اصلی:
- ✅ تبدیل به async methods
- ✅ استفاده از `UserRepository` و `AlertRepository`
- ✅ Cache برای performance بهتر
- ✅ متد `initialize()` برای اتصال به DB
- ✅ متد `cleanup()` برای قطع اتصال

```python
# قبل
def get_user_settings(self, user_id: int) -> UserSettings:
    if user_id not in self.user_settings:
        self.user_settings[user_id] = UserSettings(user_id=user_id)
        self.save_state()
    return self.user_settings[user_id]

# بعد
async def get_user_settings(self, user_id: int) -> UserSettings:
    if user_id in self.user_settings_cache:
        return self.user_settings_cache[user_id]
    
    settings_data = await self.user_repo.get_or_create_user_settings(user_id)
    settings = UserSettings(...)
    self.user_settings_cache[user_id] = settings
    return settings
```

### 4. `src/trading/portfolio.py` - PortfolioManager
**قبل:** ذخیره در حافظه (RAM)
**بعد:** ذخیره در MongoDB

تغییرات اصلی:
- ✅ تبدیل به async methods
- ✅ استفاده از `PortfolioRepository` و `TradingHistoryRepository`
- ✅ ذخیره خودکار تاریخچه معاملات
- ✅ متد `get_trading_stats()` برای آمار

```python
# قبل
def add_position(self, symbol: str, risk_percent: float):
    self.positions.append({"symbol": symbol, "risk": risk_percent})
    self.total_risk += risk_percent

# بعد
async def add_position(self, symbol: str, risk_percent: float, 
                      entry_price: float = 0.0, size: float = 0.0):
    position = {...}
    await self.portfolio_repo.add_position(self.user_id, position)
    self.positions.append(position)
    self.total_risk += risk_percent
```

### 5. `src/bot/handlers.py` - CommandHandlers
تمام متدهایی که با `BotStateManager` کار می‌کنند به async تبدیل شدند:

```python
# قبل
settings = self.state_manager.get_user_settings(user_id)

# بعد
settings = await self.state_manager.get_user_settings(user_id)
```

تغییرات در متدها:
- ✅ `settings_command()` - await برای get_user_settings
- ✅ `alerts_command()` - await برای get_user_alerts
- ✅ `setalert_command()` - await برای add_alert
- ✅ `button_callback()` - await برای update_user_settings
- ✅ `check_alerts_task()` - await برای remove_alert

### 6. `bot.py` - TradingBot
```python
async def post_init(self, application: Application):
    """Post initialization - setup jobs and database"""
    # Initialize database connection
    await self.handlers.state_manager.initialize()
    
    # Setup job queue
    job_queue = application.job_queue
    job_queue.run_repeating(self.handlers.check_alerts_task, interval=60, first=10)
```

### 7. `.env.example`
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=trading_bot
```

## 📊 ساختار Collections در MongoDB

### 1. `user_settings`
```javascript
{
  user_id: 123456789,          // Telegram User ID (unique index)
  notifications: true,
  favorite_symbols: ["BTCUSDT", "ETHUSDT"],
  created_at: ISODate,
  updated_at: ISODate
}
```

### 2. `alerts`
```javascript
{
  user_id: 123456789,
  symbol: "BTCUSDT",
  target_price: 50000.0,
  condition: "above",           // "above" or "below"
  created_at: ISODate
}
```
**Indexes:** `(user_id, symbol)`, `created_at`

### 3. `portfolio`
```javascript
{
  user_id: 123456789,
  positions: [
    {
      symbol: "BTCUSDT",
      risk: 2.0,
      entry_price: 45000.0,
      size: 0.1,
      opened_at: ISODate
    }
  ],
  total_risk: 2.0,
  winning_streak: 3,
  losing_streak: 0,
  recent_drawdown: 0.0,
  updated_at: ISODate
}
```
**Indexes:** `user_id`, `(user_id, symbol)`

### 4. `trading_history`
```javascript
{
  user_id: 123456789,
  symbol: "BTCUSDT",
  entry_price: 45000.0,
  exit_price: 47000.0,
  size: 0.1,
  pnl: 200.0,
  is_win: true,
  risk: 2.0,
  timestamp: ISODate
}
```
**Indexes:** `(user_id, timestamp DESC)`, `symbol`, `timestamp`

### 5. `performance`
```javascript
{
  user_id: 123456789,
  date: "2024-10-26",
  daily_pnl: 500.0,
  trades_count: 5,
  win_rate: 0.8,
  timestamp: ISODate
}
```
**Indexes:** `(user_id, date DESC)`

## 🚀 راه‌اندازی

### گام 1: نصب MongoDB

```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb-org
sudo systemctl start mongod

# یا با Docker
docker run -d --name mongodb -p 27017:27017 mongo:7.0
```

### گام 2: نصب Dependencies

```bash
pip install -r requirements.txt
```

### گام 3: تنظیم Environment Variables

```bash
# ویرایش .env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=trading_bot
```

### گام 4: تست اتصال

```bash
python test_mongodb.py
```

خروجی موفق:
```
✅ Connected to MongoDB successfully!
✅ All tests passed successfully!
🎉 MongoDB is ready to use!
```

### گام 5: اجرای Bot

```bash
python bot.py
```

## 🔍 مزایای استفاده از MongoDB

### 1. **Persistence** - ماندگاری داده
- ❌ قبل: داده‌ها در RAM یا فایل JSON (از دست می‌رفت با restart)
- ✅ حالا: ذخیره دائمی در دیتابیس

### 2. **Scalability** - مقیاس‌پذیری
- ❌ قبل: محدودیت حافظه RAM
- ✅ حالا: ذخیره میلیون‌ها رکورد

### 3. **Query Performance** - عملکرد Query
- ❌ قبل: جستجو در لیست‌ها (O(n))
- ✅ حالا: استفاده از Indexes (O(log n))

### 4. **Concurrent Access** - دسترسی همزمان
- ❌ قبل: مشکل race condition
- ✅ حالا: Transaction support

### 5. **Analytics** - تحلیل داده
- ❌ قبل: محدود به داده‌های RAM
- ✅ حالا: Aggregation pipeline برای آمار پیشرفته

### 6. **Backup & Recovery** - پشتیبان‌گیری
- ❌ قبل: دستی و خطاپذیر
- ✅ حالا: ابزارهای حرفه‌ای MongoDB

## 📈 استفاده از Repository Pattern

### مثال: ذخیره معامله

```python
from src.database.connection import DatabaseManager
from src.database.repositories import TradingHistoryRepository

async def record_trade():
    db = DatabaseManager()
    await db.connect()
    
    history_repo = TradingHistoryRepository(db)
    
    trade = {
        "user_id": 123456789,
        "symbol": "BTCUSDT",
        "entry_price": 45000.0,
        "exit_price": 47000.0,
        "size": 0.1,
        "pnl": 200.0,
        "is_win": True,
        "risk": 2.0
    }
    
    trade_id = await history_repo.add_trade(trade)
    print(f"Trade saved with ID: {trade_id}")
    
    await db.disconnect()
```

### مثال: دریافت آمار

```python
async def get_stats(user_id: int):
    db = DatabaseManager()
    await db.connect()
    
    history_repo = TradingHistoryRepository(db)
    stats = await history_repo.get_trade_stats(user_id)
    
    print(f"Total trades: {stats['total_trades']}")
    print(f"Win rate: {stats['winning_trades'] / stats['total_trades'] * 100:.1f}%")
    print(f"Total PnL: ${stats['total_pnl']:,.2f}")
    
    await db.disconnect()
```

## 🛡️ امنیت

### 1. Connection String Security
```python
# ❌ هرگز hardcode نکنید
MONGODB_URI = "mongodb://user:pass@host:27017"

# ✅ از environment variable استفاده کنید
MONGODB_URI = os.getenv("MONGODB_URI")
```

### 2. Input Validation
```python
# Repository ها خودکار validation انجام می‌دهند
# اما همیشه input را بررسی کنید
if not isinstance(user_id, int) or user_id <= 0:
    raise ValueError("Invalid user_id")
```

### 3. Error Handling
```python
try:
    await repo.add_trade(trade)
except Exception as e:
    logger.error(f"Failed to save trade: {e}")
    # Fallback logic
```

## 🔧 Troubleshooting

### مشکل: Connection Timeout
```
pymongo.errors.ServerSelectionTimeoutError
```
**راه‌حل:**
```bash
sudo systemctl status mongod
sudo systemctl start mongod
```

### مشکل: Import Error
```
ModuleNotFoundError: No module named 'motor'
```
**راه‌حل:**
```bash
pip install -r requirements.txt
```

### مشکل: Async Error
```
RuntimeError: no running event loop
```
**راه‌حل:** همیشه از `await` در async functions استفاده کنید

## 📚 منابع

- [MongoDB Setup Guide](./MONGODB_SETUP.md) - راهنمای کامل نصب
- [Motor Documentation](https://motor.readthedocs.io/) - Async MongoDB driver
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html) - معماری

## ✅ Checklist برای Production

- [ ] MongoDB با authentication راه‌اندازی شده
- [ ] Backup روزانه تنظیم شده
- [ ] Monitoring فعال است
- [ ] SSL/TLS برای اتصال فعال است
- [ ] Connection pooling بهینه شده
- [ ] Indexes بررسی شده
- [ ] Error logging فعال است
- [ ] Environment variables امن هستند

## 🎯 آینده پروژه

امکانات پیشنهادی برای توسعه:

1. **Real-time Analytics Dashboard**
   - استفاده از Aggregation Pipeline
   - نمایش آمار لحظه‌ای

2. **Multi-user Support**
   - هر کاربر portfolio جداگانه
   - مدیریت دسترسی

3. **Advanced Reporting**
   - گزارش‌های هفتگی/ماهانه
   - Export به PDF/Excel

4. **Machine Learning Integration**
   - ذخیره training data
   - مدل‌های پیش‌بینی

5. **API Endpoints**
   - RESTful API برای دسترسی خارجی
   - WebSocket برای real-time updates
