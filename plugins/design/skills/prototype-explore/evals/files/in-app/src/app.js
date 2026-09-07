document.querySelector('#detail-toggle').addEventListener('click', event => {
  const details = document.querySelector('#details');
  details.hidden = !details.hidden;
  event.currentTarget.setAttribute('aria-expanded', String(!details.hidden));
});
document.querySelector('#sort').addEventListener('change', event => {
  const records = document.querySelector('#records');
  const direction = event.target.value === 'oldest' ? 1 : -1;
  [...records.children].sort((a, b) => direction * (Number(a.dataset.order) - Number(b.dataset.order)))
    .forEach(record => records.append(record));
});
const tabs = [...document.querySelectorAll('[role="tab"]')];
function activateTab(tab) {
  tabs.forEach(item => {
    const active = item === tab;
    item.setAttribute('aria-selected', String(active));
    item.tabIndex = active ? 0 : -1;
    document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
  });
}
tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => activateTab(tab));
  tab.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const next = tabs[(index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
    activateTab(next); next.focus();
  });
});
