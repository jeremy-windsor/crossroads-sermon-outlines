"""Socket-free rendered checks, with explicit limits versus real Chromium.

WeasyPrint renders the actual HTML/CSS after media conditions are resolved for the
test viewport. Node executes the unchanged theme scripts against a small DOM/storage
harness. Chromium's accessibility tree and first paint remain a separate browser gate.
"""

import json
import logging
from pathlib import Path
import re
import subprocess

from bs4 import BeautifulSoup
import fitz
import pytest
import tinycss2
from weasyprint import CSS, HTML

import render

logging.getLogger('weasyprint').setLevel(logging.ERROR)


def resolved_css(width, theme, medium='screen'):
    """WeasyPrint supports media types; resolve the site's media features explicitly."""
    def include(condition):
        if condition.startswith('print') and medium != 'print':
            return False
        if condition.startswith('screen') and medium != 'screen':
            return False
        if 'prefers-color-scheme: dark' in condition and theme != 'dark':
            return False
        match = re.search(r'max-width:\s*([\d.]+)rem', condition)
        if match and width > float(match[1]) * 16:
            return False
        if 'prefers-reduced-motion' in condition:
            return False
        return True

    def select(rules):
        output = []
        for rule in rules:
            if rule.type == 'at-rule' and rule.lower_at_keyword == 'media':
                if include(tinycss2.serialize(rule.prelude).strip()):
                    output.extend(select(tinycss2.parse_rule_list(rule.content)))
            else:
                output.append(rule.serialize())
        return output

    source = (render.ROOT / 'site/assets/site.css').read_text()
    return '\n'.join(select(tinycss2.parse_stylesheet(source)))


def rendered(path, width, theme, medium='screen', target=None, font_scale=1):
    soup = BeautifulSoup((render.ROOT / path).read_text(), 'html.parser')
    for node in soup.select('link[rel="stylesheet"], script, iframe'):
        node.decompose()
    css = resolved_css(width, theme, medium)
    css += f'\nhtml {{font-size: {font_scale * 100}%;}}'
    if target:
        soup.find(id=target)['data-render-target'] = ''
        css = css.replace(':target', '[data-render-target]')
    css += f'\n@page {{size: {width}px 6000px; margin: 0;}}'
    return HTML(string=str(soup), media_type=medium).render(stylesheets=[CSS(string=css)])


def boxes(document, selector):
    return [box for page in document.pages for box in page._page_box.descendants() if box.element is not None and selector(box)]


def has_class(box, name):
    return name in box.element.get('class', '').split()


def rgb(value):
    return tuple(round(c * 255) for c in value.coordinates[:3])


@pytest.mark.parametrize('name,path', [('home', 'index.html'), ('archive', 'archive/2026.html'), ('sermon', 'sermons/2026-08-16-inside-out.html')])
@pytest.mark.parametrize('width', [1280, 375])
@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_equivalent_rendered_surfaces(name, path, width, theme):
    doc = rendered(path, width, theme)
    body = boxes(doc, lambda b: b.element_tag == 'body')[0]
    assert rgb(body.style['background_color']) == ((20, 29, 25) if theme == 'dark' else (250, 250, 246))
    assert body.width <= width
    assert not boxes(doc, lambda b: has_class(b, 'theme-toggle'))  # no-JS fallback
    # Actual layout boxes, rather than just stylesheet-string assertions.
    for box in boxes(doc, lambda b: b.element_tag in ('main', 'header', 'table') or has_class(b, 'sermon-card')):
        assert box.width <= width + 1
    if name == 'sermon':
        tables = boxes(doc, lambda b: b.element_tag == 'table')
        assert any(b.__class__.__name__ == ('BlockBox' if width == 375 else 'TableBox') for b in tables)
        assert boxes(doc, lambda b: b.element.get('id') == 'ledger-SCR-003')
    evidence = render.ROOT / '.test-artifacts/rendered'
    evidence.mkdir(parents=True, exist_ok=True)
    pdf = fitz.open(stream=doc.write_pdf(), filetype='pdf')
    height = 812 if width == 375 else 900
    pdf[0].get_pixmap(matrix=fitz.Matrix(4/3, 4/3), clip=fitz.Rect(0, 0, width*.75, height*.75)).save(str(evidence / f'{name}-{width}-{theme}.png'))
    pdf.close()


