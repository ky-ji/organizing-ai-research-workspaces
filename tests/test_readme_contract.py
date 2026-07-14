import re
import unittest
from pathlib import Path, PureWindowsPath
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
        section_positions = []
        for section_name in required_sections:
            with self.subTest(section_name=section_name):
                section_match = re.search(
                    rf"(?m)^## {re.escape(section_name)}[ \t]*$",
                    readme,
                )
                self.assertIsNotNone(section_match)
                if section_match is not None:
                    section_positions.append(section_match.start())
        self.assertEqual(len(section_positions), len(required_sections))
        self.assertTrue(
            all(
                earlier < later
                for earlier, later in zip(section_positions, section_positions[1:])
            ),
            "README sections must appear in the documented narrative order",
        )
        first_level_two_heading = re.search(r"(?m)^##[ \t]+", readme)
        self.assertIsNotNone(first_level_two_heading)
        preamble = readme[: first_level_two_heading.start()]
        self.assertRegex(preamble, r"[\u3400-\u4dbf\u4e00-\u9fff]")

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
        setup_calls = []
        code_lines = quick_start_code.splitlines(keepends=True)
        line_positions = []
        position = 0
        for line in code_lines:
            line_positions.append(position)
            position += len(line)
        line_index = 0
        while line_index < len(code_lines):
            command_line = code_lines[line_index].rstrip("\r\n")
            if not re.match(
                r'^[ \t]*python3 "\$SETUP_SCRIPT"(?=$|[ \t])', command_line
            ):
                line_index += 1
                continue
            call_lines = [command_line]
            call_position = line_positions[line_index]
            while call_lines[-1].rstrip().endswith("\\"):
                line_index += 1
                self.assertLess(
                    line_index,
                    len(code_lines),
                    "continued setup call is missing its next line",
                )
                call_lines.append(code_lines[line_index].rstrip("\r\n"))
            call_end = line_positions[line_index] + len(code_lines[line_index])
            setup_calls.append(("\n".join(call_lines), call_position, call_end))
            line_index += 1

        self.assertGreaterEqual(len(setup_calls), 3)
        self.assertIn("--dry-run", setup_calls[0][0])
        self.assertNotIn("--dry-run", setup_calls[1][0])
        self.assertNotIn("--dry-run", setup_calls[2][0])
        source_match = re.search(
            r'(?m)^(?:source|\.) "\$HOME/\.config/research-workspace/env\.sh"[ \t]*$',
            quick_start_code,
        )
        self.assertIsNotNone(source_match)
        self.assertLessEqual(setup_calls[1][2], source_match.start())
        self.assertLess(source_match.start(), setup_calls[2][1])
        self.assertNotIn("--shell-rc", quick_start_code)

        for required_text in (
            "$RUNS_ROOT/<project>/<run-id>/checkpoints/",
            "results/paper-runs.yaml",
            "KEEP",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, readme)
        for policy_pattern in (
            r"(?im)^.*\b(?:retain|keep)\b[^\n]*`last`[^\n]*\bbest\b[^\n]*$",
            r"(?im)^(?=[^\n]*\b(?:do not|don't|never|no|not|without|avoid)\b)"
            r"(?=[^\n]*\bpaper[- ]model\b)"
            r"(?=[^\n]*\b(?:copy|copies|duplicate|duplicates|duplicated|duplication)\b)"
            r"[^\n]+$",
            r"(?im)^(?=[^\n]*\bmodel registr(?:y|ies)\b)"
            r"(?=[^\n]*\b(?:default|by default)\b)"
            r"(?=[^\n]*\b(?:do not|don't|never|no|not|without)\b)[^\n]+$",
            r"(?im)^.*\bworld-writable\b[^\n]*\bsticky bit\b[^\n]*$",
            r"(?im)^.*\baudit\b[^\n]*\bbefore\b[^\n]*\bapply\b[^\n]*$",
        ):
            with self.subTest(policy_pattern=policy_pattern):
                self.assertRegex(readme, policy_pattern)

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
        repository_root = REPO_ROOT.resolve()
        for target in internal_targets:
            relative_target = unquote(target.split("#", 1)[0])
            with self.subTest(target=target):
                target_path = Path(relative_target)
                self.assertFalse(
                    target_path.is_absolute()
                    or PureWindowsPath(relative_target).is_absolute(),
                    f"internal README link must be relative: {target}",
                )
                resolved_target = (repository_root / target_path).resolve()
                self.assertTrue(
                    resolved_target == repository_root
                    or repository_root in resolved_target.parents,
                    f"internal README link escapes the repository: {target}",
                )
                self.assertTrue(
                    resolved_target.exists(),
                    f"internal README link does not resolve: {target}",
                )


if __name__ == "__main__":
    unittest.main()
