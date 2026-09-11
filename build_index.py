"""Builds the vector index and the prompt catalogue from the website corpus.

Run at image build time, not at boot: the Space has an ephemeral disk and
restarts often, so anything computed here would otherwise be paid for on every
wake-up.
"""
import json
import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from corpus_schema import PROSE_KINDS, Corpus
from embeddings import EMBEDDING_MODEL_NAME, get_embeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "corpus", "corpus.json")
CATALOG_PATH = os.path.join(BASE_DIR, "corpus", "catalog.txt")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]
SITE_URL = os.getenv("SITE_URL", "https://marcellomartini.tech")
KIND_LABELS = {
    "project": "Projects",
    "post": "Blog posts",
    "page": "Pages",
    "publication": "Publications",
}
# Spelling the pattern out once per section beats making the model infer it.
URL_PATTERNS = {
    "project": "/projects/<id>/",
    "post": "/posts/<id>/",
    "page": "/<id>/",
}


def load_corpus() -> Corpus:
    with open(CORPUS_PATH, "r", encoding="utf-8") as handle:
        corpus = Corpus.model_validate(json.load(handle))
    corpus.check_totals()
    return corpus


def short_id(doc_id: str) -> str:
    """`projects/sre-agent` -> `sre-agent`, which is what the catalogue shows."""
    return doc_id.split("/", 1)[-1]


def chunk_documents(corpus: Corpus) -> list[Document]:
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS, strip_headers=False)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[Document] = []
    for doc in corpus.documents:
        # Chroma only accepts scalar metadata, so lists are flattened here.
        metadata = {
            "doc_id": doc.id,
            "slug": short_id(doc.id),
            "kind": doc.kind,
            "url": doc.url,
            "title": doc.title,
            "description": doc.description,
            "icon": doc.icon,
            "date": doc.date or "",
            "technologies": ", ".join(doc.technologies),
            "categories": ", ".join(doc.categories),
        }

        text = doc.body.strip() or f"{doc.title}\n\n{doc.description}"

        if doc.kind in PROSE_KINDS:
            sections = markdown_splitter.split_text(text) or [Document(page_content=text)]
            for section in sections:
                section.metadata = {**metadata, **section.metadata}
            pieces = text_splitter.split_documents(sections)
        else:
            # Short records stay whole: splitting a tool note loses more than it gains.
            pieces = [Document(page_content=text, metadata=dict(metadata))]

        # Every chunk carries its title, so a mid-document match still retrieves
        # something the model can attribute.
        for piece in pieces:
            if doc.title.lower() not in piece.page_content.lower():
                piece.page_content = f"{doc.title}\n\n{piece.page_content}"
            chunks.append(piece)

    return chunks


def build_catalog(corpus: Corpus) -> str:
    """A compact index of everything, injected into the system prompt.

    This is what lets common questions be answered with no tool call, and stops
    the model guessing at slugs it cannot see.
    """
    lines = [
        "# Content catalogue",
        "",
        "Everything listed here exists on marcellomartini.tech.",
        'Read any item in full with get_content("<id>").',
        "The id is for tool calls and for building links. Never show it to the user:",
        "write the title as a link instead.",
    ]

    for kind in ("project", "post", "page", "publication"):
        docs = [d for d in corpus.documents if d.kind == kind]
        if not docs:
            continue
        docs.sort(key=lambda d: (d.weight, d.date or "", d.title))
        if kind == "post":
            docs.sort(key=lambda d: d.date or "", reverse=True)

        heading = f"## {KIND_LABELS[kind]} ({len(docs)})"
        pattern = URL_PATTERNS.get(kind)
        if pattern:
            heading += f"  -  link as {SITE_URL}{pattern}"
        lines += ["", heading]

        for doc in docs:
            parts = [f"- {short_id(doc.id)} | {doc.title}"]
            when = doc.extra.get("year") or doc.date
            if when:
                parts.append(f"({when})")
            summary = doc.description.strip()
            if len(summary) > 110:
                summary = summary[:107].rstrip() + "..."
            if summary:
                parts.append(f"| {summary}")
            if doc.technologies:
                parts.append(f"| tech: {', '.join(doc.technologies[:8])}")
            # Publications point at a DOI, so the pattern above does not apply.
            if pattern is None:
                parts.append(f"| url: {doc.url}")
            lines.append(" ".join(parts))

    tools = [d for d in corpus.documents if d.kind == "tool"]
    if tools:
        by_category: dict[str, list[str]] = {}
        for tool in tools:
            category = str(tool.extra.get("category", "other"))
            by_category.setdefault(category, []).append(tool.title)
        lines += ["", f"## Tools he uses ({len(tools)})"]
        for category, names in sorted(by_category.items()):
            lines.append(f"- {category}: {', '.join(sorted(names))}")

    cv = [d for d in corpus.documents if d.kind == "cv"]
    if cv:
        sections = sorted({str(d.extra.get("section", "")) for d in cv} - {""})
        lines += [
            "",
            f"## CV ({len(cv)} entries)",
            f"- sections available via get_cv_section: {', '.join(sections)}",
        ]

    return "\n".join(lines) + "\n"


def main() -> None:
    print("Loading corpus...")
    corpus = load_corpus()
    print(f"Corpus {corpus.meta.contentHash[:12]} with {corpus.meta.total} documents")
    print(f"   counts: {corpus.meta.counts}")

    print("Chunking...")
    chunks = chunk_documents(corpus)
    print(f"   {len(chunks)} chunks")

    print(f"Embedding with {EMBEDDING_MODEL_NAME}...")
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=CHROMA_DB_DIR,
    )
    print(f"   stored in {CHROMA_DB_DIR}")

    catalog = build_catalog(corpus)
    with open(CATALOG_PATH, "w", encoding="utf-8") as handle:
        handle.write(catalog)
    # Rough token estimate; the catalogue rides in every request.
    print(f"Catalogue: {len(catalog)} chars, about {len(catalog) // 4} tokens")


if __name__ == "__main__":
    main()
