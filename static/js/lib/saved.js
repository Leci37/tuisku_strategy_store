// What the browser remembers between visits. Storage can be off (private mode, blocked site data):
// every read falls back and every write is best effort, so the shop works the same without it.
export function read(key, fallback = null) {
  try {
    const v = localStorage.getItem(key);
    return v == null ? fallback : v;
  } catch (e) {
    return fallback;
  }
}

export function write(key, value) {
  try {
    if (value == null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch (e) { /* storage unavailable: nothing to keep */ }
}

export function readJSON(key, fallback) {
  try {
    const v = JSON.parse(read(key, 'null'));
    return v == null ? fallback : v;
  } catch (e) {
    return fallback;
  }
}

export const writeJSON = (key, value) => write(key, value == null ? null : JSON.stringify(value));
