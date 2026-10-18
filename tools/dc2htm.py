# -*- coding: utf-8 -*-
"""Una plantilla .dc.html del diseño (x-dc) hecha vistas de Preact + htm, a máquina.

Es lo que hizo static/js/views/ a partir de docs/design/: el marcado y los estilos en línea quedan como en
el diseño, y sólo cambia la forma de escribir lo que es dinámico:

  {{ ruta }}            -> ${v.ruta} (o la variable del sc-for)
  <sc-if value>         -> ${cond ? html`...` : null}
  <sc-for list as>      -> ${(lista || []).map((as, $index) => html`...`)}
  style-hover/focus     -> una clase CSS con las declaraciones en !important (como hace el runtime del diseño)
  onChange de un input  -> onInput (el onChange de React salta con cada tecla; el de Preact es el del DOM)

Los espacios siguen al runtime: un texto sólo de espacios que lleva un espacio se pinta como un espacio, así
que donde puede notarse (entre hermanos en línea fuera de un flex o un grid) se escribe ${' '}.

    python tools/dc2htm.py PLANTILLA.dc.html CARPETA [PREFIJO]

Sin más argumentos, la plantilla se parte como las vistas de la tienda (SPLITS). tools/design_update.py lo
usa para aplicar una exportación nueva del diseño (docs/design/README.md).
"""
import json
import re
import sys
from pathlib import Path

VOID = {"img", "input", "br", "hr", "meta", "link", "source", "path", "circle", "rect", "line", "polyline", "polygon",
        "stop", "use"}
INLINE = {"span", "a", "i", "b", "strong", "em", "img", "button", "input", "label", "kbd", "small", "code", "svg", "select",
          "textarea", "u", "sub", "sup", "sc-if", "sc-for", "dc-import"}
EVENT_MAP = {"onchange": "onInput", "onclick": "onClick", "oninput": "onInput", "onkeydown": "onKeyDown",
             "onkeyup": "onKeyUp", "onblur": "onBlur", "onfocus": "onFocus", "onmouseenter": "onMouseEnter",
             "onmouseleave": "onMouseLeave", "onpointerdown": "onPointerDown", "onpointerup": "onPointerUp",
             "onpointermove": "onPointerMove", "onpointerleave": "onPointerLeave", "onsubmit": "onSubmit",
             "onmousedown": "onMouseDown"}

# Cómo se parte cada plantilla en módulos de static/js/views: cada elemento de primer nivel de la plantilla
# (un sc-if por su condición, lo demás por su etiqueta) va al módulo que lo nombra; el módulo raíz los
# llama en orden. «footer» lo dibuja la carcasa del núcleo: se genera, pero la tienda no lo usa.
SPLITS = {
    "Storefront v7.dc.html": {
        "prefix": "sf", "views": "static/js/views",
        "modules": {"header": ["header", "anyMenu"], "lite": ["isLite"], "pro": ["isPro"], "thanks": ["isThanks"],
                    "mine": ["isMine"], "detail": ["isDetail"], "footer": ["footer"],
                    "dialogs": ["freeOpen", "tourOpen", "instOpen", "cmpHas", "cmpFloat", "cmpOpen", "packOpen"],
                    "phonebar": ["isPhone"]},
        "fn": {"header": "Header", "lite": "Lite", "pro": "Pro", "thanks": "Thanks", "mine": "Mine", "detail": "Detail",
               "footer": "Footer", "dialogs": "Dialogs", "phonebar": "PhoneBar"},
        "root_module": "storefront", "root_fn": "Storefront", "lib": "../lib",
    },
    "Strategy Tree.dc.html": {
        "prefix": "tr", "views": "static/js/views/tree",
        "modules": {"tree_header": ["standalone"], "tree_main": ["main"], "tree_tip": ["tipOn"]},
        "fn": {"tree_header": "TreeHeader", "tree_main": "TreeMain", "tree_tip": "TreeTip"},
        "root_module": "tree_root", "root_fn": "TreeRoot", "lib": "../../lib",
    },
}


class UnknownElement(ValueError):
    """La plantilla trae un elemento de primer nivel que SPLITS no reparte: hay que decir a qué módulo va."""


