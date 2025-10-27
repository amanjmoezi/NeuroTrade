"""
Telegram Bot Entry Point
Modular version with clean architecture
"""
import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from src.bot.handlers import CommandHandlers

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if x]


class TradingBot:
    """Telegram Trading Bot"""
    
    def __init__(self):
        self.handlers = CommandHandlers()
        self.app = None
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    async def post_init(self, application: Application):
        """Post initialization - setup jobs and database"""
        # Initialize database connection and repositories
        await self.handlers.initialize()
        
        # Setup job queue
        job_queue = application.job_queue
        job_queue.run_repeating(self.handlers.check_alerts_task, interval=60, first=10)
    
    def run(self):
        """Run the bot"""
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file!")
        
        # Enable concurrent updates for handling multiple users simultaneously
        self.app = (Application.builder()
                   .token(BOT_TOKEN)
                   .concurrent_updates(True)
                   .post_init(self.post_init)
                   .build())
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.handlers.start_command))
        self.app.add_handler(CommandHandler("help", self.handlers.help_command))
        self.app.add_handler(CommandHandler("analyze", self.handlers.analyze_command))
        self.app.add_handler(CommandHandler("smartanalyze", self.handlers.smartanalyze_command))
        # self.app.add_handler(CommandHandler("positions", self.handlers.positions_command))
        # self.app.add_handler(CommandHandler("exchange", self.handlers.exchange_command))
        self.app.add_handler(CommandHandler("alerts", self.handlers.alerts_command))
        self.app.add_handler(CommandHandler("setalert", self.handlers.setalert_command))
        self.app.add_handler(CommandHandler("settings", self.handlers.settings_command))
        self.app.add_handler(CommandHandler("status", self.handlers.status_command))
        
        # New feature handlers
        self.app.add_handler(CommandHandler("analyses", self.handlers.analyses_command))
        self.app.add_handler(CommandHandler("market", self.handlers.market_command))
        self.app.add_handler(CommandHandler("topmovers", self.handlers.topmovers_command))
        
        self.app.add_handler(CallbackQueryHandler(self.handlers.button_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))
        
        self.logger.info("🤖 Bot is starting...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    print("🚀 Starting ICT Trading Telegram Bot v3.0...")
    print("="*80)
    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    from telegram import Update
    main()
