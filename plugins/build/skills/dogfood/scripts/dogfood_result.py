#!/usr/bin/env python3
"""Capture local QA scope/source and assess records; never run apps or browser actions."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys


class RecordError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def revision_identity(value):
    value = value.strip().removeprefix('commit:').strip()
    # Normalize full Git object IDs without treating arbitrary build IDs as SHAs.
    return value.lower() if re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})', value) else value


def rows(value, label):
    if not isinstance(value, list):
        raise RecordError(label + ' must be an array')
    result = {}
    for row in value:
        if not isinstance(row, dict) or not text(row.get('id')) or row['id'] in result:
            raise RecordError(label + ' needs unique stable IDs')
        result[row['id']] = row
    return result


def read(path):
    if path.is_symlink() or not path.is_file():
        raise RecordError('Expected a regular file')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        return stream.read()


def safe_file(root, value):
    if not text(value) or '\\' in value or '\x00' in value:
        raise RecordError('Invalid evidence path')
    part = PurePosixPath(value)
    if part.is_absolute() or '..' in part.parts or str(part) == '.':
        raise RecordError('Evidence escapes the run directory')
    path = root
    for item in part.parts:
        path = path / item
        if path.is_symlink():
            raise RecordError('Evidence traverses a symlink')
    return path


def load(path):
    value = json.loads(read(path))
    if not isinstance(value, dict):
        raise RecordError('Expected JSON object')
    return value


def plan(run):
    if type(run.get('schema_version')) is not int or run['schema_version'] != 1:
        raise RecordError('Expected schema_version 1')
    target = run.get('target')
    if not isinstance(target, dict) or any(not text(target.get(k)) for k in ('url', 'environment', 'role', 'backend', 'served_build')):
        raise RecordError('Identify target URL/environment/role/backend/served_build; use unknown when unverified')
    for field in ('desired_revision', 'served_revision'):
        if field in target and (not text(target[field]) or not text(revision_identity(target[field]))):
            raise RecordError(field + ' must be a nonempty revision when supplied')
    if target.get('desired_revision') and revision_identity(target['desired_revision']) == 'unknown':
        raise RecordError('Resolve the requested revision before declaring an exact revision target')
    journeys = rows(run.get('journeys'), 'journeys')
    checks = rows(run.get('checks'), 'checks')
    if not journeys or not checks or not any(c.get('required') is True for c in checks.values()):
        raise RecordError('Declare journeys and nonempty required checks')
    if not any(c.get('axis') == 'visual' and c.get('required') is True for c in checks.values()):
        raise RecordError('Actual-app dogfood includes a required visual check')
    definitions = []
    for row in checks.values():
        if (row.get('journey') not in journeys or type(row.get('required')) is not bool
                or row.get('axis') not in ('functional', 'visual', 'persistence', 'accessibility')
                or not text(row.get('purpose'))):
            raise RecordError('Check needs a journey, required boolean, axis and purpose')
        expectation = row.get('expectation')
        if (not isinstance(expectation, dict) or any(not text(expectation.get(k)) for k in ('source', 'text'))
                or expectation.get('certainty') not in ('confirmed', 'needs_intent')):
            raise RecordError('Check needs an independent expectation or explicit needs_intent')
        definitions.append({k: row[k] for k in ('id', 'journey', 'required', 'axis', 'purpose', 'expectation')})
    return {'target': target, 'journeys': run['journeys'], 'checks': definitions}


def local_source(target):
    if not target.get('local_root'):
        return {'mode': 'remote_only', 'limitation': 'External served build is observed through tool traces, not authenticated by this helper.'}
    root = Path(target['local_root']).resolve()
    if not root.is_dir():
        raise RecordError('Local source root is missing')
    files = {}
    # Fixed runtime exclusions are disclosed, never caller-selected exclusions.
    ignored = {'.git', 'node_modules', '.next', 'dist', '__pycache__'}
    for directory, folders, names in os.walk(root, followlinks=False):
        folders[:] = sorted(f for f in folders if f not in ignored)
        for name in sorted(names + [f for f in folders if (Path(directory) / f).is_symlink()]):
            path = Path(directory) / name
            if name == '.git':
                continue
            if path.is_symlink():
                value = {'kind': 'symlink', 'sha256': hashlib.sha256(os.readlink(path).encode()).hexdigest()}
            else:
                value = {'kind': 'file', 'sha256': hashlib.sha256(read(path)).hexdigest(),
                         'mode': stat.S_IMODE(path.stat().st_mode)}
            files[str(path.relative_to(root))] = value
    return {'mode': 'local', 'root': str(root), 'files': files,
            'excluded_runtime': sorted(ignored)}


def observation_targets(value):
    """Bind observations to their source and definition, not unrelated scope."""
    definition = value['plan']
    target = digest({'target': definition['target'], 'local_source': value['local_source']})
    journeys = rows(definition['journeys'], 'journeys')
    return {'observation_target': target,
            'check_targets': {check['id']: digest({'target': target, 'check': check,
                                                  'journey': journeys[check['journey']]})
                              for check in definition['checks']}}


def capture(run_path):
    run_path = Path(run_path).absolute()
    run = load(run_path)
    definition = plan(run)
    local = local_source(definition['target'])
    if local['mode'] == 'local' and run_path.resolve().is_relative_to(Path(local['root'])):
        raise RecordError('Keep QA artifacts outside the inspected source tree')
    value = {'schema_version': 1, 'plan': definition, 'local_source': local}
    value.update(observation_targets(value))
    return {**value, 'digest': digest(value)}


def snapshot(path):
    value = load(Path(path))
    if value.get('schema_version') != 1 or value.get('digest') != digest({k: v for k, v in value.items() if k != 'digest'}):
        raise RecordError('Invalid capture digest')
    if not isinstance(value.get('plan'), dict) or not isinstance(value.get('local_source'), dict):
        raise RecordError('Incomplete capture')
    if 'observation_target' in value or 'check_targets' in value:
        if any(value.get(k) != v for k, v in observation_targets(value).items()):
            raise RecordError('Observation targets disagree with captured definitions')
    return value


def evidence(root, records):
    if not isinstance(records, list) or not records:
        raise RecordError('Completed observations need evidence files')
    result = {}
    for entry in records:
        if not isinstance(entry, dict):
            raise RecordError('Invalid evidence entry')
        path = safe_file(root, entry.get('path'))
        raw = read(path)
        if not raw or hashlib.sha256(raw).hexdigest() != entry.get('sha256'):
            raise RecordError('Evidence is empty or changed')
        result[entry['path']] = raw
    return result


def image_dimensions(raw):
    if len(raw) >= 24 and raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR':
        return list(struct.unpack('>II', raw[16:24]))
    if raw[:2] == b'\xff\xd8':
        offset = 2
        while offset < len(raw):
            if raw[offset] != 0xff:
                break
            while offset < len(raw) and raw[offset] == 0xff:
                offset += 1
            if offset >= len(raw):
                break
            marker = raw[offset]
            offset += 1
            if marker in (0xd9, 0xda):
                break
            if marker in (0x01, 0xd8, *range(0xd0, 0xd8)):
                continue
            if offset + 2 > len(raw):
                break
            length = struct.unpack('>H', raw[offset:offset + 2])[0]
            if length < 2 or offset + length > len(raw):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 8:
                height, width = struct.unpack('>HH', raw[offset + 3:offset + 7])
                return [width, height]
            offset += length
    raise RecordError('Unsupported or truncated image metadata; supported formats are PNG and JPEG')


def visual_check(check, captured):
    image = check.get('visual')
    if not isinstance(image, dict) or image.get('inspected') is not True or not text(image.get('observation')):
        raise RecordError('Visual check requires an actual image inspection record')
    if image.get('image') not in captured or image.get('inspection_trace') not in captured:
        raise RecordError('Image and actual inspection trace must be evidence files')
    raw = captured[image['image']]
    dimensions = image_dimensions(raw)
    if dimensions != image.get('pixels') or any(x <= 0 for x in dimensions):
        raise RecordError('Capture dimensions disagree with image metadata')
    if (image.get('capture') not in ('viewport', 'full_page', 'region')
            or not isinstance(image.get('css_viewport'), list) or len(image['css_viewport']) != 2
            or any(type(x) is not int or x <= 0 for x in image['css_viewport'])
            or any(type(image.get(k)) not in (int, float) or image[k] <= 0 for k in ('dpr', 'scale'))
            or not text(image.get('comparison_scope'))):
        raise RecordError('Record viewport, capture mode, DPR/scale and actual comparison scope')


def assess(run_path, before_path, after_path):
    value = {'status': 'invalid', 'product_result': 'undetermined', 'gaps': []}
    try:
        run_path = Path(run_path).resolve()
        run = load(run_path)
        before, after = snapshot(before_path), snapshot(after_path)
        current = capture(run_path)
        if 'observation_target' not in after:
            # Compare old captures in their original shape without rewriting them.
            for field in ('digest', 'observation_target', 'check_targets'):
                current.pop(field)
            current['digest'] = digest(current)
        if current != after or before['local_source'] != after['local_source'] or before['plan']['target'] != after['plan']['target']:
            raise RecordError('Source/target changed; reconcile and reverify under a new run')
        # Exploration can append checks, but cannot erase or weaken the initial scope.
        for label in ('checks', 'journeys'):
            prior, latest = rows(before['plan'][label], label), rows(after['plan'][label], label)
            if any(latest.get(k) != r for k, r in prior.items()):
                raise RecordError('Initial scope was removed or changed')
        checks = rows(run['checks'], 'checks')
        issues = rows(run.get('issues', []), 'issues')
        targets = observation_targets(after)
        prior_checks = rows(before['plan']['checks'], 'checks')

        def check_targets(key):
            allowed = {targets['check_targets'][key], after['digest']}
            # Legacy evidence belongs only to definitions present in its capture.
            if 'observation_target' not in before and key in prior_checks:
                allowed.add(before['digest'])
            return allowed

        gaps = value['gaps']
        target_evidence = run.get('target_evidence', {})
        if target_evidence.get('target') not in {targets['observation_target'], before['digest'], after['digest']}:
            gaps.append({'reason': 'target_unverified'})
        else:
            evidence(run_path.parent, target_evidence.get('evidence'))
        desired = run['target'].get('desired_revision')
        if desired:
            served = run['target'].get('served_revision')
            if not served or revision_identity(served) == 'unknown':
                gaps.append({'reason': 'served_revision_unverified'})
            elif revision_identity(desired) != revision_identity(served):
                raise RecordError('Served revision does not match the requested revision')
        for key, check in checks.items():
            status = check.get('status')
            if status not in ('passed', 'failed', 'blocked', 'skipped') or not text(check.get('detail')):
                raise RecordError('Every check needs its real status and detail')
            if status in ('blocked', 'skipped'):
                if not text(check.get('reason')):
                    raise RecordError('Blocked/skipped checks need a reason')
                if check['required']:
                    gaps.append({'check': key, 'reason': status})
                continue
            if check.get('target') not in check_targets(key):
                raise RecordError('Observation targets another capture')
            if check['expectation']['certainty'] != 'confirmed':
                gaps.append({'check': key, 'reason': 'needs_intent'})
            captured = evidence(run_path.parent, check.get('evidence'))
            if check['axis'] == 'visual':
                visual_check(check, captured)
            if check['axis'] == 'persistence':
                persistence = check.get('persistence', {})
                if persistence.get('mode') != 'real_api' or not text(persistence.get('requery_trace')) or persistence['requery_trace'] not in captured:
                    gaps.append({'check': key, 'reason': 'real_persistence_unverified'})
            if status == 'failed' and not any(i.get('check') == key and i.get('classification') in ('reproduced', 'observed_once', 'intermittent') for i in issues.values()):
                raise RecordError('Failed check needs an observed issue')
        for key, issue in issues.items():
            if (issue.get('check') not in checks or issue.get('target') not in check_targets(issue['check'])
                    or issue.get('classification') not in ('reproduced', 'observed_once', 'intermittent', 'unverified', 'needs_intent')
                    or any(not text(issue.get(k)) for k in ('expected', 'actual', 'steps', 'impact'))
                    or type(issue.get('attempts')) is not int or issue['attempts'] < 1):
                raise RecordError('Issue needs target/check, conditions, expectation, observation, impact and actual attempts')
            evidence(run_path.parent, issue.get('evidence'))
            if (issue['classification'] in ('reproduced', 'observed_once', 'intermittent')
                    and checks[issue['check']]['status'] != 'failed'):
                raise RecordError('An observed failure issue must reference a failed check; use a separate check for a different outcome')
        for operation in rows(run.get('data_operations', []), 'data operations').values():
            if not isinstance(operation.get('created_ids'), list) or any(not text(x) for x in operation['created_ids']):
                raise RecordError('Record exact created data IDs')
            if operation.get('outcome') not in ('confirmed', 'unknown', 'failed') or not text(operation.get('detail')):
                raise RecordError('Record data operation outcome/detail')
            if operation['outcome'] == 'unknown' or operation.get('cleanup') not in ('done', 'not_needed'):
                gaps.append({'operation': operation['id'], 'reason': 'data_resolution_or_cleanup_pending'})
            if operation.get('cleanup') == 'done':
                evidence(run_path.parent, operation.get('evidence'))
        observed = any(i['classification'] in ('reproduced', 'observed_once', 'intermittent') and
                       checks[i['check']]['expectation']['certainty'] == 'confirmed' for i in issues.values())
        unknown = any(i['classification'] in ('unverified', 'needs_intent') for i in issues.values())
        value.update(status='partial' if gaps else 'complete', target=after['digest'])
        if gaps and all(c['status'] in ('blocked', 'skipped') for c in checks.values() if c['required']):
            value['status'] = 'blocked'
        value['product_result'] = 'issues_found' if observed else ('undetermined' if gaps or unknown else 'no_issues_observed')
        return value
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as error:
        value['gaps'].append({'reason': 'invalid_record', 'detail': str(error)})
        return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('capture', 'assess'):
        child = sub.add_parser(action)
        child.add_argument('--run', type=Path, required=True)
        child.add_argument('--output', type=Path, required=True)
        if action == 'assess':
            child.add_argument('--before', type=Path, required=True)
            child.add_argument('--after', type=Path, required=True)
    args = parser.parse_args()
    try:
        value = capture(args.run) if args.action == 'capture' else assess(args.run, args.before, args.after)
        definition = plan(load(args.run))
        target_root = definition['target'].get('local_root')
        if target_root and args.output.resolve().is_relative_to(Path(target_root).resolve()):
            raise RecordError('Output must be outside the inspected source')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0 if value.get('status') in (None, 'complete') else 2
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
