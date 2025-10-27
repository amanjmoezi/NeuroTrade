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
from src.bot.i18n import t, get_i18n
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
    
    @staticmethod
    def _safe_float(value, default=0):
        """Safely convert value to float, handling str and None"""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default
    
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
        user_id = user.id
        
        # Get user's language preference
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        welcome_msg = f"""
{t('welcome_title', lang)}

{t('welcome_greeting', lang, name=user.first_name)}

{t('welcome_features_title', lang)}
{t('welcome_features', lang)}

{t('welcome_commands_title', lang)}
/smartanalyze - {t('cmd_smartanalyze', lang)}
/analyze - {t('cmd_analyze', lang)}
/analyses - {t('cmd_analyses', lang)}
/market - {t('cmd_market', lang)}
/help - {t('cmd_help', lang)}

{t('welcome_ready', lang)}
        """
        keyboard = [[KeyboardButton(t('btn_smart_analysis', lang)), KeyboardButton(t('btn_analyze_coin', lang))],
                    [KeyboardButton(t('btn_market_overview', lang)), KeyboardButton(t('btn_analysis_history', lang))],
                    [KeyboardButton(t('btn_my_alerts', lang)), KeyboardButton(t('btn_settings', lang))]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        help_text = f"""
{t('help_title', lang)}

{t('help_analysis_section', lang)}

{t('help_history_section', lang)}

{t('help_alerts_section', lang)}

{t('help_settings_section', lang)}

{t('help_need_help', lang)}
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        popular_cryptos = [
            "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "TRX", "DOT", "MATIC",
            "LTC", "SHIB", "AVAX", "UNI", "LINK", "ATOM", "XLM", "ETC", "BCH", "FIL",
            "APT", "ARB", "OP", "NEAR", "INJ", "SUI", "PEPE", "FTM", "ALGO", "VET",
            "HBAR", "QNT", "IMX", "AAVE", "GRT", "SAND", "MANA", "AXS", "THETA", "XTZ",
            "EOS", "RUNE", "FLR", "EGLD", "KAVA", "ZIL", "ENJ", "CHZ", "BAT", "ZRX",
            "CRV", "COMP", "SNX", "MKR", "SUSHI", "YFI", "1INCH", "LDO", "RPL", "BLUR"
        ]
        
        keyboard = []
        for i in range(0, len(popular_cryptos), 3):
            row = []
            for crypto in popular_cryptos[i:i+3]:
                row.append(InlineKeyboardButton(crypto, callback_data=f"analyze_{crypto}USDT"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            t('select_crypto', lang),
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def perform_analysis(self, update: Update, symbol: str, query=None):
        """Perform analysis for a symbol - runs in background"""
        if query:
            user_id = query.from_user.id
            message_obj = query.message
        else:
            user_id = update.effective_user.id
            message_obj = update.message
        
        # Get user's language
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        analysis_msg = f"{t('analyzing', lang, symbol=symbol)}\n{t('fetching_data', lang)}\n\n{t('can_use_other_commands', lang)}"
        
        if query:
            msg = await query.message.reply_text(analysis_msg)
        else:
            msg = await update.message.reply_text(analysis_msg)
        
        # Run analysis in background
        self._run_in_background(self._perform_analysis_background(msg, message_obj, user_id, symbol, lang))
    
    async def _refresh_analysis_background(self, msg, message_obj, symbol: str, lang: str = 'fa'):
        """Background task for refreshing analysis"""
        try:
            result = await self.trading_system.analyze(symbol)
            signal_msg = self.formatters.format_signal_detailed(result['market_data'], result['signal'])
            await msg.delete()
            await message_obj.reply_text(signal_msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            error_msg = t('error_refresh_symbol', lang, symbol=symbol, error=str(e))
            try:
                await msg.edit_text(error_msg)
            except:
                await message_obj.reply_text(error_msg)
    
    async def _perform_analysis_background(self, msg, message_obj, user_id: int, symbol: str, lang: str):
        """Background task for performing analysis"""
        try:
            result = await self.trading_system.analyze(symbol)
            
            # Check for errors in market data
            market_data = result.get('market_data', {})
            if 'error' in market_data:
                error_msg = market_data.get('user_message', market_data.get('error', t('error_unknown', lang)))
                await msg.edit_text(f"❌ {error_msg}")
                return
            
            # Check for errors in signal
            signal = result.get('signal', {})
            if 'error' in signal:
                error_msg = signal.get('user_message', signal.get('error', t('error_unknown', lang)))
                await msg.edit_text(f"❌ {error_msg}")
                return
            
            # Check if deep thinking was used
            deep_thinking_used = signal.get('deep_thinking_used', False)
            thinking_reason = signal.get('thinking_reason', '')
            
            if deep_thinking_used:
                await msg.edit_text(t('deep_thinking', lang, reason=thinking_reason))
            
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
                        reasoning = persian_summary.get('reasoning', context.get('primary_driver', t('ict_analysis', lang)))
                        
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
                thinking_badge = t('deep_thinking_badge', lang, reason=thinking_reason)
                signal_msg_full += thinking_badge
            
            if chart:
                await message_obj.reply_photo(photo=chart)
                await message_obj.reply_text(signal_msg_full, parse_mode=ParseMode.HTML)
                signal_summary = self.formatters.format_signal_summary(result['market_data'], result['signal'])
                await message_obj.reply_text(signal_summary, parse_mode=ParseMode.HTML)
            else:
                await message_obj.reply_text(signal_msg_full, parse_mode=ParseMode.HTML)
            await msg.delete()
            
            keyboard = [[InlineKeyboardButton(t('btn_set_alert', lang), callback_data=f"alert_{symbol}"),
                        InlineKeyboardButton(t('btn_refresh', lang), callback_data=f"refresh_{symbol}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message_obj.reply_text(t('what_to_do', lang), reply_markup=reply_markup)
        except Exception as e:
            error_text = t('error_analysis', lang, symbol=symbol) + "\n\n"
            if "timeout" in str(e).lower():
                error_text += t('error_timeout', lang)
            elif "connection" in str(e).lower():
                error_text += t('error_connection', lang)
            else:
                error_text += f"{t('error', lang)}: {str(e)}"
            
            try:
                await msg.edit_text(error_text)
            except:
                await message_obj.reply_text(error_text)
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        alerts = await self.state_manager.get_user_alerts(user_id)
        
        if not alerts:
            msg = f"{t('alerts_title', lang)}\n\n{t('no_alerts', lang)}"
        else:
            msg = f"{t('active_alerts', lang)}\n\n"
            for alert in alerts:
                condition_text = t('condition_above', lang) if alert.condition == 'above' else t('condition_below', lang)
                msg += f"• {alert.symbol}: ${alert.target_price:,.2f} ({condition_text})\n"
            msg += f"\n{t('total_alerts', lang, count=len(alerts))}"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    async def setalert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setalert command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        if len(context.args) < 2:
            await update.message.reply_text(t('alert_usage', lang))
            return
        
        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        try:
            target_price = float(context.args[1])
            current_price = await self.trading_system.provider.get_current_price(symbol)
            condition = "above" if target_price > current_price else "below"
            condition_text = t('condition_above', lang) if condition == "above" else t('condition_below', lang)
            
            alert = PriceAlert(user_id=user_id, symbol=symbol, target_price=target_price, 
                             condition=condition, created_at=datetime.now(timezone.utc).isoformat())
            await self.state_manager.add_alert(alert)
            
            await update.message.reply_text(
                f"{t('alert_set', lang)}\n\n{t('symbol', lang)}: {symbol}\n{t('target', lang)}: ${target_price:,.2f}\n"
                f"{t('current_price', lang).replace('<b>', '').replace('</b>', '').replace('💰 ', '')}: ${current_price:,.2f}\n"
                f"{t('condition_above' if condition == 'above' else 'condition_below', lang).capitalize()}: {condition_text}\n\n{t('will_notify', lang)}"
            )
        except ValueError:
            await update.message.reply_text(t('invalid_price', lang))
        except Exception as e:
            await update.message.reply_text(f"{t('error', lang)}: {str(e)}")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        i18n = get_i18n()
        
        notifications_status = t('enabled', lang) if settings.notifications else t('disabled', lang)
        lang_display = f"{i18n.get_language_flag(settings.language)} {i18n.get_language_name(settings.language)}"
        
        msg = f"""
{t('settings_title', lang)}

{t('default_timeframe', lang)} {settings.default_timeframe}
{t('default_leverage', lang)} {settings.default_leverage}x
{t('risk_per_trade', lang)} {settings.risk_per_trade}%
{t('notifications', lang)} {notifications_status}
{t('language', lang)} {lang_display}
{t('favorites', lang)} {', '.join(settings.favorite_symbols)}

{t('customize_settings', lang)}
        """
        keyboard = [
            [InlineKeyboardButton(f"📊 {t('default_timeframe', lang).replace('<b>', '').replace('</b>', '').replace('📊 ', '')}", callback_data="settings_timeframe"),
             InlineKeyboardButton(f"⚡ {t('default_leverage', lang).replace('<b>', '').replace('</b>', '').replace('⚡ ', '')}", callback_data="settings_leverage")],
            [InlineKeyboardButton(f"💰 {t('risk_per_trade', lang).replace('<b>', '').replace('</b>', '').replace('💰 ', '')}", callback_data="settings_risk"),
             InlineKeyboardButton(f"🔔 {t('notifications', lang).replace('<b>', '').replace('</b>', '').replace('🔔 ', '')}", callback_data="toggle_notifications")],
            [InlineKeyboardButton(f"🌐 {t('language', lang).replace('<b>', '').replace('</b>', '').replace('🌐 ', '')}", callback_data="settings_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        msg = f"""
{t('status_title', lang)}

{t('trading_system_online', lang)}
{t('data_provider_connected', lang)}
{t('ai_model_active', lang)}
{t('alerts_running', lang)}

{t('bot_version', lang)}
{t('response_time', lang)}
        """
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            data = query.data
            user_id = query.from_user.id
            settings = await self.state_manager.get_user_settings(user_id)
            lang = settings.language
            print(f"🔘 Button pressed: {data}")  # Debug log
            
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
                await query.message.reply_text(t('refreshing_details', lang))
                await self.analysis_detail_command(update, context, analysis_id)
            
            elif data.startswith("refresh_"):
                symbol = data.split("_")[1]
                msg = await query.message.reply_text(t('refreshing_with_hint', lang, symbol=symbol))
                # Run refresh in background
                self._run_in_background(self._refresh_analysis_background(msg, query.message, symbol, lang))
            
            elif data.startswith("alert_"):
                symbol = data.split("_")[1]
                await query.message.reply_text(t('for_alert_set', lang, symbol=symbol))
            
            elif data == "settings_timeframe":
                # Show timeframe selection menu
                keyboard = [
                    [InlineKeyboardButton("15m", callback_data="timeframe_15m"),
                     InlineKeyboardButton("1h", callback_data="timeframe_1h"),
                     InlineKeyboardButton("4h", callback_data="timeframe_4h")],
                    [InlineKeyboardButton("1d", callback_data="timeframe_1d")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(t('select_timeframe_msg', lang), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
            elif data.startswith("timeframe_"):
                timeframe = data.split("_")[1]
                settings.default_timeframe = timeframe
                await self.state_manager.update_user_settings(user_id, settings)
                await query.message.reply_text(t('timeframe_changed_msg', lang, value=timeframe), parse_mode=ParseMode.HTML)
            
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
                await query.message.reply_text(t('select_leverage_msg', lang), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
            elif data.startswith("leverage_"):
                leverage = int(data.split("_")[1])
                settings.default_leverage = leverage
                await self.state_manager.update_user_settings(user_id, settings)
                await query.message.reply_text(t('leverage_changed_msg', lang, value=leverage), parse_mode=ParseMode.HTML)
            
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
                await query.message.reply_text(t('select_risk_msg', lang), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
            elif data.startswith("risk_"):
                risk = float(data.split("_")[1])
                settings.risk_per_trade = risk
                await self.state_manager.update_user_settings(user_id, settings)
                await query.message.reply_text(t('risk_changed_msg', lang, value=risk), parse_mode=ParseMode.HTML)
            
            elif data == "settings_language":
                # Show language selection menu
                keyboard = [
                    [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
                     InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(t('select_language_msg', lang), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
            elif data.startswith("lang_"):
                language = data.split("_")[1]
                settings.language = language
                await self.state_manager.update_user_settings(user_id, settings)
                lang_name = "فارسی" if language == "fa" else "English"
                msg_key = 'language_changed_fa' if language == "fa" else 'language_changed_en'
                await query.message.reply_text(t(msg_key, language, lang_name=lang_name), parse_mode=ParseMode.HTML)
            
            elif data == "back_to_analyses":
                await self.analyses_command(update, context)
            
            elif data == "toggle_notifications":
                settings.notifications = not settings.notifications
                await self.state_manager.update_user_settings(user_id, settings)
                status = t('status_enabled', lang) if settings.notifications else t('status_disabled', lang)
                await query.message.reply_text(t('notifications_toggled', lang, status=status))
        
        except Exception as e:
            print(f"❌ Button callback error: {e}")
            import traceback
            traceback.print_exc()
            try:
                await update.callback_query.message.reply_text(t('error_button_processing', lang, error=str(e)))
            except:
                pass
    
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
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        # Handle both message and callback query contexts
        if hasattr(update, 'callback_query') and update.callback_query:
            message_obj = update.callback_query.message
        else:
            message_obj = update.message
            
        await message_obj.reply_text(t('loading_history_msg', lang))
        
        try:
            if not self.analysis_history_repo:
                await message_obj.reply_text(t('error_db_not_ready', lang))
                return
            
            analyses = await self.analysis_history_repo.get_user_analyses(user_id, limit=20)
            stats = await self.analysis_history_repo.get_analysis_stats(user_id)
            
            if not analyses:
                msg = f"{t('analysis_history_title', lang)}\n\n{t('no_analyses', lang)}"
            else:
                msg = f"{t('recent_analyses', lang)}\n\n"
                
                for analysis in analyses[:10]:
                    symbol = analysis.get('symbol', 'N/A')
                    signal_type = analysis.get('signal_type', 'N/A')
                    signal_grade = analysis.get('signal_grade', '')
                    
                    # Convert to float to handle both str and numeric types from database
                    confidence = self._safe_float(analysis.get('confidence'))
                    price = self._safe_float(analysis.get('price'))
                    entry_price = self._safe_float(analysis.get('entry_price'))
                    stop_loss = self._safe_float(analysis.get('stop_loss'))
                    tp1 = self._safe_float(analysis.get('take_profit_1'))
                    tp2 = self._safe_float(analysis.get('take_profit_2'))
                    tp3 = self._safe_float(analysis.get('take_profit_3'))
                    
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
                    msg += f"{t('statistics_section', lang)}\n"
                    msg += f"• {t('total_analyses_label', lang)}: {total_analyses}\n"
                    msg += f"• {t('buy_signals_label', lang)}: {buy_signals}\n"
                    msg += f"• {t('sell_signals_label', lang)}: {sell_signals}\n"
                    msg += f"• {t('hold_signals_label', lang)}: {hold_signals}\n"
                    msg += f"• {t('avg_confidence', lang)}: {avg_confidence:.1f}%\n"
            
            # Create detail buttons for each analysis
            keyboard = []
            for analysis in analyses[:5]:  # Show buttons for first 5 analyses
                analysis_id = str(analysis.get('_id', ''))
                symbol = analysis.get('symbol', 'N/A')
                signal_type = analysis.get('signal_type', 'N/A')
                signal_emoji = "🟢" if signal_type in ['BUY', 'LONG'] else "🔴" if signal_type in ['SELL', 'SHORT'] else "⚪"
                keyboard.append([InlineKeyboardButton(f"{signal_emoji} {t('btn_detail_prefix', lang)} {symbol}", callback_data=f"analysis_detail_{analysis_id}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message_obj.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
        except Exception as e:
            await message_obj.reply_text(t('error_history', lang, error=str(e)))
            print(f"Analyses error: {e}")
    
    async def analysis_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, analysis_id: str):
        """Handle detailed analysis view - runs in background"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        if query:
            msg = await query.message.reply_text(t('loading_details_msg', lang))
        else:
            msg = await update.message.reply_text(t('loading_details_msg', lang))
        
        # Run in background
        self._run_in_background(self._analysis_detail_background(update, msg, query, user_id, analysis_id, lang))
    
    async def _analysis_detail_background(self, update: Update, msg, query, user_id: int, analysis_id: str, lang: str):
        """Background task for analysis detail view"""
        try:
            if not self.analysis_history_repo:
                await update.message.reply_text(t('error_db_not_ready', lang))
                return
            
            # Get specific analysis by ID
            from bson import ObjectId
            analysis = await self.analysis_history_repo.db.analysis_history.find_one({
                "_id": ObjectId(analysis_id),
                "user_id": user_id
            })
            
            if not analysis:
                await update.message.reply_text(t('analysis_not_found', lang))
                return
            
            # Format detailed analysis
            symbol = analysis.get('symbol', 'N/A')
            signal_type = analysis.get('signal_type', 'N/A')
            signal_grade = analysis.get('signal_grade', '')
            
            # Convert to float to handle both str and numeric types from database
            confidence = self._safe_float(analysis.get('confidence'))
            price = self._safe_float(analysis.get('price'))
            entry_price = self._safe_float(analysis.get('entry_price'))
            stop_loss = self._safe_float(analysis.get('stop_loss'))
            tp1 = self._safe_float(analysis.get('take_profit_1'))
            tp2 = self._safe_float(analysis.get('take_profit_2'))
            tp3 = self._safe_float(analysis.get('take_profit_3'))
            rsi = self._safe_float(analysis.get('rsi'))
            
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
                        profit_loss_info += f"\n{t('no_targets_defined', lang)}\n"
                    
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
                profit_loss_info = t('error_current_price', lang, error=str(market_error)) + "\n"
            
            # Format the detailed message
            signal_emoji = "🟢" if signal_type in ['BUY', 'LONG'] else "🔴" if signal_type in ['SELL', 'SHORT'] else "⚪"
            type_badge = "🧠" if analysis_type == 'smart' else "📊"
            
            detail_msg = f"""
{t('analysis_detail_title', lang, emoji=signal_emoji, badge=type_badge, symbol=symbol)}

━━━━━━━━━━━━━━━━━━━━━━
{t('signal_info_section', lang)}
{t('type', lang)} {signal_type} ({signal_grade})
{t('confidence_level', lang)} {confidence:.1f}%
{t('analysis_time', lang)} {timestamp if isinstance(timestamp, str) else timestamp.strftime('%Y-%m-%d %H:%M') if timestamp else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━
{t('price_info_section', lang)}
{t('analysis_price', lang)} ${price:,.4f}
{t('entry_price_label', lang)} ${entry_price:,.4f}
{t('current_price_label', lang)} ${current_price:,.4f}
{t('stop_loss_label', lang)} ${stop_loss:,.4f}
<b>{t('targets', lang)} 1:</b> ${tp1:,.4f}
<b>{t('targets', lang)} 2:</b> ${tp2:,.4f}
<b>{t('targets', lang)} 3:</b> ${tp3:,.4f}

━━━━━━━━━━━━━━━━━━━━━━
<b>📈 {t('current_price', lang).replace('<b>', '').replace('</b>', '').replace('💰 ', '')}</b>
{profit_loss_info}
{potential_profit_loss}

━━━━━━━━━━━━━━━━━━━━━━
{t('technical_analysis_section', lang)}
{t('rsi_label', lang)} {rsi:.1f}
{t('trend_label', lang)} {trend}

━━━━━━━━━━━━━━━━━━━━━━
{t('analysis_reasoning_section', lang)}
{reasoning}
"""
            
            # Add action buttons
            keyboard = [
                [InlineKeyboardButton(t('btn_refresh_detail', lang), callback_data=f"refresh_detail_{analysis_id}")],
                [InlineKeyboardButton(t('btn_back_to_history', lang), callback_data="back_to_analyses")]
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
                await msg.edit_text(t('error_getting_details', lang, error=str(e)))
            except:
                error_msg = t('error_getting_details', lang, error=str(e))
                if query:
                    await query.message.reply_text(error_msg)
                else:
                    await update.message.reply_text(error_msg)
            print(f"Analysis detail error: {e}")
    
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command - Market overview"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        await update.message.reply_text(t('loading_market', lang))
        
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
            
            msg += f"\n{t('market_hint', lang)}"
            
            keyboard = [[InlineKeyboardButton(t('btn_analyze_btc', lang), callback_data="analyze_BTCUSDT"),
                        InlineKeyboardButton(t('btn_analyze_eth', lang), callback_data="analyze_ETHUSDT")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
        except Exception as e:
            await update.message.reply_text(t('error_market_data', lang, error=str(e)))
    
    
    async def topmovers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /topmovers command - Show top price movers"""
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        await update.message.reply_text(t('loading_topmovers', lang))
        
        msg = f"{t('topmovers_title', lang)}\n\n{t('topmovers_coming_soon', lang)}"
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
        Handle /smartanalyze command - Smart analysis with best coin selection - runs in background
        """
        user_id = update.effective_user.id
        settings = await self.state_manager.get_user_settings(user_id)
        lang = settings.language
        
        # Initial message
        msg = await update.message.reply_text(
            f"{t('smart_analysis_title', lang)}\n\n"
            f"{t('smart_analysis_preparing', lang)}\n\n"
            f"{t('can_use_other_commands', lang)}",
            parse_mode=ParseMode.HTML
        )
        
        # Run in background
        self._run_in_background(self._smartanalyze_background(update, context, msg, user_id, lang))
    
    async def _smartanalyze_background(self, update: Update, context: ContextTypes.DEFAULT_TYPE, msg, user_id: int, lang: str):
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
            
            # Send analysis report
            report_text = f"{t('smart_analysis_report', lang)}\n"
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
            
            # Full ICT analysis for best coin
            await asyncio.sleep(2)  # Delay to prevent flood
            signal_msg = await update.message.reply_text(
                t('analyzing_ict_for', lang, symbol=best_symbol),
                parse_mode=ParseMode.HTML
            )
            
            try:
                # ICT Analysis
                market_data = await self.trading_system.aggregator.aggregate_ict_data(best_symbol)
                
                # Check for errors in market data
                if 'error' in market_data:
                    error_msg = market_data.get('user_message', market_data.get('error', t('error_unknown', lang)))
                    await signal_msg.edit_text(f"❌ {error_msg}", parse_mode=ParseMode.HTML)
                    await advanced_selector.close()
                    return
                
                signal = await self.trading_system.ai.get_signal(market_data)
                
                # Check for errors in signal
                if 'error' in signal:
                    error_msg = signal.get('user_message', signal.get('error', t('error_unknown', lang)))
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
                    t('error_ict_analysis', lang, error=str(e)),
                    parse_mode=ParseMode.HTML
                )
                print(f"ICT analysis error: {e}")
            
            # بستن selector
            await advanced_selector.close()
            
        except Exception as e:
            error_msg = t('error_smart_analysis', lang, error=str(e))
            try:
                await msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
            print(f"Smart analyze error: {e}")
            import traceback
            traceback.print_exc()
