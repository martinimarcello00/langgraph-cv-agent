"""Turns the site links in an answer into cards the website can render.

The agent already cites pages by URL, so cards are built from the answer's own
links rather than asked of the model as structured output. A card can then only
ever point at a document that exists: an invented link matches nothing and is
dropped, which is the property that makes this safe to render as a button.
"""

import re
from functools import lru_cache

from tools import SITE_URL, get_corpus

MAX_SUGGESTIONS = 3

# Most documents share a URL with others: all 17 CV entries sit on /about/ and
# all 30 tools on /tools/. A link to those should offer the page itself rather
# than one arbitrary entry from it.
_KIND_RANK = {"page": 0, "post": 1, "project": 2, "publication": 3, "tool": 4, "cv": 5}

_MARKDOWN_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?\s*(?:\"[^\"]*\")?\)")
_BARE_URL = re.compile(r"https?://[^\s<>\"')\]]+")


def _path_of(url: str) -> str:
    """Reduces a link to a comparable site path, or "" if it leaves the site."""
    url = url.strip()
    if url.startswith(SITE_URL):
        url = url[len(SITE_URL) :]
    elif url.startswith(("http://", "https://")):
        return ""
    url = url.split("#", 1)[0].split("?", 1)[0]
    if not url.startswith("/"):
        return ""
    trimmed = url.strip("/").lower()
    return f"/{trimmed}/" if trimmed else "/"


@lru_cache(maxsize=1)
def _cards_by_path() -> dict[str, dict]:
    best: dict[str, tuple[int, dict]] = {}
    for doc in get_corpus().documents:
        path = _path_of(doc.url)
        if not path:
            continue
        rank = _KIND_RANK.get(doc.kind, 9)
        if path in best and best[path][0] <= rank:
            continue
        best[path] = (
            rank,
            {
                "id": doc.id,
                "title": doc.title,
                "description": doc.description or "",
                "url": f"{SITE_URL}{doc.url}",
                "kind": doc.kind,
                "icon": doc.icon or "",
            },
        )
    return {path: card for path, (_, card) in best.items()}


def suggestions_for(answer: str) -> list[dict]:
    """Cards for the site pages an answer links to, in the order they appear."""
    if not answer:
        return []

    index = _cards_by_path()
    positioned = [(m.start(), m.group(1)) for m in _MARKDOWN_LINK.finditer(answer)]
    positioned += [(m.start(), m.group(0)) for m in _BARE_URL.finditer(answer)]
    positioned.sort(key=lambda pair: pair[0])

    cards: list[dict] = []
    seen: set[str] = set()
    for _, raw in positioned:
        card = index.get(_path_of(raw))
        if card is None or card["id"] in seen:
            continue
        seen.add(card["id"])
        cards.append(card)
        if len(cards) == MAX_SUGGESTIONS:
            break
    return cards
