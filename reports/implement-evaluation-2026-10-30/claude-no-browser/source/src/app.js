import { projects } from './api.js';
import { createProjectList } from './projectList.js';
import { renderRows, selectField, showProblem } from './ui.js';

const statuses = [['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']];
const toolbar = document.querySelector('#toolbar');
const rows = document.querySelector('#rows');
const selection = document.querySelector('#selection');
const count = document.createElement('span');
count.setAttribute('aria-live', 'polite');

function view(state) {
  selection.textContent = state.selected?.name ?? 'None';
  if (state.phase === 'loading') {
    count.textContent = '';
    rows.replaceChildren(Object.assign(document.createElement('p'), { className: 'status', textContent: 'Loading projects…' }));
  } else if (state.phase === 'error') {
    count.textContent = '';
    showProblem(rows, () => list.refresh());
  } else if (state.rows.length === 0) {
    count.textContent = '0 projects';
    const title = statuses.find(([key]) => key === state.status)[1].toLowerCase();
    rows.replaceChildren(Object.assign(document.createElement('p'), { className: 'empty', textContent: `No ${title} projects.` }));
  } else {
    count.textContent = `${state.rows.length} ${state.rows.length === 1 ? 'project' : 'projects'}`;
    renderRows(rows, state.rows, state.selected?.id, project => list.select(project));
  }
}

const list = createProjectList({ load: projects, view });
toolbar.className = 'filter';
toolbar.append(selectField({ label: 'Status', options: statuses, value: list.state.status, onChange: status => list.filter(status) }), count);
list.refresh();
