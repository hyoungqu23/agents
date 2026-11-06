"""Validate the automated review envelope; source truth is checked separately."""
import re


LABELS = ('P1', 'P2', 'P3', 'P999', '질문')
SCENARIOS = ('S1', 'S2', 'S3', 'S4')
VERDICTS = ('confirmed', 'partial', 'refuted', 'unresolved')
STATES = ('present', 'already_addressed', 'not_applicable', 'unknown')
ACTIONS = ('fix', 'answer', 'pushback', 'already-addressed', 'defer')


class ContractError(ValueError):
    pass


def text(value):
    return isinstance(value, str) and bool(value.strip())


def check_comment(label, body):
    if label not in LABELS or not text(body) or not re.match(r'^\[' + re.escape(label) + r'\]\s+\S', body):
        raise ContractError('Comment needs exactly its allowed prefix and nonempty text')


def keyed(rows):
    if not isinstance(rows, list):
        raise ContractError('Claims must be an array')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not text(row.get('id')) or row['id'] in result:
            raise ContractError('Claim IDs must be present and unique')
        result[row['id']] = row
    return result


def validate(request, result):
    if (request.get('schema_version') != 1 or request.get('mode') != 'draft-only'
            or request.get('scenario') not in SCENARIOS or not isinstance(request.get('target'), dict)):
        raise ContractError('Invalid trusted automation request')
    if (not isinstance(result, dict) or result.get('schema_version') != 1
            or result.get('scenario') != request['scenario'] or result.get('target') != request['target']):
        raise ContractError('Result belongs to another scenario or source snapshot')
    if not isinstance(result.get('limitations'), list) or any(not text(x) for x in result['limitations']):
        raise ContractError('Limitations must be a text array')
    inputs, outputs = keyed(request.get('claims')), keyed(result.get('claims'))
    if inputs.keys() != outputs.keys():
        raise ContractError('Every input claim must be assessed exactly once')
    review = result.get('review')
    if request['scenario'] in ('S1', 'S3', 'S4'):
        if (not isinstance(review, dict) or review.get('target') != request['target']
                or review.get('comment_policy') != 'hm2-five'):
            raise ContractError('This scenario requires the current five-prefix code ledger')
    elif review is not None:
        raise ContractError('Claim-only S2 must not claim a whole-code review')
    for row in outputs.values():
        if (row.get('verdict') not in VERDICTS or row.get('current_state') not in STATES
                or row.get('action') not in ACTIONS):
            raise ContractError('Unknown claim verdict, state or action')
        for name in ('evidence', 'counterevidence'):
            if not isinstance(row.get(name), list):
                raise ContractError('Claim evidence and counterevidence must be arrays')
        if row['verdict'] == 'unresolved' and not text(row.get('missing_evidence')):
            raise ContractError('Unresolved claims must identify missing evidence')
        if row['verdict'] != 'unresolved' and not row['evidence']:
            raise ContractError('Resolved judgments need source evidence')
        reply = row.get('reply')
        if reply is None:
            continue
        if not isinstance(reply, dict):
            raise ContractError('Reply must be null or a labelled body')
        check_comment(reply.get('label'), reply.get('body'))
        if row['action'] == 'answer' and reply['label'] != '질문':
            raise ContractError('Question answers have no severity and use 질문')
        if row['action'] == 'fix' and row['current_state'] != 'already_addressed':
            raise ContractError('Unimplemented fixes cannot produce completion replies')
        if row['action'] == 'already-addressed' and row['current_state'] != 'already_addressed':
            raise ContractError('Already-addressed action needs the matching current state')
        if row['verdict'] == 'unresolved' and reply['label'] != '질문':
            raise ContractError('Unresolved claims may only draft a specific question')
    return result
