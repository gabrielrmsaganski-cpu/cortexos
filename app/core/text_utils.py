from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:-]*")
SPACE_RE = re.compile(r"\\s+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\\s+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "you",
    "your",
}


def normalize_text(text: str) -> str:
    return SPACE_RE.sub(" ", text.strip()).lower()


def content_sha256(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def extract_keywords(text: str) -> list[str]:
    keywords: list[str] = []
    for token in tokenize(text):
        if len(token) < 3 or token in STOP_WORDS:
            continue
        keywords.append(token)
    return keywords


def lexical_overlap_score(query: str, passage: str) -> float:
    q = set(extract_keywords(query))
    if not q:
        return 0.0
    p = set(extract_keywords(passage))
    return len(q & p) / len(q)


def sentence_chunks(text: str, target_chars: int, overlap_chars: int) -> list[tuple[str, int, int]]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= target_chars:
        return [(text, 0, len(text))]

    sentences = SENTENCE_RE.split(text)
    chunks: list[tuple[str, int, int]] = []
    start_char = 0
    cursor = 0
    current: list[str] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and sum(len(s) + 1 for s in current) + len(sentence) > target_chars:
            chunk_text = " ".join(current).strip()
            end_char = start_char + len(chunk_text)
            chunks.append((chunk_text, start_char, end_char))
            overlap_text = chunk_text[max(0, len(chunk_text) - overlap_chars) :]
            start_char = max(0, end_char - len(overlap_text))
            current = [overlap_text.strip()] if overlap_text.strip() else []
        if not current:
            start_char = cursor
        current.append(sentence)
        cursor += len(sentence) + 1

    if current:
        chunk_text = " ".join(current).strip()
        end_char = min(len(text), start_char + len(chunk_text))
        chunks.append((chunk_text, start_char, end_char))
    return chunks


def hashed_dense_vector(text: str, dim: int) -> list[float]:
    vec = [0.0] * dim
    counts = Counter(tokenize(text))
    if not counts:
        return vec
    for token, count in counts.items():
        idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
        vec[idx] += float(count)
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def hashed_sparse_vector(text: str) -> tuple[list[int], list[float]]:
    counts = Counter(tokenize(text))
    if not counts:
        return [], []
    indices: list[int] = []
    values: list[float] = []
    for token, count in counts.items():
        indices.append(int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % 100_000)
        values.append(1.0 + math.log(count))
    return indices, values
