// A small DOM stand-in for Node behavior tests. This does not verify browser layout.
export class Element {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.attributes = new Map();
    this.listeners = new Map();
    this.dataset = {};
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  set textContent(value) { this.replaceChildren(String(value)); }
  get textContent() {
    return this.children.map(child => typeof child === 'string' ? child : child.textContent).join('');
  }
  setAttribute(key, value) { this.attributes.set(key, value); }
  getAttribute(key) { return this.attributes.get(key); }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  fire(type) { this.listeners.get(type)?.(); }
  add(option) { this.append(option); }
}

export function createDocument() {
  const elements = new Map(['toolbar', 'rows', 'selection'].map(id => [id, new Element('div')]));
  return {
    querySelector: selector => elements.get(selector.slice(1)),
    createElement: tagName => new Element(tagName),
    createTextNode: text => text
  };
}

export class Option extends Element {
  constructor(text, value) {
    super('option');
    this.textContent = text;
    this.value = value;
  }
}
