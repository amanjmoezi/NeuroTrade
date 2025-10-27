#!/usr/bin/env python3
"""
Test script for i18n functionality
"""
from src.bot.i18n import t, get_i18n


def test_translations():
    """Test translation system"""
    print("🧪 Testing i18n system...\n")
    
    # Test basic translations
    print("=" * 60)
    print("TEST 1: Basic Translations")
    print("=" * 60)
    
    print("\n📝 Welcome Title:")
    print(f"  Persian: {t('welcome_title', 'fa')}")
    print(f"  English: {t('welcome_title', 'en')}")
    
    print("\n📝 Help Title:")
    print(f"  Persian: {t('help_title', 'fa')}")
    print(f"  English: {t('help_title', 'en')}")
    
    # Test translations with variables
    print("\n" + "=" * 60)
    print("TEST 2: Translations with Variables")
    print("=" * 60)
    
    print("\n📝 Welcome Greeting:")
    print(f"  Persian: {t('welcome_greeting', 'fa', name='علی')}")
    print(f"  English: {t('welcome_greeting', 'en', name='John')}")
    
    print("\n📝 Analyzing:")
    print(f"  Persian: {t('analyzing', 'fa', symbol='BTCUSDT')}")
    print(f"  English: {t('analyzing', 'en', symbol='BTCUSDT')}")
    
    # Test signal types
    print("\n" + "=" * 60)
    print("TEST 3: Signal Types")
    print("=" * 60)
    
    print("\n📝 Signal Types:")
    print(f"  Long (FA): {t('signal_long', 'fa')}")
    print(f"  Long (EN): {t('signal_long', 'en')}")
    print(f"  Short (FA): {t('signal_short', 'fa')}")
    print(f"  Short (EN): {t('signal_short', 'en')}")
    print(f"  No Trade (FA): {t('signal_no_trade', 'fa')}")
    print(f"  No Trade (EN): {t('signal_no_trade', 'en')}")
    
    # Test error messages
    print("\n" + "=" * 60)
    print("TEST 4: Error Messages")
    print("=" * 60)
    
    print("\n📝 Errors:")
    print(f"  Timeout (FA): {t('error_timeout', 'fa')}")
    print(f"  Timeout (EN): {t('error_timeout', 'en')}")
    print(f"  Connection (FA): {t('error_connection', 'fa')}")
    print(f"  Connection (EN): {t('error_connection', 'en')}")
    
    # Test settings
    print("\n" + "=" * 60)
    print("TEST 5: Settings")
    print("=" * 60)
    
    print("\n📝 Settings:")
    print(f"  Title (FA): {t('settings_title', 'fa')}")
    print(f"  Title (EN): {t('settings_title', 'en')}")
    print(f"  Enabled (FA): {t('enabled', 'fa')}")
    print(f"  Enabled (EN): {t('enabled', 'en')}")
    print(f"  Disabled (FA): {t('disabled', 'fa')}")
    print(f"  Disabled (EN): {t('disabled', 'en')}")
    
    # Test language info
    print("\n" + "=" * 60)
    print("TEST 6: Language Information")
    print("=" * 60)
    
    i18n = get_i18n()
    print("\n📝 Supported Languages:")
    for lang in i18n.SUPPORTED_LANGUAGES:
        flag = i18n.get_language_flag(lang)
        name = i18n.get_language_name(lang)
        print(f"  {flag} {lang}: {name}")
    
    # Test fallback
    print("\n" + "=" * 60)
    print("TEST 7: Fallback Behavior")
    print("=" * 60)
    
    print("\n📝 Non-existent message ID:")
    result = t('non_existent_key', 'fa')
    print(f"  Result: {result}")
    print(f"  (Should return the message ID itself)")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


def test_message_formatting():
    """Test message formatting with complex variables"""
    print("\n\n🧪 Testing Message Formatting...\n")
    
    print("=" * 60)
    print("Complex Formatting Tests")
    print("=" * 60)
    
    # Test alerts
    print("\n📝 Alert Messages:")
    print(f"  Total Alerts (FA): {t('total_alerts', 'fa', count=5)}")
    print(f"  Total Alerts (EN): {t('total_alerts', 'en', count=5)}")
    
    # Test settings changes
    print("\n📝 Settings Changes:")
    print(f"  Timeframe (FA): {t('timeframe_changed', 'fa', value='4h')}")
    print(f"  Timeframe (EN): {t('timeframe_changed', 'en', value='4h')}")
    print(f"  Leverage (FA): {t('leverage_changed', 'fa', value=10)}")
    print(f"  Leverage (EN): {t('leverage_changed', 'en', value=10)}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        test_translations()
        test_message_formatting()
        print("\n\n🎉 All i18n tests passed successfully!")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
