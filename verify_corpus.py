"""Phase 1c + 2 verification. Run: .venv/bin/python verify_corpus.py"""
import os
import sys

os.environ.setdefault("OPENAI_API_KEY", "sk-dummy-for-import-test")

results = []


def check(name, fn):
    try:
        results.append(("PASS", name, fn()))
    except Exception as exc:
        results.append(("FAIL", name, f"{type(exc).__name__}: {exc}"))


def corpus_validates():
    from tools import get_corpus
    corpus = get_corpus()
    corpus.check_totals()
    return f"{corpus.meta.total} documents, hash {corpus.meta.contentHash[:12]}"


def catalog_is_sane():
    with open("corpus/catalog.txt", encoding="utf-8") as handle:
        catalog = handle.read()
    for needle in ("sre-agent", "Blog posts", "Tools he uses", "get_content"):
        assert needle in catalog, f"catalogue missing {needle!r}"
    tokens = len(catalog) // 4
    assert tokens < 2500, f"catalogue too big: ~{tokens} tokens"
    return f"~{tokens} tokens, all sections present"


def sre_agent_resolves():
    """The exact failure from the live test: it answered with the PhD project."""
    from tools import get_content
    out = get_content("sre-agent")
    assert "SRE Agent" in out, out[:200]
    assert "phd-information-technology" not in out, "still resolving to the wrong project"
    assert "/projects/sre-agent/" in out, "url missing"
    return out.splitlines()[0]


def phd_topic_is_reachable():
    """Also failed live: it claimed the research topic was not in its data."""
    from tools import get_cv_section
    education = get_cv_section("education")
    assert "Multi-Agent" in education, education[:300]
    return "education section carries the PhD research topic"


def search_finds_posts():
    from tools import search_content
    out = search_content("what does it cost to run a chatbot", kind="post")
    assert "[1]" in out, out[:200]
    return f"{out.count('url:')} post hits, previously posts were not indexed at all"


def search_finds_tools():
    from tools import search_content
    out = search_content("which editor does he use", kind="tool")
    assert "[1]" in out, out[:200]
    return "tools are searchable, previously they were not in the index at all"


def url_resolution_by_path():
    from tools import get_content
    out = get_content("/posts/how-this-site-is-built/")
    assert "how this site" in out.lower() or "site is built" in out.lower(), out[:200]
    return "site URLs resolve as ids too"


def unknown_id_is_honest():
    from tools import get_content
    out = get_content("does-not-exist")
    assert "No item with id" in out, out[:200]
    return "unknown ids are refused rather than guessed"


def tool_count():
    from tools import tools
    names = [t.__name__ for t in tools]
    assert len(names) == 4, names
    return f"{len(names)} tools: {', '.join(names)} (was 7)"


def agent_loads_catalog():
    from agent import SYSTEM_MESSAGE
    content = SYSTEM_MESSAGE.content
    assert "Content catalogue" in content, "catalogue not in system prompt"
    assert "sre-agent" in content, "ids not visible to the model"
    return f"system prompt is ~{len(content) // 4} tokens including the catalogue"


check("corpus validates", corpus_validates)
check("catalogue is sane", catalog_is_sane)
check("sre-agent resolves correctly", sre_agent_resolves)
check("PhD topic reachable", phd_topic_is_reachable)
check("search finds posts", search_finds_posts)
check("search finds tools", search_finds_tools)
check("url resolves as id", url_resolution_by_path)
check("unknown id refused", unknown_id_is_honest)
check("tool count", tool_count)
check("agent loads catalogue", agent_loads_catalog)

print("\n" + "=" * 72)
for status, name, detail in results:
    print(f"[{status}] {name}: {detail}")
print("=" * 72)
failed = [r for r in results if r[0] == "FAIL"]
print(f"{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
