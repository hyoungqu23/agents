import { projects } from './api.js';
import { renderRows, selectField, showProblem } from './ui.js';

const toolbar = document.querySelector('#toolbar');
const rows = document.querySelector('#rows');
const selection = document.querySelector('#selection');
const count = document.createElement('span');
count.setAttribute('role', 'status');
count.setAttribute('aria-live', 'polite');
rows.setAttribute('aria-live', 'polite');

let status = 'all';
let selected = null;
let visible = [];
let latestRequest = 0;

toolbar.className = 'filter';
toolbar.append(selectField({
  label: 'Status',
  options: [['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']],
  value: status,
  onChange(value) {
    status = value;
    void load();
  }
}), count);

function render() {
  if (visible.length === 0) {
    rows.textContent = 'No projects found.';
    return;
  }
  renderRows(rows, visible, selected?.id, project => {
    selected = project;
    selection.textContent = project.name;
    render();
  });
}

async function load() {
  const request = ++latestRequest;
  rows.setAttribute('aria-busy', 'true');
  rows.textContent = 'Loading projects…';
  count.textContent = 'Loading…';
  try {
    const result = await projects(status);
    if (request !== latestRequest) return;
    visible = result;
    count.textContent = `${visible.length} ${visible.length === 1 ? 'project' : 'projects'}`;
    render();
  } catch {
    if (request !== latestRequest) return;
    count.textContent = '';
    showProblem(rows, () => { void load(); });
  } finally {
    if (request === latestRequest) rows.setAttribute('aria-busy', 'false');
  }
}

await load();
