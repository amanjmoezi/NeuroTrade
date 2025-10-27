"""
Smart Coin Selector - Intelligent Analysis & Selection
تحلیل هوشمند و انتخاب بهترین ارز برای ترید
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from src.core.config import Config
from src.data.providers import BinanceDataProvider
from src.analysis.technical import TechnicalAnalyzer


class SmartCoinSelector:
    """
    انتخابگر هوشمند ارز با قابلیت:
    - تحلیل تکنیکال چندین ارز
    - جستجوی اخبار و ترندهای بازار
    - امتیازدهی هوشمند
    - گزارش شفاف از تمام مراحل
    """
    
    def __init__(self, config: Config, provider: BinanceDataProvider):
        self.config = config
        self.provider = provider
        self.session = None
        
        # لیست ارزهای محبوب برای تحلیل
        self.popular_coins = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
            "XRPUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT", "AVAXUSDT",
            "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "APTUSDT"
        ]
        
        # وزن‌های امتیازدهی
        self.weights = {
            "volume": 0.20,          # حجم معاملات
            "volatility": 0.15,      # نوسان قیمت
            "trend_strength": 0.20,  # قدرت ترند
            "momentum": 0.15,        # مومنتوم
            "market_sentiment": 0.15,# احساسات بازار
            "liquidity": 0.15        # نقدینگی
        }
        
        self.analysis_log = []  # لاگ شفاف تحلیل
    
    async def _get_session(self):
        """ایجاد session برای درخواست‌های HTTP"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """بستن session"""
        if self.session:
            await self.session.close()
    
    def _log(self, message: str, level: str = "INFO"):
        """ثبت لاگ شفاف"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.analysis_log.append(log_entry)
        
        # نمایش در کنسول
        emoji = "🔍" if level == "INFO" else "✅" if level == "SUCCESS" else "⚠️"
        print(f"{emoji} [{timestamp}] {message}")
    
    async def search_market_news(self, symbol: str) -> Dict:
        """
        جستجوی اخبار و اطلاعات بازار
        """
        self._log(f"جستجوی اخبار و اطلاعات {symbol}...")
        
        try:
            session = await self._get_session()
            
            # استخراج نام ارز (بدون USDT)
            coin_name = symbol.replace("USDT", "")
            
            # جستجوی ترندهای Google (از API عمومی)
            search_query = f"{coin_name} cryptocurrency news today"
            
            # در اینجا می‌توانید از API های مختلف استفاده کنید:
            # - CoinGecko API برای اطلاعات بازار
            # - NewsAPI برای اخبار
            # - Twitter API برای احساسات
            
            # برای مثال، از CoinGecko استفاده می‌کنیم
            coingecko_url = f"https://api.coingecko.com/api/v3/coins/{coin_name.lower()}"
            
            sentiment_score = 0.5  # پیش‌فرض خنثی
            news_count = 0
            
            try:
                async with session.get(coingecko_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # تحلیل داده‌های CoinGecko
                        sentiment_data = data.get('sentiment_votes_up_percentage', 50)
                        sentiment_score = sentiment_data / 100
                        
                        # تعداد توییت‌ها و اخبار
                        community_data = data.get('community_data', {})
                        news_count = community_data.get('twitter_followers', 0)
                        
                        self._log(f"✓ احساسات بازار {coin_name}: {sentiment_score:.2%} مثبت")
            except:
                self._log(f"⚠ نتوانستم اطلاعات CoinGecko را دریافت کنم", "WARNING")
            
            return {
                "sentiment_score": sentiment_score,
                "news_count": news_count,
                "search_query": search_query
            }
            
        except Exception as e:
            self._log(f"خطا در جستجوی اخبار: {str(e)}", "WARNING")
            return {"sentiment_score": 0.5, "news_count": 0, "search_query": ""}
    
    async def analyze_coin_metrics(self, symbol: str) -> Dict:
        """
        تحلیل معیارهای تکنیکال یک ارز
        """
        self._log(f"تحلیل معیارهای تکنیکال {symbol}...")
        
        try:
            # دریافت داده‌های قیمت
            df_1h = await self.provider.fetch_ohlcv(symbol, "1h", limit=100)
            
            if df_1h is None or len(df_1h) < 50:
                self._log(f"⚠ داده کافی برای {symbol} وجود ندارد", "WARNING")
                return None
            
            # محاسبه اندیکاتورها
            rsi = TechnicalAnalyzer.calculate_rsi(df_1h)
            macd_data = TechnicalAnalyzer.calculate_macd(df_1h)
            macd_line = macd_data['value']
            signal_line = macd_data['signal']
            ema_20 = TechnicalAnalyzer.calculate_ema(df_1h, 20)
            ema_50 = TechnicalAnalyzer.calculate_ema(df_1h, 50)
            atr = TechnicalAnalyzer.calculate_atr(df_1h)
            
            current_price = float(df_1h['close'].iloc[-1])
            
            # محاسبه معیارها
            metrics = {}
            
            # 1. حجم معاملات (Volume Score)
            avg_volume = float(df_1h['volume'].tail(20).mean())
            current_volume = float(df_1h['volume'].iloc[-1])
            volume_ratio = float(current_volume / avg_volume if avg_volume > 0 else 1)
            metrics['volume_score'] = min(volume_ratio / 2, 1.0)  # نرمال‌سازی
            
            # 2. نوسان (Volatility Score)
            atr_value = float(atr.iloc[-1])
            volatility = (atr_value / current_price) * 100
            metrics['volatility_score'] = min(volatility / 5, 1.0)  # نرمال‌سازی
            
            # 3. قدرت ترند (Trend Strength)
            ema_20_value = float(ema_20.iloc[-1])
            ema_50_value = float(ema_50.iloc[-1])
            trend_score = 0.5
            if ema_20_value > ema_50_value:
                trend_score = 0.7 + (0.3 * (ema_20_value - ema_50_value) / ema_50_value)
            else:
                trend_score = 0.3 - (0.3 * (ema_50_value - ema_20_value) / ema_50_value)
            metrics['trend_strength'] = max(0, min(trend_score, 1.0))
            
            # 4. مومنتوم (Momentum Score)
            rsi_value = float(rsi.iloc[-1])
            macd_value = float(macd_line.iloc[-1])
            
            # RSI بین 40-60 عالی، بیشتر یا کمتر ضعیف‌تر
            if 40 <= rsi_value <= 60:
                momentum_score = 0.8
            elif 30 <= rsi_value <= 70:
                momentum_score = 0.6
            else:
                momentum_score = 0.3
            
            # MACD مثبت = مومنتوم خوب
            if macd_value > 0:
                momentum_score += 0.2
            
            metrics['momentum_score'] = min(momentum_score, 1.0)
            
            # 5. نقدینگی (Liquidity Score)
            quote_volume = float((df_1h['close'] * df_1h['volume']).tail(24).sum())
            liquidity_score = min(quote_volume / 1_000_000_000, 1.0)  # نرمال‌سازی به میلیارد
            metrics['liquidity_score'] = liquidity_score
            
            # اطلاعات اضافی
            metrics['current_price'] = current_price
            metrics['rsi'] = rsi_value
            metrics['macd'] = macd_value
            metrics['volatility_pct'] = volatility
            metrics['volume_ratio'] = volume_ratio
            
            self._log(f"✓ تحلیل {symbol} کامل شد - RSI: {rsi_value:.1f}, حجم: {volume_ratio:.2f}x")
            
            return metrics
            
        except Exception as e:
            self._log(f"خطا در تحلیل {symbol}: {str(e)}", "WARNING")
            return None
    
    async def calculate_coin_score(self, symbol: str) -> Optional[Dict]:
        """
        محاسبه امتیاز نهایی یک ارز
        """
        self._log(f"محاسبه امتیاز کلی {symbol}...")
        
        # تحلیل تکنیکال
        metrics = await self.analyze_coin_metrics(symbol)
        if not metrics:
            return None
        
        # جستجوی اخبار و احساسات
        news_data = await self.search_market_news(symbol)
        metrics['market_sentiment'] = news_data['sentiment_score']
        
        # محاسبه امتیاز نهایی
        final_score = 0
        final_score += metrics.get('volume_score', 0) * self.weights['volume']
        final_score += metrics.get('volatility_score', 0) * self.weights['volatility']
        final_score += metrics.get('trend_strength', 0) * self.weights['trend_strength']
        final_score += metrics.get('momentum_score', 0) * self.weights['momentum']
        final_score += metrics.get('market_sentiment', 0.5) * self.weights['market_sentiment']
        final_score += metrics.get('liquidity_score', 0) * self.weights['liquidity']
        
        result = {
            "symbol": symbol,
            "final_score": final_score,
            "metrics": metrics,
            "news_data": news_data
        }
        
        self._log(f"✓ امتیاز نهایی {symbol}: {final_score:.2%}", "SUCCESS")
        
        return result
    
    async def find_best_coins(self, top_n: int = 5, custom_symbols: List[str] = None) -> List[Dict]:
        """
        پیدا کردن بهترین ارزها برای ترید
        
        Args:
            top_n: تعداد ارزهای برتر
            custom_symbols: لیست سفارشی ارزها (اختیاری)
        
        Returns:
            لیست ارزهای برتر با امتیازات
        """
        self._log("=" * 60)
        self._log("🚀 شروع تحلیل هوشمند ارزها", "SUCCESS")
        self._log("=" * 60)
        
        symbols = custom_symbols if custom_symbols else self.popular_coins
        self._log(f"تعداد ارزها برای تحلیل: {len(symbols)}")
        
        # تحلیل همزمان تمام ارزها
        tasks = [self.calculate_coin_score(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # فیلتر کردن نتایج معتبر
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._log(f"⚠ خطا در تحلیل {symbols[i]}: {str(result)}", "WARNING")
            elif isinstance(result, dict) and result is not None:
                valid_results.append(result)
            else:
                self._log(f"⚠ نتیجه نامعتبر برای {symbols[i]}", "WARNING")
        
        # مرتب‌سازی بر اساس امتیاز
        sorted_results = sorted(valid_results, key=lambda x: x['final_score'], reverse=True)
        top_coins = sorted_results[:top_n]
        
        self._log("=" * 60)
        self._log(f"✅ تحلیل کامل شد! {len(valid_results)} ارز تحلیل شد", "SUCCESS")
        self._log(f"🏆 {top_n} ارز برتر انتخاب شد", "SUCCESS")
        self._log("=" * 60)
        
        # نمایش نتایج
        for i, coin in enumerate(top_coins, 1):
            self._log(
                f"#{i} {coin['symbol']}: امتیاز {coin['final_score']:.2%} | "
                f"قیمت: ${coin['metrics']['current_price']:.2f} | "
                f"RSI: {coin['metrics']['rsi']:.1f}",
                "SUCCESS"
            )
        
        return top_coins
    
    def get_analysis_log(self) -> List[Dict]:
        """دریافت لاگ کامل تحلیل"""
        return self.analysis_log
    
    def clear_log(self):
        """پاک کردن لاگ"""
        self.analysis_log = []
    
    def format_analysis_report(self, top_coins: List[Dict]) -> str:
        """
        فرمت کردن گزارش تحلیل برای نمایش
        """
        report = "📊 گزارش تحلیل هوشمند ارزها\n"
        report += "=" * 50 + "\n\n"
        
        for i, coin in enumerate(top_coins, 1):
            metrics = coin['metrics']
            report += f"🏆 رتبه {i}: {coin['symbol']}\n"
            report += f"   امتیاز کلی: {coin['final_score']:.1%}\n"
            report += f"   💰 قیمت: ${metrics['current_price']:.2f}\n"
            report += f"   📊 RSI: {metrics['rsi']:.1f}\n"
            report += f"   📈 حجم: {metrics['volume_ratio']:.2f}x میانگین\n"
            report += f"   🎯 نوسان: {metrics['volatility_pct']:.2f}%\n"
            report += f"   💪 قدرت ترند: {metrics['trend_strength']:.1%}\n"
            report += f"   ⚡ مومنتوم: {metrics['momentum_score']:.1%}\n"
            report += f"   💧 نقدینگی: {metrics['liquidity_score']:.1%}\n"
            report += f"   😊 احساسات: {metrics['market_sentiment']:.1%}\n"
            report += "\n"
        
        report += "=" * 50 + "\n"
        report += f"⏰ زمان تحلیل: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        return report
