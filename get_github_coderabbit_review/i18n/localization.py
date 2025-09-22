"""Localization management for international support."""

import gettext
import json
import locale
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SupportedLanguage(Enum):
    """Supported languages enumeration."""

    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    KOREAN = "ko"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"


@dataclass
class LocaleConfig:
    """Locale configuration."""

    language: SupportedLanguage
    country_code: Optional[str] = None
    encoding: str = "UTF-8"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    number_format: str = "{:,.2f}"
    currency_symbol: str = "$"
    decimal_separator: str = "."
    thousands_separator: str = ","
    rtl: bool = False  # Right-to-left languages

    @property
    def locale_code(self) -> str:
        """Get full locale code."""
        if self.country_code:
            return f"{self.language.value}_{self.country_code}"
        return self.language.value

    @property
    def is_rtl(self) -> bool:
        """Check if language is right-to-left."""
        return self.language in [SupportedLanguage.ARABIC] or self.rtl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "country_code": self.country_code,
            "locale_code": self.locale_code,
            "encoding": self.encoding,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "datetime_format": self.datetime_format,
            "number_format": self.number_format,
            "currency_symbol": self.currency_symbol,
            "decimal_separator": self.decimal_separator,
            "thousands_separator": self.thousands_separator,
            "rtl": self.is_rtl,
        }


