Full target : TP4# 🚀 Quick Start Guide

## Step 1: Install Dependencies

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```


## Step 2: Configure Bot Token

Your `.env` file already has the Telegram bot token configured! ✅

If you need to change it:
1. Open `.env` file
2. Update `TELEGRAM_BOT_TOKEN=your_new_token`

## Step 3: Get Your Telegram User ID (Optional)

1. Open Telegram
2. Search for `@userinfobot`
3. Start the bot
4. Copy your user ID
5. Add it to `.env`: `TELEGRAM_ADMIN_IDS=your_user_id`

## Step 4: Run the Bot

```bash
python main.py
```

You should see:
```
🤖 ICT Trading Bot Started!
================================================================================
✅ Bot is running... Press Ctrl+C to stop
================================================================================
```

## Step 5: Start Using the Bot

1. Open Telegram
2. Search for your bot (the username you created with @BotFather)
3. Click "Start" or send `/start`
4. Try these commands:
   - `/quick` - Quick BTC & ETH analysis
   - `/analyze BTC` - Analyze Bitcoin
   - `/help` - See all commands

## 🎯 Quick Commands

- **Quick Analysis**: Just type `/quick`
- **Analyze Symbol**: Type `/analyze BTC` or just `BTC`
- **Set Alert**: Type `/setalert BTC 50000`
- **View Alerts**: Type `/alerts`
- **Settings**: Type `/settings`

## 🔥 Pro Tips

1. Use the keyboard buttons for quick access
2. Type any symbol directly (e.g., "ETH", "SOL")
3. Set alerts to never miss important price levels
4. Enable notifications in settings

## ❓ Troubleshooting

### Bot doesn't respond
- Check if `python main.py` is running
- Verify bot token in `.env` is correct
- Make sure you started the bot with `/start`

### Analysis fails
- Check internet connection
- Verify OpenAI API key is valid
- Try again in a few seconds

### Need help?
- Type `/help` in the bot
- Check README.md for detailed docs
- Review error messages in terminal

## 🎉 You're Ready!

Your ICT Trading Bot is now running and ready to provide:
- ✅ Real-time market analysis
- ✅ ICT concepts (MSS, FVG, Order Blocks)
- ✅ Trading signals with entry/exit
- ✅ Beautiful charts
- ✅ Price alerts
- ✅ And much more!

**Happy Trading! 📈🚀**
