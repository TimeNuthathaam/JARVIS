#!/usr/bin/env python3
"""Rebuildable SQLite FTS5 + Gemini embedding search for the /sb vault."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_VAULT = Path(os.environ.get("SECOND_BRAIN_DIR", Path.home() / ".second-brain"))
DEFAULT_MODEL = "gemini-embedding-2"
DEFAULT_DIM = 768
SCHEMA_VERSION = 1
STRUCTURED_DIRS = ("entities", "concepts", "comparisons", "queries", "people", "journal")
RAW_WEIGHT = 0.35
RRF_K = 60
CHUNK_CHARS = 12_000
BATCH_SIZE = 20


@dataclass(frozen=True)
class SourceChunk:
    path: str
    kind: str
    ordinal: int
    title: str
    aliases: str
    tags: str
    sources: str
    updated: str
    captured: str
    status: str
    content: str
    content_hash: str
    should_embed: bool


def load_env(path: Path) -> None:
    """Load simple KEY=VALUE pairs without overriding the process environment."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    body_start = end + 4
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    return meta, text[body_start:]


def clean_list(value: str) -> str:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return " ".join(part.strip().strip("'\"") for part in value.split(",") if part.strip())


def split_chunks(body: str, limit: int = CHUNK_CHARS) -> list[str]:
    body = body.strip()
    if not body:
        return [""]
    sections = re.split(r"(?=^#{1,3}\s)", body, flags=re.MULTILINE)
    output: list[str] = []
    current = ""
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) > limit:
            pieces = [section[i : i + limit] for i in range(0, len(section), limit)]
        else:
            pieces = [section]
        for piece in pieces:
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if current and len(candidate) > limit:
                output.append(current)
                current = piece
            else:
                current = candidate
    if current:
        output.append(current)
    return output or [body[:limit]]


