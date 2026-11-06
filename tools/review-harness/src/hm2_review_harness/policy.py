"""Read current local authorization at each remote-write boundary."""
from pathlib import Path

from .state import HarnessError, device, load_config


class PolicyChanged(HarnessError):
    pass


def require_pending(config, root, event):
    try:
        current = load_config(Path(root))
    except (OSError, ValueError, HarnessError) as error:
        raise PolicyChanged('Pending policy is unavailable; new writes are blocked') from error
    identity = ('hostname', 'login', 'gh_path', 'git_path')
    if (any(current[key] != config[key] for key in identity)
            or event['hostname'] != current['hostname']
            or event.get('account', current['login']) != current['login']
            or event['repo'] not in [row['name'] for row in current['repositories']]
            or current['paused'] or not current['pending_enabled']
            or current['active_device'] != device(root)):
        raise PolicyChanged('Pending authorization changed; keep candidates local')
    return current
