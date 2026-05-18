import html as _html
import re

_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def html_to_text(content: str) -> str:
    """Convert HTML content to plain text.

    Greenhouse returns double-escaped HTML in the ``content`` field
    (e.g. ``&lt;h2&gt;...&lt;/h2&gt;``).  Unescape → strip tags → collapse
    whitespace.
    """
    unescaped = _html.unescape(content)
    text = _TAG_PATTERN.sub(" ", unescaped)
    return _WHITESPACE_PATTERN.sub(" ", text).strip()
