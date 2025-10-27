"""
Advanced Smart Coin Selector - Enhanced with Market Regime Detection
تحلیل هوشمند پیشرفته با تشخیص وضعیت بازار
"""
import asyncio
import aiohttp
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
from src.core.config import Config
from src.data.providers import BinanceDataProvider
from src.analysis.technical import TechnicalAnalyzer


class AdvancedCoinSelector:
    """
    انتخابگر هوشمند پیشرفته با قابلیت:
    - تشخیص رنج و ترند
    - فیلتر ارزهای نامناسب
    - تحلیل عمیق‌تر بازار
    - گزارش‌دهی کامل و شفاف
    """
    
    def __init__(self, config: Config, provider: BinanceDataProvider, 
                 progress_callback: Optional[Callable] = None):
        self.config = config
        self.provider = provider
        self.session = None
        self.progress_callback = progress_callback
        
        # لیست ارزهای محبوب
        self.popular_coins = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
            "XRPUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT", "AVAXUSDT",
            "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "APTUSDT"
        ]
        
        # وزن‌های امتیازدهی پیشرفته
        self.weights = {
            "trend_quality": 0.25,      # کیفیت ترند (جدید)
            "volume_profile": 0.15,     # پروفایل حجم
            "volatility_health": 0.15,  # سلامت نوسان
            "momentum_strength": 0.15,  # قدرت مومنتوم
            "market_structure": 0.15,   # ساختار بازار
            "liquidity": 0.15           # نقدینگی
        }
        
        self.analysis_log = []
        self.rejected_coins = []  # ارزهای رد شده
        self.telegram_updates_enabled = True  # کنترل ارسال به تلگرام
    
    async def _get_session(self):
        """ایجاد session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """بستن session"""
        if self.session:
            await self.session.close()
    
    def _log(self, message: str, level: str = "INFO", send_to_telegram: bool = None):
        """ثبت لاگ و ارسال به callback"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.analysis_log.append(log_entry)
        
        # نمایش در کنسول
        emoji = "🔍" if level == "INFO" else "✅" if level == "SUCCESS" else "⚠️" if level == "WARNING" else "❌"
        print(f"{emoji} [{timestamp}] {message}")
        
        # ارسال به callback فقط برای پیام‌های مهم
        # send_to_telegram=True: حتماً ارسال شود
        # send_to_telegram=False: اصلاً ارسال نشود
        # send_to_telegram=None: فقط SUCCESS و ERROR ارسال شوند
        should_send = send_to_telegram if send_to_telegram is not None else (level in ["SUCCESS", "ERROR"])
        
        if self.progress_callback and should_send and self.telegram_updates_enabled:
            try:
                asyncio.create_task(self.progress_callback(f"{emoji} {message}"))
            except Exception:
                pass  # Ignore callback errors
    
    def _is_range_bound(self, df, ema_20, ema_50) -> Dict:
        """
        تشخیص رنج - ارزهایی که در رنج هستند نباید ترید شوند
        """
        # 1. فاصله EMA ها
        ema_distance = abs(ema_20.iloc[-1] - ema_50.iloc[-1]) / ema_50.iloc[-1]
        
        # 2. نوسان قیمت در 20 کندل اخیر
        high_20 = df['high'].tail(20).max()
        low_20 = df['low'].tail(20).min()
        range_pct = ((high_20 - low_20) / low_20) * 100
        
        # 3. تعداد کراس EMA در 50 کندل اخیر
        ema_20_tail = ema_20.tail(50)
        ema_50_tail = ema_50.tail(50)
        crosses = sum((ema_20_tail.shift(1) < ema_50_tail.shift(1)) & (ema_20_tail > ema_50_tail) |
                     (ema_20_tail.shift(1) > ema_50_tail.shift(1)) & (ema_20_tail < ema_50_tail))
        
        # تشخیص رنج
        is_range = (
            ema_distance < 0.02 or  # EMA ها خیلی نزدیک
            range_pct < 5 or         # نوسان کم
            crosses > 3              # کراس زیاد
        )
        
        return {
            "is_range": is_range,
            "ema_distance": ema_distance,
            "range_pct": range_pct,
            "ema_crosses": crosses,
            "reason": self._get_range_reason(ema_distance, range_pct, crosses)
        }
    
    def _get_range_reason(self, ema_dist, range_pct, crosses) -> str:
        """دلیل رنج بودن"""
        reasons = []
        if ema_dist < 0.02:
            reasons.append(f"EMA ها خیلی نزدیک ({ema_dist:.3f})")
        if range_pct < 5:
            reasons.append(f"نوسان کم ({range_pct:.1f}%)")
        if crosses > 3:
            reasons.append(f"کراس زیاد ({crosses})")
        return " | ".join(reasons) if reasons else "رنج"
    
    def _check_volume_health(self, df) -> Dict:
        """
        بررسی سلامت حجم معاملات
        """
        # حجم 24 ساعت اخیر
        volume_24h = df['volume'].tail(24).sum()
        avg_volume = df['volume'].tail(100).mean()
        
        # حجم دلاری
        quote_volume = (df['close'] * df['volume']).tail(24).sum()
        
        # ثبات حجم (انحراف معیار)
        volume_std = df['volume'].tail(50).std()
        volume_cv = volume_std / avg_volume if avg_volume > 0 else 0
        
        # حجم کافی؟
        is_healthy = (
            quote_volume > 10_000_000 and  # حداقل 10 میلیون دلار
            volume_cv < 2.0                 # انحراف معیار نسبی کمتر از 2
        )
        
        return {
            "is_healthy": is_healthy,
            "quote_volume_24h": quote_volume,
            "volume_consistency": 1 / (1 + volume_cv),  # نرمال‌سازی
            "avg_volume": avg_volume
        }
    
    def _check_volatility_health(self, df, atr) -> Dict:
        """
        بررسی سلامت نوسان - نوسان باید منطقی باشد
        """
        current_price = df['close'].iloc[-1]
        atr_value = atr.iloc[-1]
        
        # نوسان درصدی
        volatility_pct = (atr_value / current_price) * 100
        
        # سایه‌های کندل (Wicks)
        df_tail = df.tail(20)
        upper_wicks = ((df_tail['high'] - df_tail[['open', 'close']].max(axis=1)) / 
                      df_tail['close']) * 100
        lower_wicks = ((df_tail[['open', 'close']].min(axis=1) - df_tail['low']) / 
                      df_tail['close']) * 100
        
        avg_wick = (upper_wicks.mean() + lower_wicks.mean()) / 2
        
        # نوسان سالم؟
        is_healthy = (
            1.5 < volatility_pct < 8 and  # نوسان بین 1.5% تا 8%
            avg_wick < 3                   # سایه‌های کوچک
        )
        
        return {
            "is_healthy": is_healthy,
            "volatility_pct": volatility_pct,
            "avg_wick_pct": avg_wick,
            "reason": self._get_volatility_reason(volatility_pct, avg_wick)
        }
    
    def _get_volatility_reason(self, vol_pct, wick) -> str:
        """دلیل نوسان ناسالم"""
        if vol_pct < 1.5:
            return f"نوسان خیلی کم ({vol_pct:.2f}%)"
        elif vol_pct > 8:
            return f"نوسان خیلی زیاد ({vol_pct:.2f}%)"
        elif wick > 3:
            return f"سایه‌های بلند ({wick:.2f}%)"
        return "سالم"
    
    def _check_trend_quality(self, df, ema_20, ema_50, rsi) -> Dict:
        """
        بررسی کیفیت ترند
        """
        # جهت ترند
        is_uptrend = ema_20.iloc[-1] > ema_50.iloc[-1]
        
        # قدرت ترند (فاصله EMA)
        trend_strength = abs(ema_20.iloc[-1] - ema_50.iloc[-1]) / ema_50.iloc[-1]
        
        # ثبات ترند (تعداد کندل‌های همسو)
        if is_uptrend:
            consistent_candles = sum(df['close'].tail(10) > df['open'].tail(10))
        else:
            consistent_candles = sum(df['close'].tail(10) < df['open'].tail(10))
        
        # RSI در محدوده مناسب؟
        rsi_value = rsi.iloc[-1]
        rsi_healthy = 35 < rsi_value < 75
        
        # کیفیت ترند
        quality_score = 0
        if trend_strength > 0.03:  # ترند قوی
            quality_score += 0.4
        if consistent_candles >= 6:  # ثبات بالا
            quality_score += 0.3
        if rsi_healthy:  # RSI مناسب
            quality_score += 0.3
        
        return {
            "quality_score": quality_score,
            "is_uptrend": is_uptrend,
            "trend_strength": trend_strength,
            "consistent_candles": consistent_candles,
            "rsi_value": rsi_value,
            "is_quality_trend": quality_score > 0.6
        }
    
    def _check_market_structure(self, df) -> Dict:
        """
        بررسی ساختار بازار - Higher Highs / Lower Lows
        """
        highs = df['high'].tail(20)
        lows = df['low'].tail(20)
        
        # پیدا کردن قله‌ها و دره‌ها
        peaks = []
        troughs = []
        
        for i in range(1, len(highs) - 1):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                peaks.append(highs.iloc[i])
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                troughs.append(lows.iloc[i])
        
        # تشخیص ساختار
        structure_type = "NEUTRAL"
        if len(peaks) >= 2:
            if peaks[-1] > peaks[-2]:
                structure_type = "BULLISH_HH"  # Higher Highs
            elif peaks[-1] < peaks[-2]:
                structure_type = "BEARISH_LH"  # Lower Highs
        
        if len(troughs) >= 2:
            if troughs[-1] > troughs[-2]:
                structure_type += "_HL"  # Higher Lows
            elif troughs[-1] < troughs[-2]:
                structure_type += "_LL"  # Lower Lows
        
        # امتیاز ساختار
        structure_score = 0
        if "BULLISH_HH_HL" in structure_type:
            structure_score = 1.0  # ساختار صعودی کامل
        elif "BEARISH_LH_LL" in structure_type:
            structure_score = 0.3  # ساختار نزولی
        else:
            structure_score = 0.5  # ساختار نامشخص
        
        return {
            "structure_type": structure_type,
            "structure_score": structure_score,
            "peaks_count": len(peaks),
            "troughs_count": len(troughs)
        }
    
    async def analyze_coin_advanced(self, symbol: str) -> Optional[Dict]:
        """
        تحلیل پیشرفته یک ارز
        """
        self._log(f"🔍 شروع تحلیل پیشرفته {symbol}...")
        
        try:
            # دریافت داده
            df = await self.provider.fetch_ohlcv(symbol, "1h", limit=200)
            
            if df is None or len(df) < 100:
                self._log(f"❌ داده کافی برای {symbol} وجود ندارد", "ERROR")
                return None
            
            # محاسبه اندیکاتورها
            rsi = TechnicalAnalyzer.calculate_rsi(df)
            macd_data = TechnicalAnalyzer.calculate_macd(df)
            ema_20 = TechnicalAnalyzer.calculate_ema(df, 20)
            ema_50 = TechnicalAnalyzer.calculate_ema(df, 50)
            atr = TechnicalAnalyzer.calculate_atr(df)
            
            # بررسی‌های فیلتر
            self._log(f"  ├─ بررسی وضعیت رنج...", send_to_telegram=False)
            range_check = self._is_range_bound(df, ema_20, ema_50)
            
            if range_check['is_range']:
                reason = range_check['reason']
                self._log(f"  └─ ❌ {symbol} در رنج است: {reason}", "WARNING")
                self.rejected_coins.append({
                    "symbol": symbol,
                    "reason": f"رنج: {reason}",
                    "details": range_check
                })
                return None
            
            self._log(f"  ├─ بررسی سلامت حجم...", send_to_telegram=False)
            volume_check = self._check_volume_health(df)
            
            if not volume_check['is_healthy']:
                self._log(f"  └─ ❌ {symbol} حجم کافی ندارد", "WARNING")
                self.rejected_coins.append({
                    "symbol": symbol,
                    "reason": f"حجم ضعیف: ${volume_check['quote_volume_24h']/1e6:.1f}M",
                    "details": volume_check
                })
                return None
            
            self._log(f"  ├─ بررسی سلامت نوسان...", send_to_telegram=False)
            volatility_check = self._check_volatility_health(df, atr)
            
            if not volatility_check['is_healthy']:
                reason = volatility_check['reason']
                self._log(f"  └─ ⚠️ {symbol} نوسان ناسالم: {reason}", "WARNING", send_to_telegram=False)
                # نوسان ناسالم را رد نمی‌کنیم، فقط امتیاز کمتری می‌دهیم
            
            self._log(f"  ├─ بررسی کیفیت ترند...", send_to_telegram=False)
            trend_check = self._check_trend_quality(df, ema_20, ema_50, rsi)
            
            if not trend_check['is_quality_trend']:
                self._log(f"  └─ ⚠️ {symbol} ترند ضعیف (امتیاز: {trend_check['quality_score']:.2f})", "WARNING", send_to_telegram=False)
            
            self._log(f"  ├─ بررسی ساختار بازار...", send_to_telegram=False)
            structure_check = self._check_market_structure(df)
            
            self._log(f"  └─ ✅ {symbol} تمام فیلترها را گذراند", "SUCCESS")
            
            # محاسبه امتیاز نهایی
            current_price = float(df['close'].iloc[-1])
            
            metrics = {
                "trend_quality": trend_check['quality_score'],
                "volume_profile": volume_check['volume_consistency'],
                "volatility_health": 1.0 if volatility_check['is_healthy'] else 0.5,
                "momentum_strength": self._calculate_momentum(rsi, macd_data),
                "market_structure": structure_check['structure_score'],
                "liquidity": min(volume_check['quote_volume_24h'] / 100_000_000, 1.0)
            }
            
            # امتیاز نهایی
            final_score = sum(metrics[k] * self.weights[k] for k in metrics.keys())
            
            self._log(f"✅ امتیاز {symbol}: {final_score:.2%} | قیمت: ${current_price:.2f}", "SUCCESS")
            
            return {
                "symbol": symbol,
                "final_score": final_score,
                "current_price": current_price,
                "metrics": metrics,
                "checks": {
                    "range": range_check,
                    "volume": volume_check,
                    "volatility": volatility_check,
                    "trend": trend_check,
                    "structure": structure_check
                },
                "indicators": {
                    "rsi": float(rsi.iloc[-1]),
                    "macd": float(macd_data['value'].iloc[-1]),
                    "ema_20": float(ema_20.iloc[-1]),
                    "ema_50": float(ema_50.iloc[-1]),
                    "atr": float(atr.iloc[-1])
                }
            }
            
        except Exception as e:
            self._log(f"❌ خطا در تحلیل {symbol}: {str(e)}", "ERROR")
            return None
    
    def _calculate_momentum(self, rsi, macd_data) -> float:
        """محاسبه قدرت مومنتوم"""
        rsi_value = float(rsi.iloc[-1])
        macd_value = float(macd_data['value'].iloc[-1])
        
        # RSI Score
        if 45 <= rsi_value <= 65:
            rsi_score = 1.0
        elif 35 <= rsi_value <= 75:
            rsi_score = 0.7
        else:
            rsi_score = 0.3
        
        # MACD Score
        macd_score = 0.5 + (0.5 if macd_value > 0 else 0)
        
        return (rsi_score + macd_score) / 2
    
    async def find_best_coins(self, top_n: int = 5, custom_symbols: List[str] = None) -> List[Dict]:
        """پیدا کردن بهترین ارزها"""
        self._log("=" * 60)
        self._log("🚀 شروع تحلیل هوشمند پیشرفته", "SUCCESS")
        self._log("=" * 60)
        
        symbols = custom_symbols if custom_symbols else self.popular_coins
        self._log(f"📊 تعداد ارزها برای تحلیل: {len(symbols)}")
        
        # پاک کردن لیست رد شده‌ها
        self.rejected_coins = []
        
        # تحلیل همزمان
        tasks = [self.analyze_coin_advanced(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # فیلتر نتایج معتبر
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                valid_results.append(result)
        
        # مرتب‌سازی
        sorted_results = sorted(valid_results, key=lambda x: x['final_score'], reverse=True)
        top_coins = sorted_results[:top_n]
        
        self._log("=" * 60)
        self._log(f"✅ تحلیل کامل شد!", "SUCCESS")
        self._log(f"   ├─ {len(valid_results)} ارز مناسب یافت شد", "SUCCESS")
        self._log(f"   ├─ {len(self.rejected_coins)} ارز رد شد", "WARNING")
        self._log(f"   └─ {top_n} ارز برتر انتخاب شد", "SUCCESS")
        self._log("=" * 60)
        
        # نمایش ارزهای رد شده
        if self.rejected_coins:
            self._log("🚫 ارزهای رد شده:", "WARNING")
            for rejected in self.rejected_coins[:5]:
                self._log(f"   • {rejected['symbol']}: {rejected['reason']}", "WARNING")
        
        # نمایش نتایج
        for i, coin in enumerate(top_coins, 1):
            self._log(
                f"🏆 #{i} {coin['symbol']}: {coin['final_score']:.2%} | "
                f"${coin['current_price']:.2f} | RSI: {coin['indicators']['rsi']:.1f}",
                "SUCCESS"
            )
        
        return top_coins
    
    def get_analysis_log(self) -> List[Dict]:
        """دریافت لاگ تحلیل"""
        return self.analysis_log
    
    def get_rejected_coins(self) -> List[Dict]:
        """دریافت ارزهای رد شده"""
        return self.rejected_coins
    
    def clear_log(self):
        """پاک کردن لاگ"""
        self.analysis_log = []
        self.rejected_coins = []
