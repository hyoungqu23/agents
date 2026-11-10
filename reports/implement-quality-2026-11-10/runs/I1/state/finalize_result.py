import hashlib
import json
from pathlib import Path

state = Path(__file__).parent
root = state.parent / 'source'
verified = json.loads((state / 'verification-target-1.json').read_text())
target = verified['digest']

notes = '''Actual browser verification used mcp__cua_repl.js on Chrome tab 1893495263 at http://127.0.0.1:62963/. There are 43 recorded observations/control results. Default viewport was 2504x1363; responsive and error/race checks also used 700x800 and 701x800. Override was reset and only agent-created tab closed. Browser console capture returned [].
All four statuses were explicitly selected. All displayed Tide/Forest/North and 3; Active Tide/North and 2; Archived Forest and 1; Paused empty and 0. Native API test independently used the actual unchanged application server and API owner for every enum, without response replacement or mocking.
Forest was selected at All index 1. Name survived Active loading/absence and Paused empty. Archived returned Forest at index 0, aria-pressed=true. Native Tab reached SELECT, focus-visible=true, 3px solid blue outline. Picked border was rgb(36,87,197). At 700px there was one column with selected panel below; at 701px two columns with equal panel top. No horizontal overflow.
Active real 503 showed existing alert/Retry, without empty/count, while Forest remained. After authorized fixture PUT fail=false, clicking Retry kept current Active, showed loading/Forest, then returned 2 Active rows.
Race 1: older Active(600ms), later Archived(25ms) failed under fail=true. After B error, fail=false was set before A deadline. A later real 603ms Active HTTP barrier completed, while B error/Retry remained. Race 2: older Active pending, later Archived success; then fail=true and a real 603ms barrier yielded 503, while B Forest/1/selected remained. Race 3/4: older Archived and newer Active; after real 28/27ms paused HTTP barriers old success/failure/finally had time to finish, but Active was still loading/busy=true with Forest; it later completed to 2. Race 4 transition including both select actions was 19ms; Race 3 was 29ms including initial select and a pending DOM observation. Completion order is inferred from unchanged supplied server timing and actual fixture controls, not browser network interception.
Automation limits: page evaluate performance API was unavailable. Exact getByLabel('Status') had no match despite visible implicit label; observed semantic getByRole('combobox', name:'Status') worked. A locator Tab/Shift+Tab sequence focused BODY, then native Tab demonstrated correct SELECT focus. Direct CUA Node loopback request was denied EPERM. state/fixture_control.py therefore performed only authorized real fixture PUT controls and real GET barriers in an explicitly escalated local process, exchanging state-folder files with CUA. It did not replace responses or inject app state. Actual HTTP trace retained. Process stopped; final fail=false.
Same-filter Retry recovery was exercised. Concurrent overlapping same-filter Retry is not reachable through this UI because Retry disappears during loading; source cleanup is shared by reload and status replacements and was inspected. No state injection manufactured that condition.
Q-001 production deployment remains unverified. Existing all/automatic initial query and No project selected owner conventions were inspected/retained for Q-002. Input QUESTIONS was preserved. This is local implementation verification, not independent code review, independent Visual QA or release approval.
First result-generation attempt had a Python SyntaxError before writing the result. Its assess output assessment.json is retained as invalid (result file absent); it did not reflect a product-code or runtime-check failure. No source changed while correcting the record generator.
'''
(state / 'browser-verification-notes.txt').write_text(notes)

