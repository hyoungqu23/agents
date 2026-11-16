"""Check direct delegation targets in shipped skill instructions."""
import json
from pathlib import Path
import re
import unittest

PLUGINS = Path(__file__).resolve().parents[2] / 'plugins'
ROUTING = Path('review/skills/review-code/resources/skill-routing.md')
OPTIONAL = {
    'React components, hooks, rendering, state, or React performance': {'vercel-react-best-practices', 'vercel:react-best-practices'},
    'Next.js routing, server/client components, data fetching, caching, metadata, or framework APIs': {'next-best-practices', 'vercel:nextjs'},
    'Playwright tests or browser E2E behavior': {'playwright-best-practices'},
    'Accessibility semantics, keyboard flow, focus, contrast, or WCAG claims': {'wcag-audit-patterns'},
    'Visual behavior where a runnable UI is available and visual verification is relevant': {'visual-tester', 'design-review'},
    'PostgreSQL/Supabase schema, query, RLS, index, or migration behavior': {'supabase-postgres-best-practices'},
    'Unresolved framework, API, standard, or external contract': {'contract-research'},
}
NAME = r'([a-z0-9-]+(?::[a-z0-9-]+)?)'
TARGET = r'`' + NAME + r'`'
OWNER = r' from the `([a-z0-9-]+)` plugin'
DIRECT = re.compile(r'\b(?:load (?:skill )?' + TARGET + '(?:' + OWNER + ')?|use ' + TARGET + OWNER + ')', re.I)


def targets(line, path):
    result = set()
    for match in DIRECT.finditer(line):
        if re.search(r"(?:do not|never|don't)\s+$", line[:match.start()], re.I):
            continue
        load, owner, use, use_owner = match.groups()
        name, plugin = load or use, owner or use_owner
        result.add(f'{plugin}:{name}' if plugin else name)
    if path == ROUTING and line.startswith('|'):
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) == 3:
            for match in re.finditer(TARGET + '(?:' + OWNER + ')?', cells[1]):
                name, owner = match.groups()
                if owner or name not in OPTIONAL.get(cells[0], set()):
                    result.add(f'{owner}:{name}' if owner else name)
    return result


def markdown_blocks(text):
    """Join soft-wrapped prose while retaining each table row and block boundary."""
    paragraph = []
    start = 1
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        separate = line.startswith(('|', '#', '~~~', '```'))
        starts_item = re.match(r'^(?:[-+*]|[0-9]+[.)])\s', line)
        if paragraph and (not line or separate or starts_item):
            yield start, ' '.join(paragraph)
            paragraph.clear()
        if separate:
            yield number, line
        elif line:
            if not paragraph:
                start = number
            paragraph.append(line)
    if paragraph:
        yield start, ' '.join(paragraph)


class DelegationTests(unittest.TestCase):
    def test_installed_targets(self):
        entries = list(PLUGINS.glob('*/skills/*/SKILL.md'))
        known = {f'{p.parents[2].name}:{p.parent.name}' for p in entries}
        names = known | {p.parent.name for p in entries}
        docs = set(entries)
        for folder in ('references', 'resources'):
            docs.update(PLUGINS.glob(f'*/{folder}/**/*.md'))
            docs.update(PLUGINS.glob(f'*/skills/*/{folder}/**/*.md'))
        for doc in sorted(docs):
            path = doc.relative_to(PLUGINS)
            for number, line in markdown_blocks(doc.read_text()):
                self.assertFalse(missing := targets(line, path) - names,
                                 f'{path}:{number}: resolve missing skill delegation {missing}')

    def test_wording_routes(self):
        fixture = Path(__file__).with_name('fixtures') / 'skill-delegations.json'
        for case in json.loads(fixture.read_text()):
            path, line = Path(case['path']), case['line']
            self.assertEqual(targets(line, path), {'content:un-ai'})
            self.assertEqual(targets(line.replace('`un-ai`', '`missing`'), path), {'content:missing'})

    def test_wrapped_delegations(self):
        for text in ('Load\n`missing` from the `content` plugin.',
                     'Load `missing`\nfrom the `content` plugin.'):
            [(number, block)] = markdown_blocks(text)
            self.assertEqual(number, 1)
            self.assertEqual(targets(block, ROUTING), {'content:missing'})

    def test_optional_route_requires_unqualified_name(self):
        trigger = 'Unresolved framework, API, standard, or external contract'
        row = f'| {trigger} | `contract-research` | fallback |'
        qualified = row.replace('`contract-research`', '`contract-research` from the `unknown` plugin')
        blocks = list(markdown_blocks(row + '\n' + qualified))
        self.assertEqual([targets(block, ROUTING) for _, block in blocks],
                         [set(), {'unknown:contract-research'}])

    def test_alternatives_are_not_delegations(self):
        line = 'Do not use this for QA; use the sibling `think-through` skill instead. Use `draft`.'
        self.assertEqual(targets(line, ROUTING), set())
        self.assertEqual(targets(line + ' Load `dumbify`.', ROUTING), {'dumbify'})
