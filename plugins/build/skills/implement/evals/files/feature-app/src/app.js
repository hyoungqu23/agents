import { projects } from './api.js';
import { renderRows } from './ui.js';

const rows = document.querySelector('#rows');
const selection = document.querySelector('#selection');
let selected = null;
let visible = await projects();
function render() {
  renderRows(rows, visible, selected?.id, project => {
    selected = project;
    selection.textContent = project.name;
    render();
  });
}
render();
