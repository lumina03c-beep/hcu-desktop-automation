import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "hcu_setup.py"
SPEC = importlib.util.spec_from_file_location("hcu_setup", MODULE_PATH)
hcu = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hcu)


class SetupConfigTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.binary = self.root / "artifacts" / "computer-use"
        self.source = self.root / "Hybrid-Computer-Use"

    def tearDown(self):
        self.temporary.cleanup()

    def test_binary_paths(self):
        self.assertEqual(hcu.binary_path(self.source, "linux"), self.source / "artifacts/computer-use")
        self.assertEqual(hcu.binary_path(self.source, "darwin"), self.source / "artifacts/macos/computer-use")
        self.assertEqual(hcu.binary_path(self.source, "windows"), self.source / "artifacts/windows/computer-use.exe")

    def test_opencode_v2_preserves_unrelated_settings(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"theme": "light", "mcp": {"servers": {"other": {"type": "remote"}}}}))
        saved = hcu.configure_opencode(self.binary, path)
        value = json.loads(path.read_text())
        self.assertEqual(value["theme"], "light")
        self.assertIn("other", value["mcp"]["servers"])
        entry = value["mcp"]["servers"]["computer-use"]
        self.assertEqual(entry["command"], [str(self.binary), "mcp"])
        self.assertFalse(entry["codemode"])
        self.assertFalse(entry["disabled"])
        self.assertTrue(saved.exists())

    def test_opencode_v1_is_preserved(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"mcp": {"other": {"type": "local", "command": ["x"]}}}))
        hcu.configure_opencode(self.binary, path)
        value = json.loads(path.read_text())
        self.assertIn("other", value["mcp"])
        self.assertNotIn("servers", value["mcp"])
        self.assertTrue(value["mcp"]["computer-use"]["enabled"])

    def test_empty_opencode_defaults_to_v2(self):
        path = self.root / "opencode.json"
        hcu.configure_opencode(self.binary, path)
        value = json.loads(path.read_text())
        self.assertIn("servers", value["mcp"])

    def test_opencode_global_timeout_only_is_v2(self):
        path = self.root / "opencode.json"
        path.write_text(json.dumps({"mcp": {"timeout": {"startup": 30000}}}))
        hcu.configure_opencode(self.binary, path)
        value = json.loads(path.read_text())
        self.assertEqual(value["mcp"]["timeout"], {"startup": 30000})
        self.assertIn("servers", value["mcp"])
        self.assertIn("computer-use", value["mcp"]["servers"])

    def test_jsonc_is_never_rewritten(self):
        path = self.root / "opencode.jsonc"
        original = '{\n  // keep this comment\n  "mcp": {"servers": {}},\n}\n'
        path.write_text(original)
        with self.assertRaises(hcu.SetupError):
            hcu.configure_opencode(self.binary, path)
        self.assertEqual(path.read_text(), original)

    def test_gemini_uses_direct_command_and_no_trust_bypass(self):
        path = self.root / "settings.json"
        path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "ui": {"theme": "dark"}}))
        hcu.configure_gemini(self.binary, path)
        value = json.loads(path.read_text())
        self.assertEqual(value["ui"]["theme"], "dark")
        self.assertIn("other", value["mcpServers"])
        self.assertFalse(value["mcpServers"]["computer-use"]["trust"])
        self.assertEqual(value["mcpServers"]["computer-use"]["args"], ["mcp"])

    def test_claude_uses_official_adapter(self):
        adapter = self.source / "osworld/guest_files/claude_mcp_schema_adapter.py"
        adapter.parent.mkdir(parents=True)
        adapter.write_text("# adapter")
        path = self.root / ".claude.json"
        hcu.configure_claude(self.binary, self.source, path)
        value = json.loads(path.read_text())
        entry = value["mcpServers"]["computer_use"]
        self.assertEqual(entry["args"][0], str(adapter.resolve()))
        self.assertEqual(entry["args"][1:], [str(self.binary.resolve()), "mcp"])

    def test_toml_replaces_only_hcu_table(self):
        path = self.root / "config.toml"
        path.write_text(
            'model = "example"\n\n[mcp_servers.computer_use]\ncommand = "old"\n\n'
            '[mcp_servers.other]\ncommand = "keep"\n\n[ui]\ntheme = "dark"\n'
        )
        hcu.configure_toml("codex", self.binary, path)
        value = path.read_text()
        self.assertEqual(value.count("[mcp_servers.computer_use]"), 1)
        self.assertNotIn('command = "old"', value)
        self.assertIn('[mcp_servers.other]\ncommand = "keep"', value)
        self.assertIn('[ui]\ntheme = "dark"', value)
        self.assertIn("tool_timeout_sec = 180", value)

    def test_toml_appends_without_removing_existing_content(self):
        path = self.root / "config.toml"
        path.write_text('[ui]\ntheme = "dark"\n')
        hcu.configure_toml("grok-build", self.binary, path)
        value = path.read_text()
        self.assertTrue(value.startswith('[ui]\ntheme = "dark"'))
        self.assertIn("[mcp_servers.computer_use]", value)
        self.assertIn("enabled = true", value)

    def test_generic_client_uses_stdio(self):
        value = hcu.generic_config("generic", self.binary, self.source)
        entry = value["mcpServers"]["computer-use"]
        self.assertEqual(entry["type"], "stdio")
        self.assertEqual(entry["args"], ["mcp"])


if __name__ == "__main__":
    unittest.main()