details = {
    'AC-1': {
        'condition': 'App renders existing StatusField and actual useProjects owner; unchanged local server supplies actual GET responses.',
        'action': 'Browser explicitly selected Active/Archived/Paused/All; native API test passed every enum through src/api.ts to the real server.',
        'outcome': 'Browser returned names/statuses/counts: All Tide/Forest/North 3; Active Tide/North 2; Archived Forest 1; Paused empty 0. App uses rows and rows.length.',
        'interfaces': 'App StatusField onChange -> status state -> useProjects(status) -> api.projects(status) GET query -> ProjectRows. Existing theme owns tokens and 700px boundary.',
        'verification': 'Actual-server native test asserts each enum and response. Browser distinguishes 3/2/1/0, label/focus/blue border and 700/701 layout. Only local environment was verified; All initialization preserved.',
    },
    'AC-2': {
        'condition': 'Browser selected Forest from successful All result at index 1.',
        'action': 'Forest selection -> Active loading/absent -> Paused successful [] -> Archived where Forest returns at index 0.',
        'outcome': 'Independent selected Project never resets on list updates. Browser retained Forest name, empty displayed 0 without Retry, returned Forest id had aria-pressed=true despite changed index.',
        'interfaces': 'App.tsx selected object -> ProjectRows selectedId/onSelect and always-present SelectedPanel. Row identity is Project.id and panel shows Project.name; no extra API.',
        'verification': 'Browser stages forest-preserved-loading/outside-active/empty and forest-restored-archived-index-0 establish selection retention and id restoration. Existing blue token and initial unselected text retained.',
    },
    'AC-3': {
        'condition': 'Forest selected; supplied unchanged server delays Active 600ms and others 25ms, with authorized mode PUT controlling actual 503/200 behavior.',
        'action': 'Active 503 -> current Active Retry recovery; older Active/newer Archived and older Archived/newer Active sequences with real controls and real HTTP timing barriers.',
        'outcome': 'Actual error/Retry differed from empty. Current Active Retry kept Forest and returned 2. Late A success preserved B error, late A failure preserved B success, old completion left newer Active loading. Guard also covers reload replacements; overlapping same-filter Retry is inaccessible while button is hidden.',
        'interfaces': 'useProjects current flag guards then/catch/finally; cleanup invalidates previous status/reload effect. Request key masks old presentation immediately. Existing ProblemPanel connects Retry, selected object stays independent.',
        'verification': 'Real 503 vs [] and Retry data distinguished. Race evidence includes latest pending/completed screens and supplied-server timing barriers, without interception/state injection. Retry recovery exercised; shared reload cleanup inspected for inaccessible overlapping same-filter case. No production claim.',
    },
}
columns = {'condition': '사전 조건', 'action': '행동', 'outcome': '기대 관찰 결과', 'interfaces': '관련 화면·흐름·API', 'verification': '확인 방법·미결 참조'}
originals = verified['coverage']['handoffs'][0]['spec']['acs']
trace = ['Source-bound review for target ' + target, 'SPEC revision 2 / QUESTIONS revision 1. All ACs mapped once, none excluded, no active blockers.']
for original in originals:
    ac = original['AC ID']
    trace.append('\n' + ac)
    for facet, column in columns.items():
        trace.extend([facet + ' expected: ' + original[column], facet + ' comparison: ' + details[ac][facet]])
trace.append('Read current App.tsx lines 7-21, useProjects.ts 5-10, ui.tsx 2-6, api.ts 2-5, theme.css 1 and actual-server API test. Author semantic judgments are supported by actual checks; helper validates bytes/records, not independent semantic correctness or authenticity of claimed execution.')
(state / 'source-review.txt').write_text('\n'.join(trace) + '\n')

def evidence(*names):
    return [{'path': name, 'sha256': hashlib.sha256((state / name).read_bytes()).hexdigest()} for name in names]

def quote(path, line):
    return {'path': path, 'line': line, 'quote': (root / path).read_text().splitlines()[line - 1]}

requirements = [
    {'id': 'AC-1', 'state': 'implemented', 'reason': 'Status/API/query/row owners drive actual filtered rows and length count. Browser verified all options, system accent, keyboard focus and breakpoint.', 'code': [quote('src/App.tsx',16), quote('src/App.tsx',17), quote('src/App.tsx',19), quote('src/api.ts',3), quote('src/ui.tsx',3), quote('src/ui.tsx',4), quote('src/theme.css',1)]},
    {'id': 'AC-2', 'state': 'implemented', 'reason': 'Independent selected object survives pending/error/empty/filtering; rows compare selected id. Browser verified Forest moves index 1 to index 0 with selection restored.', 'code': [quote('src/App.tsx',8), quote('src/App.tsx',19), quote('src/App.tsx',21), quote('src/ui.tsx',4), quote('src/ui.tsx',6)]},
    {'id': 'AC-3', 'state': 'implemented', 'reason': 'Query owner retains latest-only success/error/finally guard and immediately masks old query. Error/current Retry connected. Actual browser failure/recovery and timing reversals passed with selection retained.', 'code': [quote('src/useProjects.ts',8), quote('src/useProjects.ts',9), quote('src/useProjects.ts',10), quote('src/App.tsx',19), quote('src/ui.tsx',5), quote('src/api.ts',4)]},
]
verification = []
for key, command, logfile in [('typecheck',['npm','run','typecheck'],'native-typecheck-1.log'), ('tests',['npm','test'],'native-test-2.log'), ('build',['npm','run','build'],'native-build-1.log')]:
    verification.append({'id':key, 'status':'passed', 'detail': {'typecheck':'Native TypeScript check exited 0.', 'tests':'Actual unchanged server integration test passed all statuses, empty, 503 and recovery. Initial sandbox IPC EPERM retained; escalated retry exited 0, no skips.', 'build':'Native production build exited 0, 34 modules transformed.'}[key], 'target':target, 'command':command, 'cwd':str(root), 'exit_code':0, 'evidence':evidence(logfile,'native-verification-notes.txt')})

