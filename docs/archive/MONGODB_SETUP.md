# راه‌اندازی MongoDB برای پروژه Trading Bot

این پروژه از MongoDB برای ذخیره‌سازی داده‌های زیر استفاده می‌کند:
- تنظیمات کاربران
- هشدارهای قیمت
- پورتفولیو و پوزیشن‌های معاملاتی
- تاریخچه معاملات
- آمار عملکرد

## نصب MongoDB

### روش 1: نصب Local (توصیه می‌شود برای Development)

#### Ubuntu/Debian:
```bash
# Import MongoDB public GPG Key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Create list file
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update package database
sudo apt-get update

# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Check status
sudo systemctl status mongod
```

#### macOS:
```bash
# با استفاده از Homebrew
brew tap mongodb/brew
brew install mongodb-community@7.0

# Start MongoDB
brew services start mongodb-community@7.0
```

#### Windows:
1. دانلود MongoDB Community Server از: https://www.mongodb.com/try/download/community
2. نصب با تنظیمات پیش‌فرض
3. MongoDB به صورت خودکار به عنوان سرویس اجرا می‌شود

### روش 2: استفاده از Docker (سریع‌ترین روش)

```bash
# اجرای MongoDB با Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:7.0

# برای استفاده با authentication، URI را تغییر دهید:
# MONGODB_URI=mongodb://admin:password123@localhost:27017
```

### روش 3: MongoDB Atlas (Cloud - رایگان)

1. ثبت‌نام در https://www.mongodb.com/cloud/atlas
2. ایجاد یک Cluster رایگان
3. تنظیم IP Whitelist (اضافه کردن 0.0.0.0/0 برای دسترسی از همه جا)
4. ایجاد Database User
5. دریافت Connection String و قرار دادن در `.env`:

```env
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=trading_bot
```

## پیکربندی پروژه

### 1. نصب Dependencies

```bash
pip install -r requirements.txt
```

این دستور پکیج‌های زیر را نصب می‌کند:
- `motor==3.3.2` - MongoDB async driver
- `pymongo==4.6.1` - MongoDB sync driver

### 2. تنظیم متغیرهای محیطی

فایل `.env` را ایجاد کنید (یا از `.env.example` کپی کنید):

```bash
cp .env.example .env
```