def _hash(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8", errors="replace"))
        h.update(b"\0")
    return h.hexdigest()


def scan_corpus(vault: Path) -> list[SourceChunk]:
    files: list[tuple[Path, str, bool]] = []
    for kind in STRUCTURED_DIRS:
        files.extend((p, kind, True) for p in sorted((vault / kind).glob("*.md")) if p.name != ".gitkeep")
    files.extend((p, "raw", False) for p in sorted((vault / "raw").glob("*.md")))

    chunks: list[SourceChunk] = []
    for path, kind, should_embed in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        meta, body = split_frontmatter(text)
        if kind == "raw" and meta.get("status") != "processed":
            continue
        rel = path.relative_to(vault).as_posix()
        title = meta.get("title") or meta.get("name") or path.stem
        aliases = clean_list(meta.get("aliases", ""))
        tags = clean_list(meta.get("tags", ""))
        sources = clean_list(meta.get("sources", ""))
        for ordinal, content in enumerate(split_chunks(body)):
            content_hash = _hash(title, aliases, content)
            chunks.append(
                SourceChunk(
                    path=rel,
                    kind=kind,
                    ordinal=ordinal,
                    title=title,
                    aliases=aliases,
                    tags=tags,
                    sources=sources,
                    updated=meta.get("updated", ""),
                    captured=meta.get("captured", ""),
                    status=meta.get("status", ""),
                    content=content,
                    content_hash=content_hash,
                    should_embed=should_embed,
                )
            )
    return chunks


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version not in (0, SCHEMA_VERSION):
        raise RuntimeError(f"unsupported search database schema {version}; run reindex")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY,
          path TEXT NOT NULL,
          kind TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          title TEXT NOT NULL,
          aliases TEXT NOT NULL DEFAULT '',
          tags TEXT NOT NULL DEFAULT '',
          sources TEXT NOT NULL DEFAULT '',
          updated TEXT NOT NULL DEFAULT '',
          captured TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT '',
          content TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          embedding BLOB,
          embedding_model TEXT,
          embedding_dim INTEGER,
          embedded_hash TEXT,
          embedding_status TEXT NOT NULL DEFAULT 'pending',
          last_error TEXT NOT NULL DEFAULT '',
          UNIQUE(path, ordinal)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
          title, aliases, content,
          content='chunks', content_rowid='id', tokenize='trigram'
        );
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
          INSERT INTO chunks_fts(rowid,title,aliases,content)
          VALUES (new.id,new.title,new.aliases,new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
          INSERT INTO chunks_fts(chunks_fts,rowid,title,aliases,content)
          VALUES ('delete',old.id,old.title,old.aliases,old.content);
        END;
        DROP TRIGGER IF EXISTS chunks_au;
        CREATE TRIGGER chunks_au AFTER UPDATE OF title,aliases,content ON chunks BEGIN
          INSERT INTO chunks_fts(chunks_fts,rowid,title,aliases,content)
          VALUES ('delete',old.id,old.title,old.aliases,old.content);
          INSERT INTO chunks_fts(rowid,title,aliases,content)
          VALUES (new.id,new.title,new.aliases,new.content);
        END;
        CREATE TABLE IF NOT EXISTS query_cache (
          query_hash TEXT NOT NULL,
          model TEXT NOT NULL,
          dim INTEGER NOT NULL,
          embedding BLOB NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(query_hash, model, dim)
        );
        """
    )
    if version == 0:
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.commit()
    return conn


def pack_vector(values: Sequence[float]) -> bytes:
    return array("f", values).tobytes()


def unpack_vector(blob: bytes) -> array:
    values = array("f")
    values.frombytes(blob)
    return values


def normalize(values: Sequence[float], dim: int) -> list[float]:
    if len(values) != dim:
        raise ValueError(f"embedding dimension {len(values)} != expected {dim}")
    norm = math.sqrt(sum(v * v for v in values))
    if not norm:
        raise ValueError("zero-length embedding")
    return [float(v) / norm for v in values]


class GeminiClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, dim: int = DEFAULT_DIM):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing")
        self.api_key = api_key
        self.model = model
        self.dim = dim
        self.base = f"https://generativelanguage.googleapis.com/v1beta/models/{model}"

    def _post(self, endpoint: str, payload: dict) -> dict:
        request = urllib.request.Request(
            f"{self.base}:{endpoint}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if attempt == 0 and exc.code in (429, 500, 502, 503, 504):
                    time.sleep(1)
                    continue
                detail = exc.read(500).decode("utf-8", errors="replace")
                raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"Gemini request failed: {exc.reason if hasattr(exc, 'reason') else exc}") from None
        raise RuntimeError("Gemini request failed")

    def embed_documents(self, items: Sequence[tuple[str, str]]) -> list[list[float]]:
        requests = []
        for title, content in items:
            requests.append(
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": content}]},
                    "embedContentConfig": {
                        "taskType": "RETRIEVAL_DOCUMENT",
                        "title": title,
                        "outputDimensionality": self.dim,
                        "autoTruncate": True,
                    },
                }
            )
        data = self._post("batchEmbedContents", {"requests": requests})
        embeddings = data.get("embeddings", [])
        if len(embeddings) != len(items):
            raise RuntimeError(f"Gemini returned {len(embeddings)} embeddings for {len(items)} inputs")
        return [normalize(item.get("values", []), self.dim) for item in embeddings]

    def embed_query(self, query: str) -> list[float]:
        data = self._post(
            "embedContent",
            {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": query}]},
                "embedContentConfig": {
                    "taskType": "RETRIEVAL_QUERY",
                    "outputDimensionality": self.dim,
                    "autoTruncate": True,
                },
            },
        )
        return normalize(data.get("embedding", {}).get("values", []), self.dim)


def sync_index(
    conn: sqlite3.Connection,
    vault: Path,
    client: GeminiClient | None,
    model: str = DEFAULT_MODEL,
    dim: int = DEFAULT_DIM,
    best_effort: bool = False,
) -> dict[str, int | str]:
    scanned = scan_corpus(vault)
    seen: set[tuple[str, int]] = set()
    changed = 0
    for chunk in scanned:
        seen.add((chunk.path, chunk.ordinal))
        existing = conn.execute(
            """SELECT id,kind,title,aliases,tags,sources,updated,captured,status,content,content_hash,
                      embedding_model,embedding_dim
               FROM chunks WHERE path=? AND ordinal=?""",
            (chunk.path, chunk.ordinal),
        ).fetchone()
        keep_embedding = bool(
            existing
            and existing["content_hash"] == chunk.content_hash
            and (
                not chunk.should_embed
                or (existing["embedding_model"] == model and existing["embedding_dim"] == dim)
            )
        )
        status = "lexical" if not chunk.should_embed else ("ready" if keep_embedding else "pending")
        values = (
            chunk.path,
            chunk.kind,
            chunk.ordinal,
            chunk.title,
            chunk.aliases,
            chunk.tags,
            chunk.sources,
            chunk.updated,
            chunk.captured,
            chunk.status,
            chunk.content,
            chunk.content_hash,
            status,
        )
        if not existing:
            conn.execute(
                """INSERT INTO chunks
                   (path,kind,ordinal,title,aliases,tags,sources,updated,captured,status,content,content_hash,embedding_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            changed += 1
        elif keep_embedding and (
            existing["kind"],
            existing["title"],
            existing["aliases"],
            existing["tags"],
            existing["sources"],
            existing["updated"],
            existing["captured"],
            existing["status"],
            existing["content"],
        ) == (
            chunk.kind,
            chunk.title,
            chunk.aliases,
            chunk.tags,
            chunk.sources,
            chunk.updated,
            chunk.captured,
            chunk.status,
            chunk.content,
        ):
            continue
        elif keep_embedding:
            conn.execute(
                """UPDATE chunks SET kind=?,title=?,aliases=?,tags=?,sources=?,updated=?,captured=?,status=?,content=?,embedding_status=?,last_error=''
                   WHERE path=? AND ordinal=?""",
                (
                    chunk.kind,
                    chunk.title,
                    chunk.aliases,
                    chunk.tags,
                    chunk.sources,
                    chunk.updated,
                    chunk.captured,
                    chunk.status,
                    chunk.content,
                    status,
                    chunk.path,
                    chunk.ordinal,
                ),
            )
        else:
            conn.execute(
                """UPDATE chunks SET kind=?,title=?,aliases=?,tags=?,sources=?,updated=?,captured=?,status=?,content=?,content_hash=?,
                   embedding=NULL,embedding_model=NULL,embedding_dim=NULL,embedded_hash=NULL,embedding_status=?,last_error=''
                   WHERE path=? AND ordinal=?""",
                (
                    chunk.kind,
                    chunk.title,
                    chunk.aliases,
                    chunk.tags,
                    chunk.sources,
                    chunk.updated,
                    chunk.captured,
                    chunk.status,
                    chunk.content,
                    chunk.content_hash,
                    status,
                    chunk.path,
                    chunk.ordinal,
                ),
            )
            changed += 1

    # Reuse an identical ready vector across renames or stable chunks whose ordinal
    # shifted. The content hash includes title + aliases, so semantically different
    # documents cannot borrow each other's embedding.
    conn.execute(
        """UPDATE chunks AS target SET
             embedding=(SELECT source.embedding FROM chunks source
                        WHERE source.content_hash=target.content_hash
                          AND source.embedding_status='ready'
                          AND source.embedding_model=? AND source.embedding_dim=? LIMIT 1),
             embedding_model=?, embedding_dim=?, embedded_hash=target.content_hash,
             embedding_status='ready', last_error=''
           WHERE target.embedding_status='pending'
             AND EXISTS (SELECT 1 FROM chunks source
                         WHERE source.content_hash=target.content_hash
                           AND source.embedding_status='ready'
                           AND source.embedding_model=? AND source.embedding_dim=?)""",
        (model, dim, model, dim, model, dim),
    )

    current = conn.execute("SELECT path,ordinal FROM chunks").fetchall()
    stale = [(row["path"], row["ordinal"]) for row in current if (row["path"], row["ordinal"]) not in seen]
    conn.executemany("DELETE FROM chunks WHERE path=? AND ordinal=?", stale)
    conn.commit()

    pending = conn.execute(
        "SELECT id,title,content,content_hash FROM chunks WHERE embedding_status='pending' ORDER BY path,ordinal"
    ).fetchall()
    embedded = 0
    api_error = ""
    if pending and client:
        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset : offset + BATCH_SIZE]
            try:
                vectors = client.embed_documents([(row["title"], row["content"]) for row in batch])
                for row, vector in zip(batch, vectors):
                    conn.execute(
                        """UPDATE chunks SET embedding=?,embedding_model=?,embedding_dim=?,embedded_hash=?,embedding_status='ready',last_error=''
                           WHERE id=?""",
                        (pack_vector(vector), model, dim, row["content_hash"], row["id"]),
                    )
                    embedded += 1
                conn.commit()
            except Exception as exc:
                api_error = str(exc)[:500]
                conn.executemany(
                    "UPDATE chunks SET last_error=? WHERE id=?",
                    [(api_error, row["id"]) for row in batch],
                )
                conn.commit()
                if not best_effort:
                    raise
                break

    remaining = conn.execute("SELECT count(*) FROM chunks WHERE embedding_status='pending'").fetchone()[0]
    return {
        "chunks": len(scanned),
        "changed": changed,
        "deleted": len(stale),
        "embedded": embedded,
        "pending": remaining,
        "api_error": api_error,
    }


def fts_match(query: str) -> str:
    candidates = [query.strip(), *re.findall(r"[\w\u0E00-\u0E7F-]+", query, flags=re.UNICODE)]
    unique: list[str] = []
    for item in candidates:
        item = item.strip()
        if len(item) >= 3 and item not in unique:
            unique.append(item)
    return " OR ".join(f'"{item.replace(chr(34), chr(34) * 2)}"' for item in unique)


def _filters(kinds: Sequence[str], after: str) -> tuple[str, list[str]]:
    clauses: list[str] = []
    args: list[str] = []
    if kinds:
        clauses.append(f"c.kind IN ({','.join('?' for _ in kinds)})")
        args.extend(kinds)
    if after:
        clauses.append("COALESCE(NULLIF(c.updated,''),c.captured) >= ?")
        args.append(after)
    return (" AND " + " AND ".join(clauses) if clauses else ""), args


def fts_search(
    conn: sqlite3.Connection, query: str, limit: int = 20, kinds: Sequence[str] = (), after: str = ""
) -> list[sqlite3.Row]:
    match = fts_match(query)
    if not match:
        return []
    where, args = _filters(kinds, after)
    return conn.execute(
        f"""SELECT c.*, bm25(chunks_fts,2.0,1.5,1.0) AS lexical_score
            FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid
            WHERE chunks_fts MATCH ?{where}
            ORDER BY lexical_score LIMIT ?""",
        [match, *args, limit],
    ).fetchall()


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def query_vector(
    conn: sqlite3.Connection, query: str, client: GeminiClient, model: str, dim: int
) -> list[float]:
    query_hash = _hash(query)
    row = conn.execute(
        "SELECT embedding FROM query_cache WHERE query_hash=? AND model=? AND dim=?",
        (query_hash, model, dim),
    ).fetchone()
    if row:
        return list(unpack_vector(row["embedding"]))
    vector = client.embed_query(query)
    conn.execute(
        "INSERT OR REPLACE INTO query_cache(query_hash,model,dim,embedding) VALUES (?,?,?,?)",
        (query_hash, model, dim, pack_vector(vector)),
    )
    conn.commit()
    return vector


def semantic_search(
    conn: sqlite3.Connection,
    query: str,
    client: GeminiClient,
    model: str,
    dim: int,
    limit: int = 20,
    kinds: Sequence[str] = (),
    after: str = "",
) -> list[tuple[sqlite3.Row, float]]:
    vector = query_vector(conn, query, client, model, dim)
    where, args = _filters(kinds, after)
    rows = conn.execute(
        f"SELECT c.* FROM chunks c WHERE embedding_status='ready' AND embedding_model=? AND embedding_dim=?{where}",
        [model, dim, *args],
    ).fetchall()
    ranked = [(row, cosine(vector, unpack_vector(row["embedding"]))) for row in rows]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]


