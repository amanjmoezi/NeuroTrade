# 📁 ساختار پروژه - نسخه ماژولار

```
tarder/
├── 📂 src/                          # کدهای اصلی
│   ├── 📂 core/                     # هسته اصلی سیستم
│   │   ├── __init__.py
│   │   ├── config.py                # تنظیمات سیستم
│   │   └── models.py                # مدل‌های داده (dataclasses)
│   │
│   ├── 📂 data/                     # لایه داده
│   │   ├── __init__.py
│   │   ├── providers.py             # ارائه‌دهندگان داده (Binance)
│   │   └── aggregator.py            # جمع‌آوری و ترکیب داده
│   │
│   ├── 📂 analysis/                 # تحلیل‌گران
│   │   ├── __init__.py
│   │   ├── technical.py             # تحلیل تکنیکال (RSI, MACD, ATR, ADX)
│   │   ├── ict.py                   # تحلیل ICT (MSS, FVG, OB, Liquidity)
│   │   └── regime.py                # تشخیص رژیم بازار
│   │
│   ├── 📂 ai/                       # هوش مصنوعی
│   │   ├── __init__.py
│   │   └── advisor.py               # مشاور معاملاتی AI
│   │
│   ├── 📂 trading/                  # سیستم معاملاتی
│   │   ├── __init__.py
│   │   ├── system.py                # سیستم اصلی معاملات
│   │   └── portfolio.py             # مدیریت پورتفولیو
│   │
│   └── 📂 bot/                      # ربات تلگرام
│       ├── __init__.py
│       ├── handlers.py              # هندلرهای دستورات
│       ├── formatters.py            # فرمت‌کننده‌های پیام
│       ├── charts.py                # تولید نمودار
│       └── state.py                 # مدیریت وضعیت کاربران
│
├── 📂 init/                         # فایل‌های اولیه
│   ├── systemPrompt.txt             # پرامپت سیستم AI
│   └── systemPrompt_performance_tracking.txt
│
├── 📂 data/                         # داده‌ها
│   ├── output/                      # خروجی‌های تحلیل
│   └── bot_state.json               # وضعیت ربات
│
├── 📂 tests/                        # تست‌ها
│   ├── __init__.py
│   ├── test_technical.py
│   ├── test_ict.py
│   └── test_system.py
│
├── 📂 docs/                         # مستندات
│   ├── CHANGELOG_v3.0.md
│   └── API.md
│
├── main.py                          # نقطه ورود CLI
├── bot.py                           # نقطه ورود Bot
├── requirements.txt                 # وابستگی‌ها
├── .env                             # متغیرهای محیطی
├── .gitignore
└── README.md
```

## 📦 توضیح ماژول‌ها

### 🔹 `src/core/`
- **config.py**: کلاس Config با تمام تنظیمات
- **models.py**: dataclass‌ها (MSS, FVG, OrderBlock, LiquidityZone)

### 🔹 `src/data/`
- **providers.py**: BinanceDataProvider - دریافت داده از Binance
- **aggregator.py**: MarketDataAggregator - ترکیب و آماده‌سازی داده

### 🔹 `src/analysis/`
- **technical.py**: TechnicalAnalyzer - RSI, MACD, ATR, EMA, ADX
- **ict.py**: ICTAnalyzer - MSS, FVG, OrderBlock, Liquidity
- **regime.py**: RegimeDetector - تشخیص رژیم بازار و Order Flow

### 🔹 `src/ai/`
- **advisor.py**: AITradingAdvisor - ارتباط با OpenAI

### 🔹 `src/trading/`
- **system.py**: TradingSystem - هماهنگی کل سیستم
- **portfolio.py**: PortfolioManager - مدیریت پورتفولیو

### 🔹 `src/bot/`
- **handlers.py**: CommandHandlers - هندلرهای دستورات تلگرام
- **formatters.py**: MessageFormatters - فرمت پیام‌ها
- **charts.py**: ChartGenerator - تولید نمودار
- **state.py**: BotStateManager - مدیریت وضعیت

## 🎯 مزایا

✅ **Separation of Concerns**: هر ماژول مسئولیت مشخص دارد  
✅ **Testability**: تست هر بخش به صورت مستقل  
✅ **Maintainability**: نگهداری و توسعه آسان‌تر  
✅ **Reusability**: استفاده مجدد از ماژول‌ها  
✅ **Scalability**: افزودن قابلیت‌های جدید راحت‌تر  
