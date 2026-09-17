import tempfile
import unittest
from pathlib import Path
import server
from server import build_graph, create_memory, load_memories, search_memories


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_vault = server.VAULT_DIR
        server.VAULT_DIR = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()
        server.VAULT_DIR = self.old_vault

    def test_create_search_graph(self):
        create_memory("Bali Trip", "Ubud and Uluwatu", ["travel"])
        create_memory("Travel Budget", "Bali budget planning", ["money", "travel"])
        memories = load_memories()
        self.assertEqual(len(memories), 2)
        self.assertEqual(search_memories(memories, "bali")[0]["title"], "Bali Trip")
        graph = build_graph(memories)
        self.assertEqual(len(graph["links"]), 1)

    def test_second_brain_frontmatter_and_wikilinks(self):
        vault = server.VAULT_DIR / "concepts"
        vault.mkdir(parents=True)
        (vault / "ai-memory.md").write_text(
            """---\ntitle: AI Memory\naliases: [ความจำ AI]\ntags: [ai]\n---\n\nSee [[Travel Budget]].\n""",
            encoding="utf-8",
        )
        (vault / "money.md").write_text(
            """---\ntitle: Travel Budget\naliases: [งบเดินทาง]\n---\n\nMoney plan.\n""",
            encoding="utf-8",
        )
        graph = build_graph(load_memories())
        self.assertEqual(graph["nodes"][0]["aliases"], ["ความจำ AI"])
        self.assertEqual(len(graph["links"]), 1)


if __name__ == "__main__":
    unittest.main()