def excerpt(content: str, query: str, length: int = 260) -> str:
    flat = re.sub(r"\s+", " ", content).strip()
    position = flat.lower().find(query.lower())
    start = max(0, position - 80) if position >= 0 else 0
    text = flat[start : start + length]
    return ("…" if start else "") + text + ("…" if start + length < len(flat) else "")


def search(
    conn: sqlite3.Connection,
    query: str,
    mode: str,
    limit: int,
    client: GeminiClient | None,
    model: str,
    dim: int,
    kinds: Sequence[str] = (),
    after: str = "",
) -> list[dict]:
    fetch_limit = max(20, limit * 4)
    lexical = fts_search(conn, query, fetch_limit, kinds, after) if mode in ("fts", "hybrid") else []
    semantic: list[tuple[sqlite3.Row, float]] = []
    if mode in ("semantic", "hybrid") and client:
        try:
            semantic = semantic_search(conn, query, client, model, dim, fetch_limit, kinds, after)
        except Exception as exc:
            if mode == "semantic":
                raise
            print(f"Gemini semantic search unavailable; using FTS5: {str(exc)[:200]}", file=sys.stderr)

    scores: dict[int, float] = {}
    rows: dict[int, sqlite3.Row] = {}
    channels: dict[int, set[str]] = {}
    if mode == "fts":
        for rank, row in enumerate(lexical, 1):
            scores[row["id"]] = 1.0 / rank
            rows[row["id"]] = row
            channels[row["id"]] = {"fts"}
    elif mode == "semantic":
        for row, score in semantic:
            scores[row["id"]] = score
            rows[row["id"]] = row
            channels[row["id"]] = {"semantic"}
    else:
        for rank, row in enumerate(lexical, 1):
            weight = RAW_WEIGHT if row["kind"] == "raw" else 1.0
            scores[row["id"]] = scores.get(row["id"], 0.0) + weight / (RRF_K + rank)
            rows[row["id"]] = row
            channels.setdefault(row["id"], set()).add("fts")
        for rank, (row, _) in enumerate(semantic, 1):
            scores[row["id"]] = scores.get(row["id"], 0.0) + 1.0 / (RRF_K + rank)
            rows[row["id"]] = row
            channels.setdefault(row["id"], set()).add("semantic")

    ranked = sorted(scores, key=scores.get, reverse=True)
    results: list[dict] = []
    seen_paths: set[str] = set()
    for row_id in ranked:
        row = rows[row_id]
        if row["path"] in seen_paths:
            continue
        seen_paths.add(row["path"])
        results.append(
            {
                "path": row["path"],
                "title": row["title"],
                "kind": row["kind"],
                "score": round(scores[row_id], 8),
                "channels": sorted(channels[row_id]),
                "updated": row["updated"] or row["captured"],
                "sources": row["sources"],
                "excerpt": excerpt(row["content"], query),
            }
        )
        if len(results) >= limit:
            break
    return results