# ---------------------------------------------------------------- leer la plantilla
class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, attrs or [], [], parent


class Text:
    def __init__(self, text, parent):
        self.text, self.parent = text, parent


ATTR_RE = re.compile(r'\s*([^\s=/>"]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+)))?')


def parse(src):
    root = Node("#root")
    cur = root
    i = 0
    while i < len(src):
        if src.startswith("<!--", i):
            i = src.index("-->", i) + 3
            continue
        if src[i] == "<" and i + 1 < len(src) and src[i + 1] == "/":
            j = src.index(">", i)
            tag = src[i + 2:j].strip()
            if tag.lower() in VOID and cur.tag != tag:
                i = j + 1                     # el cierre explícito de una etiqueta vacía (<path></path>)
                continue
            while cur.tag != tag:
                if cur.parent is None:
                    raise ValueError(f"</{tag}> sin abrir en {i}")
                cur = cur.parent
            cur = cur.parent
            i = j + 1
            continue
        if src[i] == "<" and i + 1 < len(src) and re.match(r"[A-Za-z]", src[i + 1]):
            m = re.match(r"<([A-Za-z][\w:-]*)", src[i:])
            tag = m.group(1)
            j = i + m.end()
            attrs = []
            while True:
                while j < len(src) and src[j].isspace():
                    j += 1
                if src[j] == ">":
                    selfclose = False
                    j += 1
                    break
                if src.startswith("/>", j):
                    selfclose = True
                    j += 2
                    break
                am = ATTR_RE.match(src, j)
                name = am.group(1)
                val = next((g for g in am.groups()[1:] if g is not None), None)
                attrs.append((name, val))
                j = am.end()
            node = Node(tag, attrs, cur)
            cur.children.append(node)
            if tag in ("style", "script"):
                end = src.index(f"</{tag}>", j)
                node.children.append(Text(src[j:end], node))
                i = end + len(tag) + 3
                continue
            if not selfclose and tag.lower() not in VOID:
                cur = node
            i = j
            continue
        j = src.find("<", i + 1) if src[i] == "<" else src.find("<", i)
        if j == -1:
            j = len(src)
        cur.children.append(Text(src[i:j], cur))
        i = j
    return root


# ---------------------------------------------------------------- expresiones
IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def expr_js(expr, scope):
    """Lo de dentro de un {{ ... }}, en JS."""
    e = expr.strip()
    if e.startswith("(") and e.endswith(")"):
        return "(" + expr_js(e[1:-1], scope) + ")"
    for op in ("===", "!==", "==", "!="):
        depth = 0
        for k, c in enumerate(e):
            if c in "([":
                depth += 1
            elif c in ")]":
                depth -= 1
            elif depth == 0 and e.startswith(op, k) and (k == 0 or e[k - 1] not in "=!"):
                if op in ("==", "!=") and e.startswith(op + "=", k):
                    continue
                return expr_js(e[:k], scope) + " " + op + " " + expr_js(e[k + len(op):], scope)
    if e.startswith("!"):
        return "!" + expr_js(e[1:], scope)
    if e in ("true", "false", "null", "undefined") or re.fullmatch(r"-?\d+(\.\d+)?", e):
        return e
    if len(e) >= 2 and e[0] in "\"'" and e[-1] == e[0]:
        return json.dumps(e[1:-1])
    head = IDENT.match(e).group(0)
    rest = e[len(head):]
    rest = re.sub(r"\.(\d+)", r"[\1]", rest)
    # el encadenado opcional deja callada una ruta que no existe, como resolvePath en el runtime del diseño
    rest = rest.replace(".", "?.").replace("[", "?.[")
    if head == "$index":
        return "$index" + rest
    base = head if head in scope else "v." + head
    return base + rest


