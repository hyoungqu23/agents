"""Checks every skill's SKILL.md frontmatter and its reference links.

Neither `claude plugin validate` nor the plugin load check reads skill
frontmatter: a SKILL.md whose `name` disagrees with its directory, or whose
description cannot route a request, passes both. A missing `name` is worse than
a visible error, because the loader falls back to the directory name and the
skill keeps working while the manifest says otherwise.

These checks are the contract a marketplace of several overlapping skills
relies on, so they are errors rather than style advice.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
PLUGINS = REPO_ROOT / "plugins"

KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)
FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)$")

# A skill is selected from its description alone, so the description has to say
# when to reach for it and when to reach for a neighbour instead.
TRIGGER_PHRASES = ("use when", "use for", "use this", "use it when")
NEGATIVE_SCOPE_PHRASES = ("do not use", "don't use", "not for", "not intended for")
MAX_DESCRIPTION = 1024

REFERENCE_DIRS = ("references", "resources")


def skill_dirs():
    return sorted(path for path in PLUGINS.glob("*/skills/*") if path.is_dir())


def plugin_dirs():
    return sorted(path for path in PLUGINS.glob("*") if path.is_dir())


def parse_frontmatter(text):
    """Return (fields, unparsed_lines, body) for a SKILL.md.

    Only single-line scalars are read: PyYAML is not guaranteed to be installed
    where these tests run, and the standard library has no YAML parser. Any line
    the parser does not recognize is returned so a test can fail on it rather
    than let it pass unchecked.
    """
    match = FRONTMATTER.match(text)
    if match is None:
        return None, [], ""

    fields = {}
    unparsed = []
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        field = FIELD.match(line)
        if field is None:
            unparsed.append(line)
            continue
        fields[field.group(1)] = field.group(2).strip()

    return fields, unparsed, text[match.end() :]


class SkillFrontmatterTests(unittest.TestCase):
    def setUp(self):
        self.skills = skill_dirs()
        self.assertTrue(self.skills, f"No skills found under {PLUGINS}")

    def read(self, skill):
        path = skill / "SKILL.md"
        self.assertTrue(path.is_file(), f"{skill.name}: SKILL.md is missing")
        return parse_frontmatter(path.read_text(encoding="utf-8"))

    def test_skill_md_exists_with_exact_casing(self):
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                names = [entry.name for entry in skill.iterdir()]
                self.assertIn(
                    "SKILL.md",
                    names,
                    f"{skill.name}: SKILL.md is missing (the loader matches the name exactly)",
                )
                wrong = [
                    name for name in names if name.lower() == "skill.md" and name != "SKILL.md"
                ]
                self.assertEqual(wrong, [], f"{skill.name}: wrong casing {wrong}")

    def test_frontmatter_parses(self):
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                fields, unparsed, _ = self.read(skill)
                self.assertIsNotNone(
                    fields, f"{skill.name}: no --- delimited frontmatter at the top of SKILL.md"
                )
                self.assertEqual(
                    unparsed,
                    [],
                    f"{skill.name}: unreadable frontmatter line(s) {unparsed}. "
                    "Keep every value a single-line scalar.",
                )

    def test_name_matches_its_directory(self):
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                fields, _, _ = self.read(skill)
                name = fields.get("name", "")
                self.assertTrue(name, f"{skill.name}: frontmatter has no name")
                self.assertRegex(
                    name, KEBAB_CASE, f"{skill.name}: name '{name}' is not kebab-case"
                )
                self.assertEqual(
                    name,
                    skill.name,
                    f"{skill.name}: name '{name}' disagrees with the directory, "
                    "and the loader would use the directory name",
                )

    def test_description_can_route_a_request(self):
        for skill in self.skills:
            with self.subTest(skill=skill.name):
                fields, _, _ = self.read(skill)
                description = fields.get("description", "")
                self.assertTrue(description, f"{skill.name}: frontmatter has no description")

                self.assertLessEqual(
                    len(description),
                    MAX_DESCRIPTION,
                    f"{skill.name}: description is {len(description)} characters "
                    f"(limit {MAX_DESCRIPTION})",
                )
                self.assertNotRegex(
                    description,
                    r"[<>]",
                    f"{skill.name}: description contains an angle bracket",
                )

                lowered = description.lower()
                self.assertTrue(
                    any(phrase in lowered for phrase in TRIGGER_PHRASES),
                    f"{skill.name}: description states no trigger. "
                    f"Add one of {TRIGGER_PHRASES}.",
                )
                self.assertTrue(
                    any(phrase in lowered for phrase in NEGATIVE_SCOPE_PHRASES),
                    f"{skill.name}: description states no negative scope. "
                    f"Add one of {NEGATIVE_SCOPE_PHRASES} naming what to use instead.",
                )


def mentions(text, name):
    """Whether `text` links `name`, without matching it as a filename suffix.

    `patterns.md` is a substring of `korean-patterns.md`, so a plain containment
    test would call the first one linked wherever the second is.
    """
    return re.search(r"(?<![A-Za-z0-9_-])" + re.escape(name), text) is not None


def unreachable_references(plugin):
    """Reference files no SKILL.md in the plugin reaches, directly or through another.

    A skill may route through an intermediate index — un-ai's SKILL.md links
    `korean-patterns.md`, which links the A-J category files — so reachability is
    followed rather than requiring every file to appear in SKILL.md itself.
    """
    roots = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(plugin.glob("skills/*/SKILL.md"))
    )

    pending = {}
    for directory in REFERENCE_DIRS:
        for base in [plugin, *sorted(plugin.glob("skills/*"))]:
            for reference in sorted((base / directory).glob("**/*")):
                if reference.is_file():
                    pending[str(reference.relative_to(plugin))] = reference

    frontier = roots
    while pending:
        found = {
            path: reference
            for path, reference in pending.items()
            if mentions(frontier, reference.name)
        }
        if not found:
            break
        for path in found:
            del pending[path]
        frontier = "\n".join(
            reference.read_text(encoding="utf-8", errors="replace")
            for reference in found.values()
        )

    return sorted(pending)


class ReferenceLinkTests(unittest.TestCase):
    """A reference nothing points at is never read, and the skill silently loses it."""

    def test_every_reference_is_reachable_from_a_skill(self):
        for plugin in plugin_dirs():
            with self.subTest(plugin=plugin.name):
                orphans = unreachable_references(plugin)
                self.assertEqual(
                    orphans,
                    [],
                    f"{plugin.name}: no skill reaches {orphans}",
                )


if __name__ == "__main__":
    unittest.main()
