import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "organizing-ai-research-workspaces"


class SkillContractTests(unittest.TestCase):
    def _read_required(self, path):
        self.assertTrue(path.is_file(), f"required file does not exist: {path}")
        return path.read_text(encoding="utf-8")

    def test_skill_frontmatter_is_minimal_and_valid(self):
        skill_contents = self._read_required(SKILL_ROOT / "SKILL.md")

        frontmatter_match = re.match(
            r"\A---\n(?P<frontmatter>.*?)\n---(?:\n|\Z)",
            skill_contents,
            re.DOTALL,
        )
        self.assertIsNotNone(frontmatter_match)
        frontmatter = frontmatter_match.group("frontmatter")
        frontmatter_lines = frontmatter.splitlines()
        self.assertEqual(len(frontmatter_lines), 2)
        self.assertEqual(
            frontmatter_lines[0], "name: organizing-ai-research-workspaces"
        )
        self.assertTrue(frontmatter_lines[1].startswith("description: Use when "))
        self.assertLessEqual(len(frontmatter), 1024)

    def test_contract_documents_only_the_minimal_layout(self):
        skill_contents = self._read_required(SKILL_ROOT / "SKILL.md")

        contract_match = re.search(
            r"<!-- contract:start -->\s*(.*?)\s*<!-- contract:end -->",
            skill_contents,
            re.DOTALL,
        )
        self.assertIsNotNone(contract_match)
        contract = contract_match.group(1)
        contract_lines = [line for line in contract.splitlines() if line.strip()]
        self.assertTrue(contract_lines)
        opening = contract_lines[0].strip()
        if opening.startswith(("```", "~~~")):
            opening_match = re.fullmatch(r"(?P<fence>```|~~~)[^`~]*", opening)
            self.assertIsNotNone(opening_match)
            fence = opening_match.group("fence")
            self.assertEqual(contract_lines[-1].strip(), fence)
            contract_lines = contract_lines[1:-1]
        for line in contract_lines:
            self.assertFalse(line.strip().startswith(("```", "~~~")))
        self.assertEqual(
            contract_lines,
            [
                "research/",
                "├── projects/",
                "├── shared/",
                "│   ├── datasets/",
                "│   └── pretrained/",
                "├── runs/",
                "└── scratch/",
            ],
        )

    def test_skill_contains_operational_contract_and_stays_concise(self):
        skill_contents = self._read_required(SKILL_ROOT / "SKILL.md")

        for required_text in (
            "runs/<project>/<run-id>/checkpoints/",
            "paper-runs.yaml",
            "KEEP",
            "RESEARCH_ROOT",
            "PROJECTS_ROOT",
            "SHARED_ROOT",
            "DATASETS_ROOT",
            "PRETRAINED_ROOT",
            "RUNS_ROOT",
            "SCRATCH_ROOT",
            "world-writable",
            "sticky bit",
            "For audit-only requests, report the mapping and risks, then stop.",
            "Run setup only when the user requests setup or apply.",
            "absolute directory containing this `SKILL.md`",
            "Do not assume the current working directory",
            "identify the user's shell",
            "explicit opt-in",
            "Linux-only",
            "within each workspace on each machine",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, skill_contents)

        example_match = re.search(
            r"## Example\n(?P<example>.*?)(?=\n## )",
            skill_contents,
            re.DOTALL,
        )
        self.assertIsNotNone(example_match)
        example = example_match.group("example")
        setup_block_match = re.search(
            r"~~~bash\n(?P<code>.*?)\n~~~", example, re.DOTALL
        )
        self.assertIsNotNone(setup_block_match)
        setup_code = setup_block_match.group("code")
        self.assertIn(
            'python3 "$SKILL_DIR/scripts/setup_workspace.py"', setup_code
        )
        self.assertNotIn("--shell-rc", setup_code)
        source_position = example.find(
            '. "$HOME/.config/research-workspace/env.sh"'
        )
        linux_check_position = example.find('findmnt -T "$RUNS_ROOT"')
        self.assertGreaterEqual(source_position, 0)
        self.assertGreater(linux_check_position, source_position)
        self.assertLessEqual(len(skill_contents.split()), 800)

    def test_openai_agent_metadata_references_the_skill(self):
        agent_contents = self._read_required(SKILL_ROOT / "agents" / "openai.yaml")

        self.assertIn(
            'display_name: "Organizing AI Research Workspaces"', agent_contents
        )
        self.assertIn("$organizing-ai-research-workspaces", agent_contents)


if __name__ == "__main__":
    unittest.main()
