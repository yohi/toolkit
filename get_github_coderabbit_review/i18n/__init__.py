"""Internationalization (i18n) module for CodeRabbit fetcher."""

from .localization import (
    LocalizationManager,
    LocaleConfig,
    MessageCatalog,
    TranslationProvider
)

from .timezone_handler import (
    TimezoneHandler,
    TimezoneConfig,
    DateTimeFormatter,
    TimezoneConverter
)

from .content_localization import (
    ContentLocalizer,
    LocalizedContent,
    LanguageDetector,
    ContentTranslator
)

from .region_handler import (
    RegionHandler,
    RegionConfig,
    RegionalSettings,
    CurrencyFormatter,
    NumberFormatter
)

__all__ = [
    # Localization
    "LocalizationManager",
    "LocaleConfig",
    "MessageCatalog",
    "TranslationProvider",

    # Timezone
    "TimezoneHandler",
    "TimezoneConfig",
    "DateTimeFormatter",
    "TimezoneConverter",

    # Content Localization
    "ContentLocalizer",
    "LocalizedContent",
    "LanguageDetector",
    "ContentTranslator",

    # Regional Settings
    "RegionHandler",
    "RegionConfig",
    "RegionalSettings",
    "CurrencyFormatter",
    "NumberFormatter"
]
