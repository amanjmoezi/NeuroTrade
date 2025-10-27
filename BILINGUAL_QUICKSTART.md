# 🚀 Bilingual Bot - Quick Start Guide

## ⚡ Quick Commands

### Compile Translations
```bash
python compile_translations.py
```

### Test Translations
```bash
python test_i18n_simple.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 📝 Quick Reference

### Get User Language
```python
user_id = update.effective_user.id
settings = await self.state_manager.get_user_settings(user_id)
lang = settings.language  # 'fa' or 'en'
```

### Translate a Message
```python
from src.bot.i18n import t

# Simple
message = t('welcome_title', lang)

# With variables
message = t('analyzing', lang, symbol='BTCUSDT')
message = t('welcome_greeting', lang, name='John')
```

### Add New Translation

1. **Edit** `locales/fa/LC_MESSAGES/messages.po`:
```po
msgid "my_new_message"
msgstr "پیام جدید من"
```

2. **Edit** `locales/en/LC_MESSAGES/messages.po`:
```po
msgid "my_new_message"
msgstr "My New Message"
```

3. **Compile**:
```bash
python compile_translations.py
```

4. **Use in code**:
```python
msg = t('my_new_message', lang)
```

## 🎯 Common Message IDs

### Welcome & Help
- `welcome_title` - Welcome message title
- `welcome_greeting` - Greeting with {name}
- `help_title` - Help command title

### Buttons
- `btn_smart_analysis` - Smart analysis button
- `btn_analyze_coin` - Analyze coin button
- `btn_settings` - Settings button

### Signals
- `signal_long` - Long signal
- `signal_short` - Short signal
- `signal_no_trade` - No trade signal

### Errors
- `error` - Generic error
- `error_timeout` - Timeout error
- `error_connection` - Connection error

### Settings
- `settings_title` - Settings title
- `enabled` - Enabled status
- `disabled` - Disabled status
- `language` - Language label

## 🔧 File Locations

```
locales/
├── messages.pot              # Template
├── fa/LC_MESSAGES/
│   ├── messages.po          # Persian source
│   └── messages.mo          # Persian compiled
└── en/LC_MESSAGES/
    ├── messages.po          # English source
    └── messages.mo          # English compiled
```

## ⚠️ Important Notes

1. **Always compile** after editing .po files
2. **Use UTF-8** encoding for all files
3. **Keep HTML tags** in translations (`<b>`, `</b>`, etc.)
4. **Keep emojis** in translations (🚀, 💰, etc.)
5. **Test both languages** before deploying

## 🐛 Troubleshooting

### Translations not showing?
```bash
# Recompile
python compile_translations.py

# Check .mo files exist
ls -la locales/*/LC_MESSAGES/*.mo
```

### Wrong language?
```python
# Check user settings
settings = await self.state_manager.get_user_settings(user_id)
print(f"User language: {settings.language}")
```

### Message ID not found?
- Check spelling in .po file
- Ensure message ID exists in both languages
- Recompile translations

## 📚 Full Documentation

See `docs/I18N_GUIDE.md` for complete documentation.

---

Made with ❤️ - Now serving users in Persian and English!
