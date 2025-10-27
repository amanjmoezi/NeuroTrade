# 📋 CHANGELOG - Version 3.0

## تاریخ: 2025-10-26

### 🎯 تغییرات اصلی

این آپدیت سیستم معاملاتی را از نسخه 2.2 به **نسخه 3.0 (Advanced Strategic)** ارتقا می‌دهد.

---

## 🔧 تغییرات در `main.py`

### ✅ اضافه شده به `TechnicalAnalyzer`:

#### 1. **`calculate_adx()`** - محاسبه ADX برای قدرت روند
```python
@staticmethod
def calculate_adx(df: pd.DataFrame, period: int = 14) -> float
```
- محاسبه Average Directional Index
- استفاده برای تشخیص قدرت روند
- خروجی: عدد بین 0-100

#### 2. **`detect_market_regime()`** - تشخیص رژیم بازار
```python
@staticmethod
def detect_market_regime(df: pd.DataFrame, atr: float) -> Dict
```
**خروجی:**
```json
{
  "type": "TRENDING | RANGING | VOLATILE | TRANSITIONAL",
  "confidence": 0.85,
  "volatility_state": "LOW | NORMAL | HIGH | EXTREME",
  "trend_strength": 0.75
}
```

**منطق تشخیص:**
- **TRENDING**: ADX > 25 و Price Range Ratio > 15
- **RANGING**: ADX < 20 و Price Range Ratio < 10
- **VOLATILE**: ATR Percentile > 80
- **TRANSITIONAL**: سایر موارد

#### 3. **`calculate_order_flow()`** - تحلیل جریان سفارشات
```python
@staticmethod
def calculate_order_flow(df: pd.DataFrame) -> Dict
```
**خروجی:**
```json
{
  "bid_ask_imbalance": 0.65,
  "large_orders": [
    {"side": "BUY", "size": 1000000, "price": 45200}
  ],
  "aggressive_buy_ratio": 0.58,
  "order_book_depth": {
    "bid_depth_5": 5000000,
    "ask_depth_5": 3500000
  }
}
```

**روش محاسبه:**
- **Bid-Ask Imbalance**: نسبت کندل‌های صعودی به کل
- **Large Orders**: سفارشات با حجم > 2x میانگین
- **Order Book Depth**: حجم خرید/فروش بر اساس کندل‌ها

### ✅ اضافه شده به `Config`:

#### **Portfolio State Tracking**
```python
self.portfolio_state = {
    "open_positions": 0,
    "total_risk_exposure": 0.0,
    "winning_streak": 0,
    "recent_drawdown": 0.0
}
```
- قابلیت توسعه با دیتابیس
- فعلاً به صورت ساده در Config نگهداری می‌شود

### ✅ تغییرات در `MarketDataAggregator.aggregate_ict_data()`:

**فیلدهای جدید اضافه شده به خروجی:**
```python
data = {
    # ... فیلدهای قبلی ...
    "order_flow": order_flow,           # جدید
    "market_regime": market_regime,     # جدید
    "portfolio_state": self.config.portfolio_state  # جدید
}
```

---

## 🤖 تغییرات در `bot.py`

### ✅ آپدیت `_format_signal()`:

#### 1. **بخش Risk Metrics - نمایش اطلاعات جدید**

**امتیازهای تنظیم شده:**
```
امتیاز استراتژیک: 6.8/10
امتیاز تنظیم رژیم: 7.2/10        ← جدید
امتیاز تنظیم نوسان: 6.5/10       ← جدید
```

**رژیم بازار:**
```
🌐 رژیم بازار:                    ← جدید
• نوع: TRENDING
• اطمینان: 85%
• وضعیت نوسان: NORMAL
```

**تاثیر پورتفولیو:**
```
💼 تاثیر پورتفولیو:                ← جدید
• ریسک کل جدید: 4.2%
• استفاده از ریسک: 52.5%
• همبستگی: LOW
```

#### 2. **بخش Invalidation Conditions - کاملاً جدید**

```
🚫 شرایط ابطال

شکست ساختار: $109,200
• Break below recent swing low

محدودیت زمانی: 48 hours
آستانه حجم: If volume drops below 50% average for 4+ hours
تغییر رژیم: Exit if volatility spikes above 90th percentile
```

