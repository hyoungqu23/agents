export function selectField({ label, options, value, onChange }) {
  const wrapper = document.createElement('label');
  wrapper.append(document.createTextNode(`${label} `));
  const select = document.createElement('select');
  for (const [key, title] of options) select.add(new Option(title, key));
  select.value = value;
  select.addEventListener('change', () => onChange(select.value));
  wrapper.append(select);
  return wrapper;
}

export function renderRows(container, rows, selectedId, onSelect) {
  container.replaceChildren();
  for (const row of rows) {
    const button = document.createElement('button');
    button.className = 'project'; button.dataset.projectId = row.id;
    button.setAttribute('aria-pressed', String(selectedId === row.id));
    button.textContent = `${row.name} — ${row.status}`;
    button.addEventListener('click', () => onSelect(row));
    container.append(button);
  }
}

export function showProblem(container, retry) {
  const problem = document.createElement('div'); problem.className = 'problem';
  problem.setAttribute('role', 'alert'); problem.append('Could not load projects. ');
  const button = document.createElement('button'); button.textContent = 'Retry';
  button.addEventListener('click', retry); problem.append(button);
  container.replaceChildren(problem);
}
