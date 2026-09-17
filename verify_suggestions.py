"""Smoke test for the suggestion cards. Run: python verify_suggestions.py"""

import sys

from suggestions import MAX_SUGGESTIONS, suggestions_for

SITE = "https://marcellomartini.tech"
failures = 0


def check(label: str, condition: bool, detail: object = "") -> None:
    global failures
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    if not condition:
        failures += 1
        if detail:
            print(f"       {detail}")


cards = suggestions_for(f"I wrote about it in [The price]({SITE}/posts/chatbot-without-a-server/).")
check("a real link yields a card", len(cards) == 1 and cards[0]["kind"] == "post", cards)

# 17 CV entries share /about/ and 30 tools share /tools/, so a plain URL index
# would return an arbitrary one of them.
cards = suggestions_for(f"See [my tools]({SITE}/tools/).")
check("/tools/ resolves to the page", len(cards) == 1 and cards[0]["id"] == "pages/tools", cards)
cards = suggestions_for(f"See [about]({SITE}/about/).")
check("/about/ resolves to the page", len(cards) == 1 and cards[0]["id"] == "pages/about", cards)

check(
    "invented links are dropped",
    suggestions_for(f"[x]({SITE}/projects/does-not-exist/)") == [],
)
check("external links are dropped", suggestions_for("[x](https://example.com/a/)") == [])
check("no links yields no cards", suggestions_for("He is a PhD student.") == [])
check("empty answer is safe", suggestions_for("") == [])

for label, text in {
    "bare url": f"See {SITE}/posts/how-this-site-is-built/",
    "no trailing slash": f"[x]({SITE}/posts/how-this-site-is-built)",
    "anchor": f"[x]({SITE}/posts/how-this-site-is-built/#build)",
    "site relative": "[x](/posts/how-this-site-is-built/)",
}.items():
    check(f"resolves a {label}", len(suggestions_for(text)) == 1, text)

check(
    "repeated links are deduplicated",
    len(suggestions_for(f"[a]({SITE}/tools/) [b]({SITE}/tools/)")) == 1,
)

many = " ".join(
    f"[{i}]({SITE}{path})"
    for i, path in enumerate(
        [
            "/posts/terminal-from-a-git-clone/",
            "/posts/how-this-site-is-built/",
            "/tools/",
            "/about/",
        ]
    )
)
cards = suggestions_for(many)
check(f"capped at {MAX_SUGGESTIONS}", len(cards) == MAX_SUGGESTIONS, cards)
check(
    "order follows the answer",
    [c["id"] for c in cards][:2]
    == ["posts/terminal-from-a-git-clone", "posts/how-this-site-is-built"],
    [c["id"] for c in cards],
)
check(
    "every card has what the widget renders",
    all(c["title"] and c["url"].startswith(f"{SITE}/") and c["kind"] for c in cards),
    cards,
)

print("=" * 72)
print(f"{'all checks passed' if failures == 0 else f'{failures} check(s) failed'}")
sys.exit(1 if failures else 0)