#### 3. **بخش Trade Management - بهبود یافته**

**Trailing Stop:**
```
🎯 استاپ دنباله‌دار:               ← جدید
• فعال‌سازی: TP2_HIT
• فاصله: 0.5_ATR
• روش: DYNAMIC_ATR_BASED
```

**Scale Out Plan:**
```
📉 برنامه خروج تدریجی:             ← جدید
• TP1: بستن 25% → MOVE_SL_TO_BREAKEVEN
• TP2: بستن 30% → MOVE_SL_TO_TP1
• TP3: بستن 25% → TRAIL_BY_0.5_ATR
```

**خروج اضطراری:**
```
خروج اضطراری: FLATTEN_ON_MAJOR_NEWS_OR_REGIME_CHANGE  ← جدید
```

#### 4. **بخش Persian Summary - کاملاً جدید**

```
📝 خلاصه فارسی

سیگنال: خرید (LONG)
درجه: درجه A - سیگنال قوی
ورود: 110450 دلار
حد ضرر: 109700 دلار (1.8%)
اهداف: 111200 / 111800 / 112500 / 113200
ریسک: 1.5% از سرمایه

دلیل: نقدینگی نزدیک + تغییر ساختار بازار + همسویی تایم فریم بالا

⚠️ هشدار: حجم معاملات پایین - با احتیاط وارد شوید
```

---

## 📊 مقایسه ورودی/خروجی

### ورودی به AI (Input):

#### ❌ قبلاً (v2.2):
```json
{
  "market_data": {...},
  "market_structure": {...},
  "liquidity": {...},
  "zones": {...},
  "indicators": {...},
  "volume": {...},
  "institutional": {...}
}
```

#### ✅ حالا (v3.0):
```json
{
  "market_data": {...},
  "market_structure": {...},
  "liquidity": {...},
  "zones": {...},
  "indicators": {...},
  "volume": {...},
  "institutional": {...},
  "order_flow": {                    // جدید
    "bid_ask_imbalance": 0.65,
    "large_orders": [...],
    "aggressive_buy_ratio": 0.58,
    "order_book_depth": {...}
  },
  "market_regime": {                 // جدید
    "type": "TRENDING",
    "confidence": 0.85,
    "volatility_state": "NORMAL",
    "trend_strength": 0.75
  },
  "portfolio_state": {               // جدید
    "open_positions": 2,
    "total_risk_exposure": 3.5,
    "winning_streak": 3,
    "recent_drawdown": 0.0
  }
}
```

### خروجی از AI (Output):

#### ❌ قبلاً (v2.2):
```json
{
  "signal": "LONG",
  "context": {...},
  "position": {...},
  "risk_metrics": {
    "strategic_score": 6.8,
    "signal_grade": "A",
    "confidence_percent": 75
  },
  "trade_management": {
    "breakeven_trigger": "TP1_HIT_OR_24H",
    "max_trade_duration": "48 hours"
  }
}
```

#### ✅ حالا (v3.0):
```json
{
  "signal": "LONG",
  "context": {...},
  "position": {...},
  "risk_metrics": {
    "strategic_score": 6.8,
    "regime_adjusted_score": 7.2,      // جدید
    "volatility_adjusted_score": 6.5,  // جدید
    "signal_grade": "A",
    "confidence_percent": 75,
    "market_regime": {                 // جدید
      "type": "TRENDING",
      "confidence": 0.85,
      "volatility_state": "NORMAL"
    },
    "portfolio_impact": {              // جدید
      "new_total_risk": 4.2,
      "risk_utilization": "52.5%",
      "position_correlation": "LOW"
    }
  },
  "invalidation_conditions": {        // جدید
    "structure_break": {
      "price_level": 109200,
      "description": "Break below recent swing low"
    },
    "time_limit": "48 hours",
    "volume_threshold": "...",
    "regime_change": "..."
  },
  "trade_management": {
    "breakeven_trigger": "TP1_HIT_OR_24H",
    "trailing_stop": {                 // جدید
      "activate_after": "TP2_HIT",
      "trail_distance": "0.5_ATR",
      "method": "DYNAMIC_ATR_BASED"
    },
    "scale_out_plan": [                // جدید
      {"trigger": "TP1", "close_percent": 25, "action": "MOVE_SL_TO_BREAKEVEN"},
      {"trigger": "TP2", "close_percent": 30, "action": "MOVE_SL_TO_TP1"}
    ],
    "max_trade_duration": "48 hours",
    "emergency_exit": "..."            // جدید
  },
  "persian_summary": {                 // جدید
    "signal": "خرید (LONG)",
    "grade": "درجه A - سیگنال قوی",
    "entry": "ورود: 110450 دلار",
    "stop_loss": "حد ضرر: 109700 دلار (1.8%)",
    "targets": "اهداف: 111200 / 111800 / 112500 / 113200",
    "risk": "ریسک: 1.5% از سرمایه",
    "reasoning": "نقدینگی نزدیک + تغییر ساختار بازار + همسویی تایم فریم بالا",
    "warning": "هشدار: حجم معاملات پایین - با احتیاط وارد شوید"
  }
}
```