سپس تنظیمات MongoDB را اضافه کنید:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=trading_bot
```

## ساختار دیتابیس

پروژه از Collections زیر استفاده می‌کند:

### 1. `user_settings` - تنظیمات کاربران
```javascript
{
  "_id": ObjectId,
  "user_id": 123456789,
  "notifications": true,
  "favorite_symbols": ["BTCUSDT", "ETHUSDT"],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 2. `alerts` - هشدارهای قیمت
```javascript
{
  "_id": ObjectId,
  "user_id": 123456789,
  "symbol": "BTCUSDT",
  "target_price": 50000.0,
  "condition": "above", // or "below"
  "created_at": ISODate
}
```

### 3. `portfolio` - پورتفولیو کاربران
```javascript
{
  "_id": ObjectId,
  "user_id": 123456789,
  "positions": [
    {
      "symbol": "BTCUSDT",
      "risk": 2.0,
      "entry_price": 45000.0,
      "size": 0.1,
      "opened_at": ISODate
    }
  ],
  "total_risk": 2.0,
  "winning_streak": 3,
  "losing_streak": 0,
  "recent_drawdown": 0.0,
  "updated_at": ISODate
}
```

### 4. `trading_history` - تاریخچه معاملات
```javascript
{
  "_id": ObjectId,
  "user_id": 123456789,
  "symbol": "BTCUSDT",
  "entry_price": 45000.0,
  "exit_price": 47000.0,
  "size": 0.1,
  "pnl": 200.0,
  "is_win": true,
  "risk": 2.0,
  "timestamp": ISODate
}
```

### 5. `performance` - آمار عملکرد روزانه
```javascript
{
  "_id": ObjectId,
  "user_id": 123456789,
  "date": "2024-10-26",
  "daily_pnl": 500.0,
  "trades_count": 5,
  "win_rate": 0.8,
  "timestamp": ISODate
}
```

## Indexes

پروژه به صورت خودکار Indexes زیر را ایجاد می‌کند:

```javascript
// user_settings
db.user_settings.createIndex({ "user_id": 1 }, { unique: true })

// alerts
db.alerts.createIndex({ "user_id": 1, "symbol": 1 })
db.alerts.createIndex({ "created_at": 1 })

// portfolio
db.portfolio.createIndex({ "user_id": 1 })
db.portfolio.createIndex({ "user_id": 1, "symbol": 1 })

// trading_history
db.trading_history.createIndex({ "user_id": 1, "timestamp": -1 })
db.trading_history.createIndex({ "symbol": 1 })
db.trading_history.createIndex({ "timestamp": 1 })

// performance
db.performance.createIndex({ "user_id": 1, "date": -1 })
```

## تست اتصال

برای تست اتصال به MongoDB:

```python
import asyncio
from src.database.connection import DatabaseManager

async def test_connection():
    db = DatabaseManager()
    await db.connect()
    print("✅ Connected to MongoDB successfully!")
    await db.disconnect()

asyncio.run(test_connection())
```

## مدیریت دیتابیس

### استفاده از MongoDB Compass (GUI)

1. دانلود از: https://www.mongodb.com/products/compass
2. اتصال با URI: `mongodb://localhost:27017`
3. مشاهده و مدیریت Collections

### استفاده از MongoDB Shell

```bash
# اتصال به MongoDB
mongosh

# انتخاب دیتابیس
use trading_bot

# مشاهده Collections
show collections

# Query نمونه
db.user_settings.find()
db.alerts.find({ user_id: 123456789 })
db.trading_history.find().sort({ timestamp: -1 }).limit(10)
```

## Backup و Restore

### Backup
```bash
# Backup کل دیتابیس
mongodump --db=trading_bot --out=/backup/

# Backup یک Collection خاص
mongodump --db=trading_bot --collection=trading_history --out=/backup/
```

### Restore
```bash
# Restore کل دیتابیس
mongorestore --db=trading_bot /backup/trading_bot/

# Restore یک Collection خاص
mongorestore --db=trading_bot --collection=trading_history /backup/trading_bot/trading_history.bson
```

## Migration از JSON به MongoDB

اگر قبلاً از فایل JSON استفاده می‌کردید:

```python
import json
import asyncio
from src.database.connection import DatabaseManager
from src.database.repositories import UserRepository, AlertRepository

async def migrate_from_json():
    # Load old data
    with open('data/bot_state.json', 'r') as f:
        old_data = json.load(f)
    
    # Connect to MongoDB
    db = DatabaseManager()
    await db.connect()
    
    user_repo = UserRepository(db)
    alert_repo = AlertRepository(db)
    
    # Migrate user settings
    for user_id, settings in old_data.get('user_settings', {}).items():
        await user_repo.create_user_settings(int(user_id), settings)
    
    # Migrate alerts
    for alert in old_data.get('price_alerts', []):
        await alert_repo.create_alert(alert)
    
    print("✅ Migration completed!")
    await db.disconnect()

asyncio.run(migrate_from_json())
```

## Troubleshooting

### خطای اتصال
```
pymongo.errors.ServerSelectionTimeoutError
```
**راه‌حل:**
- بررسی کنید MongoDB در حال اجرا است: `sudo systemctl status mongod`
- بررسی کنید پورت 27017 باز است: `sudo netstat -tulpn | grep 27017`
- بررسی کنید URI صحیح است

### خطای Authentication
```
pymongo.errors.OperationFailure: Authentication failed
```
**راه‌حل:**
- بررسی username و password در MONGODB_URI
- اطمینان از ایجاد user در MongoDB

### مشکل Performance
**راه‌حل:**
- بررسی Indexes با: `db.collection.getIndexes()`
- استفاده از Connection Pooling (پیش‌فرض در Motor)
- محدود کردن تعداد نتایج با `.limit()`

## امنیت

### توصیه‌های امنیتی:

1. **استفاده از Authentication:**
```bash
# ایجاد admin user
mongosh
use admin
db.createUser({
  user: "admin",
  pwd: "strong_password",
  roles: ["userAdminAnyDatabase", "readWriteAnyDatabase"]
})
```

2. **محدود کردن دسترسی شبکه:**
```bash
# ویرایش /etc/mongod.conf
net:
  bindIp: 127.0.0.1  # فقط localhost
```

3. **استفاده از SSL/TLS برای Production:**
```env
MONGODB_URI=mongodb://user:pass@host:27017/?ssl=true
```

4. **Backup منظم:**
- تنظیم cron job برای backup روزانه
- ذخیره backups در مکان امن

## منابع بیشتر

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor (Async Driver) Documentation](https://motor.readthedocs.io/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB University - Free Courses](https://university.mongodb.com/)
