// Minimal DOM simulation for Node behavior tests, not browser or layout evidence.
class Element {
  constructor(tagName) {
    this.tagName = tagName;
    this.childNodes = [];
    this.attributes = new Map();
    this.listeners = new Map();
    this.dataset = {};
  }

  get children() { return this.childNodes.filter(node => node instanceof Element); }
  get textContent() {
    return this.childNodes.map(node => typeof node === 'string' ? node : node.textContent).join('');
  }
  set textContent(value) { this.childNodes = [String(value)]; }
  append(...nodes) { this.childNodes.push(...nodes); }
  replaceChildren(...nodes) { this.childNodes = [...nodes]; }
  add(option) { this.append(option); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) ?? [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }
  dispatch(type) {
    for (const listener of this.listeners.get(type) ?? []) listener({ target: this });
  }
  click() { this.dispatch('click'); }
}

export function simulatedDocument() {
  const elements = Object.fromEntries(['toolbar', 'rows', 'selection'].map(id => [id, new Element('div')]));
  elements.selection.textContent = 'None';
  return {
    elements,
    document: {
      createElement: tagName => new Element(tagName),
      createTextNode: text => String(text),
      querySelector: selector => elements[selector.slice(1)] ?? null
    },
    Option: class extends Element {
      constructor(text, value) {
        super('option');
        this.textContent = text;
        this.value = value;
      }
    }
  };
}
