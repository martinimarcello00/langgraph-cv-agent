import json
import logging
import os
from functools import lru_cache
from typing import Literal, Optional

import requests
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from corpus_schema import Corpus
from embeddings import get_embeddings

# --- Initialization ---
load_dotenv()
logger = logging.getLogger(__name__)

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "corpus", "corpus.json")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
SITE_URL = os.getenv("SITE_URL", "https://marcellomartini.tech")

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_URL = os.getenv("MAILGUN_URL")
MAILGUN_FROM = os.getenv("MAILGUN_SENDER")

CvSection = Literal[
    "experience", "education", "awards", "certifications", "volunteer", "activities"
]


# --- Corpus access ---

@lru_cache(maxsize=1)
def get_corpus() -> Corpus:
    with open(CORPUS_PATH, "r", encoding="utf-8") as handle:
        return Corpus.model_validate(json.load(handle))


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    return Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=get_embeddings())


@lru_cache(maxsize=1)
def get_bm25() -> Optional[BM25Retriever]:
    """Built once. It used to be rebuilt from the whole collection on every search."""
    raw = get_vectorstore().get(include=["documents", "metadatas"])
    documents = [
        Document(page_content=text, metadata=(raw["metadatas"][i] or {}))
        for i, text in enumerate(raw.get("documents") or [])
    ]
    if not documents:
        logger.warning("Vector store is empty, keyword search disabled.")
        return None
    retriever = BM25Retriever.from_documents(documents)
    retriever.k = 6
    return retriever


def _format_hit(index: int, doc: Document) -> str:
    meta = doc.metadata
    header = f"[{index}] {meta.get('title', 'Untitled')} ({meta.get('kind', 'content')})"
    location = f"id: {meta.get('slug', '')} | url: {SITE_URL}{meta.get('url', '')}"
    return f"{header}\n{location}\n{doc.page_content.strip()}\n---"


# --- Tools ---

def search_content(query: str, kind: str = "") -> str:
    """Searches everything on Marcello's website: blog posts, projects, pages, the
    tools he uses, publications and CV entries.

    Use this when you do not already know which item answers the question. If the
    catalogue in your instructions already names the right item, call get_content
    instead, which is exact and faster.

    Args:
        query: what to look for, in natural language.
        kind: optional filter, one of post, project, page, tool, publication, cv.
    """
    try:
        vector_hits = get_vectorstore().similarity_search(query, k=6)
        bm25 = get_bm25()
        keyword_hits = bm25.invoke(query) if bm25 else []

        # Semantic first, keyword results fill the gaps.
        merged: list[Document] = []
        seen: set[str] = set()
        for doc in [*vector_hits, *keyword_hits]:
            if kind and doc.metadata.get("kind") != kind:
                continue
            key = f"{doc.metadata.get('doc_id')}|{doc.page_content[:80]}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(doc)

        if not merged:
            suffix = f" (filtered to kind={kind})" if kind else ""
            return f"Nothing found for '{query}'.{suffix}"

        return "\n\n".join(_format_hit(i, doc) for i, doc in enumerate(merged[:5], 1))
    except Exception as exc:
        logger.error("search_content failed: %s", exc, exc_info=True)
        return "Search is unavailable right now."


def get_content(item_id: str) -> str:
    """Returns one item from the website in full: a project, blog post, page, tool,
    publication or CV entry.

    Accepts the id shown in the catalogue (for example "sre-agent"), a full id
    ("projects/sre-agent"), or a site URL.
    """
    try:
        needle = item_id.strip().strip("/").lower()
        documents = get_corpus().documents

        match = next(
            (
                d
                for d in documents
                if needle in (d.id.lower(), d.id.split("/", 1)[-1].lower())
                or d.url.strip("/").lower() == needle
            ),
            None,
        )
        # Fall back to the title, so a human-sounding name still resolves.
        if match is None:
            match = next((d for d in documents if d.title.lower() == needle), None)

        if match is None:
            return (
                f"No item with id '{item_id}'. Use the catalogue ids from your "
                "instructions, or call search_content."
            )

        lines = [f"# {match.title}", f"url: {SITE_URL}{match.url}"]
        if match.description:
            lines.append(f"summary: {match.description}")
        if match.technologies:
            lines.append(f"technologies: {', '.join(match.technologies)}")
        when = match.extra.get("year") or match.date
        if when:
            lines.append(f"when: {when}")
        if match.body.strip():
            lines += ["", match.body.strip()]
        return "\n".join(lines)
    except Exception as exc:
        logger.error("get_content failed: %s", exc, exc_info=True)
        return "That item could not be read right now."


def get_cv_section(section: CvSection) -> str:
    """Returns a section of Marcello's CV: experience, education, awards,
    certifications, volunteer or activities.
    """
    try:
        entries = [
            d
            for d in get_corpus().documents
            if d.kind == "cv" and str(d.extra.get("section", "")) == section
        ]
        if not entries:
            return f"No CV entries found for '{section}'."
        return "\n\n".join(f"- {entry.body.strip()}" for entry in entries)
    except Exception as exc:
        logger.error("get_cv_section failed: %s", exc, exc_info=True)
        return "The CV could not be read right now."


def send_cv_email(email_address: str) -> str:
    """
    Sends Marcello's CV to the specified email address.
    """
    try:
        # Basic validation
        if "@" not in email_address or "." not in email_address:
             return "Error: Invalid email address format. Please provide a valid email."
             
        response = requests.post(
            MAILGUN_URL,
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": MAILGUN_FROM,
                "to": email_address,
                "subject": "Hello from Marcello Martini",
                "template": "send cv",
                "h:X-Mailgun-Variables": '{"test": "test"}' 
            },
            timeout=10
        )
        
        response.raise_for_status()
        return f"CV successfully sent to {email_address}!"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Mailgun API Error: {e}")
        return f"Error sending email: Failed to connect to mail service." 
    except Exception as e:
        logger.error(f"Unexpected error in send_cv_email: {e}")
        return f"Error sending email: {str(e)}"

# Export the list of tools for the agent
tools = [search_content, get_content, get_cv_section, send_cv_email]