@dataclass
class MessageCatalog:
    """Message catalog for translations."""

    language: SupportedLanguage
    messages: Dict[str, str] = field(default_factory=dict)
    plurals: Dict[str, Dict[str, str]] = field(default_factory=dict)
    contexts: Dict[str, Dict[str, str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, key: str, message: str, context: Optional[str] = None) -> None:
        """Add translated message.

        Args:
            key: Message key
            message: Translated message
            context: Optional context for disambiguation
        """
        if context:
            if context not in self.contexts:
                self.contexts[context] = {}
            self.contexts[context][key] = message
        else:
            self.messages[key] = message

    def add_plural(self, key: str, singular: str, plural: str) -> None:
        """Add plural form.

        Args:
            key: Message key
            singular: Singular form
            plural: Plural form
        """
        self.plurals[key] = {"singular": singular, "plural": plural}

    def get_message(
        self, key: str, context: Optional[str] = None, default: Optional[str] = None
    ) -> str:
        """Get translated message.

        Args:
            key: Message key
            context: Optional context
            default: Default message if not found

        Returns:
            Translated message
        """
        if context and context in self.contexts and key in self.contexts[context]:
            return self.contexts[context][key]

        if key in self.messages:
            return self.messages[key]

        return default or key

    def get_plural(
        self,
        key: str,
        count: int,
        default_singular: Optional[str] = None,
        default_plural: Optional[str] = None,
    ) -> str:
        """Get plural form.

        Args:
            key: Message key
            count: Count for plural determination
            default_singular: Default singular form
            default_plural: Default plural form

        Returns:
            Appropriate plural form
        """
        if key in self.plurals:
            forms = self.plurals[key]
            # Simple English plural rules (expand for other languages)
            if count == 1:
                return forms["singular"]
            else:
                return forms["plural"]

        # Fallback to regular messages
        message = self.get_message(key)
        if message != key:
            return message

        # Use defaults
        if count == 1:
            return default_singular or key
        else:
            return default_plural or key

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "messages": self.messages,
            "plurals": self.plurals,
            "contexts": self.contexts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageCatalog":
        """Create from dictionary."""
        return cls(
            language=SupportedLanguage(data["language"]),
            messages=data.get("messages", {}),
            plurals=data.get("plurals", {}),
            contexts=data.get("contexts", {}),
            metadata=data.get("metadata", {}),
        )


class TranslationProvider:
    """Translation provider interface."""

    def __init__(self, translations_path: Optional[Path] = None):
        """Initialize translation provider.

        Args:
            translations_path: Path to translations directory
        """
        self.translations_path = translations_path or Path(__file__).parent / "translations"
        self.catalogs: Dict[SupportedLanguage, MessageCatalog] = {}

        # Load translations
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files."""
        if not self.translations_path.exists():
            logger.warning(f"Translations directory not found: {self.translations_path}")
            return

        for lang_file in self.translations_path.glob("*.json"):
            try:
                lang_code = lang_file.stem
                language = SupportedLanguage(lang_code)

                with open(lang_file, encoding="utf-8") as f:
                    data = json.load(f)

                catalog = MessageCatalog.from_dict(data)
                self.catalogs[language] = catalog

                logger.info(
                    f"Loaded translations for {language.value}: {len(catalog.messages)} messages"
                )

            except Exception as e:
                logger.error(f"Failed to load translation file {lang_file}: {e}")

    def get_catalog(self, language: SupportedLanguage) -> Optional[MessageCatalog]:
        """Get message catalog for language.

        Args:
            language: Target language

        Returns:
            Message catalog or None
        """
        return self.catalogs.get(language)

    def add_catalog(self, catalog: MessageCatalog) -> None:
        """Add message catalog.

        Args:
            catalog: Message catalog to add
        """
        self.catalogs[catalog.language] = catalog
        logger.info(f"Added catalog for {catalog.language.value}")

    def save_catalog(self, language: SupportedLanguage) -> None:
        """Save catalog to file.

        Args:
            language: Language to save
        """
        if language not in self.catalogs:
            logger.warning(f"No catalog found for {language.value}")
            return

        catalog = self.catalogs[language]
        output_file = self.translations_path / f"{language.value}.json"

        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(catalog.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved catalog for {language.value} to {output_file}")

    def extract_messages_from_code(self, source_paths: List[Path]) -> Dict[str, str]:
        """Extract translatable messages from source code.

        Args:
            source_paths: Paths to source files

        Returns:
            Dictionary of message keys and default values
        """
        messages = {}

        # Patterns for extracting translatable strings
        patterns = [
            r'_\(["\']([^"\']+)["\']\)',  # _("message")
            r'gettext\(["\']([^"\']+)["\']\)',  # gettext("message")
            r'ngettext\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*,',  # ngettext("singular", "plural", count)
            r'translate\(["\']([^"\']+)["\']\)',  # translate("message")
        ]

        for source_path in source_paths:
            if source_path.is_file() and source_path.suffix == ".py":
                try:
                    with open(source_path, encoding="utf-8") as f:
                        content = f.read()

                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple):
                                # Plural forms
                                messages[match[0]] = match[0]  # Singular
                                messages[match[1]] = match[1]  # Plural
                            else:
                                messages[match] = match

                except Exception as e:
                    logger.error(f"Error processing {source_path}: {e}")

        logger.info(f"Extracted {len(messages)} translatable messages")
        return messages


class LocalizationManager:
    """Main localization manager."""

    def __init__(self, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """Initialize localization manager.

        Args:
            default_language: Default language
        """
        self.default_language = default_language
        self.current_language = default_language
        self.locale_configs: Dict[SupportedLanguage, LocaleConfig] = {}
        self.translation_provider = TranslationProvider()

        # Initialize default locale configs
        self._init_default_configs()

        # Set up gettext
        self._setup_gettext()

    def _init_default_configs(self) -> None:
        """Initialize default locale configurations."""
        # English (default)
        self.locale_configs[SupportedLanguage.ENGLISH] = LocaleConfig(
            language=SupportedLanguage.ENGLISH,
            country_code="US",
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            datetime_format="%Y-%m-%d %H:%M:%S",
            currency_symbol="$",
            decimal_separator=".",
            thousands_separator=",",
        )

        # Japanese
        self.locale_configs[SupportedLanguage.JAPANESE] = LocaleConfig(
            language=SupportedLanguage.JAPANESE,
            country_code="JP",
            date_format="%Y年%m月%d日",
            time_format="%H:%M:%S",
            datetime_format="%Y年%m月%d日 %H:%M:%S",
            currency_symbol="¥",
            decimal_separator=".",
            thousands_separator=",",
        )

        # Chinese Simplified
        self.locale_configs[SupportedLanguage.CHINESE_SIMPLIFIED] = LocaleConfig(
            language=SupportedLanguage.CHINESE_SIMPLIFIED,
            country_code="CN",
            date_format="%Y年%m月%d日",
            time_format="%H:%M:%S",
            datetime_format="%Y年%m月%d日 %H:%M:%S",
            currency_symbol="¥",
            decimal_separator=".",
            thousands_separator=",",
        )

        # German
        self.locale_configs[SupportedLanguage.GERMAN] = LocaleConfig(
            language=SupportedLanguage.GERMAN,
            country_code="DE",
            date_format="%d.%m.%Y",
            time_format="%H:%M:%S",
            datetime_format="%d.%m.%Y %H:%M:%S",
            currency_symbol="€",
            decimal_separator=",",
            thousands_separator=".",
        )

        # Arabic (RTL)
        self.locale_configs[SupportedLanguage.ARABIC] = LocaleConfig(
            language=SupportedLanguage.ARABIC,
            country_code="SA",
            date_format="%Y/%m/%d",
            time_format="%H:%M:%S",
            datetime_format="%Y/%m/%d %H:%M:%S",
            currency_symbol="ر.س",
            decimal_separator=".",
            thousands_separator=",",
            rtl=True,
        )

    def _setup_gettext(self) -> None:
        """Setup gettext for translation."""
        try:
            # Set up gettext domain
            locale_dir = self.translation_provider.translations_path / "gettext"
            if locale_dir.exists():
                gettext.bindtextdomain("coderabbit", str(locale_dir))
                gettext.textdomain("coderabbit")
        except Exception as e:
            logger.warning(f"Failed to setup gettext: {e}")

    def set_language(self, language: SupportedLanguage) -> None:
        """Set current language.

        Args:
            language: Language to set
        """
        if language not in self.locale_configs:
            logger.warning(f"Unsupported language: {language.value}")
            return

        self.current_language = language

        # Update system locale if possible
        try:
            config = self.locale_configs[language]
            locale.setlocale(locale.LC_ALL, config.locale_code)
        except Exception as e:
            logger.warning(f"Failed to set system locale: {e}")

        logger.info(f"Set language to {language.value}")

    def get_current_config(self) -> LocaleConfig:
        """Get current locale configuration.

        Returns:
            Current locale configuration
        """
        return self.locale_configs[self.current_language]

    def translate(self, key: str, context: Optional[str] = None, **kwargs) -> str:
        """Translate message.

        Args:
            key: Message key
            context: Optional context
            **kwargs: Format parameters

        Returns:
            Translated message
        """
        catalog = self.translation_provider.get_catalog(self.current_language)

        if catalog:
            message = catalog.get_message(key, context, key)
        else:
            message = key

        # Format message with parameters
        try:
            if kwargs:
                return message.format(**kwargs)
            return message
        except Exception as e:
            logger.warning(f"Translation formatting error: {e}")
            return message

    def translate_plural(self, key: str, count: int, **kwargs) -> str:
        """Translate plural message.

        Args:
            key: Message key
            count: Count for plural determination
            **kwargs: Format parameters

        Returns:
            Translated plural message
        """
        catalog = self.translation_provider.get_catalog(self.current_language)

        if catalog:
            message = catalog.get_plural(key, count, key, key + "s")
        else:
            # Simple English pluralization
            if count == 1:
                message = key
            else:
                message = key + "s"

        # Format message with parameters
        try:
            if kwargs:
                kwargs["count"] = count
                return message.format(**kwargs)
            return message
        except Exception as e:
            logger.warning(f"Plural translation formatting error: {e}")
            return message

    def format_date(self, date: datetime, format_type: str = "date") -> str:
        """Format date according to current locale.

        Args:
            date: Date to format
            format_type: Format type ("date", "time", "datetime")

        Returns:
            Formatted date string
        """
        config = self.get_current_config()

        if format_type == "date":
            return date.strftime(config.date_format)
        elif format_type == "time":
            return date.strftime(config.time_format)
        elif format_type == "datetime":
            return date.strftime(config.datetime_format)
        else:
            return date.isoformat()

    def format_number(self, number: Union[int, float], currency: bool = False) -> str:
        """Format number according to current locale.

        Args:
            number: Number to format
            currency: Whether to format as currency

        Returns:
            Formatted number string
        """
        config = self.get_current_config()

        # Format the number
        formatted = f"{number:,.2f}"

        # Replace separators according to locale
        if config.decimal_separator != "." or config.thousands_separator != ",":
            # Split into integer and decimal parts
            parts = formatted.split(".")
            integer_part = parts[0].replace(",", config.thousands_separator)
            decimal_part = parts[1] if len(parts) > 1 else "00"

            formatted = f"{integer_part}{config.decimal_separator}{decimal_part}"

        # Add currency symbol if requested
        if currency:
            if config.language == SupportedLanguage.ARABIC:
                # RTL currency formatting
                formatted = f"{formatted} {config.currency_symbol}"
            else:
                formatted = f"{config.currency_symbol}{formatted}"

        return formatted

    def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available languages.

        Returns:
            List of language information
        """
        languages = []

        for language, config in self.locale_configs.items():
            languages.append(
                {
                    "code": language.value,
                    "name": self._get_language_name(language),
                    "native_name": self._get_native_language_name(language),
                    "rtl": config.is_rtl,
                }
            )

        return languages

    def _get_language_name(self, language: SupportedLanguage) -> str:
        """Get English language name.

        Args:
            language: Language

        Returns:
            English language name
        """
        names = {
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.JAPANESE: "Japanese",
            SupportedLanguage.CHINESE_SIMPLIFIED: "Chinese (Simplified)",
            SupportedLanguage.CHINESE_TRADITIONAL: "Chinese (Traditional)",
            SupportedLanguage.KOREAN: "Korean",
            SupportedLanguage.GERMAN: "German",
            SupportedLanguage.FRENCH: "French",
            SupportedLanguage.SPANISH: "Spanish",
            SupportedLanguage.PORTUGUESE: "Portuguese",
            SupportedLanguage.RUSSIAN: "Russian",
            SupportedLanguage.ARABIC: "Arabic",
            SupportedLanguage.HINDI: "Hindi",
        }
        return names.get(language, language.value)

    def _get_native_language_name(self, language: SupportedLanguage) -> str:
        """Get native language name.

        Args:
            language: Language

        Returns:
            Native language name
        """
        names = {
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.JAPANESE: "日本語",
            SupportedLanguage.CHINESE_SIMPLIFIED: "简体中文",
            SupportedLanguage.CHINESE_TRADITIONAL: "繁體中文",
            SupportedLanguage.KOREAN: "한국어",
            SupportedLanguage.GERMAN: "Deutsch",
            SupportedLanguage.FRENCH: "Français",
            SupportedLanguage.SPANISH: "Español",
            SupportedLanguage.PORTUGUESE: "Português",
            SupportedLanguage.RUSSIAN: "Русский",
            SupportedLanguage.ARABIC: "العربية",
            SupportedLanguage.HINDI: "हिन्दी",
        }
        return names.get(language, language.value)

    def create_translation_template(self, source_paths: List[Path], output_path: Path) -> None:
        """Create translation template from source code.

        Args:
            source_paths: Source file paths
            output_path: Output template path
        """
        messages = self.translation_provider.extract_messages_from_code(source_paths)

        template = {
            "language": "template",
            "messages": messages,
            "plurals": {},
            "contexts": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "generator": "CodeRabbit LocalizationManager",
                "total_messages": len(messages),
            },
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        logger.info(f"Created translation template: {output_path}")


# Global localization manager
_global_manager: Optional[LocalizationManager] = None


def get_localization_manager() -> LocalizationManager:
    """Get global localization manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = LocalizationManager()
    return _global_manager


def set_localization_manager(manager: LocalizationManager) -> None:
    """Set global localization manager."""
    global _global_manager
    _global_manager = manager
    logger.info("Set global localization manager")


# Convenience functions
def _(message: str, **kwargs) -> str:
    """Translate message (shorthand).

    Args:
        message: Message to translate
        **kwargs: Format parameters

    Returns:
        Translated message
    """
    manager = get_localization_manager()
    return manager.translate(message, **kwargs)


def ngettext(singular: str, plural: str, count: int, **kwargs) -> str:
    """Translate plural message.

    Args:
        singular: Singular form
        plural: Plural form
        count: Count for plural determination
        **kwargs: Format parameters

    Returns:
        Translated plural message
    """
    manager = get_localization_manager()
    if count == 1:
        return manager.translate(singular, **kwargs)
    else:
        return manager.translate(plural, count=count, **kwargs)


def set_language(language: Union[str, SupportedLanguage]) -> None:
    """Set current language.

    Args:
        language: Language to set
    """
    if isinstance(language, str):
        language = SupportedLanguage(language)

    manager = get_localization_manager()
    manager.set_language(language)


def get_current_language() -> SupportedLanguage:
    """Get current language.

    Returns:
        Current language
    """
    manager = get_localization_manager()
    return manager.current_language


# Example usage
if __name__ == "__main__":
    # Initialize localization
    manager = LocalizationManager()

    # Set language to Japanese
    manager.set_language(SupportedLanguage.JAPANESE)

    # Translate messages
    print(manager.translate("Hello, World!"))
    print(manager.format_date(datetime.now()))
    print(manager.format_number(1234.56, currency=True))

    # Test plural forms
    print(manager.translate_plural("comment", 1))
    print(manager.translate_plural("comment", 5))