---

## 🚀 نحوه استفاده

### تست سیستم:

```bash
# تست CLI
python main.py --cli --symbol BTCUSDT

# اجرای ربات تلگرام
python main.py
```

### بررسی خروجی:

فایل‌های خروجی در `data/output/` ذخیره می‌شوند:
```
data/output/
├── 01_market_BTCUSDT.json    # ورودی AI (با فیلدهای جدید)
└── 01_signal_BTCUSDT.json    # خروجی AI (با فیلدهای جدید)
```

---

## ⚠️ نکات مهم

### 1. سازگاری با نسخه قبل:
- کد قدیمی همچنان کار می‌کند
- فیلدهای جدید اختیاری هستند
- AI می‌تواند با یا بدون فیلدهای جدید کار کند

### 2. Portfolio State:
- فعلاً ساده است (در Config)
- برای production باید با دیتابیس یکپارچه شود
- می‌توان با Redis یا PostgreSQL توسعه داد

### 3. Order Flow:
- محاسبات ساده‌سازی شده است
- برای دقت بیشتر نیاز به WebSocket و Order Book واقعی
- برای تست و توسعه کافی است

### 4. Market Regime:
- بر اساس ADX و ATR محاسبه می‌شود
- دقت خوبی دارد اما قابل بهبود
- می‌توان با Machine Learning بهبود داد

---

## 📈 بهبودهای آینده (پیشنهادی)

1. **Portfolio Management با دیتابیس**
   - ذخیره تاریخچه معاملات
   - محاسبه Win Rate واقعی
   - Kelly Criterion با داده‌های واقعی

2. **Order Flow واقعی**
   - اتصال به WebSocket Binance
   - Order Book Depth واقعی
   - Trade Flow Analysis

3. **Backtesting Engine**
   - تست استراتژی روی داده‌های تاریخی
   - محاسبه متریک‌های عملکرد
   - بهینه‌سازی پارامترها

4. **Risk Management پیشرفته**
   - Correlation Analysis بین پوزیشن‌ها
   - Dynamic Position Sizing
   - Portfolio Heat Map

---

## ✅ چک‌لیست تست

- [x] `calculate_adx()` کار می‌کند
- [x] `detect_market_regime()` خروجی صحیح دارد
- [x] `calculate_order_flow()` داده‌های معتبر برمی‌گرداند
- [x] `aggregate_ict_data()` فیلدهای جدید را شامل می‌شود
- [x] `_format_signal()` فیلدهای جدید را نمایش می‌دهد
- [x] Persian Summary به درستی نمایش داده می‌شود
- [x] Invalidation Conditions نمایش داده می‌شود
- [x] Trade Management بهبود یافته نمایش داده می‌شود

---

## 🎉 نتیجه

سیستم معاملاتی با موفقیت به نسخه 3.0 ارتقا یافت و اکنون:

✅ **3 فیلد جدید** به ورودی AI اضافه شد  
✅ **5 بخش جدید** به خروجی AI اضافه شد  
✅ **نمایش فارسی** کامل پیاده‌سازی شد  
✅ **مدیریت ریسک** پیشرفته‌تر شد  
✅ **شرایط ابطال** واضح تعریف شد  

سیستم آماده تولید سیگنال‌های پیشرفته‌تر و دقیق‌تر است! 🚀
