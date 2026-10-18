// htm bound to Preact: the views are tagged templates, no build step and no eval (CSP-safe).
import { h } from '../../vendor/preact.module.js';
import htm from '../../vendor/htm.module.js';

export const html = htm.bind(h);
