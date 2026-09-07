const keys = ['A', 'B', 'C'];
const params = new URLSearchParams(location.search);
let current = keys.includes(params.get('variant')) ? params.get('variant') : 'A';
function renderVariant() {
  document.querySelectorAll('[data-variant]').forEach(el => { el.hidden = el.dataset.variant !== current; });
  document.querySelector('#variant-label').value = current;
}
function cycle(direction) {
  current = keys[(keys.indexOf(current) + direction + keys.length) % keys.length];
  const url = new URL(location.href);
  url.searchParams.set('variant', current);
  history.pushState(null, '', url);
  renderVariant();
}
document.querySelector('#previous').addEventListener('click', () => cycle(-1));
document.querySelector('#next').addEventListener('click', () => cycle(1));
document.addEventListener('keydown', event => {
  if (event.target.closest('input,textarea,select,[contenteditable],[role="tab"],[role="slider"],[role="radio"],[role="combobox"],[role="spinbutton"]')) return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault(); cycle(event.key === 'ArrowLeft' ? -1 : 1);
  }
});
window.addEventListener('popstate', () => {
  const key = new URLSearchParams(location.search).get('variant');
  current = keys.includes(key) ? key : 'A'; renderVariant();
});
document.querySelector('#detail-toggle').addEventListener('click', event => {
  const details = document.querySelector('#details');
  details.hidden = !details.hidden;
  event.currentTarget.setAttribute('aria-expanded', String(!details.hidden));
});
renderVariant();