def status(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "chunks": conn.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "documents": conn.execute("SELECT count(DISTINCT path) FROM chunks").fetchone()[0],
        "embedded": conn.execute("SELECT count(*) FROM chunks WHERE embedding_status='ready'").fetchone()[0],
        "pending": conn.execute("SELECT count(*) FROM chunks WHERE embedding_status='pending'").fetchone()[0],
        "lexical_only": conn.execute("SELECT count(*) FROM chunks WHERE embedding_status='lexical'").fetchone()[0],
        "cached_queries": conn.execute("SELECT count(*) FROM query_cache").fetchone()[0],
    }


def print_results(results: Sequence[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(list(results), ensure_ascii=False, indent=2))
        return
    if not results:
        print("ไม่พบข้อมูลที่เกี่ยวข้อง")
        return
    for index, item in enumerate(results, 1):
        channels = "+".join(item["channels"])
        print(f"{index}. {item['title']} — {item['path']} [{channels}]")
        print(f"   {item['excerpt']}")


def make_client(model: str, dim: int) -> GeminiClient | None:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return GeminiClient(key, model, dim) if key else None


def run_benchmark(
    conn: sqlite3.Connection,
    fixture: Path,
    client: GeminiClient | None,
    model: str,
    dim: int,
    limit: int,
) -> dict:
    cases = json.loads(fixture.read_text(encoding="utf-8"))
    counts = {"fts": 0, "hybrid": 0}
    details = []
    for case in cases:
        expected = set(case["expected"] if isinstance(case["expected"], list) else [case["expected"]])
        row = {"query": case["query"], "expected": sorted(expected)}
        for mode in ("fts", "hybrid"):
            results = search(conn, case["query"], mode, limit, client, model, dim)
            found = [item["path"] for item in results]
            hit = bool(expected.intersection(found))
            counts[mode] += int(hit)
            row[mode] = {"hit": hit, "found": found}
        details.append(row)
    total = len(cases)
    return {
        "queries": total,
        "limit": limit,
        "fts_hits": counts["fts"],
        "fts_recall": round(counts["fts"] / total, 4) if total else 0,
        "hybrid_hits": counts["hybrid"],
        "hybrid_recall": round(counts["hybrid"] / total, 4) if total else 0,
        "passed": bool(total and counts["hybrid"] / total >= 0.9 and counts["hybrid"] >= counts["fts"]),
        "details": details,
    }


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--db", type=Path)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dim", type=int, default=DEFAULT_DIM)
    sub = ap.add_subparsers(dest="command", required=True)

    sync = sub.add_parser("sync", help="incrementally sync Markdown into the derived index")
    sync.add_argument("--best-effort", action="store_true")
    sync.add_argument("--no-embed", action="store_true")
    sync.add_argument("--dry-run", action="store_true")

    reindex = sub.add_parser("reindex", help="delete and rebuild the derived index")
    reindex.add_argument("--best-effort", action="store_true")
    reindex.add_argument("--no-embed", action="store_true")

    query = sub.add_parser("search", help="search the vault")
    query.add_argument("query")
    query.add_argument("--mode", choices=("fts", "semantic", "hybrid"), default="hybrid")
    query.add_argument("--limit", type=int, default=6)
    query.add_argument("--kind", action="append", default=[])
    query.add_argument("--after", default="")
    query.add_argument("--json", action="store_true")

    sub.add_parser("status", help="show index health")

    bench = sub.add_parser("benchmark", help="measure Top-K path recall")
    bench.add_argument("fixture", type=Path)
    bench.add_argument("--limit", type=int, default=5)
    bench.add_argument("--json", action="store_true")
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    vault = args.vault.resolve()
    db_path = (args.db or vault / ".sb" / "search.db").resolve()
    load_env(vault / ".env")

    if args.command == "sync" and args.dry_run:
        chunks = scan_corpus(vault)
        print(json.dumps({"chunks": len(chunks), "embeddable": sum(c.should_embed for c in chunks)}, ensure_ascii=False))
        return 0

    if args.command == "reindex" and db_path.exists():
        db_path.unlink()

    conn = connect(db_path)
    try:
        if args.command in ("sync", "reindex"):
            client = None if args.no_embed else make_client(args.model, args.dim)
            report = sync_index(conn, vault, client, args.model, args.dim, args.best_effort)
            print(json.dumps(report, ensure_ascii=False))
            return 0 if args.best_effort or not report["pending"] else 1

        if args.command == "status":
            print(json.dumps(status(conn), ensure_ascii=False))
            return 0

        if args.command == "search":
            if status(conn)["chunks"] == 0:
                sync_index(conn, vault, make_client(args.model, args.dim), args.model, args.dim, True)
            client = make_client(args.model, args.dim) if args.mode != "fts" else None
            if args.mode == "semantic" and not client:
                print("GEMINI_API_KEY is missing; semantic search unavailable", file=sys.stderr)
                return 2
            results = search(
                conn, args.query, args.mode, args.limit, client, args.model, args.dim, args.kind, args.after
            )
            print_results(results, args.json)
            return 0

        if args.command == "benchmark":
            if status(conn)["chunks"] == 0:
                sync_index(conn, vault, make_client(args.model, args.dim), args.model, args.dim, True)
            report = run_benchmark(conn, args.fixture, make_client(args.model, args.dim), args.model, args.dim, args.limit)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(
                    f"FTS Top-{args.limit}: {report['fts_hits']}/{report['queries']} ({report['fts_recall']:.0%})"
                )
                print(
                    f"Hybrid Top-{args.limit}: {report['hybrid_hits']}/{report['queries']} ({report['hybrid_recall']:.0%})"
                )
                print("PASS" if report["passed"] else "FAIL")
                for item in report["details"]:
                    if not item["hybrid"]["hit"]:
                        print(f"miss: {item['query']} -> {', '.join(item['hybrid']['found'])}")
            return 0 if report["passed"] else 1
    finally:
        conn.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
