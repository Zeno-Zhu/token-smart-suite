"""Run with python -m unittest discover -s tests. All writes use temporary directories."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("installer", Path(__file__).resolve().parents[1] / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.skills = root / "skills with spaces"
        self.rules = root / "AGENTS.md"
        self.source = root / "source"
        (self.source / "references").mkdir(parents=True)
        (self.source / "SKILL.md").write_text("---\nname: token-smart\ndescription: Test\n---\nTest", encoding="utf-8")
        (self.source / "references" / "onboarding.md").write_text("首次说明", encoding="utf-8")
        (self.source / "references" / "onboarding.en.md").write_text("Introduction", encoding="utf-8")
        self.patcher = patch.object(installer, "SOURCE", self.source)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def run_install(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = installer.main(["--target", "codex", "--skills-dir", str(self.skills), *args])
        return status, output.getvalue()

    def test_install_and_repeat_without_activation(self):
        status, text = self.run_install()
        self.assertEqual(status, 0)
        self.assertIn("首次说明", text)
        self.assertFalse(self.rules.exists())
        status, text = self.run_install()
        self.assertEqual(status, 0)
        self.assertNotIn("首次说明", text)

    def test_existing_unowned_directory_is_unchanged(self):
        dest = self.skills / installer.NAME
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("user", encoding="utf-8")
        self.assertEqual(self.run_install()[0], 1)
        self.assertEqual((dest / "SKILL.md").read_text(), "user")

    def test_activation_repeat_and_uninstall_preserve_bytes(self):
        original = "用户规则\r\n".encode("utf-8")
        self.rules.write_bytes(original)
        args = ("--activate", "--instructions", str(self.rules))
        self.assertEqual(self.run_install(*args)[0], 0)
        self.assertEqual(self.run_install(*args)[0], 0)
        self.assertEqual(self.rules.read_bytes().count(installer.START), 1)
        self.rules.write_bytes(self.rules.read_bytes() + b"later user text\n")
        self.assertEqual(self.run_install("--uninstall", "--instructions", str(self.rules))[0], 0)
        self.assertEqual(self.rules.read_bytes(), original + b"later user text\n")

    def test_modified_files_and_rules_survive_uninstall(self):
        self.run_install("--activate", "--instructions", str(self.rules))
        changed = self.skills / installer.NAME / "SKILL.md"
        changed.write_text("user edit", encoding="utf-8")
        self.rules.write_bytes(self.rules.read_bytes().replace(b"efficiency", b"custom"))
        rules = self.rules.read_bytes()
        self.assertEqual(self.run_install()[0], 1)
        status, text = self.run_install("--uninstall")
        self.assertEqual(status, 0)
        self.assertEqual(changed.read_text(), "user edit")
        self.assertEqual(self.rules.read_bytes(), rules)
        self.assertIn("Preserved user changes", text)

    def test_foreign_block_conflict_leaves_skill_uninstalled(self):
        self.rules.write_bytes(installer.START + b"\nuser\n" + installer.END)
        self.assertEqual(self.run_install("--activate", "--instructions", str(self.rules))[0], 1)
        self.assertFalse((self.skills / installer.NAME).exists())
        with self.assertRaises(ValueError):
            installer.install(self.source / "nested", self.rules, False, "zh")
        self.assertEqual(self.run_install("--activate", "--instructions", str(self.skills / installer.NAME / "SKILL.md"))[0], 1)

    def test_missing_source_and_wrong_uninstall_rule_path(self):
        self.run_install("--activate", "--instructions", str(self.rules))
        before = self.rules.read_bytes()
        self.assertEqual(self.run_install("--uninstall", "--instructions", str(self.rules.with_name("other.md")))[0], 1)
        self.assertEqual(self.rules.read_bytes(), before)
        (self.source / "SKILL.md").unlink()
        self.assertEqual(self.run_install()[0], 1)

    def test_claude_target_and_english_intro(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = installer.main(["--target", "claude", "--skills-dir", str(self.skills), "--lang", "en"])
        self.assertEqual(status, 0)
        self.assertIn("Introduction", output.getvalue())
        self.run_install("--uninstall")
        self.assertFalse((self.skills / installer.NAME).exists())


if __name__ == "__main__":
    unittest.main()