# ---------------------------------------------------------------- escribir las vistas
class Gen:
    def __init__(self, prefix):
        self.prefix = prefix
        self.pseudo = {}       # (pseudo, css) -> clase
        self.uses_s = False
        self.uses_T = False

    def pseudo_class(self, pseudo, css):
        k = (pseudo, css)
        if k not in self.pseudo:
            self.pseudo[k] = f"{self.prefix}-{pseudo}{len(self.pseudo)}"
        return self.pseudo[k]

    def css(self):
        out = []
        for (pseudo, css), cls in self.pseudo.items():
            decls = [d.strip() for d in css.split(";") if d.strip()]
            body = ";".join(d if "!important" in d else d + " !important" for d in decls)
            out.append(f".{cls}:{pseudo}{{{body}}}")
        return "\n".join(out) + "\n"


def esc_text(t):
    return t.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def attr_value_js(val, scope, g):
    """Da (tipo, código): ('static', texto) | ('expr', js) | ('mixed', 'a${...}b')."""
    whole = re.fullmatch(r"\s*\{\{([^{}]+?)\}\}\s*", val)
    if whole:
        return "expr", expr_js(whole.group(1), scope)
    if "{{" in val:
        parts = re.split(r"\{\{([^{}]+?)\}\}", val)
        out = []
        for k, p in enumerate(parts):
            if k % 2:
                g.uses_s = True
                out.append("${s(" + expr_js(p, scope) + ")}")
            else:
                out.append(esc_text(p))
        return "mixed", "".join(out)
    return "static", val


def parent_display_ignores_ws(node):
    if not isinstance(node, Node):
        return True
    if node.tag in ("#root", "sc-if", "sc-for"):
        return parent_display_ignores_ws(node.parent) if node.tag != "#root" else True
    style = dict(node.attrs).get("style") or ""
    return (bool(re.search(r"display\s*:\s*(inline-)?(flex|grid)", style))
            or node.tag in ("table", "thead", "tbody", "tr", "ol", "ul", "select"))


def is_inlineish(n):
    if isinstance(n, Text):
        return bool(n.text.strip())
    if n is None:
        return False
    style = dict(n.attrs).get("style") or ""
    if re.search(r"display\s*:\s*(block|flex|grid)", style):
        return False
    return n.tag in INLINE


def in_pre(node):
    while isinstance(node, Node):
        style = dict(node.attrs).get("style") or ""
        if "white-space:pre" in style.replace(" ", ""):
            return True
        node = node.parent
    return False


def gen_children(node, scope, g, ind):
    kids = node.children
    out = []
    for idx, c in enumerate(kids):
        prev = kids[idx - 1] if idx > 0 else None
        nxt = kids[idx + 1] if idx + 1 < len(kids) else None
        if isinstance(c, Text):
            out.append(gen_text(c, prev, nxt, scope, g, ind))
        else:
            out.append(gen_node(c, scope, g, ind))
    return "".join(out)


def gen_text(t, prev, nxt, scope, g, ind):
    txt = t.text
    if in_pre(t.parent):
        m = re.fullmatch(r"\{\{([^{}]+?)\}\}", txt)
        if m:
            return "${" + expr_js(m.group(1), scope) + "}"
        if "{{" in txt:
            raise ValueError("un valor dentro de white-space:pre: no se sabe convertir")
        return "${" + json.dumps(txt) + "}" if txt else ""
    has_binding = "{{" in txt
    if not txt.strip() and not has_binding:
        if " " not in txt:
            return ""                         # el runtime lo quita
        if parent_display_ignores_ws(t.parent):
            return "\n" + ind if "\n" in txt else ""
        if is_inlineish(prev) or is_inlineish(nxt):
            return "${' '}" + ("\n" + ind if "\n" in txt else "")
        return "\n" + ind if "\n" in txt else ""
    flexy = parent_display_ignores_ws(t.parent)
    # el único hijo, y es un solo valor: no hace falta el span
    sole = (len(t.parent.children) == 1 and re.fullmatch(r"\{\{([^{}]+?)\}\}", txt.strip())
            and (txt == txt.strip() or flexy))
    lead = re.match(r"^\s*", txt).group(0)
    trail = re.search(r"\s*$", txt).group(0) if txt.strip() else ""
    core = txt[len(lead):len(txt) - len(trail)] if trail else txt[len(lead):]
    if sole:
        return "${" + expr_js(re.fullmatch(r"\{\{([^{}]+?)\}\}", core).group(1), scope) + "}"

    def ws_edge(w, neighbour):
        if not w:
            return ""
        if "\n" not in w:
            return w                          # htm lo conserva
        if flexy or neighbour is None:
            return ""                         # se pierde de todos modos
        return "${' '}"

    parts = re.split(r"\{\{([^{}]+?)\}\}", core)
    body = []
    for k, p in enumerate(parts):
        if k % 2:
            g.uses_T = True
            body.append("${T(" + expr_js(p, scope) + ")}")
        else:
            p = re.sub(r"\s*\n\s*", " ", p)  # un salto de línea dentro del texto se pinta como un espacio
            body.append(esc_text(p))
    lead_out = ws_edge(lead, prev) if lead else ""
    return lead_out + "".join(body) + ws_edge(trail, nxt)


