"""Genera los flujos de las dos instancias Node-RED del producto final.

Fuente única: vacuum_controller.html, dashboard.html y sus JavaScript se incrustan tal cual
(HTML, CSS y JS) en un ui-template de FlowFuse Dashboard. main.py (127.0.0.1:8000) es todo
el backend y controla las Pi-Plates. Sin simulación.
Ejecutar después de editar cualquier HTML/JS:  python3 build_dashboards.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
PORTS = {'vacuum': 1880, 'dashboard': 1881}
SOURCES = {'vacuum': 'vacuum_controller.html', 'dashboard': 'dashboard.html'}
LINKS = {'dashboard.html': 'dashboard', 'vacuum_controller.html': 'vacuum'}
THEMES = {'vacuum': ('#292d3b', '#f6f7fb'), 'dashboard': ('#e9edf1', '#1e2731')}

def scope_css(css, root):
    """Prefija cada selector con la raíz para no alterar la interfaz de Dashboard 2."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out, i = [], 0
    while i < len(css):
        brace = css.find('{', i)
        if brace < 0:
            break
        head = css[i:brace].strip()
        depth, j = 1, brace + 1
        while depth:
            depth += {'{': 1, '}': -1}.get(css[j], 0)
            j += 1
        block = css[brace + 1:j - 1]
        if head.startswith('@media') or head.startswith('@supports'):
            out.append(f'{head}{{{scope_css(block, root)}}}')
        elif head.startswith('@'):
            out.append(f'{head}{{{block}}}')
        else:
            selectors = []
            for sel in head.split(','):
                sel = sel.strip()
                m = re.match(r'(:root|html|body)(.*)', sel)
                selectors.append(root + m.group(2) if m else f'{root} {sel}')
                if sel == '*':
                    selectors[-1] = f'{root}, {root} *'
            out.append(f'{",".join(selectors)}{{{block}}}')
        i = j
    return '\n'.join(out)


def parse(name):
    """Separa el HTML original en cuerpo, CSS y scripts (incluidos los .js locales en orden)."""
    html = re.sub(r'<!--.*?-->', '', (ROOT / name).read_text(), flags=re.S)
    css = '\n'.join(re.findall(r'<style>(.*?)</style>', html, re.S))
    body = re.search(r'<body>(.*)</body>', html, re.S).group(1)
    scripts = []

    def take(m):
        src = re.search(r'src="([^"]+)"', m.group(1))
        scripts.append((ROOT / src.group(1)).read_text() if src else m.group(2))
        return ''
    body = re.sub(r'<script([^>]*)>(.*?)</script>', take, body, flags=re.S)
    for href, target in LINKS.items():
        body = body.replace(f'href="{href}"', f'href="#" data-plasma-link="{target}"')
    return body.strip(), css, scripts


def template(root_class, body, css, scripts):
    """Vue SFC de ui-template: los scripts originales corren en mounted() con document limitado a la raíz."""
    links = json.dumps({'vacuum': [PORTS['vacuum'], '/dashboard/main'], 'dashboard': [PORTS['dashboard'], '/dashboard/main']})
    code = '\n'.join(scripts)
    return f"""<template><div class="{root_class}">{body}</div></template>
<script>
export default {{
  mounted() {{
    const root = this.$el, timers = [], listeners = [];
    this.$plasmaCleanup = () => {{ timers.forEach(t => {{ clearTimeout(t); clearInterval(t); }}); listeners.forEach(a => window.removeEventListener(...a)); }};
    const links = {links};
    root.querySelectorAll('[data-plasma-link]').forEach(a => {{
      const [port, path] = links[a.dataset.plasmaLink];
      a.href = port ? `${{location.protocol}}//${{location.hostname}}:${{port}}${{path}}` : path;
    }});
    // Los scripts originales buscan elementos con document.*; aquí solo ven esta pantalla.
    const document = new Proxy(window.document, {{
      get(target, key) {{
        if (key === 'querySelector') return s => root.querySelector(s);
        if (key === 'querySelectorAll') return s => root.querySelectorAll(s);
        if (key === 'getElementById') return id => root.querySelector('#' + CSS.escape(id));
        const value = Reflect.get(target, key);
        return typeof value === 'function' ? value.bind(target) : value;
      }}
    }});
    const setTimeout = (f, ms) => {{ const t = window.setTimeout(f, ms); timers.push(t); return t; }};
    const setInterval = (f, ms) => {{ const t = window.setInterval(f, ms); timers.push(t); return t; }};
    const addEventListener = (...a) => {{ window.addEventListener(...a); listeners.push(a); }};
{code}
  }},
  unmounted() {{ this.$plasmaCleanup?.(); }}
}}
</script>
<style>
/* Devuelve a los controles el estilo del navegador que el reset de Vuetify elimina. */
.{root_class} :where(button,input,textarea,select,h1,h2,p,ol,ul,li,details,summary,a,pre) {{ all: revert; }}
.{root_class} [hidden] {{ display: none !important; }}
{scope_css(css, '.' + root_class)}
</style>"""


