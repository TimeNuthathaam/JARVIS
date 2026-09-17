#!/usr/bin/env python3
"""Offline checks for the Level 7 hybrid search sidecar."""

from __future__ import annotations

import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "bin" / "sb-search.py"
SPEC = importlib.util.spec_from_file_location("sb_search", MODULE_PATH)
assert SPEC and SPEC.loader
sb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sb
SPEC.loader.exec_module(sb)


KEYWORDS = ("memory", "ความจำ", "ลูกค้า", "retention", "hifu", "นัด", "calendar", "โฆษณา")


def vector(text: str) -> list[float]:
    lower = text.lower()
    values = [float(lower.count(word)) for word in KEYWORDS]
    if not any(values):
        values[0] = 0.01
    norm = math.sqrt(sum(value * value for value in values))
    return [value / norm for value in values]


class FakeClient:
    def __init__(self) -> None:
        self.document_calls = 0
        self.query_calls = 0

    def embed_documents(self, items):
        self.document_calls += len(items)
        return [vector(f"{title} {content}") for title, content in items]

    def embed_query(self, query):
        self.query_calls += 1
        return vector(query)


class FailingClient(FakeClient):
    def embed_documents(self, items):
        raise RuntimeError("quota unavailable")


class FailingQueryClient(FakeClient):
    def embed_query(self, query):
        raise RuntimeError("query API unavailable")


class SearchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        for folder in (*sb.STRUCTURED_DIRS, "raw", "output"):
            (self.vault / folder).mkdir()
        (self.vault / "concepts" / "ai-memory.md").write_text(
            """---
title: AI Memory Architecture
aliases: [ความจำ AI, agent memory]
updated: 2026-08-15
sources: [source-memory.md]
---
# AI Memory Architecture

ระบบความจำระยะยาวช่วย agent เรียกบริบทเดิมกลับมาใช้งาน
""",
            encoding="utf-8",
        )
        (self.vault / "concepts" / "customer-retention.md").write_text(
            """---
title: Customer Retention
aliases: [การรักษาลูกค้า, retention]
updated: 2026-08-14
sources: [source-retention.md]
---
# Customer Retention

รักษาลูกค้าเดิมด้วยการติดตามและข้อเสนอที่เกี่ยวข้อง
""",
            encoding="utf-8",
        )
        (self.vault / "raw" / "source-memory.md").write_text(
            """---
title: Memory transcript
captured: 2026-08-15
type: youtube
status: processed
tags: [AI]
---
ต้นฉบับยาวเกี่ยวกับระบบความจำ AI และ context
""",
            encoding="utf-8",
        )
        (self.vault / "raw" / "unprocessed.md").write_text(
            """---
title: Do not index
captured: 2026-08-15
type: note
status: raw
tags: []
---
ข้อมูลที่ยังไม่ผ่าน process
""",
            encoding="utf-8",
        )
        (self.vault / "output" / "noise.md").write_text("ระบบความจำ", encoding="utf-8")
        self.db = self.vault / ".sb" / "search.db"
        self.conn = sb.connect(self.db)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_thai_fts_scope_and_metadata(self) -> None:
        report = sb.sync_index(self.conn, self.vault, None, "fake", 8, True)
        self.assertEqual(report["chunks"], 3)
        self.assertEqual(report["pending"], 2)
        results = sb.search(self.conn, "ความจำระยะยาว", "fts", 5, None, "fake", 8)
        self.assertEqual(results[0]["path"], "concepts/ai-memory.md")
        paths = {row["path"] for row in self.conn.execute("SELECT path FROM chunks")}
        self.assertNotIn("raw/unprocessed.md", paths)
        self.assertNotIn("output/noise.md", paths)

    def test_embeddings_are_incremental_and_raw_is_lexical_only(self) -> None:
        client = FakeClient()
        first = sb.sync_index(self.conn, self.vault, client, "fake", 8)
        self.assertEqual(first["embedded"], 2)
        self.assertEqual(client.document_calls, 2)
        raw = self.conn.execute("SELECT embedding_status FROM chunks WHERE kind='raw'").fetchone()[0]
        self.assertEqual(raw, "lexical")

        second = sb.sync_index(self.conn, self.vault, client, "fake", 8)
        self.assertEqual(second["embedded"], 0)
        self.assertEqual(second["changed"], 0)
        self.assertEqual(client.document_calls, 2)

        path = self.vault / "concepts" / "customer-retention.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nretention campaign\n", encoding="utf-8")
        third = sb.sync_index(self.conn, self.vault, client, "fake", 8)
        self.assertEqual(third["embedded"], 1)
        self.assertEqual(client.document_calls, 3)

    def test_hybrid_semantic_search_and_query_cache(self) -> None:
        client = FakeClient()
        sb.sync_index(self.conn, self.vault, client, "fake", 8)
        results = sb.search(self.conn, "agent memory", "hybrid", 5, client, "fake", 8)
        self.assertEqual(results[0]["path"], "concepts/ai-memory.md")
        self.assertIn("semantic", results[0]["channels"])
        sb.search(self.conn, "agent memory", "hybrid", 5, client, "fake", 8)
        self.assertEqual(client.query_calls, 1)

    def test_remote_failure_keeps_fts_and_pending(self) -> None:
        report = sb.sync_index(self.conn, self.vault, FailingClient(), "fake", 8, best_effort=True)
        self.assertEqual(report["pending"], 2)
        self.assertIn("quota unavailable", report["api_error"])
        results = sb.search(self.conn, "การรักษาลูกค้า", "hybrid", 5, None, "fake", 8)
        self.assertEqual(results[0]["path"], "concepts/customer-retention.md")

    def test_query_failure_falls_back_to_fts(self) -> None:
        sb.sync_index(self.conn, self.vault, None, "fake", 8, True)
        results = sb.search(
            self.conn, "การรักษาลูกค้า", "hybrid", 5, FailingQueryClient(), "fake", 8
        )
        self.assertEqual(results[0]["path"], "concepts/customer-retention.md")

    def test_deleted_files_leave_the_index(self) -> None:
        sb.sync_index(self.conn, self.vault, None, "fake", 8, True)
        (self.vault / "concepts" / "customer-retention.md").unlink()
        report = sb.sync_index(self.conn, self.vault, None, "fake", 8, True)
        self.assertEqual(report["deleted"], 1)
        count = self.conn.execute(
            "SELECT count(*) FROM chunks WHERE path='concepts/customer-retention.md'"
        ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_rename_reuses_identical_embedding(self) -> None:
        client = FakeClient()
        sb.sync_index(self.conn, self.vault, client, "fake", 8)
        calls = client.document_calls
        source = self.vault / "concepts" / "customer-retention.md"
        source.rename(self.vault / "concepts" / "customer-loyalty.md")
        report = sb.sync_index(self.conn, self.vault, client, "fake", 8)
        self.assertEqual(report["embedded"], 0)
        self.assertEqual(client.document_calls, calls)
        self.assertEqual(report["pending"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
