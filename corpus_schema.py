"""Schema for the corpus the website publishes.

Validated in CI before it is committed, so a malformed export fails the refresh
instead of quietly producing an index full of empty documents.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, field_validator

CorpusKind = Literal["post", "project", "page", "tool", "publication", "cv"]

# Long-form kinds get chunked; the rest are short enough to index whole.
PROSE_KINDS = {"post", "project", "page"}


class CorpusDoc(BaseModel):
    id: str
    kind: CorpusKind
    url: str
    title: str
    description: str = ""
    body: str = ""
    date: str | None = None
    categories: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    icon: str = ""
    weight: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("url")
    @classmethod
    def url_is_addressable(cls, value: str) -> str:
        if not value.startswith(("/", "http://", "https://")):
            raise ValueError(f"url must be site-relative or absolute, got {value!r}")
        return value

    @field_validator("title")
    @classmethod
    def title_is_present(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


class CorpusMeta(BaseModel):
    contentHash: str
    generatedAt: str
    counts: Dict[str, int]
    total: int


class Corpus(BaseModel):
    meta: CorpusMeta
    documents: List[CorpusDoc]

    @field_validator("documents")
    @classmethod
    def documents_are_usable(cls, docs: List[CorpusDoc]) -> List[CorpusDoc]:
        if not docs:
            raise ValueError("corpus contains no documents")

        seen = set()
        for doc in docs:
            if doc.id in seen:
                raise ValueError(f"duplicate document id {doc.id!r}")
            seen.add(doc.id)

        # A prose document with no body means the site's MDX stripping regressed.
        empty = [d.id for d in docs if d.kind in PROSE_KINDS and not d.body.strip()]
        if empty:
            raise ValueError(f"prose documents with empty body: {empty}")

        return docs

    def check_totals(self) -> None:
        """Meta and documents must agree, or something truncated the export."""
        if self.meta.total != len(self.documents):
            raise ValueError(
                f"meta.total is {self.meta.total} but {len(self.documents)} documents were sent"
            )
