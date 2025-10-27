"""
Internationalization (i18n) Module
Handles translation management using .po/.pot files
"""
import os
import gettext
from typing import Dict, Optional
from pathlib import Path


class I18n:
    """Translation manager for the bot"""
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['fa', 'en']
    DEFAULT_LANGUAGE = 'fa'
    
    def __init__(self, locale_dir: Optional[str] = None):
        """
        Initialize i18n manager
        
        Args:
            locale_dir: Path to locales directory (default: project_root/locales)
        """
        if locale_dir is None:
            # Get project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            locale_dir = str(project_root / 'locales')
        
        self.locale_dir = locale_dir
        self.translations: Dict[str, gettext.GNUTranslations] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files"""
        for lang in self.SUPPORTED_LANGUAGES:
            try:
                translation = gettext.translation(
                    'messages',
                    localedir=self.locale_dir,
                    languages=[lang],
                    fallback=True
                )
                self.translations[lang] = translation
            except Exception as e:
                print(f"⚠️ Warning: Could not load translation for '{lang}': {e}")
                # Create a fallback NullTranslations
                self.translations[lang] = gettext.NullTranslations()
    
    def get(self, message_id: str, lang: str = None, **kwargs) -> str:
        """
        Get translated message
        
        Args:
            message_id: Message ID from .po file
            lang: Language code (default: DEFAULT_LANGUAGE)
            **kwargs: Format arguments for the message
        
        Returns:
            Translated and formatted message
        """
        if lang is None:
            lang = self.DEFAULT_LANGUAGE
        
        # Fallback to default language if requested language not supported
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = self.DEFAULT_LANGUAGE
        
        # Get translation
        translation = self.translations.get(lang)
        if translation is None:
            return message_id
        
        # Get translated text
        translated = translation.gettext(message_id)
        
        # If translation not found, return the message_id
        if translated == message_id and lang != self.DEFAULT_LANGUAGE:
            # Try fallback to default language
            translation = self.translations.get(self.DEFAULT_LANGUAGE)
            if translation:
                translated = translation.gettext(message_id)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                translated = translated.format(**kwargs)
            except (KeyError, ValueError) as e:
                print(f"⚠️ Warning: Could not format message '{message_id}': {e}")
        
        return translated
    
    def get_language_name(self, lang: str) -> str:
        """Get display name for language"""
        names = {
            'fa': 'فارسی',
            'en': 'English'
        }
        return names.get(lang, lang)
    
    def get_language_flag(self, lang: str) -> str:
        """Get flag emoji for language"""
        flags = {
            'fa': '🇮🇷',
            'en': '🇬🇧'
        }
        return flags.get(lang, '🌐')


# Global instance
_i18n_instance: Optional[I18n] = None


def get_i18n() -> I18n:
    """Get or create global i18n instance"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def t(message_id: str, lang: str = None, **kwargs) -> str:
    """
    Shorthand for translation
    
    Args:
        message_id: Message ID from .po file
        lang: Language code
        **kwargs: Format arguments
    
    Returns:
        Translated message
    """
    return get_i18n().get(message_id, lang, **kwargs)


def set_user_language(user_id: int, language: str):
    """
    Set user's preferred language (to be stored in database)
    This is a placeholder - actual implementation should store in database
    """
    # This will be implemented with the state manager
    pass


def get_user_language(user_id: int) -> str:
    """
    Get user's preferred language from database
    This is a placeholder - actual implementation should retrieve from database
    """
    # This will be implemented with the state manager
    return I18n.DEFAULT_LANGUAGE
