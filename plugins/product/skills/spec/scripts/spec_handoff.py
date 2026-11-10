"""Strict, dependency-free reader for the bundled Markdown handoff v1 contract.

This is a format reader, not a prose/semantic correctness validator. Unsupported
syntax is an error rather than an empty canonical list. No IO or code execution.
"""
import re


class HandoffError(ValueError):
    pass


AC_HEADERS = ['AC ID', '근거', '사전 조건', '행동', '기대 관찰 결과',
              '관련 화면·흐름·API', '확인 방법·미결 참조']
Q_HEADERS = ['ID', '종류', '질문 요약', '영향 절·AC·범위', '미해결 시 차단', '상태']


def clean(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return re.sub(r'<!--[\s\S]*?-->', '', raw)


def is_spec(raw):
    # Identify only actual frontmatter. Inspect its ASCII field markers before
    # decoding the document so a malformed UTF-8 body cannot disable the gate.
    value = raw if isinstance(raw, bytes) else raw.encode('utf-8')
    lines = value.removeprefix(b'\xef\xbb\xbf').splitlines()
    if not lines or lines[0].strip() != b'---':
        return False
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == b'---'), len(lines))
    header = b'\n'.join(lines[1:end])
    return bool(re.search(rb'^id:\s*[\"\']?spec:', header, re.M)
                or (re.search(rb'^handoff_version\s*:', header, re.M)
                    and not re.search(rb'^id:\s*[\"\']?questions:', header, re.M)))


def metadata(raw, kind):
    value = clean(raw)
    match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', value, re.S)
    if not match:
        raise HandoffError('Missing handoff frontmatter')
    fields = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        item = re.fullmatch(r'([a-z_]+):\s*(.*?)\s*', line)
        if not item or item[1] in fields:
            raise HandoffError('Unsupported or duplicate metadata field')
        scalar = item[2]
        if scalar[:1] in ('"', "'"):
            if len(scalar) < 2 or scalar[-1] != scalar[0]:
                raise HandoffError('Unterminated metadata scalar')
            scalar = scalar[1:-1]
        fields[item[1]] = scalar
    if fields.get('handoff_version') != '1':
        raise HandoffError('Only handoff_version 1 is supported')
    if not fields.get('id', '').startswith(kind + ':') or not fields['id'].split(':', 1)[1]:
        raise HandoffError('Wrong document identity')
    if not re.fullmatch(r'[1-9][0-9]*', fields.get('revision', '')):
        raise HandoffError('Expected a positive revision')
    if kind == 'spec' and fields.get('status') not in ('draft', 'blocked', 'ready'):
        raise HandoffError('Invalid spec readiness state')
    link = fields.get('questions' if kind == 'spec' else 'spec', '')
    if not link or not link.endswith('.md') or any(c in link for c in ('\\', '\x00', ':', '#', '?')):
        raise HandoffError('Expected a local Markdown companion path')
    return fields, value[match.end():]


def without_fenced_examples(body):
    """Mask fenced blocks, including indented openers and longer closing fences."""
    output, fence = [], None
    for line in body.splitlines():
        if fence:
            marker, count = fence
            if re.fullmatch(r' {0,3}' + re.escape(marker) + r'{' + str(count) + r',}[ \t]*', line):
                fence = None
            output.append('')
            continue
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if opening:
            fence = (opening[1][0], len(opening[1]))
            output.append('')
        else:
            output.append(line)
    return '\n'.join(output)


def table(body, section, headers, *, ids=True):
    # Fenced examples must never become the canonical table.
    body = without_fenced_examples(body)
    lines = body.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(section, line)]
    if len(starts) != 1:
        raise HandoffError('Missing or duplicate canonical section')
    start = starts[0]
    level = len(lines[start]) - len(lines[start].lstrip('#'))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r'#{1,' + str(level) + r'}\s', lines[i])), len(lines))
    selected = []
    for line in lines[start + 1:end]:
        row = line.strip()
        if '|' in row:
            if not row.startswith('|') or not row.endswith('|'):
                raise HandoffError('Canonical table rows must use leading/trailing pipes')
            selected.append(row)
    def cells(line):
        if not line.endswith('|'):
            raise HandoffError('Table must use leading/trailing pipes')
        # Literal pipes must be written as &#124;, not ambiguous escaped delimiters.
        return [x.strip().replace('&#124;', '|') for x in line[1:-1].split('|')]
    if len(selected) < 2 or cells(selected[0]) != headers:
        raise HandoffError('Unsupported canonical table headers')
    if len(cells(selected[1])) != len(headers) or not all(re.fullmatch(r':?-{3,}:?', x) for x in cells(selected[1])):
        raise HandoffError('Invalid table separator')
    rows = []
    seen = set()
    for line in selected[2:]:
        values = cells(line)
        if len(values) != len(headers) or any(not x or re.fullmatch(r'<[^>]+>', x) for x in values):
            raise HandoffError('Incomplete or unsupported canonical row')
        if (ids and re.search(r'[\s`\[\]<>|]', values[0])) or values[0] in seen:
            raise HandoffError('Duplicate or malformed canonical ID')
        seen.add(values[0])
        rows.append(dict(zip(headers, values)))
    return rows


def read_spec(raw):
    fields, body = metadata(raw, 'spec')
    rows = table(body, r'^###\s+6\.1(?:\s|\.)', AC_HEADERS)
    if not rows:
        raise HandoffError('A handoff must declare its canonical ACs')
    return {'metadata': fields, 'acs': rows}


def read_questions(raw):
    fields, body = metadata(raw, 'questions')
    rows = table(body, r'^##\s+1\.(?:\s|$)', Q_HEADERS)
    for row in rows:
        if row['미해결 시 차단'] not in ('yes', 'no') or row['상태'] not in ('open', 'deferred', 'resolved'):
            raise HandoffError('Invalid blocking flag or question state')
    return {'metadata': fields, 'questions': rows}


def affected_ids(question, ac_ids):
    value = question['영향 절·AC·범위']
    if value in ('*', '전체', 'all'):
        return set(ac_ids)
    # IDs are opaque; token boundaries prevent AC-1 matching AC-10.
    found = set(re.split(r'[,，、\s]+', value))
    if not found or not found <= set(ac_ids):
        raise HandoffError('Blocking question has no explicit canonical AC impact')
    # Ranges/section-only impacts are intentionally unsupported; enumerate AC IDs.
    if re.search(r'(?:~|…|\.\.|–)', value):
        raise HandoffError('Enumerate affected AC IDs instead of ranges')
    return found
