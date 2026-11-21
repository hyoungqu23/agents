"""Checks every skill's SKILL.md frontmatter and its reference links.

Neither `claude plugin validate` nor the plugin load check reads skill
frontmatter: a SKILL.md whose `name` disagrees with its directory, or whose
description cannot route a request, passes both. A missing `name` is worse than
a visible error, because the loader falls back to the directory name and the
skill keeps working while the manifest says otherwise.

These checks are the contract a marketplace of several overlapping skills
relies on, so they are errors rather than style advice.
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

# Lets `python3 -m unittest scripts/tests/<this file>` find the sibling module,
# which only `discover -s scripts/tests` puts on the path by itself.
sys.path.insert(0, str(Path(__file__).parent))
import upstream_lock  # noqa: E402

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


def description_problems(skill, description, imported=None):
    """Why `description` cannot route a request, as a list of messages.

    A skill imported from upstream keeps its source wording, so the phrasing
    rules are not applied to it. The length limit still is: it is the loader's.
    """
    if imported is None:
        imported = skill.name in upstream_lock.imported_skills(skill.parents[1])
    # The parser keeps a quoted scalar's quotes and any trailing comment, so
    # `description: "" # TODO` is not falsy although YAML reads it as empty.
    if re.fullmatch(r"""(""|'')?\s*(#.*)?""", description):
        return [f"{skill.name}: frontmatter has no description"]

    problems = []
    if len(description) > MAX_DESCRIPTION:
        problems.append(
            f"{skill.name}: description is {len(description)} characters "
            f"(limit {MAX_DESCRIPTION})"
        )
    if imported:
        return problems

    if re.search(r"[<>]", description):
        problems.append(f"{skill.name}: description contains an angle bracket")
    lowered = description.lower()
    if not any(phrase in lowered for phrase in TRIGGER_PHRASES):
        problems.append(
            f"{skill.name}: description states no trigger. Add one of {TRIGGER_PHRASES}."
        )
    if not any(phrase in lowered for phrase in NEGATIVE_SCOPE_PHRASES):
        problems.append(
            f"{skill.name}: description states no negative scope. "
            f"Add one of {NEGATIVE_SCOPE_PHRASES} naming what to use instead."
        )
    return problems


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
                self.assertEqual(description_problems(skill, description), [])


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

    def follow(frontier, candidates):
        while candidates:
            found = {
                path: reference
                for path, reference in candidates.items()
                if mentions(frontier, reference.name)
            }
            if not found:
                break
            for path in found:
                del candidates[path], pending[path]
            frontier = "\n".join(
                reference.read_text(encoding="utf-8", errors="replace")
                for reference in found.values()
            )

    follow(roots, dict(pending))
    # Upstream skills route through playbooks: SKILL.md picks a playbook, and
    # the playbook names the reference. That start reaches only the imported
    # files of the same skill, so it cannot vouch for a reference written here.
    imported = upstream_lock.imported_files(plugin)
    for skill in sorted(upstream_lock.imported_skills(plugin)):
        playbooks = sorted((plugin / "skills" / skill / "playbooks").glob("**/*.md"))
        follow(
            "\n".join(path.read_text(encoding="utf-8") for path in playbooks),
            {
                path: reference
                for path, reference in pending.items()
                if path in imported and path.startswith(f"skills/{skill}/")
            },
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


class ImportedSkillExemptionTests(unittest.TestCase):
    """The upstream exemption reaches the paths the lock names and nothing else."""

    BARE = "Runs the thing with <flags>."

    def plugin(self, root, entries):
        plugin = Path(root) / "plugins" / "demo"
        for name in ("imported", "authored", "skipped"):
            (plugin / "skills" / name).mkdir(parents=True)
            (plugin / "skills" / name / "SKILL.md").write_text("body\n")
        (plugin / upstream_lock.LOCK_NAME).write_text(json.dumps({"files": entries}))
        return plugin

    def problems(self, plugin, name, description=None):
        return description_problems(plugin / "skills" / name, description or self.BARE)

    def test_only_imported_statuses_are_exempt(self):
        for status, exempt in (("verbatim", True), ("injected", True), ("patched", True),
                               ("local", False), ("skipped", False)):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as root:
                plugin = self.plugin(root, [
                    {"path": "skills/imported/SKILL.md", "status": status}])
                self.assertEqual(self.problems(plugin, "imported") == [], exempt)
                self.assertEqual(len(self.problems(plugin, "authored")), 3)

    def test_exemption_needs_the_skill_md_entry_itself(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = self.plugin(root, [
                {"path": "skills/imported/references/note.md", "status": "verbatim"},
                {"path": "skills/imported/README.md", "status": "verbatim"},
                {"path": "skills/authored-twin/SKILL.md", "status": "verbatim"},
                {"path": "docs/skills/imported/SKILL.md", "status": "verbatim"}])
            self.assertEqual(len(self.problems(plugin, "imported")), 3)

    def test_plugin_without_a_lock_is_never_exempt(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = self.plugin(root, [])
            (plugin / upstream_lock.LOCK_NAME).unlink()
            self.assertEqual(len(self.problems(plugin, "imported")), 3)

    def test_imported_skill_still_obeys_the_loader_limits(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = self.plugin(root, [
                {"path": "skills/imported/SKILL.md", "status": "verbatim"}])
            self.assertEqual(len(self.problems(plugin, "imported", "x" * 1025)), 1)
            for empty in ('""', "''", "", '"" # TODO', "# TODO", "''  #"):
                skill = plugin / "skills/imported"
                (skill / "SKILL.md").write_text(f"---\nname: imported\ndescription: {empty}\n---\n")
                fields, _, _ = parse_frontmatter((skill / "SKILL.md").read_text())
                self.assertEqual(
                    description_problems(skill, fields.get("description", "")),
                    ["imported: frontmatter has no description"],
                )

    def test_unknown_status_is_an_error_not_an_exemption(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = self.plugin(root, [
                {"path": "skills/imported/SKILL.md", "status": "vendored"}])
            with self.assertRaises(ValueError):
                self.problems(plugin, "imported")

    def test_playbooks_reach_only_imported_references_of_their_own_skill(self):
        with tempfile.TemporaryDirectory() as root:
            plugin = self.plugin(root, [
                {"path": "skills/imported/SKILL.md", "status": "verbatim"},
                {"path": "skills/imported/references/imported-triage.md", "status": "verbatim"},
                {"path": "skills/imported/references/deep.md", "status": "verbatim"},
                {"path": "skills/authored/references/authored-triage.md", "status": "local"}])
            for name in ("imported", "authored"):
                skill = plugin / "skills" / name
                (skill / "playbooks").mkdir()
                (skill / "references").mkdir()
                (skill / "playbooks" / "ship.md").write_text(
                    f"read {name}-triage.md, guide.md and added.md\n")
                (skill / "references" / f"{name}-triage.md").write_text("then deep.md\n")
            (plugin / "skills/imported/references/deep.md").write_text("end\n")
            # Written here, inside and outside the imported skill: the lock does
            # not call either imported, so the playbook cannot vouch for them.
            (plugin / "skills/imported/references/added.md").write_text("local\n")
            (plugin / "skills/authored/references/guide.md").write_text("local\n")
            self.assertEqual(
                unreachable_references(plugin),
                ["skills/authored/references/authored-triage.md",
                 "skills/authored/references/guide.md",
                 "skills/imported/references/added.md"],
            )


if __name__ == "__main__":
    unittest.main()