def build(role):
    bg, fg = THEMES[role]
    proxy = json.loads((ROOT / 'flows.json').read_text())
    nodes = [
        {'id': 'tab', 'type': 'tab', 'label': 'Vacuum Controller' if role == 'vacuum' else 'Reactor Dashboard',
         'disabled': False, 'info': 'GUI original (HTML/CSS/JS) en ui-template. Generado por build_dashboards.py; '
                                    'editar los HTML/JS fuente y regenerar. main.py controla las Pi-Plates en 127.0.0.1:8000.'},
        {'id': 'base', 'type': 'ui-base', 'name': 'Plasma', 'path': '/dashboard', 'includeClientData': True,
         'acceptsClientConfig': ['ui-notification', 'ui-control'], 'showPathInSidebar': False, 'headerContent': 'none',
         'navigationStyle': 'none', 'titleBarStyle': 'hidden', 'showReconnectNotification': True, 'notificationDisplayTime': 1,
         'showDisconnectNotification': True},
        {'id': 'theme', 'type': 'ui-theme', 'name': 'Plasma ' + role,
         'colors': {'surface': bg, 'primary': '#739cbb', 'bgPage': bg, 'groupBg': bg, 'groupOutline': bg},
         'sizes': {'density': 'default', 'pagePadding': '0px', 'groupGap': '0px', 'groupBorderRadius': '0px', 'widgetGap': '0px'}},
    ]
    pages = [('main', ('Vacuum Controller' if role == 'vacuum' else 'Reactor Dashboard'), 'plasma-' + role, *parse(SOURCES[role]))]
    for order, (page, title, root_class, body, css, scripts) in enumerate(pages, 1):
        nodes += [
            {'id': 'page_' + page, 'type': 'ui-page', 'name': title, 'ui': 'base', 'path': '/' + page, 'icon': 'science',
             'layout': 'grid', 'theme': 'theme', 'breakpoints': [{'name': 'Default', 'px': 0, 'cols': 12}],
             'order': order, 'className': '', 'visible': True, 'disabled': False},
            {'id': 'group_' + page, 'type': 'ui-group', 'name': title, 'page': 'page_' + page, 'width': 12, 'height': 1,
             'order': 1, 'showTitle': False, 'className': '', 'visible': True, 'disabled': False, 'groupType': 'default'},
            {'id': 'template_' + page, 'type': 'ui-template', 'z': 'tab', 'group': 'group_' + page, 'page': '', 'ui': '',
             'name': title + ' (HTML/CSS/JS)', 'order': 1, 'width': 0, 'height': 0, 'head': '',
             'format': template(root_class, body, css, scripts), 'storeOutMessages': False, 'passthru': False,
             'resendOnRefresh': False, 'templateScope': 'local', 'className': '', 'x': 200, 'y': 60 * order, 'wires': [[]]},
        ]
    # Quita el relleno de la página para que el diseño original ocupe toda la pantalla.
    nodes.append({'id': 'page_style', 'type': 'ui-template', 'z': 'tab', 'group': '', 'page': '', 'ui': 'base',
                  'name': 'Pantalla completa', 'order': 0, 'width': 0, 'height': 0, 'head': '',
                  'format': f'.nrdb-ui-page,.nrdb-ui-group,.v-card,.v-card-text,.nrdb-ui-widget{{padding:0!important;margin:0!important;'
                            f'max-width:none!important;border:0!important;box-shadow:none!important}}'
                            f'.v-main{{padding:0!important}}body,.v-application{{background:{bg}!important;color:{fg}}}',
                  'storeOutMessages': False, 'passthru': False, 'resendOnRefresh': False, 'templateScope': 'site:style',
                  'className': '', 'x': 200, 'y': 220, 'wires': [[]]})
    # Proxy HTTP /api/* → main.py (flows.json).
    for n in proxy[1:]:
        n = dict(n, z='tab', y=n['y'] + 240)
        nodes.append(n)
    (ROOT / f'flows-{role}.json').write_text(json.dumps(nodes, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    for role in SOURCES:
        build(role)
