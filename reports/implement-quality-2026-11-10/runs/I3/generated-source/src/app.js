import { projects } from './api.js';
import { selectField, renderRows, showProblem } from './ui.js';

const toolbar = document.querySelector('#toolbar');
const rows = document.querySelector('#rows');
const selection = document.querySelector('#selection');
const count = document.createElement('span');
count.setAttribute('role', 'status');
count.setAttribute('aria-live', 'polite');
toolbar.className = 'filter';
toolbar.append(selectField({
  label: 'Status',
  options: [['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']],
  value: 'all',
  onChange(value) {
    status = value;
    void load();
  }
}), count);

let selected = null;
let visible = [];
let status = 'all';
let phase = 'loading';
let latestRequest = 0;

async function load() {
  const request = ++latestRequest;
  phase = 'loading';
  render();
  try {
    const result = await projects(status);
    if (request !== latestRequest) return;
    visible = result;
    phase = 'ready';
  } catch {
    if (request !== latestRequest) return;
    phase = 'error';
  }
  render();
}

function render() {
  selection.textContent = selected?.name ?? 'None';
  rows.setAttribute('aria-busy', String(phase === 'loading'));
  if (phase === 'loading') {
    count.textContent = 'Loading…';
    rows.textContent = 'Loading projects…';
    return;
  }
  if (phase === 'error') {
    count.textContent = 'Unavailable';
    showProblem(rows, () => void load());
    return;
  }
  count.textContent = `${visible.length} ${visible.length === 1 ? 'project' : 'projects'}`;
  if (visible.length === 0) {
    rows.textContent = 'No projects match this status.';
    return;
  }
  renderRows(rows, visible, selected?.id, project => {
    selected = project;
    render();
  });
}

void load();
