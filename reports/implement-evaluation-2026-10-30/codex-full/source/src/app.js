import { projects } from './api.js';
import { createProjectList } from './project-list.js';
import { selectField, renderRows, showProblem } from './ui.js';

const toolbar = document.querySelector('#toolbar');
const rows = document.querySelector('#rows');
const selection = document.querySelector('#selection');
const count = document.createElement('span');
count.id = 'result-count';
count.setAttribute('role', 'status');
const list = createProjectList({ loadProjects: projects, onChange: render });

toolbar.className = 'filter';
toolbar.append(selectField({
  label: 'Status',
  options: [['all', 'All'], ['active', 'Active'], ['archived', 'Archived'], ['paused', 'Paused']],
  value: 'all',
  onChange: status => list.load(status),
}), count);

function message(text) {
  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  paragraph.setAttribute('role', 'status');
  rows.replaceChildren(paragraph);
}

function render(state) {
  selection.textContent = state.selected?.name ?? 'None';
  rows.setAttribute('aria-busy', String(state.loading));
  count.textContent = '';
  if (state.loading) {
    message('Loading projects…');
  } else if (state.error) {
    showProblem(rows, () => list.load());
  } else {
    count.textContent = `${state.projects.length} ${state.projects.length === 1 ? 'project' : 'projects'}`;
    if (state.projects.length === 0) {
      message('No projects match this status.');
    } else {
      renderRows(rows, state.projects, state.selected?.id, project => list.select(project));
    }
  }
}

list.load();
