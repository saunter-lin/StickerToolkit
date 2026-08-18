from __future__ import annotations

from unittest.mock import patch

from sticker_toolkit.ui.desktop.i18n import (
    TRANSLATIONS,
    language_for_locale,
    normalize_language,
    tr,
)


def test_system_locale_mapping() -> None:
    for locale in ("zh-TW", "zh_HK", "zh-MO", "zh_Hant"):
        assert language_for_locale(locale) == "zh_TW"
    for locale in ("zh-CN", "zh_SG", "zh-Hans"):
        assert language_for_locale(locale) == "zh_CN"
    for locale in ("en_US", "ja_JP", "fr-FR", ""):
        assert language_for_locale(locale) == "en"


def test_saved_language_has_priority() -> None:
    assert normalize_language("en", "zh_TW") == "en"
    assert normalize_language("zh_CN", "en_US") == "zh_CN"
    assert normalize_language(None, "zh_TW") == "zh_TW"
    assert normalize_language("invalid", "zh_CN") == "zh_CN"


def test_translation_catalogs_have_identical_keys() -> None:
    expected = set(TRANSLATIONS["en"])
    assert expected
    for language in ("zh_TW", "zh_CN"):
        assert set(TRANSLATIONS[language]) == expected


def test_variable_translation_and_missing_key_fallback() -> None:
    assert tr("zh_TW", "batch.count", count=7) == "已選擇 7 / 16 張"
    assert tr("zh_CN", "summary.stickers", platform="LINE", count=16) == "LINE 贴图：16 张"
    assert tr("en", "unknown.translation.key") == "unknown.translation.key"


def test_missing_language_entry_falls_back_to_english() -> None:
    with patch.dict(TRANSLATIONS, {"zh_CN": {}}, clear=False):
        assert tr("zh_CN", "button.start") == "Start Processing"


def test_background_preset_labels_are_translated() -> None:
    assert tr("zh_TW", "label.background_preset") == "預設背景色："
    assert tr("zh_TW", "background_preset.darkblue") == "深藍"
    assert tr("zh_CN", "background_preset.custom") == "自定义…"
    assert tr("en", "background_preset.offwhite") == "Off-white"
