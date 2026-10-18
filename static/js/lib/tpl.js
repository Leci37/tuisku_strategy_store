import { html } from './html.js';

// A value inside an attribute: null and undefined print nothing.
export const s = x => (x == null ? '' : x);

// A value inside text gets its own span, as in the reference design: in a flex row the span is
// its own item, so the row's gap falls where the design has it. Null and booleans print nothing.
export const T = x => (x == null || typeof x === 'boolean' ? null : typeof x === 'object' ? x : html`<span>${x}</span>`);
