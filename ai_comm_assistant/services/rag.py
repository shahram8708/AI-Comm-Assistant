"""Retrieval‑Augmented Generation (RAG) utilities.

This module encapsulates embedding of knowledge base entries using a
sentence‑transformer and retrieval using a FAISS index.  The index
is rebuilt lazily when first queried.  In a production system the
index would be persisted and updated when KB entries change.
"""

from __future__ import annotations

from typing import List

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from flask import current_app

from ..extensions import db
from ..models import KBEntry


class RAGService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2') -> None:
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.id_to_entry: dict[int, KBEntry] = {}

    def build_index(self) -> None:
        """Build the FAISS index from all KB entries in the database."""
        with current_app.app_context():
            entries = KBEntry.query.all()
        if not entries:
            self.index = None
            self.id_to_entry = {}
            return
        embeddings = self.model.encode([entry.content for entry in entries])
        embeddings = np.array(embeddings).astype('float32')
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        self.id_to_entry = {idx: entry for idx, entry in enumerate(entries)}

    def get_top_k(self, query: str, k: int = 3) -> List[str]:
        """Return the top‑k knowledge base passages most relevant to the query."""
        if self.index is None:
            self.build_index()
        if self.index is None or not self.id_to_entry:
            return []
        vector = self.model.encode([query])[0].astype('float32')
        distances, indices = self.index.search(np.array([vector]), min(k, len(self.id_to_entry)))
        snippets = []
        for idx in indices[0]:
            entry = self.id_to_entry.get(int(idx))
            if entry:
                snippets.append(entry.content)
        return snippets