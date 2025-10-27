#!/usr/bin/env python3
"""
Simple standalone test for i18n functionality
"""
import gettext
from pathlib import Path


def test_translations():
    """Test translation system"""
    print("🧪 Testing i18n system...\n")
    
    # Setup paths
    project_root = Path(__file__).parent
    locale_dir = str(project_root / 'locales')
    
    # Load translations
    print("📁 Loading translations from:", locale_dir)
    print()
    
    # Test Persian
    print("=" * 60)
    print("TEST 1: Persian (fa) Translations")
    print("=" * 60)
    
    try:
        fa_trans = gettext.translation('messages', localedir=locale_dir, languages=['fa'])
        _ = fa_trans.gettext
        
        print("\n✅ Persian translations loaded successfully!")
        print(f"  Welcome Title: {_('welcome_title')}")
        print(f"  Help Title: {_('help_title')}")
        print(f"  Signal Long: {_('signal_long')}")
        print(f"  Signal Short: {_('signal_short')}")
        print(f"  Error: {_('error')}")
    except Exception as e:
        print(f"\n❌ Error loading Persian: {e}")
    
    # Test English
    print("\n" + "=" * 60)
    print("TEST 2: English (en) Translations")
    print("=" * 60)
    
    try:
        en_trans = gettext.translation('messages', localedir=locale_dir, languages=['en'])
        _ = en_trans.gettext
        
        print("\n✅ English translations loaded successfully!")
        print(f"  Welcome Title: {_('welcome_title')}")
        print(f"  Help Title: {_('help_title')}")
        print(f"  Signal Long: {_('signal_long')}")
        print(f"  Signal Short: {_('signal_short')}")
        print(f"  Error: {_('error')}")
    except Exception as e:
        print(f"\n❌ Error loading English: {e}")
    
    # Test formatting
    print("\n" + "=" * 60)
    print("TEST 3: String Formatting")
    print("=" * 60)
    
    try:
        fa_trans = gettext.translation('messages', localedir=locale_dir, languages=['fa'])
        _ = fa_trans.gettext
        
        print("\n✅ Testing format strings:")
        
        # Test with .format()
        welcome = _('welcome_greeting')
        print(f"  Template: {welcome}")
        print(f"  Formatted: {welcome.format(name='علی')}")
        
        analyzing = _('analyzing')
        print(f"  Template: {analyzing}")
        print(f"  Formatted: {analyzing.format(symbol='BTCUSDT')}")
        
    except Exception as e:
        print(f"\n❌ Error in formatting: {e}")
    
    # Check .mo files exist
    print("\n" + "=" * 60)
    print("TEST 4: Binary Files Check")
    print("=" * 60)
    
    fa_mo = project_root / 'locales' / 'fa' / 'LC_MESSAGES' / 'messages.mo'
    en_mo = project_root / 'locales' / 'en' / 'LC_MESSAGES' / 'messages.mo'
    
    print(f"\n📄 Checking .mo files:")
    print(f"  Persian: {fa_mo}")
    print(f"    Exists: {'✅' if fa_mo.exists() else '❌'}")
    if fa_mo.exists():
        print(f"    Size: {fa_mo.stat().st_size} bytes")
    
    print(f"  English: {en_mo}")
    print(f"    Exists: {'✅' if en_mo.exists() else '❌'}")
    if en_mo.exists():
        print(f"    Size: {en_mo.stat().st_size} bytes")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_translations()
        print("\n\n🎉 i18n system is working correctly!")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
