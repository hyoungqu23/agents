import { summary } from './copy.js';

document.querySelector('#summary').textContent = summary;
try {
  const response = await fetch(new URL('./details.json', import.meta.url));
  if (!response.ok) throw new Error('Unable to load sample details');
  const data = await response.json();
  document.querySelector('#details').textContent = data.text;
} catch {
  document.querySelector('#details').textContent = 'Sample details are unavailable.';
}
document.querySelector('#toggle').addEventListener('click', event => {
  const details = document.querySelector('#details');
  details.hidden = !details.hidden;
  event.currentTarget.setAttribute('aria-expanded', String(!details.hidden));
});
