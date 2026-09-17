"""Holds website content that reads like tunnel setup back from the Space.

Hugging Face paused this Space in September because the corpus carries prose
from a home lab blog post describing a Cloudflare tunnel. Their review cleared
it: writing about such tools is not a violation, using them is. The documents
that were reviewed are recorded in corpus/reviewed-vocabulary.json.

The corpus is regenerated from the website with no human in the loop, so new
writing on the same subjects would otherwise reach the Space unseen. This fails
the refresh job instead, which leaves the decision with a person.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus" / "corpus.json"
BASELINE = ROOT / "corpus" / "reviewed-vocabulary.json"

# Matched as plain substrings, which over-reports on purpose: a false positive
# costs one review, a miss costs the Space. Bare "tor" and "worker" are left out
# because they hide inside ordinary words and in agent vocabulary.
TERMS = [
    "cloudflare",
    "cloudflared",
    "tunnel",
    "proxy",
    "proxies",
    "vpn",
    "vnc",
    "ngrok",
    "localtunnel",
    "pagekite",
    "serveo",
    "zrok",
    "chisel",
    "frp",
    "wireguard",
    "openvpn",
    "tailscale",
    "shadowsocks",
    "v2ray",
    "sing-box",
    "socat",
    "autossh",
    "stunnel",
    "tor browser",
    ".onion",
    "remote desktop",
]


def scan(corpus_path: Path) -> dict[str, list[str]]:
    """Maps each document id to the flagged terms it contains."""
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    found: dict[str, list[str]] = {}
    for doc in corpus["documents"]:
        haystack = " ".join(
            str(doc.get(field) or "")
            for field in ("title", "description", "body")
        ).lower()
        hits = sorted(term for term in TERMS if term in haystack)
        if hits:
            found[doc["id"]] = hits
    return found


def url_for(corpus_path: Path, doc_id: str) -> str:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    for doc in corpus["documents"]:
        if doc["id"] == doc_id:
            return doc.get("url", "")
    return ""


def load_baseline() -> dict[str, list[str]]:
    if not BASELINE.exists():
        return {}
    return json.loads(BASELINE.read_text(encoding="utf-8"))["documents"]


def write_baseline(current: dict[str, list[str]]) -> None:
    payload = {
        "note": (
            "Documents whose website prose mentions tunnelling or proxy software. "
            "Reviewed with Hugging Face support and accepted as editorial content. "
            "Regenerate with: python check_corpus_policy.py --update"
        ),
        "documents": dict(sorted(current.items())),
    }
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="record the current corpus as reviewed",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=CORPUS,
        help="corpus to check, for testing the guard itself",
    )
    args = parser.parse_args()

    current = scan(args.corpus)

    if args.update:
        write_baseline(current)
        print(f"Recorded {len(current)} reviewed document(s) in {BASELINE.name}:")
        for doc_id, terms in sorted(current.items()):
            print(f"  {doc_id}  ->  {', '.join(terms)}")
        return 0

    baseline = load_baseline()
    new_docs = {k: v for k, v in current.items() if k not in baseline}
    new_terms = {
        k: sorted(set(v) - set(baseline[k]))
        for k, v in current.items()
        if k in baseline and set(v) - set(baseline[k])
    }

    if not new_docs and not new_terms:
        print(f"Corpus policy check passed. {len(current)} reviewed document(s), no new ones.")
        return 0

    print("Corpus policy check FAILED.\n")
    if new_docs:
        print("New documents using tunnelling or proxy vocabulary:")
        for doc_id, terms in sorted(new_docs.items()):
            print(f"  {doc_id}")
            print(f"      terms: {', '.join(terms)}")
            url = url_for(args.corpus, doc_id)
            if url:
                print(f"      url:   {url}")
    if new_terms:
        print("\nReviewed documents that gained new terms:")
        for doc_id, terms in sorted(new_terms.items()):
            print(f"  {doc_id}")
            print(f"      new terms: {', '.join(terms)}")

    print(
        "\nNothing has been pushed to the Space.\n"
        "\nThis content has not been reviewed against the Hugging Face content policy,\n"
        "which prohibits using tunnelling and proxy tools but permits writing about them.\n"
        "\nIf it is ordinary editorial writing, accept it with:\n"
        "    curl -sSf https://marcellomartini.tech/agent-corpus.json -o corpus/corpus.json\n"
        "    python check_corpus_policy.py --update\n"
        "then commit corpus/reviewed-vocabulary.json and re-run this workflow.\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
