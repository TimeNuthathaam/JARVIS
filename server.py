#!/usr/bin/env python3
"""Local Markdown memory graph server."""

import json
import os
import re
import subprocess
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
VAULT_DIR = Path(os.environ.get("SECOND_BRAIN_DIR", Path.home() / ".second-brain")).resolve()
SOURCE_DIRS = ("raw", "entities", "concepts", "comparisons", "queries", "people", "journal", "Magic")
EXCLUDED_PARTS = {".git", ".obsidian", ".sb", ".codex", ".claude", ".superpowers", "output", "graphify-out"}
SEARCH_SCRIPT = Path(os.environ.get(
    "SECOND_BRAIN_SEARCH_SCRIPT",
    Path.home() / ".local/share/second-brain-system/vault-template/bin/sb-search.py",
)).resolve()
VIEWER = ROOT / "viewer" / "index.html"


def slugify(value):
    value = re.sub(r"[^\w\s-]", "", value.lower(), flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", value).strip("-") or "memory"


def parse_frontmatter(raw):
    match = re.match(r"^---\n(.*?)\n---\n?", raw, re.DOTALL)
    values = {}
    if not match:
        return values, raw
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            values[key.strip()] = [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
        else:
            values[key.strip()] = value.strip("'\"")
    return values, raw[match.end():]


def parse_memory(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    heading = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
    title = heading.group(1).strip() if heading else path.stem.replace("-", " ").title()
    if meta.get("title"):
        title = str(meta["title"])
    aliases = [str(item) for item in meta.get("aliases", [])]
    tags = [str(item).lower() for item in meta.get("tags", [])]
    tag_line = re.search(r"^Tags:\s*(.+)$", body, re.MULTILINE | re.IGNORECASE)
    if tag_line:
        tags.extend(tag.strip().lower() for tag in tag_line.group(1).split(",") if tag.strip())
    content = re.sub(r"^#\s+.+$\n?", "", body, count=1, flags=re.MULTILINE)
    content = re.sub(r"^Tags:\s*.+$\n?", "", content, count=1, flags=re.MULTILINE | re.IGNORECASE).strip()
    links = []
    for value in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", raw):
        value = value.strip().split("#", 1)[0]
        links.append(value if value else slugify(title))
    excerpt = re.sub(r"\s+", " ", content).strip()
    return {
        "id": str(path.relative_to(VAULT_DIR).with_suffix("")),
        "title": title,
        "aliases": aliases,
        "type": path.parent.name,
        "updated": str(meta.get("updated", "")),
        "sources": [str(item) for item in meta.get("sources", [])],
        "tags": sorted(set(tags)),
        "content": content,
        "excerpt": excerpt[:240],
        "links": sorted(set(links)),
    }


def load_memories():
    if not VAULT_DIR.exists():
        return []
    memories = []
    for folder in SOURCE_DIRS:
        directory = VAULT_DIR / folder
        if not directory.exists():
            continue
        memories.extend(parse_memory(path) for path in directory.rglob("*.md") if EXCLUDED_PARTS.isdisjoint(path.parts))
    return memories


def build_graph(memories):
    ids = {memory["id"] for memory in memories}
    title_ids = {}
    for memory in memories:
        title_ids[slugify(memory["title"])] = memory["id"]
        for alias in memory["aliases"]:
            title_ids[slugify(alias)] = memory["id"]
        title_ids[Path(memory["id"]).name] = memory["id"]
    by_tag = {}
    links = set()
    for memory in memories:
        for tag in memory["tags"]:
            by_tag.setdefault(tag, []).append(memory["id"])
        for target in memory["links"]:
            normalized = title_ids.get(slugify(target))
            if normalized and normalized in ids:
                links.add(tuple(sorted((memory["id"], normalized))))
    for members in by_tag.values():
        for index, source in enumerate(members):
            for target in members[index + 1 :]:
                links.add(tuple(sorted((source, target))))
    degrees = {memory["id"]: 0 for memory in memories}
    for source, target in links:
        degrees[source] += 1
        degrees[target] += 1
    nodes = [
        {
            "id": memory["id"],
            "title": memory["title"],
            "aliases": memory["aliases"],
            "type": memory["type"],
            "tags": memory["tags"],
            "excerpt": memory["excerpt"],
            "content": memory["content"],
            "degree": degrees[memory["id"]],
        }
        for memory in memories
    ]
    return {"nodes": nodes, "links": [{"source": source, "target": target} for source, target in links]}


def search_memories(memories, query):
    terms = [term.lower() for term in query.split() if term]
    if not terms:
        return memories
    scored = []
    for memory in memories:
        title = " ".join([memory["title"], *memory["aliases"]]).lower()
        tags = " ".join(memory["tags"])
        content = memory["content"].lower()
        score = sum(8 * (term in title) + 4 * (term in tags) + int(term in content) for term in terms)
        if score:
            scored.append((score, memory))
    return [memory for _, memory in sorted(scored, key=lambda item: item[0], reverse=True)]


def hybrid_search(query):
    """Use the existing Second Brain hybrid retrieval engine when installed."""
    if not query.strip() or not SEARCH_SCRIPT.exists():
        return None
    command = [
        "python3", str(SEARCH_SCRIPT), "--vault", str(VAULT_DIR),
        "search", query, "--mode", "hybrid", "--limit", "25", "--json",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=True)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def memories_for_search_results(items):
    memories = load_memories()
    by_id = {memory["id"]: memory for memory in memories}
    by_name = {Path(memory["id"]).name: memory for memory in memories}
    selected = []
    seen = set()
    for item in items:
        result_path = Path(str(item.get("path", "")))
        memory = by_id.get(result_path.with_suffix("").as_posix()) or by_name.get(result_path.stem)
        if memory and memory["id"] not in seen:
            selected.append(memory)
            seen.add(memory["id"])
    return selected


def create_memory(title, content, tags, aliases=None):
    if not title.strip():
        raise ValueError("Title is required")
    (VAULT_DIR / "concepts").mkdir(parents=True, exist_ok=True)
    clean_tags = sorted({str(tag).strip().lower() for tag in tags if str(tag).strip()})
    clean_aliases = sorted({str(alias).strip() for alias in (aliases or []) if str(alias).strip()})
    base = slugify(title)
    path = VAULT_DIR / "concepts" / f"{base}.md"
    if path.exists():
        path = VAULT_DIR / "concepts" / f"{base}-{int(time.time())}.md"
    frontmatter = "\n".join([
        "---",
        f"title: {title.strip()}",
        f"aliases: [{', '.join(clean_aliases)}]",
        f"updated: {date.today().isoformat()}",
        "sources: [memory-galaxy-ui]",
        f"tags: [{', '.join(clean_tags)}]",
        "---",
    ])
    body = f"{frontmatter}\n\n{content.strip()}\n"
    path.write_text(body, encoding="utf-8")
    return parse_memory(path)


class MemoryHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/viewer", "/viewer/index.html"):
            self.send_response(200)
            body = VIEWER.read_bytes()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/graph":
            self.send_json(200, build_graph(load_memories()))
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            items = hybrid_search(query)
            engine = "second-brain-hybrid"
            if items is None:
                engine = "lexical-fallback"
                results = search_memories(load_memories(), query)
            else:
                results = memories_for_search_results(items)
            self.send_json(200, {
                "query": query,
                "engine": engine,
                "results": build_graph(results),
                "count": len(results),
            })
            return
        if parsed.path == "/api/health":
            count = len(load_memories())
            self.send_json(200, {"ok": True, "memories": count, "vault_dir": str(VAULT_DIR)})
            return
        self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/memories":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("Memory is too large")
            data = json.loads(self.rfile.read(length) or b"{}")
            memory = create_memory(data.get("title", ""), data.get("content", ""), data.get("tags", []), data.get("aliases", []))
            self.send_json(201, memory)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})


def run(port=None):
    port = int(port or os.environ.get("PORT", 4700))
    server = ThreadingHTTPServer(("127.0.0.1", port), MemoryHandler)
    print(f"Memory Galaxy: http://127.0.0.1:{port}")
    print(f"Vault: {VAULT_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
