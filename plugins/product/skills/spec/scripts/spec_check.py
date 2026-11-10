#!/usr/bin/env python3
"""Check local Markdown handoff records; never certify source truth or app behavior."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import re
import sys

_module = importlib.util.spec_from_file_location('spec_handoff', Path(__file__).with_name('spec_handoff.py'))
handoff = importlib.util.module_from_spec(_module)
_module.loader.exec_module(handoff)


def read(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('Input path traverses a symlink; use the actual resolved path')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        return stream.read()


def check(spec_path, questions_path):
    result = {'structure': 'invalid', 'gaps': [], 'limitation': 'Record checks do not certify semantic correctness or runtime behavior.'}
    try:
        spec_path, questions_path = Path(spec_path).absolute(), Path(questions_path).absolute()
        raw, qraw = read(spec_path), read(questions_path)
        spec, questions = handoff.read_spec(raw), handoff.read_questions(qraw)
        sm, qm = spec['metadata'], questions['metadata']
        if ((spec_path.parent / sm['questions']).resolve() != questions_path.resolve()
                or (questions_path.parent / qm['spec']).resolve() != spec_path.resolve()
                or sm['id'].split(':', 1)[1] != qm['id'].split(':', 1)[1]):
            raise ValueError('Companion paths or identities disagree')
        ids = [r['AC ID'] for r in spec['acs']]
        active = [{'id': q['ID'], 'acs': sorted(handoff.affected_ids(q, ids))}
                  for q in questions['questions'] if q['미해결 시 차단'] == 'yes' and q['상태'] in ('open', 'deferred')]
        body = handoff.clean(raw)
        for number in range(1, 7):
            if len(re.findall(r'^## ' + str(number) + r'\.\s', body, re.M)) != 1:
                result['gaps'].append('Missing/duplicate SPEC section ' + str(number))
        reviews = handoff.table(body, r'^###\s+6\.2(?:\s|\.)', ['검토', '수행 범위·방식', '결과와 한계'], ids=False)
        expected = {'구조·ID·상호 참조', '원자료·권위·판본 대조', '화면·정책·API·AC 정합성', 'AC별 구현 내용 재구성'}
        if {r['검토'] for r in reviews} != expected:
            result['gaps'].append('All four review records are required')
        if re.search(r'(?:^|[|:])\s*<[^>\n]+>', body, re.M) or re.search(r'(?:^|[|:])\s*<[^>\n]+>', handoff.clean(qraw), re.M):
            result['gaps'].append('Unfilled template placeholders remain')
        if sm['status'] == 'ready' and active:
            result['gaps'].append('Ready contradicts active blocking questions')
        result.update(structure='valid' if not result['gaps'] else 'invalid', declared_status=sm['status'],
                      active_blockers=active, ac_ids=ids,
                      sources={'spec': hashlib.sha256(raw).hexdigest(), 'questions': hashlib.sha256(qraw).hexdigest()})
    except (ValueError, OSError, UnicodeError) as error:
        result['gaps'].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--questions', type=Path, required=True)
    args = parser.parse_args()
    value = check(args.spec, args.questions)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if value['structure'] == 'valid' else 2


if __name__ == '__main__':
    sys.exit(main())
