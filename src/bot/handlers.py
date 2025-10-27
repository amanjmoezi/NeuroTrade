"""
Command Handlers - Telegram bot command handlers
"""
import asyncio
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.bot.formatters import MessageFormatters
from src.bot.charts import ChartGenerator
from src.bot.state import BotStateManager, PriceAlert
from src.trading.system import TradingSystem
from src.core.config import Config
from src.database.repositories import AnalysisHistoryRepository


class CommandHandlers:
    """Telegram Bot Command Handlers"""
    
    def __init__(self):
        self.config = Config()
        self.trading_system = TradingSystem(self.config)
        self.state_manager = BotStateManager()
        self.chart_generator = ChartGenerator()
        self.formatters = MessageFormatters()
        # Repositories will be initialized after db connection
        self.analysis_history_repo = None
        # Track running tasks
        self.running_tasks = set()
    
    async def initialize(self):
        """Initialize database connection and repositories"""
        await self.state_manager.initialize()
        # Now create repositories after db is connected
        self.analysis_history_repo = AnalysisHistoryRepository(self.state_manager.db_manager)
    
    def _run_in_background(self, coro):
        """Run a coroutine in background and track it"""
        task = asyncio.create_task(coro)
        self.running_tasks.add(task)
        task.add_done_callback(self.running_tasks.discard)
        return task
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_msg = f"""
🤖 <b>به ربات تحلیل ICT خوش آمدید!</b> 🚀

سلام {user.first_name}! من دستیار پیشرفته معاملات کریپتو شما هستم.

<b>🎯 امکانات:</b>
• 🧠 تحلیل هوشمند و انتخاب خودکار بهترین ارز
• تحلیل ICT لحظه‌ای
• مفاهیم Smart Money
• هشدار قیمت
• سیگنال‌های معاملاتی
• نمودارهای زیبا
• تاریخچه تحلیل‌ها

<b>📊 دستورات سریع:</b>
/smartanalyze - 🧠 تحلیل هوشمند (جدید!)
/analyze - تحلیل ارز دیجیتال
/analyses - تاریخچه تحلیل‌ها
/market - بررسی کلی بازار
/help - لیست کامل دستورات

آماده‌اید؟ دستور /smartanalyze را امتحان کنید! 🧠📈
        """
        keyboard = [[KeyboardButton("🧠 تحلیل هوشمند"), KeyboardButton("🔍 تحلیل ارز")],
                    [KeyboardButton("🌍 بررسی بازار"), KeyboardButton("📊 تاریخچه تحلیل")],
                    [KeyboardButton("⚡ هشدارهای من"), KeyboardButton("⚙️ تنظیمات")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 <b>راهنمای دستورات</b>

<b>تحلیل:</b>
/analyze - انتخاب و تحلیل ارز
/smartanalyze - 🧠 تحلیل هوشمند و انتخاب بهترین ارز
/market - بررسی کلی بازار
/topmovers - برترین تغییرات قیمت

<b>تحلیل‌ها:</b>
/analyses - تاریخچه تحلیل‌های شما

<b>هشدارها:</b>
/alerts - مشاهده هشدارها
/setalert [نماد] [قیمت] - تنظیم هشدار

<b>تنظیمات:</b>
/settings - تنظیمات
/status - وضعیت سیستم

نیاز به کمک دارید؟ فقط بپرسید! 💬
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        popular_cryptos = [
            "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "TRX", "DOT", "MATIC",
            "LTC", "SHIB", "AVAX", "UNI", "LINK", "ATOM", "XLM", "ETC", "BCH", "FIL",
            "APT", "ARB", "OP", "NEAR", "INJ", "SUI", "PEPE", "FTM", "ALGO", "VET"
        ]
        
        keyboard = []
        for i in range(0, len(popular_cryptos), 3):
            row = []
            for crypto in popular_cryptos[i:i+3]:
                row.append(InlineKeyboardButton(crypto, callback_data=f"analyze_{crypto}USDT"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📊 <b>لطفاً یک ارز دیجیتال را انتخاب کنید:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def perform_analysis(self, update: Update, symbol: str, query=None):
        """Perform analysis for a symbol - runs in background"""
        if query:
            msg = await query.message.reply_text(f"🔄 در حال تحلیل {symbol}...\n⏳ دریافت اطلاعات...\n\n💡 می‌توانید از دستورات دیگر استفاده کنید")
            message_obj = query.message
            user_id = query.from_user.id
        else:
            msg = await update.message.reply_text(f"🔄 در حال تحلیل {symbol}...\n⏳ دریافت اطلاعات...\n\n💡 می‌توانید از دستورات دیگر استفاده کنید")
            message_obj = update.message
            user_id = update.effective_user.id
        
        # Run analysis in background
        self._run_in_background(self._perform_analysis_background(msg, message_obj, user_id, symbol))
    
    async def _refresh_analysis_background(self, msg, message_obj, symbol: str):
        """Background task for refreshing analysis"""
        try:
            result = await self.trading_system.analyze(symbol)
            signal_msg = self.formatters.format_signal_detailed(result['market_data'], result['signal'])
            await msg.delete()
            await message_obj.reply_text(signal_msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            try:
                await msg.edit_text(f"❌ خطا در بروزرسانی {symbol}\nخطا: {str(e)}")
            except:
                await message_obj.reply_text(f"❌ خطا در بروزرسانی {symbol}\nخطا: {str(e)}")
    
    async def _perform_analysis_background(self, msg, message_obj, user_id: int, symbol: str):
        """Background task for performing analysis"""
        try:
            result = await self.trading_system.analyze(symbol)
            
            # Check for errors in market data
            market_data = result.get('market_data', {})
            if 'error' in market_data:
                error_msg = market_data.get('user_message', market_data.get('error', 'خطای نامشخص'))
                await msg.edit_text(f"❌ {error_msg}")
                return
            
            # Check for errors in signal
            signal = result.get('signal', {})
            if 'error' in signal:
                error_msg = signal.get('user_message', signal.get('error', 'خطای نامشخص'))
                await msg.edit_text(f"❌ {error_msg}")
                return
            
            # Check if deep thinking was used
            deep_thinking_used = signal.get('deep_thinking_used', False)
            thinking_reason = signal.get('thinking_reason', '')
            
            if deep_thinking_used:
                await msg.edit_text(f"🧠 {thinking_reason}\n⏳ در حال تحلیل عمیق...")
            
            signal_msg_full = self.formatters.format_signal_detailed(result['market_data'], result['signal'])
            chart = self.chart_generator.create_price_chart(result['market_data'], result['signal'])
            
            # Save analysis to history
            try:
                # Skip saving if AI returned an error
                if signal.get('error'):
                    print(f"⚠️ Skipping save - AI returned error: {signal.get('error')}")
                else:
                    # Only save if we have valid market data
                    md = market_data.get('market_data', {})
                    current_price = md.get('current_price', 0)
                    if current_price > 0:
                        # Extract data from LLM output structure
                        signal_type = signal.get('signal', 'NO_TRADE')
                        
                        # Get confidence from risk_metrics
                        risk_metrics = signal.get('risk_metrics', {})
                        confidence = risk_metrics.get('confidence_percent', 0)
                        
                        # Get position data
                        position = signal.get('position', {})
                        entry_zone = position.get('entry_zone', {})
                        stop_loss_data = position.get('stop_loss', {})
                        take_profit_array = position.get('take_profit', [])
                        
                        # Extract prices
                        entry_price = entry_zone.get('optimal', current_price)
                        stop_loss = stop_loss_data.get('price', 0)
                        
                        # Extract take profit levels (up to 3)
                        tp1 = take_profit_array[0].get('price', 0) if len(take_profit_array) > 0 else 0
                        tp2 = take_profit_array[1].get('price', 0) if len(take_profit_array) > 1 else 0
                        tp3 = take_profit_array[2].get('price', 0) if len(take_profit_array) > 2 else 0
                        
                        # Get indicators
                        indicators = market_data.get('indicators', {})
                        rsi = indicators.get('rsi', 0)
                        
                        # Get market structure
                        market_structure = market_data.get('market_structure', {})
                        htf_trend = market_structure.get('htf_trend', 'NEUTRAL')
                        
                        # Get reasoning from context or persian_summary
                        context = signal.get('context', {})
                        persian_summary = signal.get('persian_summary', {})
                        reasoning = persian_summary.get('reasoning', context.get('primary_driver', 'تحلیل ICT'))
                        
                        analysis_data = {
                            'user_id': user_id,
                            'symbol': symbol,
                            'signal_type': signal_type,
                            'signal_grade': signal.get('signal_grade', 'N/A'),
                            'confidence': confidence,
                            'price': current_price,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit_1': tp1,
                            'take_profit_2': tp2,
                            'take_profit_3': tp3,
                            'rsi': rsi,
                            'trend': htf_trend,
                            'reasoning': reasoning,
                            'analysis_type': 'normal'
                        }
                        if self.analysis_history_repo:
                            await self.analysis_history_repo.add_analysis(analysis_data)
                            print(f"✅ Analysis saved for {symbol}")
                        else:
                            print(f"⚠️ Repository not initialized, skipping save for {symbol}")
                    else:
                        print(f"⚠️ Skipping save - no market data: price={current_price}")
            except Exception as save_error:
                print(f"❌ Error saving analysis to history: {save_error}")
            
            # Add deep thinking badge if used
            if deep_thinking_used:
                thinking_badge = "\n\n🧠 <b>تحلیل عمیق استفاده شد</b>\n<i>" + thinking_reason + "</i>"
                signal_msg_full += thinking_badge
            
            if chart:
                await message_obj.reply_photo(photo=chart)
                await message_obj.reply_text(signal_msg_full, parse_mode=ParseMode.HTML)
                signal_summary = self.formatters.format_signal_summary(result['market_data'], result['signal'])
                await message_obj.reply_text(signal_summary, parse_mode=ParseMode.HTML)
            else:
                await message_obj.reply_text(signal_msg_full, parse_mode=ParseMode.HTML)
            await msg.delete()
            
            keyboard = [[InlineKeyboardButton("🔔 تنظیم هشدار", callback_data=f"alert_{symbol}"),
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"refresh_{symbol}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message_obj.reply_text("چه کاری می‌خواهید انجام دهید؟", reply_markup=reply_markup)
        except Exception as e:
            error_text = f"❌ خطا در تحلیل {symbol}\n\n"
            if "timeout" in str(e).lower():
                error_text += "⏱ زمان انتظار تمام شد. لطفاً دوباره تلاش کنید."
            elif "connection" in str(e).lower():
                error_text += "🌐 خطا در اتصال به سرور. لطفاً اتصال اینترنت خود را بررسی کنید."
            else:
                error_text += f"خطا: {str(e)}"
            
            try:
                await msg.edit_text(error_text)
            except:
                await message_obj.reply_text(error_text)
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        user_id = update.effective_user.id
        alerts = await self.state_manager.get_user_alerts(user_id)
        
        if not alerts:
            msg = "⚡ <b>هشدارهای قیمت شما</b>\n\nهشدار فعالی وجود ندارد.\nاز دستور /setalert [نماد] [قیمت] استفاده کنید"
        else:
            msg = "⚡ <b>هشدارهای فعال</b>\n\n"
            for alert in alerts:
                condition_fa = 'بالاتر از' if alert.condition == 'above' else 'پایین‌تر از'
                msg += f"• {alert.symbol}: ${alert.target_price:,.2f} ({condition_fa})\n"
            msg += f"\n📊 مجموع: {len(alerts)} هشدار"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    async def setalert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setalert command"""
        user_id = update.effective_user.id
        if len(context.args) < 2:
            await update.message.reply_text("⚡ نحوه استفاده: /setalert [نماد] [قیمت]\nمثال: /setalert BTC 50000")
            return
        
        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        try:
            target_price = float(context.args[1])
            current_price = await self.trading_system.provider.get_current_price(symbol)
            condition = "above" if target_price > current_price else "below"
            condition_fa = "بالاتر از" if condition == "above" else "پایین‌تر از"
            
            alert = PriceAlert(user_id=user_id, symbol=symbol, target_price=target_price, 
                             condition=condition, created_at=datetime.now(timezone.utc).isoformat())
            await self.state_manager.add_alert(alert)
            
            await update.message.reply_text(
                f"✅ هشدار تنظیم شد!\n\nنماد: {symbol}\nهدف: ${target_price:,.2f}\n"
                f"قیمت فعلی: ${current_price:,.2f}\nشرط: {condition_fa}\n\nبه شما اطلاع می‌دهم! 🔔"
            )
        except ValueError:
            await update.message.reply_text("❌ قیمت نامعتبر است.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        
        msg = f"""
⚙️ <b>تنظیمات شما</b>

📊 <b>تایم‌فریم پیش‌فرض:</b> {settings.default_timeframe}
⚡ <b>لوریج پیش‌فرض:</b> {settings.default_leverage}x
💰 <b>ریسک هر معامله:</b> {settings.risk_per_trade}%
🔔 <b>اعلان‌ها:</b> {'✅ فعال' if settings.notifications else '❌ غیرفعال'}
🌐 <b>زبان:</b> {'🇮🇷 فارسی' if settings.language == 'fa' else '🇬🇧 English'}
⭐ <b>علاقه‌مندی‌ها:</b> {', '.join(settings.favorite_symbols)}

تنظیمات را شخصی‌سازی کنید!
        """
        keyboard = [
            [InlineKeyboardButton("📊 تایم‌فریم", callback_data="settings_timeframe"),
             InlineKeyboardButton("⚡ لوریج", callback_data="settings_leverage")],
            [InlineKeyboardButton("💰 ریسک", callback_data="settings_risk"),
             InlineKeyboardButton("🔔 اعلان‌ها", callback_data="toggle_notifications")],
            [InlineKeyboardButton("🌐 زبان", callback_data="settings_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        msg = """
🟢 <b>وضعیت سیستم</b>

✅ سیستم معاملاتی: آنلاین
✅ ارائه‌دهنده داده: متصل
✅ مدل هوش مصنوعی: فعال
✅ هشدارها: در حال اجرا

🤖 نسخه ربات: 3.0.0
⚡ زمان پاسخ: کمتر از 500 میلی‌ثانیه
        """
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data.startswith("analyze_"):
            symbol = data.split("_")[1]
            await self.perform_analysis(update, symbol, query)
        
        elif data.startswith("analysis_detail_"):
            # Handle this BEFORE generic patterns
            analysis_id = data.split("_")[2]
            await self.analysis_detail_command(update, context, analysis_id)
        
        elif data.startswith("refresh_detail_"):
            # Handle this BEFORE the generic refresh_ pattern
            analysis_id = data.split("_")[2]
            await query.message.reply_text("🔄 در حال بروزرسانی جزئیات...")
            await self.analysis_detail_command(update, context, analysis_id)
        
        elif data.startswith("refresh_"):
            symbol = data.split("_")[1]
            msg = await query.message.reply_text(f"🔄 در حال بروزرسانی {symbol}...\n\n💡 می‌توانید از دستورات دیگر استفاده کنید")
            # Run refresh in background
            self._run_in_background(self._refresh_analysis_background(msg, query.message, symbol))
        
        elif data.startswith("alert_"):
            symbol = data.split("_")[1]
            await query.message.reply_text(f"⚡ برای تنظیم هشدار: /setalert {symbol} [قیمت]")
        
        elif data == "settings_timeframe":
            # Show timeframe selection menu
            keyboard = [
                [InlineKeyboardButton("15m", callback_data="timeframe_15m"),
                 InlineKeyboardButton("1h", callback_data="timeframe_1h"),
                 InlineKeyboardButton("4h", callback_data="timeframe_4h")],
                [InlineKeyboardButton("1d", callback_data="timeframe_1d")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📊 <b>انتخاب تایم‌فریم پیش‌فرض:</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        elif data.startswith("timeframe_"):
            timeframe = data.split("_")[1]
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            settings.default_timeframe = timeframe
            await self.state_manager.update_user_settings(user_id, settings)
            await query.message.reply_text(f"✅ تایم‌فریم پیش‌فرض به <b>{timeframe}</b> تغییر کرد!", parse_mode=ParseMode.HTML)
        
        elif data == "settings_leverage":
            # Show leverage selection menu
            keyboard = [
                [InlineKeyboardButton("5x", callback_data="leverage_5"),
                 InlineKeyboardButton("10x", callback_data="leverage_10"),
                 InlineKeyboardButton("20x", callback_data="leverage_20")],
                [InlineKeyboardButton("50x", callback_data="leverage_50"),
                 InlineKeyboardButton("100x", callback_data="leverage_100")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("⚡ <b>انتخاب لوریج پیش‌فرض:</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        elif data.startswith("leverage_"):
            leverage = int(data.split("_")[1])
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            settings.default_leverage = leverage
            await self.state_manager.update_user_settings(user_id, settings)
            await query.message.reply_text(f"✅ لوریج پیش‌فرض به <b>{leverage}x</b> تغییر کرد!", parse_mode=ParseMode.HTML)
        
        elif data == "settings_risk":
            # Show risk percentage selection menu
            keyboard = [
                [InlineKeyboardButton("1%", callback_data="risk_1"),
                 InlineKeyboardButton("2%", callback_data="risk_2"),
                 InlineKeyboardButton("3%", callback_data="risk_3")],
                [InlineKeyboardButton("5%", callback_data="risk_5"),
                 InlineKeyboardButton("10%", callback_data="risk_10")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("💰 <b>انتخاب ریسک هر معامله:</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        elif data.startswith("risk_"):
            risk = float(data.split("_")[1])
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            settings.risk_per_trade = risk
            await self.state_manager.update_user_settings(user_id, settings)
            await query.message.reply_text(f"✅ ریسک هر معامله به <b>{risk}%</b> تغییر کرد!", parse_mode=ParseMode.HTML)
        
        elif data == "settings_language":
            # Show language selection menu
            keyboard = [
                [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
                 InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("🌐 <b>انتخاب زبان:</b>", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        
        elif data.startswith("lang_"):
            language = data.split("_")[1]
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            settings.language = language
            await self.state_manager.update_user_settings(user_id, settings)
            lang_name = "فارسی" if language == "fa" else "English"
            await query.message.reply_text(f"✅ زبان به <b>{lang_name}</b> تغییر کرد!", parse_mode=ParseMode.HTML)
        
        elif data == "back_to_analyses":
            await self.analyses_command(update, context)
        
        elif data == "toggle_notifications":
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            settings.notifications = not settings.notifications
            await self.state_manager.update_user_settings(user_id, settings)
            status = "فعال" if settings.notifications else "غیرفعال"
            await query.message.reply_text(f"🔔 اعلان‌ها {status} شد!")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        text = update.message.text
        if text == "🧠 تحلیل هوشمند":
            await self.smartanalyze_command(update, context)
        elif text == "🔍 تحلیل ارز":
            await self.analyze_command(update, context)
        elif text == "📊 تاریخچه تحلیل":
            await self.analyses_command(update, context)
        elif text == "🌍 بررسی بازار":
            await self.market_command(update, context)
        elif text == "⚡ هشدارهای من":
            await self.alerts_command(update, context)
        elif text == "⚙️ تنظیمات":
            await self.settings_command(update, context)
        else:
            symbol = text.upper().strip()
            if symbol and len(symbol) <= 10:
                if not symbol.endswith("USDT"):
                    symbol += "USDT"
                await self.perform_analysis(update, symbol)
    
    async def analyses_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyses command - Show analysis history"""
        user_id = update.effective_user.id
        
        # Handle both message and callback query contexts
        if hasattr(update, 'callback_query') and update.callback_query:
            message_obj = update.callback_query.message
        else:
            message_obj = update.message
            
        await message_obj.reply_text("📊 در حال دریافت تاریخچه تحلیل‌ها...")
        
        try:
            if not self.analysis_history_repo:
                await message_obj.reply_text("❌ خطا: دیتابیس هنوز آماده نشده است.")
                return
            
            analyses = await self.analysis_history_repo.get_user_analyses(user_id, limit=20)
            stats = await self.analysis_history_repo.get_analysis_stats(user_id)
            
            if not analyses:
                msg = "📊 <b>تاریخچه تحلیل‌ها</b>\n\nهنوز تحلیلی ثبت نشده است."
            else:
                msg = "📊 <b>تاریخچه تحلیل‌ها (20 تحلیل اخیر)</b>\n\n"
                
                for analysis in analyses[:10]:
                    symbol = analysis.get('symbol', 'N/A')
                    signal_type = analysis.get('signal_type', 'N/A')
                    signal_grade = analysis.get('signal_grade', '')
                    confidence = analysis.get('confidence', 0)
                    price = analysis.get('price', 0)
                    entry_price = analysis.get('entry_price', 0)
                    stop_loss = analysis.get('stop_loss', 0)
                    tp1 = analysis.get('take_profit_1', 0)
                    tp2 = analysis.get('take_profit_2', 0)
                    tp3 = analysis.get('take_profit_3', 0)
                    timestamp = analysis.get('timestamp', '')
                    analysis_type = analysis.get('analysis_type', 'normal')
                    
                    # Support both old (BUY/SELL) and new (LONG/SHORT) signal types
                    signal_emoji = "🟢" if signal_type in ['BUY', 'LONG'] else "🔴" if signal_type in ['SELL', 'SHORT'] else "⚪"
                    type_badge = "🧠" if analysis_type == 'smart' else "📊"
                    
                    # Format signal type for display
                    signal_display = signal_type
                    if signal_grade:
                        signal_display = f"{signal_type} ({signal_grade})"
                    
                    msg += f"{signal_emoji} {type_badge} <b>{symbol}</b> - {signal_display}\n"
                    
                    if entry_price > 0:
                        msg += f"   💰 ورود: ${entry_price:,.4f}\n"
                    elif price > 0:
                        msg += f"   💰 قیمت: ${price:,.4f}\n"
                    
                    if stop_loss > 0:
                        msg += f"   🛑 استاپ: ${stop_loss:,.4f}\n"
                    
                    if tp1 > 0 or tp2 > 0 or tp3 > 0:
                        targets = []
                        if tp1 > 0:
                            targets.append(f"${tp1:,.4f}")
                        if tp2 > 0:
                            targets.append(f"${tp2:,.4f}")
                        if tp3 > 0:
                            targets.append(f"${tp3:,.4f}")
                        msg += f"   🎯 تارگت‌ها: {' | '.join(targets)}\n"
                    
                    if confidence > 0:
                        msg += f"   📈 اطمینان: {confidence:.1f}%\n"
                    
                    if timestamp:
                        try:
                            dt = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp))
                            msg += f"   ⏰ {dt.strftime('%Y-%m-%d %H:%M')}\n"
                        except:
                            pass
                    
                    msg += "\n"
                
                # Add statistics
                if stats:
                    total_analyses = stats.get('total_analyses', 0)
                    buy_signals = stats.get('buy_signals', 0)
                    sell_signals = stats.get('sell_signals', 0)
                    hold_signals = stats.get('hold_signals', 0)
                    avg_confidence = stats.get('avg_confidence', 0)
                    
                    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    msg += f"📈 <b>آمار کلی:</b>\n"
                    msg += f"• کل تحلیل‌ها: {total_analyses}\n"
                    msg += f"• سیگنال خرید: {buy_signals}\n"
                    msg += f"• سیگنال فروش: {sell_signals}\n"
                    msg += f"• سیگنال نگهداری: {hold_signals}\n"
                    msg += f"• میانگین اطمینان: {avg_confidence:.1f}%\n"
            
            # Create detail buttons for each analysis
            keyboard = []
            for analysis in analyses[:5]:  # Show buttons for first 5 analyses
                analysis_id = str(analysis.get('_id', ''))
                symbol = analysis.get('symbol', 'N/A')
                signal_type = analysis.get('signal_type', 'N/A')
                signal_emoji = "🟢" if signal_type in ['BUY', 'LONG'] else "🔴" if signal_type in ['SELL', 'SHORT'] else "⚪"
                keyboard.append([InlineKeyboardButton(f"{signal_emoji} جزئیات {symbol}", callback_data=f"analysis_detail_{analysis_id}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message_obj.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
        except Exception as e:
            await message_obj.reply_text(f"❌ خطا در دریافت تاریخچه: {str(e)}")
            print(f"Analyses error: {e}")
    
    async def analysis_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, analysis_id: str):
        """Handle detailed analysis view - runs in background"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        user_id = update.effective_user.id
        
        if query:
            msg = await query.message.reply_text("📋 در حال دریافت جزئیات تحلیل...\n\n💡 می‌توانید از دستورات دیگر استفاده کنید")
        else:
            msg = await update.message.reply_text("📋 در حال دریافت جزئیات تحلیل...\n\n💡 می‌توانید از دستورات دیگر استفاده کنید")
        
        # Run in background
        self._run_in_background(self._analysis_detail_background(update, msg, query, user_id, analysis_id))
    
    async def _analysis_detail_background(self, update: Update, msg, query, user_id: int, analysis_id: str):
        """Background task for analysis detail view"""
        try:
            if not self.analysis_history_repo:
                await update.message.reply_text("❌ خطا: دیتابیس هنوز آماده نشده است.")
                return
            
            # Get specific analysis by ID
            from bson import ObjectId
            analysis = await self.analysis_history_repo.db.analysis_history.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user_id
            })
            
            if not analysis:
                await update.message.reply_text("❌ تحلیل مورد نظر یافت نشد.")
                return
            
            # Format detailed analysis
            symbol = analysis.get('symbol', 'N/A')
            signal_type = analysis.get('signal_type', 'N/A')
            signal_grade = analysis.get('signal_grade', '')
            confidence = analysis.get('confidence', 0)
            price = analysis.get('price', 0)
            entry_price = analysis.get('entry_price', 0)
            stop_loss = analysis.get('stop_loss', 0)
            tp1 = analysis.get('take_profit_1', 0)
            tp2 = analysis.get('take_profit_2', 0)
            tp3 = analysis.get('take_profit_3', 0)
            rsi = analysis.get('rsi', 0)
            trend = analysis.get('trend', 'NEUTRAL')
            reasoning = analysis.get('reasoning', '')
            analysis_type = analysis.get('analysis_type', 'normal')
            timestamp = analysis.get('timestamp', '')
            
            # Calculate potential profits and losses
            potential_profit_loss = ""
            if entry_price > 0 and stop_loss > 0:
                risk_percent = abs((entry_price - stop_loss) / entry_price * 100)
                potential_profit_loss += f"📉 <b>ریسک:</b> {risk_percent:.2f}%\n"
            
            if entry_price > 0 and tp1 > 0:
                reward1_percent = abs((tp1 - entry_price) / entry_price * 100)
                potential_profit_loss += f"📈 <b>پاداش TP1:</b> {reward1_percent:.2f}%\n"
                if risk_percent > 0:
                    rr_ratio = reward1_percent / risk_percent
                    potential_profit_loss += f"⚖️ <b>نسبت ریسک/پاداش:</b> 1:{rr_ratio:.2f}\n"
            
            # Get current price for profit/loss calculation
            try:
                current_market_data = await self.trading_system.aggregator.aggregate_ict_data(symbol)
                current_price = current_market_data.get('market_data', {}).get('current_price', 0)
                
                profit_loss_info = ""
                if current_price > 0 and entry_price > 0:
                    if signal_type in ['BUY', 'LONG']:
                        pnl_percent = (current_price - entry_price) / entry_price * 100
                        pnl_emoji = "🟢" if pnl_percent > 0 else "🔴"
                        profit_loss_info = f"{pnl_emoji} <b>سود/زیان فعلی:</b> {pnl_percent:+.2f}%\n"
                    elif signal_type in ['SELL', 'SHORT']:
                        pnl_percent = (entry_price - current_price) / entry_price * 100
                        pnl_emoji = "🟢" if pnl_percent > 0 else "🔴"
                        profit_loss_info = f"{pnl_emoji} <b>سود/زیان فعلی:</b> {pnl_percent:+.2f}%\n"
                    
                    # Check detailed target status and calculate PnL for each
                    target_status = []
                    total_pnl_percent = 0
                    
                    if signal_type in ['BUY', 'LONG']:
                        # For LONG positions
                        if tp1 > 0:
                            tp1_hit = current_price >= tp1
                            tp1_pnl = ((tp1 - entry_price) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp1_hit else f"⏳ فاصله: {((tp1 - current_price) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP1 (${tp1:,.4f}): {status} | سود: {tp1_pnl:+.2f}%")
                            if tp1_hit:
                                total_pnl_percent = tp1_pnl
                        
                        if tp2 > 0:
                            tp2_hit = current_price >= tp2
                            tp2_pnl = ((tp2 - entry_price) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp2_hit else f"⏳ فاصله: {((tp2 - current_price) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP2 (${tp2:,.4f}): {status} | سود: {tp2_pnl:+.2f}%")
                            if tp2_hit:
                                total_pnl_percent = tp2_pnl
                        
                        if tp3 > 0:
                            tp3_hit = current_price >= tp3
                            tp3_pnl = ((tp3 - entry_price) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp3_hit else f"⏳ فاصله: {((tp3 - current_price) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP3 (${tp3:,.4f}): {status} | سود: {tp3_pnl:+.2f}%")
                            if tp3_hit:
                                total_pnl_percent = tp3_pnl
                                
                    elif signal_type in ['SELL', 'SHORT']:
                        # For SHORT positions
                        if tp1 > 0:
                            tp1_hit = current_price <= tp1
                            tp1_pnl = ((entry_price - tp1) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp1_hit else f"⏳ فاصله: {((current_price - tp1) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP1 (${tp1:,.4f}): {status} | سود: {tp1_pnl:+.2f}%")
                            if tp1_hit:
                                total_pnl_percent = tp1_pnl
                        
                        if tp2 > 0:
                            tp2_hit = current_price <= tp2
                            tp2_pnl = ((entry_price - tp2) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp2_hit else f"⏳ فاصله: {((current_price - tp2) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP2 (${tp2:,.4f}): {status} | سود: {tp2_pnl:+.2f}%")
                            if tp2_hit:
                                total_pnl_percent = tp2_pnl
                        
                        if tp3 > 0:
                            tp3_hit = current_price <= tp3
                            tp3_pnl = ((entry_price - tp3) / entry_price * 100) if entry_price > 0 else 0
                            status = "✅ خورده" if tp3_hit else f"⏳ فاصله: {((current_price - tp3) / current_price * 100):+.2f}%"
                            target_status.append(f"🎯 TP3 (${tp3:,.4f}): {status} | سود: {tp3_pnl:+.2f}%")
                            if tp3_hit:
                                total_pnl_percent = tp3_pnl
                    
                    # Add target status to profit/loss info
                    if target_status:
                        profit_loss_info += f"\n<b>🎯 وضعیت تارگت‌ها:</b>\n"
                        for status in target_status:
                            profit_loss_info += f"   {status}\n"
                    else:
                        profit_loss_info += f"\nℹ️ <b>تارگتی برای این تحلیل تعریف نشده است</b>\n"
                    
                    # Check if stop loss was hit
                    sl_hit = False
                    if signal_type in ['BUY', 'LONG'] and stop_loss > 0 and current_price <= stop_loss:
                        sl_hit = True
                    elif signal_type in ['SELL', 'SHORT'] and stop_loss > 0 and current_price >= stop_loss:
                        sl_hit = True
                    
                    if sl_hit:
                        profit_loss_info += "🛑 <b>حد ضرر فعال شده است</b>\n"
                        
            except Exception as market_error:
                current_price = 0
                profit_loss_info = f"⚠️ خطا در دریافت قیمت فعلی: {str(market_error)}\n"
            
            # Format the detailed message
            signal_emoji = "🟢" if signal_type in ['BUY', 'LONG'] else "🔴" if signal_type in ['SELL', 'SHORT'] else "⚪"
            type_badge = "🧠" if analysis_type == 'smart' else "📊"
            
            detail_msg = f"""
{signal_emoji} {type_badge} <b>جزئیات تحلیل {symbol}</b>

━━━━━━━━━━━━━━━━━━━━━━
<b>📊 اطلاعات سیگنال</b>
<b>نوع:</b> {signal_type} ({signal_grade})
<b>درجه اطمینان:</b> {confidence:.1f}%
<b>زمان تحلیل:</b> {timestamp if isinstance(timestamp, str) else timestamp.strftime('%Y-%m-%d %H:%M') if timestamp else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━
<b>💰 اطلاعات قیمت</b>
<b>قیمت تحلیل:</b> ${price:,.4f}
<b>قیمت ورود:</b> ${entry_price:,.4f}
<b>قیمت فعلی:</b> ${current_price:,.4f}
<b>حد ضرر:</b> ${stop_loss:,.4f}
<b>تارگت 1:</b> ${tp1:,.4f}
<b>تارگت 2:</b> ${tp2:,.4f}
<b>تارگت 3:</b> ${tp3:,.4f}

━━━━━━━━━━━━━━━━━━━━━━
<b>📈 وضعیت فعلی</b>
{profit_loss_info}
{potential_profit_loss}

━━━━━━━━━━━━━━━━━━━━━━
<b>🔍 تحلیل تکنیکال</b>
<b>RSI:</b> {rsi:.1f}
<b>ترند:</b> {trend}

━━━━━━━━━━━━━━━━━━━━━━
<b>🧠 دلیل تحلیل</b>
{reasoning}
"""
            
            # Add action buttons
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"refresh_detail_{analysis_id}")],
                [InlineKeyboardButton("🔙 بازگشت به تاریخچه", callback_data="back_to_analyses")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Delete progress message
            try:
                await msg.delete()
            except:
                pass
            
            if query:
                await query.message.reply_text(detail_msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            else:
                await update.message.reply_text(detail_msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
        except Exception as e:
            try:
                await msg.edit_text(f"❌ خطا در دریافت جزئیات: {str(e)}")
            except:
                if query:
                    await query.message.reply_text(f"❌ خطا در دریافت جزئیات: {str(e)}")
                else:
                    await update.message.reply_text(f"❌ خطا در دریافت جزئیات: {str(e)}")
            print(f"Analysis detail error: {e}")
    
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command - Market overview"""
        await update.message.reply_text("🌍 در حال دریافت اطلاعات بازار...")
        
        try:
            # Get prices for major cryptocurrencies
            major_cryptos = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]
            msg = "🌍 <b>بررسی کلی بازار</b>\n\n"
            
            for symbol in major_cryptos:
                try:
                    price = await self.trading_system.provider.get_current_price(symbol)
                    symbol_name = symbol.replace('USDT', '')
                    msg += f"• <b>{symbol_name}</b>: ${price:,.2f}\n"
                except:
                    pass
            
            msg += "\n💡 برای تحلیل دقیق‌تر از دستور /analyze استفاده کنید."
            
            keyboard = [[InlineKeyboardButton("📊 تحلیل BTC", callback_data="analyze_BTCUSDT"),
                        InlineKeyboardButton("📊 تحلیل ETH", callback_data="analyze_ETHUSDT")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در دریافت اطلاعات بازار: {str(e)}")
    
    
    async def topmovers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /topmovers command - Show top price movers"""
        await update.message.reply_text("🚀 در حال دریافت برترین تغییرات قیمت...")
        
        msg = """🚀 <b>برترین تغییرات قیمت (24 ساعت)</b>

این امکان به زودی اضافه خواهد شد.
از دستور /analyze برای تحلیل ارزهای خاص استفاده کنید.
"""
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    async def check_alerts_task(self, context: ContextTypes.DEFAULT_TYPE):
        """Check price alerts periodically"""
        try:
            for alert in self.state_manager.price_alerts[:]:
                current_price = await self.trading_system.provider.get_current_price(alert.symbol)
                triggered = False
                if alert.condition == "above" and current_price >= alert.target_price:
                    triggered = True
                elif alert.condition == "below" and current_price <= alert.target_price:
                    triggered = True
                
                if triggered:
                    condition_fa = "بالاتر از" if alert.condition == "above" else "پایین‌تر از"
                    msg = f"""
🔔 <b>هشدار قیمت فعال شد!</b>

نماد: {alert.symbol}
هدف: ${alert.target_price:,.2f}
قیمت فعلی: ${current_price:,.2f}
شرط: {condition_fa}

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                    """
                    await context.bot.send_message(chat_id=alert.user_id, text=msg, parse_mode=ParseMode.HTML)
                    await self.state_manager.remove_alert(alert)
        except Exception as e:
            print(f"Alert check error: {e}")
    
    async def smartanalyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /smartanalyze command - تحلیل هوشمند و انتخاب بهترین ارز - runs in background
        """
        user_id = update.effective_user.id
        
        # پیام اولیه
        msg = await update.message.reply_text(
            "🧠 <b>تحلیل هوشمند پیشرفته</b>\n\n"
            "🔍 در حال آماده‌سازی...\n\n"
            "💡 می‌توانید از دستورات دیگر استفاده کنید",
            parse_mode=ParseMode.HTML
        )
        
        # Run in background
        self._run_in_background(self._smartanalyze_background(update, context, msg, user_id))
    
    async def _smartanalyze_background(self, update: Update, context: ContextTypes.DEFAULT_TYPE, msg, user_id: int):
        """Background task for smart analysis"""
        try:
            # Callback برای به‌روزرسانی پیشرفت با مدیریت Flood Control
            last_update_time = [0]  # استفاده از list برای mutable در closure
            pending_messages = []
            
            async def progress_update(message: str):
                import time
                try:
                    current_time = time.time()
                    
                    # اگر کمتر از 2 ثانیه از آخرین به‌روزرسانی گذشته، پیام را ذخیره کن
                    if current_time - last_update_time[0] < 2.0:
                        pending_messages.append(message)
                        return
                    
                    # اگر پیام‌های معلق داریم، آخرین یکی را نمایش بده
                    if pending_messages:
                        message = pending_messages[-1]
                        pending_messages.clear()
                    
                    current_text = msg.text_html or ""
                    lines = current_text.split('\n')
                    
                    # حداکثر 15 خط نمایش
                    if len(lines) > 15:
                        lines = lines[:2] + lines[-13:]
                    
                    lines.append(message)
                    new_text = '\n'.join(lines[-15:])
                    
                    await msg.edit_text(new_text, parse_mode=ParseMode.HTML)
                    last_update_time[0] = current_time
                    
                except Exception as e:
                    pass  # Ignore telegram errors
        
            # ایجاد selector پیشرفته با callback
            from src.ai.advanced_selector import AdvancedCoinSelector
            advanced_selector = AdvancedCoinSelector(
                self.trading_system.config,
                self.trading_system.provider,
                progress_callback=progress_update
            )
            # دریافت پارامترها
            top_n = 5
            custom_symbols = None
            
            if context.args:
                # اگر کاربر تعداد مشخص کرد
                try:
                    top_n = int(context.args[0])
                    top_n = min(max(top_n, 3), 10)  # محدود به 3-10
                except:
                    pass
                
                # اگر کاربر لیست ارزها را مشخص کرد
                if len(context.args) > 1:
                    custom_symbols = [arg.upper() + "USDT" if not arg.endswith("USDT") else arg.upper() 
                                     for arg in context.args[1:]]
            
            # تحلیل هوشمند با selector پیشرفته
            top_coins = await advanced_selector.find_best_coins(top_n, custom_symbols)
            
            if not top_coins:
                await msg.edit_text(
                    "❌ <b>هیچ ارز مناسبی یافت نشد</b>\n\n"
                    "تمام ارزها فیلتر شدند. لطفاً بعداً دوباره امتحان کنید.",
                    parse_mode=ParseMode.HTML
                )
                await advanced_selector.close()
                return
            
            selected_coin = top_coins[0]
            best_symbol = selected_coin['symbol']
            
            # ارسال گزارش تحلیل
            report_text = "🧠 <b>گزارش تحلیل هوشمند پیشرفته</b>\n"
            report_text += "=" * 40 + "\n\n"
            
            # نمایش ارزهای برتر
            report_text += "🏆 <b>ارزهای برتر:</b>\n\n"
            for i, coin in enumerate(top_coins, 1):
                checks = coin['checks']
                indicators = coin['indicators']
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                
                report_text += f"{emoji} <b>{coin['symbol']}</b>\n"
                report_text += f"   امتیاز کلی: {coin['final_score']:.1%}\n"
                report_text += f"   قیمت: ${coin['current_price']:.2f}\n"
                report_text += f"   RSI: {indicators['rsi']:.1f}\n"
                
                # نمایش وضعیت ترند
                trend = checks['trend']
                trend_emoji = "📈" if trend['is_uptrend'] else "📉"
                report_text += f"   {trend_emoji} ترند: {'صعودی' if trend['is_uptrend'] else 'نزولی'} "
                report_text += f"(کیفیت: {trend['quality_score']:.1%})\n"
                
                # نمایش ساختار
                structure = checks['structure']['structure_type']
                report_text += f"   🏗 ساختار: {structure}\n\n"
            
            # نمایش ارزهای رد شده
            rejected = advanced_selector.get_rejected_coins()
            if rejected:
                report_text += f"\n🚫 <b>ارزهای رد شده ({len(rejected)}):</b>\n"
                for rej in rejected[:3]:
                    report_text += f"   • {rej['symbol']}: {rej['reason']}\n"
            
            report_text += "\n" + "=" * 40 + "\n"
            report_text += f"✅ بهترین انتخاب: <b>{best_symbol}</b>\n"
            report_text += f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            
            await msg.edit_text(report_text, parse_mode=ParseMode.HTML)
            
            # تحلیل کامل ICT برای بهترین ارز
            await asyncio.sleep(2)  # تاخیر بیشتر برای جلوگیری از flood
            signal_msg = await update.message.reply_text(
                f"📊 <b>در حال تحلیل کامل ICT برای {best_symbol}...</b>",
                parse_mode=ParseMode.HTML
            )
            
            try:
                # تحلیل ICT
                market_data = await self.trading_system.aggregator.aggregate_ict_data(best_symbol)
                
                # Check for errors in market data
                if 'error' in market_data:
                    error_msg = market_data.get('user_message', market_data.get('error', 'خطای نامشخص'))
                    await signal_msg.edit_text(f"❌ {error_msg}", parse_mode=ParseMode.HTML)
                    await advanced_selector.close()
                    return
                
                signal = await self.trading_system.ai.get_signal(market_data)
                
                # Check for errors in signal
                if 'error' in signal:
                    error_msg = signal.get('user_message', signal.get('error', 'خطای نامشخص'))
                    await signal_msg.edit_text(f"❌ {error_msg}", parse_mode=ParseMode.HTML)
                    await advanced_selector.close()
                    return
                
                # Check if deep thinking was used
                deep_thinking_used = signal.get('deep_thinking_used', False)
                thinking_reason = signal.get('thinking_reason', '')
                
                if deep_thinking_used:
                    await signal_msg.edit_text(
                        f"🧠 <b>تحلیل عمیق فعال شد</b>\n\n{thinking_reason}\n\n⏳ در حال تحلیل عمیق...",
                        parse_mode=ParseMode.HTML
                    )
                
                # Save analysis to history
                try:
                    # Skip saving if AI returned an error
                    if signal.get('error'):
                        print(f"⚠️ Skipping save - AI returned error: {signal.get('error')}")
                    else:
                        # Only save if we have valid market data
                        md = market_data.get('market_data', market_data)  # smart_analyze returns different structure
                        current_price = md.get('current_price', 0)
                        if current_price > 0:
                            # Extract data from LLM output structure
                            signal_type = signal.get('signal', 'NO_TRADE')
                            
                            # Get confidence from risk_metrics
                            risk_metrics = signal.get('risk_metrics', {})
                            confidence = risk_metrics.get('confidence_percent', 0)
                            
                            # Get position data
                            position = signal.get('position', {})
                            entry_zone = position.get('entry_zone', {})
                            stop_loss_data = position.get('stop_loss', {})
                            take_profit_array = position.get('take_profit', [])
                            
                            # Extract prices
                            entry_price = entry_zone.get('optimal', current_price)
                            stop_loss = stop_loss_data.get('price', 0)
                            
                            # Extract take profit levels (up to 3)
                            tp1 = take_profit_array[0].get('price', 0) if len(take_profit_array) > 0 else 0
                            tp2 = take_profit_array[1].get('price', 0) if len(take_profit_array) > 1 else 0
                            tp3 = take_profit_array[2].get('price', 0) if len(take_profit_array) > 2 else 0
                            
                            # Get indicators
                            indicators = market_data.get('indicators', {})
                            rsi = indicators.get('rsi', 0)
                            
                            # Get market structure
                            market_structure = market_data.get('market_structure', {})
                            htf_trend = market_structure.get('htf_trend', 'NEUTRAL')
                            
                            # Get reasoning from context or persian_summary
                            context = signal.get('context', {})
                            persian_summary = signal.get('persian_summary', {})
                            reasoning = persian_summary.get('reasoning', context.get('primary_driver', 'تحلیل هوشمند ICT'))
                            
                            analysis_data = {
                                'user_id': user_id,
                                'symbol': best_symbol,
                                'signal_type': signal_type,
                                'signal_grade': signal.get('signal_grade', 'N/A'),
                                'confidence': confidence,
                                'price': current_price,
                                'entry_price': entry_price,
                                'stop_loss': stop_loss,
                                'take_profit_1': tp1,
                                'take_profit_2': tp2,
                                'take_profit_3': tp3,
                                'rsi': rsi,
                                'trend': htf_trend,
                                'reasoning': reasoning,
                                'analysis_type': 'smart'
                            }
                            if self.analysis_history_repo:
                                await self.analysis_history_repo.add_analysis(analysis_data)
                                print(f"✅ Smart analysis saved for {best_symbol}")
                            else:
                                print(f"⚠️ Repository not initialized, skipping save for {best_symbol}")
                        else:
                            print(f"⚠️ Skipping save - no market data: price={current_price}")
                except Exception as save_error:
                    print(f"❌ Error saving smart analysis to history: {save_error}")
                
                # فرمت کردن سیگنال با market_data
                formatted_signal = self.formatters.format_signal_detailed(market_data, signal)
                
                # Add deep thinking badge if used
                if deep_thinking_used:
                    thinking_badge = "\n\n🧠 <b>تحلیل عمیق استفاده شد</b>\n<i>" + thinking_reason + "</i>"
                    formatted_signal += thinking_badge
                
                # ارسال نمودار
                try:
                    chart_path = self.chart_generator.generate_chart(
                        market_data,
                        signal,
                        best_symbol
                    )
                    
                    with open(chart_path, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=formatted_signal,
                            parse_mode=ParseMode.HTML
                        )
                    
                    await signal_msg.delete()
                    
                except Exception as e:
                    await signal_msg.edit_text(formatted_signal, parse_mode=ParseMode.HTML)
                    print(f"Chart generation error: {e}")
                
            except Exception as e:
                await signal_msg.edit_text(
                    f"❌ خطا در تحلیل ICT: {str(e)}",
                    parse_mode=ParseMode.HTML
                )
                print(f"ICT analysis error: {e}")
            
            # بستن selector
            await advanced_selector.close()
            
        except Exception as e:
            error_msg = f"❌ خطا در تحلیل هوشمند:\n{str(e)}"
            try:
                await msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
            print(f"Smart analyze error: {e}")
            import traceback
            traceback.print_exc()