def gen_node(n, scope, g, ind):
    tag = n.tag
    attrs = dict(n.attrs)
    if tag == "sc-if":
        cond = attr_value_js(attrs.get("value", ""), scope, g)[1]
        inner = gen_children(n, scope, g, ind + "  ")
        return "${" + cond + " ? html`" + inner + "` : null}"
    if tag == "sc-for":
        lst = attr_value_js(attrs.get("list", ""), scope, g)[1]
        as_ = attrs.get("as") or "item"
        inner = gen_children(n, scope | {as_}, g, ind + "  ")
        return "${(" + lst + " || []).map((" + as_ + ", $index) => html`" + inner + "`)}"
    if tag == "dc-import":
        props = []
        for k, val in n.attrs:
            if k in ("name",) or k.startswith("hint-"):
                continue
            key = re.sub(r"-([a-z])", lambda m: m.group(1).upper(), k)
            kind, code = attr_value_js(val or "", scope, g)
            props.append(f"{key}=${{{code}}}" if kind == "expr" else f'{key}="{code}"')
        return "<div class=\"sc-host\"><${StrategyTree} " + " ".join(props) + " /></div>"
    parts = [tag]
    classes = []
    for k, val in n.attrs:
        if k.startswith("hint-") or k == "sc-name":
            continue
        if k.startswith("style-"):
            classes.append(g.pseudo_class(k[6:], val or ""))
            continue
        if k == "class":
            classes.insert(0, val)
            continue
        key = k
        if k.lower().startswith("on"):
            key = EVENT_MAP.get(k.lower(), k)
        if val is None:
            parts.append(key)
            continue
        if key == "translate":
            # Preact lo pone como propiedad, donde "no" sería true
            parts.append("translate=${" + ("false" if val == "no" else "true") + "}")
            continue
        kind, code = attr_value_js(val, scope, g)
        if kind == "expr":
            if key in ("value", "checked"):
                code = f"{code} ?? {'false' if key == 'checked' else repr('')}"
            parts.append(f"{key}=${{{code}}}")
        elif kind == "mixed":
            parts.append(f'{key}="{code}"')
        else:
            parts.append(f'{key}="{esc_text(val)}"')
    if classes:
        cls = " ".join(c for c in classes if c)
        if "{{" in cls:
            kind, code = attr_value_js(cls, scope, g)
            parts.insert(1, f'class="{code}"' if kind == "mixed" else f"class=${{{code}}}")
        else:
            parts.insert(1, f'class="{cls}"')
    open_ = "<" + " ".join(parts)
    if tag.lower() in VOID and not n.children:
        return open_ + " />"
    inner = gen_children(n, scope, g, ind + "  ")
    return open_ + ">" + inner + "</" + tag + ">"


def find_xdc(src):
    a = re.search(r"<x-dc(?:\s[^>]*)?>", src)
    b = src.rindex("</x-dc>")
    return src[a.end():b]


# La primera línea, la misma que llevan las vistas: así, en una mezcla a tres, la cabecera no choca.
HEAD = """// Markup and styles ported one to one from docs/design/{src} (the v7 reference design).
import {{ html }} from '{lib}/html.js';
{imports}
"""


