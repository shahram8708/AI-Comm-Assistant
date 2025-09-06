"""Tests for retrieval‑augmented generation service."""

from ai_comm_assistant.services.rag import RAGService
from ai_comm_assistant.models import KBEntry
from ai_comm_assistant.extensions import db


def test_rag_top_k(app):
    with app.app_context():
        # Clear existing entries
        KBEntry.query.delete()
        db.session.commit()
        entry1 = KBEntry(title='Returns', content='You can return items within 30 days of purchase.')
        entry2 = KBEntry(title='Shipping', content='Shipping typically takes 3–5 business days.')
        entry3 = KBEntry(title='Support', content='Contact support at support@example.com for assistance.')
        db.session.add_all([entry1, entry2, entry3])
        db.session.commit()
        rag = RAGService()
        rag.build_index()
        snippets = rag.get_top_k('How long does shipping take?', k=2)
        assert any('business days' in s for s in snippets)