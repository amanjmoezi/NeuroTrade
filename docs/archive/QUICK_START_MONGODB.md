# شروع سریع با MongoDB

## نصب و راه‌اندازی در 5 دقیقه ⚡

### گام 1: نصب MongoDB

**Ubuntu/Debian:**
```bash
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

**با Docker (سریع‌ترین روش):**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:7.0
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

### گام 2: نصب Dependencies

```bash
pip install -r requirements.txt
```

این دستور `motor` و `pymongo` را نصب می‌کند.

### گام 3: تنظیم Environment Variables

فایل `.env` را ویرایش کنید:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=trading_bot
```

### گام 4: تست اتصال

```bash
python test_mongodb.py
```

اگر پیام زیر را دیدید، همه چیز آماده است:
```
✅ Connected to MongoDB successfully!
✅ All tests passed successfully!
🎉 MongoDB is ready to use!
```

### گام 5: اجرای Bot

```bash
python bot.py
```

## 🔄 Migration از JSON (اختیاری)

اگر قبلاً از فایل JSON استفاده می‌کردید:

```bash
python migrate_json_to_mongodb.py
```

این اسکریپت:
- ✅ داده‌های قدیمی را به MongoDB منتقل می‌کند
- ✅ Backup از فایل JSON می‌گیرد
- ✅ صحت migration را بررسی می‌کند

## 🆘 مشکل دارید؟

### MongoDB اجرا نمی‌شود؟
```bash
sudo systemctl status mongod
sudo systemctl start mongod
```

### خطای Connection؟
- بررسی کنید MongoDB روی پورت 27017 اجرا می‌شود
- بررسی کنید `MONGODB_URI` در `.env` صحیح است

### نیاز به راهنمای کامل؟
- [MONGODB_SETUP.md](./MONGODB_SETUP.md) - راهنمای کامل نصب
- [MONGODB_INTEGRATION.md](./MONGODB_INTEGRATION.md) - جزئیات فنی

## 📊 چه چیزی در MongoDB ذخیره می‌شود؟

- ✅ تنظیمات کاربران (notifications, favorite symbols)
- ✅ هشدارهای قیمت (price alerts)
- ✅ پورتفولیو و پوزیشن‌ها
- ✅ تاریخچه معاملات
- ✅ آمار عملکرد

## 🚀 مزایا

- **Persistence**: داده‌ها بعد از restart حفظ می‌شوند
- **Performance**: Indexes برای سرعت بالا
- **Scalability**: ذخیره میلیون‌ها رکورد
- **Analytics**: آمار و گزارش‌های پیشرفته

## ✅ تمام!

حالا می‌توانید از bot استفاده کنید. تمام داده‌ها به صورت خودکار در MongoDB ذخیره می‌شوند.
