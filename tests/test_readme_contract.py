import re
import unittest
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"


class ReadmeContractTests(unittest.TestCase):
    def _read_readme(self):
        self.assertTrue(README_PATH.is_file(), f"README does not exist: {README_PATH}")
        return README_PATH.read_text(encoding="utf-8")

    def test_readme_has_the_project_narrative_and_exact_contract(self):
        readme = self._read_readme()

        self.assertRegex(
            readme, r"(?m)^# Organizing AI Research Workspaces[ \t]*$"
        )
        self.assertRegex(readme, r"[\u3400-\u4dbf\u4e00-\u9fff]")
        required_sections = (
            "Why this exists",
            "The four-root workspace",
            "Quick start",
            "Organizing paper projects",
            "Where checkpoints go",
            "Git and paths across machines",
            "Storage safety",
            "Deliberate non-goals",
            "Use it as a Codex skill",
            "Repository structure",
            "Validation",
            "Contributing",
            "License",
        )
        for section_name in required_sections:
            with self.subTest(section_name=section_name):
                self.assertRegex(
                    readme,
                    rf"(?m)^## {re.escape(section_name)}[ \t]*$",
                )

        workspace_section_match = re.search(
            r"(?ms)^## The four-root workspace[ \t]*\n"
            r"(?P<section>.*?)(?=^##[ \t]+|\Z)",
            readme,
        )
        self.assertIsNotNone(workspace_section_match)
        tree_block_match = re.search(
            r"(?ms)^```text[ \t]*\n(?P<tree>.*?)\n```[ \t]*$",
            workspace_section_match.group("section"),
        )
        self.assertIsNotNone(tree_block_match)
        self.assertEqual(
            tree_block_match.group("tree"),
            "\n".join(
                (
                    "research/",
                    "├── projects/",
                    "├── shared/",
                    "│   ├── datasets/",
                    "│   └── pretrained/",
                    "├── runs/",
                    "└── scratch/",
                )
            ),
        )

        self.assertLessEqual(len(readme.split()), 1800)
        self.assertIsNone(
            re.search(r"\b(?:TBD|TODO|FIXME|XXX)\b", readme, re.IGNORECASE)
        )

    def test_quick_start_and_checkpoint_policy_are_safe(self):
        readme = self._read_readme()

        quick_start_match = re.search(
            r"(?ms)^## Quick start[ \t]*\n"
            r"(?P<section>.*?)(?=^##[ \t]+|\Z)",
            readme,
        )
        self.assertIsNotNone(quick_start_match)
        bash_blocks = [
            match.group("code")
            for match in re.finditer(
                r"(?ms)^(?P<fence>`{3,}|~{3,})bash[ \t]*\n"
                r"(?P<code>.*?)\n(?P=fence)[ \t]*$",
                quick_start_match.group("section"),
            )
        ]
        self.assertTrue(bash_blocks, "Quick start must contain a bash code block")
        quick_start_code = "\n".join(bash_blocks)

        self.assertIn(
            "git clone https://github.com/ky-ji/organizing-ai-research-workspaces.git",
            quick_start_code,
        )
        self.assertIn("--dry-run", quick_start_code)
        self.assertGreaterEqual(quick_start_code.count('python3 "$SETUP_SCRIPT"'), 3)
        self.assertRegex(
            quick_start_code,
            r'(?m)^(?:source|\.) "\$HOME/\.config/research-workspace/env\.sh"[ \t]*$',
        )
        self.assertNotIn("--shell-rc", quick_start_code)

        for required_text in (
            "$RUNS_ROOT/<project>/<run-id>/checkpoints/",
            "results/paper-runs.yaml",
            "KEEP",
            "Retain `last` plus the best one or few checkpoints",
            "Do not create a separate paper-model copy",
            "world-writable directory without the sticky bit",
            "audit before apply",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, readme)

    def test_internal_markdown_links_resolve(self):
        readme = self._read_readme()

        internal_targets = []
        for match in re.finditer(
            r"(?<!!)\[[^\]\n]+\]\((?P<target>[^)\n]+)\)", readme
        ):
            target = match.group("target").strip()
            if target.startswith("<") and ">" in target:
                target = target[1 : target.index(">")]
            else:
                target = target.split(maxsplit=1)[0]
            if target.lower().startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                continue
            internal_targets.append(target)

        self.assertTrue(internal_targets, "README must contain an internal link")
        for target in internal_targets:
            relative_target = unquote(target.split("#", 1)[0])
            with self.subTest(target=target):
                self.assertTrue(
                    (REPO_ROOT / relative_target).exists(),
                    f"internal README link does not resolve: {target}",
                )


if __name__ == "__main__":
    unittest.main()