browser_checks = [
    ('browser-status',2504,1363,'Explicit four statuses in actual app returned distinct names/statuses and 3/2/1/0 counts. Native API test supplies real query/response contract evidence.', ['browser-evidence.json','native-test-2.log','browser-verification-notes.txt']),
    ('browser-design',701,800,'700x800 single column with selected panel below; 701x800 two columns, no horizontal overflow. Native Tab reached visible labelled Status select with blue 3px focus outline; selected border blue.', ['browser-evidence.json','browser-700.png','browser-701.png','browser-final.png','browser-verification-notes.txt']),
    ('browser-selection',2504,1363,'Forest All index 1 -> Active loading/absent -> Paused empty -> Archived index 0; panel retains Forest and returned id is pressed.', ['browser-evidence.json','browser-verification-notes.txt']),
    ('browser-recovery-races',701,800,'Real Active 503 vs Paused empty, current Active Retry loading/recovery with Forest. Delayed older success preserves latest error, older failure preserves latest success, older finally leaves newest request loading; server timing barriers retained.', ['browser-evidence.json','fixture-control-trace.jsonl','fixture_control.py','browser-error.png','browser-verification-notes.txt']),
]
for key, width, height, scenario, paths in browser_checks:
    verification.append({'id':key, 'status':'passed', 'detail':scenario, 'target':target, 'tool':'mcp__cua_repl.js (Chrome)', 'url':'http://127.0.0.1:62963/', 'scenario':scenario, 'viewport':{'width':width,'height':height}, 'evidence':evidence(*paths)})

reviews = []
behavior = {'AC-1':['tests','browser-status','browser-design'], 'AC-2':['browser-selection'], 'AC-3':['browser-recovery-races']}
for original in originals:
    ac = original['AC ID']
    reviews.append({'id':ac, 'target':target, 'ac_digest':hashlib.sha256(json.dumps(original,sort_keys=True,ensure_ascii=False).encode()).hexdigest(), 'facets':{facet:{'expected':original[column], 'verdict':'matched', 'detail':details[ac][facet]} for facet,column in columns.items()}, 'behavior_checks':behavior[ac], 'evidence':evidence('source-review.txt','browser-evidence.json','browser-verification-notes.txt')})

result = {
    'schema_version':1, 'target':target,
    'changes':[
        {'path':'src/App.tsx','reason':'Connect current query, actual count, independent selection and distinct loading/error/empty via existing owners.'},
        {'path':'src/useProjects.ts','reason':'Immediately mark stale presentation pending on status/reload while retaining latest-only effect guard.'},
        {'path':'src/ui.tsx','reason':'Title-case contract project status labels to match chosen reference.'},
        {'path':'tests/api.test.ts','reason':'Use unchanged actual app server rather than synthetic per-test responses for all filters and failure/recovery.'},
    ],
    'requirements':requirements, 'verification':verification, 'source_review':reviews,
    'differences':['Prototype orange uses existing system blue accent. Existing theme typography, spacing, radius and 700px boundary retained.', 'Existing all initial query and No project selected owner text retained; no automatic project selection or storage persistence.'],
    'handoff':{
        'start_command':'PORT=0 npm start', 'cwd':str(root), 'url':'http://127.0.0.1:62963/',
        'scenario_data':'Tide(active), Forest(archived), North(active); paused empty. Existing synthetic PUT /__fixture__/mode fail true/false; final fail=false.',
        'input_identity':{'spec_sha256':verified['sources']['spec']['sha256'], 'questions_sha256':verified['sources']['questions']['sha256'], 'head':verified['head']},
        'diff':'implementation.diff',
        'limitations':['Local supplied server verified; production deployment Q-001 remains unverified.', 'No independent code review, independent Visual QA or release workflow ran.', 'Browser network/performance capture unavailable; query traced through unchanged API owner and actual-server native test.', 'Concurrent overlapping same-filter Retry is inaccessible while loading; shared reload cleanup inspected and current-filter recovery exercised.'],
    },
}
(state / 'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2) + '\n')
print('Result written for target ' + target)
