/* Demo-only A2UI v1.0 renderer shared by samples 1 and 2, restricted to a custom catalog.
 * For production, integrate an official compatible renderer and catalog.
 * Never treat model-provided values as HTML.
 */
export function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
}
// Small safe Markdown subset for demonstration. No HTML parsing.
export function renderMarkdown(node, text) {
  node.replaceChildren();
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let pos = 0;
  for (const match of text.matchAll(re)) {
    node.append(document.createTextNode(text.slice(pos, match.index)));
    const v = match[0];
    node.append(element(v.startsWith('**') ? 'strong' : 'code', v.slice(v.startsWith('**') ? 2 : 1, v.startsWith('**') ? -2 : -1)));
    pos = match.index + v.length;
  }
  node.append(document.createTextNode(text.slice(pos)));
}
const UNSAFE_KEYS = new Set(['__proto__', 'constructor', 'prototype']);
const unescapePointerToken = token => token.replace(/~1/g, '/').replace(/~0/g, '~');
export function atPath(root, pointer) {
  if (!pointer || pointer === '/') return root;
  if (!pointer.startsWith('/')) return undefined;
  return pointer.slice(1).split('/').map(unescapePointerToken).reduce((obj, key) => obj == null ? undefined : obj[key], root);
}
// A data binding is {path: '/json/pointer'}.
export const bound = (surface, binding) => atPath(surface.data, binding?.path);

export function renderTable(c, surface) {
  const table = element('table');
  const head = element('thead'), headRow = element('tr');
  const columns = (c.columns || []).slice(0, 20);
  for (const col of columns) headRow.append(element('th', col.label));
  head.append(headRow); table.append(head);
  const body = element('tbody');
  const rows = bound(surface, c.rows) || [];
  for (const row of (Array.isArray(rows) ? rows : []).slice(0, 500)) {
    const tr = element('tr');
    for (const col of columns) tr.append(element('td', row[col.key] ?? ''));
    body.append(tr);
  }
  table.append(body);
  return table;
}

export class A2UIRenderer {
  /** catalog: catalogId string. components: {Name: (component, surface) => Node} beyond the built-in Column and Text. */
  constructor(host, {catalog, components}) {
    this.host = host; this.catalog = catalog; this.components = components;
    this.surfaces = new Map(); this.failed = new Set();
  }
  // Applies one message; a failing surface is discarded whole and its later messages skipped.
  safeProcess(msg) {
    const type = Object.keys(msg).find(k => k !== 'version');
    const id = msg[type]?.surfaceId;
    if (this.failed.has(id)) return;
    try { this.process(msg); }
    catch (err) {
      this.failed.add(id);
      this.surfaces.get(id)?.host.remove();
      this.surfaces.delete(id);
      throw err;
    }
  }
  process(msg) {
    if (msg.version !== 'v1.0') throw Error('Unsupported protocol version');
    const types = ['createSurface', 'updateComponents', 'updateDataModel', 'deleteSurface'];
    const matching = types.filter(x => Object.hasOwn(msg, x));
    if (matching.length !== 1) throw Error('Invalid envelope');
    const type = matching[0], p = msg[type];
    if (!p || typeof p.surfaceId !== 'string') throw Error('Missing surfaceId');
    if (type === 'createSurface') {
      if (p.catalogId !== this.catalog) throw Error('Unknown catalog');
      if (this.surfaces.has(p.surfaceId)) throw Error('Duplicate surface');
      const host = element('div', null, 'surface');
      this.host.append(host);
      this.surfaces.set(p.surfaceId, {host, components: new Map(), data: {}});
      return;
    }
    const surface = this.surfaces.get(p.surfaceId);
    if (!surface) throw Error('Unknown surface');
    if (type === 'deleteSurface') { surface.host.remove(); this.surfaces.delete(p.surfaceId); return; }
    if (type === 'updateComponents') {
      for (const c of p.components) {
        if (!['Column', 'Text'].includes(c.component) && !Object.hasOwn(this.components, c.component)) throw Error('Unsupported component');
        surface.components.set(c.id, c);
      }
    } else if (type === 'updateDataModel') {
      if (!p.path || p.path === '/') surface.data = p.value;
      else {
        const tokens = p.path.slice(1).split('/').map(unescapePointerToken);
        if (tokens.some(k => UNSAFE_KEYS.has(k))) throw Error('Unsafe data path');
        if (surface.data === null || typeof surface.data !== 'object') surface.data = {};
        let target = surface.data;
        for (const key of tokens.slice(0, -1)) {
          if (target[key] === null || typeof target[key] !== 'object') target[key] = {};
          target = target[key];
        }
        target[tokens.at(-1)] = p.value;
      }
    }
    this.render(surface);
  }
  render(surface) {
    const visit = (id, depth = 0) => {
      if (depth > 24) throw Error('Component nesting limit');
      const c = surface.components.get(id);
      if (!c) return element('div', 'Loading…');
      if (c.component === 'Column') {
        const box = element('div');
        for (const child of c.children || []) box.append(visit(child, depth + 1));
        return box;
      }
      if (c.component === 'Text') return element('h3', c.text);
      if (Object.hasOwn(this.components, c.component)) return this.components[c.component](c, surface);
      throw Error('Invalid catalog component');
    };
    surface.host.replaceChildren(visit('root'));
  }
}

export async function consumeSSE(response, onEvent) {
  if (!response.ok || !response.body) throw Error(`HTTP ${response.status}`);
  const reader = response.body.getReader(); const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, {stream: true}).replace(/\r\n/g, '\n');
    let idx;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, idx); buffer = buffer.slice(idx + 2);
      let event = 'message', data = '';
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        if (line.startsWith('data:')) data += line.slice(5).trimStart();
      }
      if (data) onEvent(event, JSON.parse(data));
    }
  }
}
