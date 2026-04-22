"""Minimal i18n utility for UI strings (RU / EN)."""

from __future__ import annotations

from byrds.i18n.strings import STRINGS

_current_lang = "ru"


def set_language(lang: str) -> None:
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang


def current_language() -> str:
    return _current_lang


def tr(key: str, **fmt: object) -> str:
    """Translate a string key into the current language."""
    bundle = STRINGS.get(_current_lang) or STRINGS["en"]
    template = bundle.get(key) or STRINGS["en"].get(key) or key
    if fmt:
        try:
            return template.format(**fmt)
        except (KeyError, IndexError):
            return template
    return template