def test_equivalent_target_and_print_layout():
    path = 'sermons/2026-08-24-start-with-me.html'
    doc = rendered(path, 375, 'dark', target='ledger-SCR-003')
    target = boxes(doc, lambda b: b.element.get('id') == 'ledger-SCR-003')[0]
    assert rgb(target.style['background_color']) == (66, 61, 37)
    assert target.style['outline_style'] == 'solid'
    printed = rendered(path, 1280, 'dark', 'print')
    body = boxes(printed, lambda b: b.element_tag == 'body')[0]
    assert rgb(body.style['background_color']) == (255, 255, 255)
    assert body.style['font_size'] == 16  # 12pt
    assert not boxes(printed, lambda b: has_class(b, 'video-block'))
    assert boxes(printed, lambda b: b.element_tag == 'thead')
    assert all(b.style['break_inside'] == 'avoid' for b in boxes(printed, lambda b: has_class(b, 'outline-node')))


@pytest.mark.parametrize('width', [375, 414])
@pytest.mark.parametrize('path', ['sermons/2026-08-24-start-with-me.html', 'sermons/2026-07-06-worship-in-the-waiting.html'])
def test_equivalent_large_text_reflows(width, path):
    doc = rendered(path, width, 'dark', font_scale=2)
    overflow = []
    for box in boxes(doc, lambda b: bool(getattr(b, 'text', '').strip())):
        if box.position_x >= 0 and box.position_x + box.width > width:
            overflow.append({'tag': box.element_tag, 'class': box.element.get('class'),
                             'text': box.text, 'right': round(box.position_x + box.width, 2)})
    assert not overflow, overflow


def test_actual_theme_scripts_in_javascript_engine():
    harness = r'''
const vm = require('node:vm');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const [early, control] = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const dark of [false, true]) {
  for (const saved of [null, 'light', 'dark', 'invalid']) {
    for (const blocked of [false, true]) {
      const root = {dataset: {}};
      const listeners = {};
      const button = () => ({hidden:true, attrs:{}, addEventListener(k, fn){this[k] = fn;}, setAttribute(k,v){this.attrs[k]=v;}, focus(){this.focused=true;}});
      const toggle = button(), reset = button();
      let value = saved;
      const storage = {getItem(){if(blocked)throw Error();return value;},setItem(k,v){if(blocked)throw Error();value=v;},removeItem(){if(blocked)throw Error();value=null;}};
      const system = {matches:dark,addEventListener(k,fn){listeners[k]=fn;}};
      const context = vm.createContext({localStorage:storage,document:{documentElement:root,querySelector(s){return s === '.theme-toggle' ? toggle : reset;}},window:{matchMedia(){return system;}}});
      vm.runInContext(early,context);
      const effective = !blocked && ['light','dark'].includes(saved) ? saved : (dark ? 'dark':'light');
      assert.equal(root.dataset.theme, !blocked && ['light','dark'].includes(saved) ? saved : undefined);
      vm.runInContext(control,context);
      assert.equal(toggle.hidden,false);
      assert.equal(toggle.attrs['aria-pressed'],String(effective==='dark'));
      toggle.click();
      const override = effective==='dark' ? 'light':'dark';
      assert.equal(root.dataset.theme,override);
      assert.equal(toggle.attrs['aria-pressed'],String(override==='dark'));
      if(!blocked)assert.equal(value,override);
      assert.equal(reset.hidden,false);
      reset.click();
      assert.equal(root.dataset.theme,undefined);
      assert.equal(reset.hidden,true);
      assert.equal(reset.focused,undefined);
      assert.equal(toggle.focused,true);
      system.matches = !dark;
      listeners.change();
      assert.equal(toggle.attrs['aria-pressed'],String(!dark));
    }
  }
}
process.stdout.write('Theme scripts: 16 system/storage scenarios passed\n');
'''
    scripts = [(render.ROOT / 'site/assets' / name).read_text() for name in ('theme-init.js', 'theme.js')]
    result = subprocess.run(['/usr/bin/node', '-e', harness], input=json.dumps(scripts), text=True, capture_output=True, check=True)
    assert result.stdout == 'Theme scripts: 16 system/storage scenarios passed\n'
