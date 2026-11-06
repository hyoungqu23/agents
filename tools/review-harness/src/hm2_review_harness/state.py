"""User state, durable queue and local service locking."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import shutil
import sqlite3
import tempfile
import time
import uuid


class HarnessError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def home():
    value = os.environ.get('HM2_REVIEW_HOME')
    return Path(value).expanduser().resolve() if value else Path.home() / 'Library/Application Support/hm2-review-harness'


def save_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise HarnessError('Expected a regular state file: ' + str(path))
    return json.loads(path.read_text())


def defaults():
    return dict(schema_version=1, hostname='github.com', login='', repositories=[],
                provider='codex', agent_path='', gh_path='', git_path='', poll_seconds=120,
                timeout_seconds=1200, daily_runs=20, max_packet_bytes=1_000_000,
                retention_days=14, max_state_bytes=2 * 1024 ** 3,
                pending_enabled=False, active_device=None, paused=False)


def device(root):
    path = Path(root) / 'device.json'
    if not path.exists():
        save_json(path, {'id': str(uuid.uuid4()), 'name': socket.gethostname()})
    return read_json(path)['id']


def validate_config(config):
    if type(config.get('schema_version')) is not int or config['schema_version'] != 1:
        raise HarnessError('Unsupported configuration version')
    if not re.fullmatch(r'[A-Za-z0-9.-]+', config.get('hostname', '')):
        raise HarnessError('Invalid GitHub hostname')
    if config.get('provider') not in ('codex', 'claude') or not isinstance(config.get('repositories'), list):
        raise HarnessError('Choose a supported provider and repository list')
    seen = set()
    for row in config['repositories']:
        name = row.get('name', '')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name) or name.lower() in seen:
            raise HarnessError('Repositories must be unique owner/name values')
        seen.add(name.lower())
        if not isinstance(row.get('teams', []), list):
            raise HarnessError('Repository teams must be a list')
    for key, low in [('poll_seconds', 30), ('timeout_seconds', 1), ('daily_runs', 1), ('max_packet_bytes', 4096), ('retention_days', 1), ('max_state_bytes', 1)]:
        if type(config.get(key)) is not int or config[key] < low:
            raise HarnessError('Invalid configured limit: ' + key)
    return config


def load_config(root):
    return validate_config({**defaults(), **read_json(Path(root) / 'config.json')})


@contextmanager
def instance_lock(root):
    import fcntl
    path = Path(root) / 'service.lock'; path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise HarnessError('Another local harness instance is active') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class Store:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / 'state.sqlite3'
        if path.is_symlink():
            raise HarnessError('State database cannot be a symlink')
        self.db = sqlite3.connect(path, timeout=10)
        identity = self.db.execute('PRAGMA application_id').fetchone()[0]
        tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if identity not in (0, 1213010514) or (identity == 0 and tables):
            self.db.close(); raise HarnessError('State database is not owned by this harness')
        if self.db.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
            self.db.close(); raise HarnessError('Unsupported database; do not downgrade it')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
          PRAGMA application_id=1213010514;
          CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, scenario TEXT NOT NULL,
            event TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL,
            updated REAL NOT NULL, run_dir TEXT, error TEXT, result TEXT);
          CREATE TABLE IF NOT EXISTS watches (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, data TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS model_calls (job_id TEXT NOT NULL, at REAL NOT NULL);
          PRAGMA user_version=1;
        ''')
        self.db.row_factory = sqlite3.Row
        path.chmod(0o600)

    def close(self):
        self.db.close()

    def _insert(self, scenario, event):
        key = digest({'scenario': scenario, 'event': event})
        self.db.execute('INSERT OR IGNORE INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                        (key, scenario, json.dumps(event), 'queued', time.time(), time.time(), None, None, None))
        return key

    def enqueue(self, scenario, event):
        with self.db:
            return self._insert(scenario, event)

    def observe(self, key, value, scenario=None, event=None):
        fingerprint = digest(value)
        prior = self.db.execute('SELECT fingerprint FROM watches WHERE id=?', (key,)).fetchone()
        if prior and prior[0] == fingerprint:
            return None
        with self.db:
            job = self._insert(scenario, event) if scenario else None
            self.db.execute('INSERT OR REPLACE INTO watches VALUES (?,?,?)', (key, fingerprint, json.dumps(value)))
        return job

    def tracked(self):
        return [json.loads(row[0]) for row in self.db.execute('SELECT data FROM watches')]

    def next(self):
        row = self.db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
        return dict(row) if row else None

    def update(self, key, status, *, run_dir=None, error=None, result=None):
        with self.db:
            self.db.execute('UPDATE jobs SET status=?,updated=?,run_dir=COALESCE(?,run_dir),error=?,result=COALESCE(?,result) WHERE id=?',
                            (status, time.time(), str(run_dir) if run_dir else None, error,
                             json.dumps(result) if result is not None else None, key))

    def recover(self):
        with self.db:
            self.db.execute("UPDATE jobs SET status='queued' WHERE status IN ('collecting','snapshotting')")
            self.db.execute("UPDATE jobs SET status='partial',error='Interrupted review; retry explicitly' WHERE status='reviewing'")
            self.db.execute("UPDATE jobs SET status='write_unconfirmed',error='Inspect receipts before retry' WHERE status='saving'")

    def daily_count(self):
        cutoff = int(time.time() // 86400) * 86400
        return self.db.execute('SELECT count(*) FROM model_calls WHERE at>=?', (cutoff,)).fetchone()[0]

    def record_model_call(self, key):
        with self.db:
            self.db.execute('INSERT INTO model_calls VALUES (?,?)', (key, time.time()))

    def wake_budget(self):
        cutoff = int(time.time() // 86400) * 86400
        with self.db:
            self.db.execute("UPDATE jobs SET status='queued' WHERE status='budget_limited' AND updated<?", (cutoff,))

    def storage_bytes(self):
        total = 0
        for path in self.root.rglob('*'):
            try:
                if not path.is_dir() or path.is_symlink():
                    total += path.lstat().st_size
            except FileNotFoundError:
                pass
        return total

    def prune(self, days, apply=False):
        if type(days) is not int or days < 1:
            raise HarnessError('Retention must be at least one day')
        cutoff = time.time() - days * 86400; candidates = []
        states = {(v.get('repo'), v.get('pr')): v.get('state') for v in self.tracked()}
        run_root = self.root / 'runs'
        if run_root.is_symlink():
            raise HarnessError('Owned run directory cannot be a symlink')
        for row in self.db.execute("SELECT * FROM jobs WHERE updated<? AND status IN ('local_ready','pending_saved','superseded','partial')", (cutoff,)):
            event = json.loads(row['event'])
            if event.get('pr') and row['status'] != 'superseded' and states.get((event['repo'], event['pr'])) != 'closed':
                continue
            if not row['run_dir']:
                continue
            path = Path(row['run_dir'])
            if path.is_symlink() or path.resolve().parent != run_root.resolve() or not path.is_dir():
                continue
            candidates.append(str(path))
            if apply:
                shutil.rmtree(path)
                with self.db:
                    self.db.execute('UPDATE jobs SET run_dir=NULL WHERE id=? AND run_dir=?', (row['id'], str(path)))
        return candidates

    def rows(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]

    def previous(self, host, repo, number):
        for row in self.db.execute('SELECT event,result FROM jobs WHERE result IS NOT NULL ORDER BY created DESC'):
            event = json.loads(row['event'])
            if event.get('hostname') == host and event.get('repo') == repo and event.get('pr') == number:
                return json.loads(row['result'])
        return None