def convert(src_path, outdir, prefix=None, spec=None, name=None) -> dict:
    """Escribe en ``outdir`` un .js por módulo, ``<prefijo>.hover.css`` (las clases de style-hover y
    style-focus) y ``<prefijo>.helmet.txt``. ``name`` es el nombre de la plantilla con el que se busca su
    reparto en SPLITS y el que lleva la cabecera (por defecto, el del fichero). Da {módulo: fichero}."""
    src_path = Path(src_path)
    name = name or src_path.name
    spec = spec or SPLITS[name]
    prefix = prefix or spec["prefix"]
    src = src_path.read_text(encoding="utf-8")
    root = parse(find_xdc(src))
    helmet = [c for c in root.children if isinstance(c, Node) and c.tag == "helmet"]
    main_div = [c for c in root.children if isinstance(c, Node) and c.tag != "helmet"][0]
    g = Gen(prefix)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    elem_nodes = [c for c in main_div.children if isinstance(c, Node)]
    assign = {nm: mod for mod, names in spec["modules"].items() for nm in names}

    def name_of(n):
        """Un sc-if, por su condición; lo demás, por su etiqueta."""
        if n.tag == "sc-if":
            return dict(n.attrs)["value"].strip("{} ").strip()
        return n.tag

    groups, order = {}, []
    for n in elem_nodes:
        nm = name_of(n)
        mod = assign.get(nm)
        if mod is None:
            raise UnknownElement(f"{name}: el elemento de primer nivel {nm!r} no va a ningún módulo "
                                 "(añádelo a SPLITS en tools/dc2htm.py)")
        if mod not in groups:
            groups[mod] = []
            order.append(mod)
        groups[mod].append(n)
    written = {}
    for mod in order:
        g.uses_s = g.uses_T = False
        joined = "".join("\n  " + gen_node(n, set(), g, "  ") for n in groups[mod])
        helpers = [h for h, used in (("s", g.uses_s), ("T", g.uses_T)) if used]
        imports = []
        if helpers:
            imports.append("import { " + ", ".join(helpers) + " } from '" + spec["lib"] + "/tpl.js';")
        if "${StrategyTree}" in joined:
            imports.append("import { StrategyTree } from '../tree.js';")
        code = HEAD.format(src=name, lib=spec["lib"], imports="\n".join(imports))
        code += f"\nexport default function {spec['fn'][mod]}(v) {{\n  return html`{joined}\n`;\n}}\n"
        (out / f"{mod}.js").write_text(code, encoding="utf-8")
        written[mod] = out / f"{mod}.js"
    # la raíz: el div de fuera, con los módulos en orden
    attrs_code = gen_node(Node(main_div.tag, main_div.attrs, None), set(), g, "")
    open_tag = attrs_code[: attrs_code.rindex("></")] + ">"
    imports = "\n".join(f"import {spec['fn'][m]} from './{m}.js';" for m in order)
    calls = "".join(f"\n    ${{{spec['fn'][m]}(v)}}" for m in order)
    root_code = HEAD.format(src=name, lib=spec["lib"], imports=imports)
    root_code += f"\nexport default function {spec['root_fn']}(v) {{\n  return html`{open_tag}{calls}\n  </{main_div.tag}>`;\n}}\n"
    (out / f"{spec['root_module']}.js").write_text(root_code, encoding="utf-8")
    written[spec["root_module"]] = out / f"{spec['root_module']}.js"
    (out / f"{prefix}.hover.css").write_text(g.css(), encoding="utf-8")
    hl = []
    for h_ in helmet:
        for c in h_.children:
            if isinstance(c, Node) and c.tag == "style":
                hl.append(c.children[0].text)
            elif isinstance(c, Node):
                hl.append("<" + c.tag + " " + " ".join(f'{k}="{v}"' for k, v in c.attrs) + ">")
    (out / f"{prefix}.helmet.txt").write_text("\n".join(hl), encoding="utf-8")
    return written


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    src, outdir = argv[0], argv[1]
    written = convert(src, outdir, argv[2] if len(argv) > 2 else None)
    print("módulos:", ", ".join(written))


if __name__ == "__main__":
    main(sys.argv[1:])
