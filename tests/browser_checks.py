"""Optional real Chromium gate (`make browser`), requiring permitted local sockets.

The default suite uses in-process rendered checks in restricted environments.
Temporary evidence is ignored under .test-artifacts/.
"""

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

from playwright.sync_api import expect, sync_playwright
import pytest

import render
from verify_live import verify

PROJECT = '/crossroads-sermon-outlines/'
SERMON = 'sermons/2026-08-16-inside-out.html'
SURFACES = [
    ('home', 'index.html'),
    ('search', 'search.html'),
    ('timeline', 'archive.html'),
    ('year', 'archive/2026.html'),
    ('series', 'series.html'),
    ('series', 'series/renew-me.html'),
    ('sermon', SERMON),
]
TRANSPARENT_PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xf8WAAAAAElFTkSuQmCC')


@pytest.fixture(scope='module')
def local_site():
    surfaces = render.build()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('?', 1)[0]
            relative = path[len(PROJECT):] or 'index.html'
            if not path.startswith(PROJECT) or relative not in surfaces:
                self.send_error(404)
                return
            self.send_response(200)
            content_type = 'text/css; charset=utf-8' if relative.endswith('.css') else ('application/json; charset=utf-8' if relative.endswith('.json') else 'text/html; charset=utf-8')
            self.send_header('Content-Type', content_type)
            self.end_headers()
            self.wfile.write(surfaces[relative])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}{PROJECT}'
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


def context_for(browser, **options):
    context = browser.new_context(reduced_motion='reduce', **options)
    context.route('https://www.youtube.com/**', lambda route: route.abort())
    context.route('https://i.ytimg.com/**', lambda route: route.fulfill(body=TRANSPARENT_PNG, content_type='image/png'))
    return context


def background(page):
    return page.evaluate('getComputedStyle(document.body).backgroundColor')


def overflow_details(page):
    """Include text bounds: nowrap text may escape an otherwise narrow grid item."""
    return page.evaluate('''() => {
      const issues = [];
      const describe = el => ({tag: el.tagName, class: el.className,
        anchor: el.closest('[id]')?.id, label: el.closest('[data-label]')?.dataset.label});
      for (const el of document.body.querySelectorAll('*')) {
        if (['SCRIPT', 'STYLE'].includes(el.tagName)) continue;
        const rect = el.getBoundingClientRect();
        if (rect.width && rect.right + scrollX > innerWidth) {
          issues.push({...describe(el), kind: 'element', right: rect.right + scrollX});
        }
        for (const node of el.childNodes) {
          if (node.nodeType !== Node.TEXT_NODE || !node.textContent.trim()) continue;
          const range = document.createRange();
          range.selectNodeContents(node);
          for (const rect of range.getClientRects()) {
            if (rect.right + scrollX > innerWidth) {
              issues.push({...describe(el), kind: 'text', text: node.textContent.trim().slice(0, 100),
                right: rect.right + scrollX});
            }
          }
        }
      }
      return {viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth, issues};
    }''')


@pytest.mark.parametrize('name,path', SURFACES)
@pytest.mark.parametrize('device,width,height', [('desktop', 1280, 900), ('mobile', 375, 812)])
@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_rendered_viewports(browser, local_site, name, path, device, width, height, theme):
    with context_for(browser, viewport={'width': width, 'height': height}, color_scheme=theme) as context:
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(local_site + path)
        assert not errors
        assert background(page) == ('rgb(20, 29, 25)' if theme == 'dark' else 'rgb(250, 250, 246)')
        target_theme = 'light' if theme == 'dark' else 'dark'
        assert page.locator('.theme-toggle').get_attribute('aria-label') == f'Switch to {target_theme} theme'
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if name == 'sermon':
            assert page.get_by_role('table', name='Scripture ledger').count() == 1
            assert page.get_by_role('row').count() == 38  # 37 rows plus column headings
            assert page.locator('table').evaluate('(el) => getComputedStyle(el).display') == ('block' if device == 'mobile' else 'table')
            page.goto(local_site + path + '#ledger-SCR-003')
            target = page.locator('[id="ledger-SCR-003"]')
            assert target.evaluate('(el) => el.matches(":target")')
            assert target.evaluate('(el) => getComputedStyle(el).outlineStyle') == 'solid'
            assert 0 <= target.bounding_box()['y'] < height
            if device == 'mobile':
                assert target.locator('td').first.evaluate('(el) => getComputedStyle(el, "::before").content') == '"Treatment"'
            page.goto(local_site + path)
        evidence = render.ROOT / '.test-artifacts/browser'
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / f'{name}-{device}-{theme}.png'), full_page=False)
        if name == 'sermon' and device == 'mobile':
            page.goto(local_site + path + '#ledger-SCR-003')
            page.screenshot(path=str(evidence / f'ledger-mobile-{theme}.png'), full_page=False)


@pytest.mark.parametrize('system', ['light', 'dark'])
def test_theme_toggle_persistence_system_default_and_early_script(browser, local_site, system):
    with context_for(browser, color_scheme=system) as context:
        page = context.new_page()
        page.goto(local_site)
        override = 'dark' if system == 'light' else 'light'
        toggle = page.get_by_role('button', name=f'Switch to {override} theme')
        assert toggle.is_visible()
        assert page.evaluate('document.documentElement.dataset.theme') is None
        toggle.click()
        assert page.evaluate('document.documentElement.dataset.theme') == override
        assert page.evaluate('localStorage.getItem("crossroads-theme")') == override
        page.goto(local_site + 'archive/2026.html')
        assert page.evaluate('document.documentElement.dataset.theme') == override
        page.reload()
        assert page.get_by_role('button', name=f'Switch to {system} theme').is_visible()
        # Remove the control script: only the early head script can restore the theme.
        early_only = render.build()['index.html'].decode()
        second_script = early_only.rfind('<script>')
        early_only = early_only[:second_script] + early_only[early_only.index('</script>', second_script) + len('</script>'):]
        context.route(local_site + 'index.html', lambda route: route.fulfill(body=early_only, content_type='text/html'))
        page.goto(local_site + 'index.html')
        assert page.evaluate('document.documentElement.dataset.theme') == override
        assert background(page) == ('rgb(20, 29, 25)' if override == 'dark' else 'rgb(250, 250, 246)')
        context.unroute(local_site + 'index.html')
        page.evaluate('localStorage.removeItem("crossroads-theme")')
        page.goto(local_site)
        assert page.evaluate('localStorage.getItem("crossroads-theme")') is None
        assert page.evaluate('document.documentElement.dataset.theme') is None
        assert page.get_by_role('button', name=f'Switch to {override} theme').is_visible()


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_no_javascript_navigation_and_ledger(browser, local_site, theme):
    with context_for(browser, java_script_enabled=False, color_scheme=theme, viewport={'width': 375, 'height': 812}) as context:
        page = context.new_page()
        page.goto(local_site)
        assert not page.locator('.theme-toggle').is_visible()
        assert background(page) == ('rgb(20, 29, 25)' if theme == 'dark' else 'rgb(250, 250, 246)')
        page.get_by_role('link', name='Series', exact=True).click()
        page.get_by_role('link', name='Renew Me', exact=True).click()
        assert page.url.endswith('series/renew-me.html')
        page.get_by_role('link', name='When Excuses Die', exact=True).click()
        assert page.url.endswith('sermons/2026-08-03-when-excuses-die.html')
        page.goto(local_site)
        page.get_by_role('link', name='Timeline', exact=True).click()
        page.locator('.year-list .year-link').click()
        page.get_by_role('link', name='July', exact=True).click()
        assert page.url.endswith('#2026-07')
        page.get_by_role('link', name='Keep Running!', exact=True).click()
        page.get_by_role('link', name='Scripture ledger', exact=True).click()
        assert page.url.endswith('#scripture-ledger')
        assert page.get_by_role('table', name='Scripture ledger').is_visible()
        page.locator('.month-return').click()
        assert page.url.endswith('archive/2026.html#2026-07')


def test_art_plate_and_watch_link_hit_targets(browser, local_site):
    with context_for(browser, viewport={'width': 1280, 'height': 900}) as context:
        page = context.new_page()
        page.goto(local_site)
        card = page.locator('.series-card').first
        plate = card.locator('.series-plate')
        plate_box = plate.bounding_box()
        plate_target = page.evaluate('''point => {
          const target = document.elementFromPoint(point.x, point.y);
          return target.closest('a')?.getAttribute('href');
        }''', {'x': plate_box['x'] + plate_box['width'] / 2, 'y': plate_box['y'] + plate_box['height'] / 2})
        assert plate_target == 'series/renew-me.html'


def test_search_control_has_one_clean_focus_ring(browser, local_site):
    with context_for(browser, viewport={'width': 1280, 'height': 900}) as context:
        page = context.new_page()
        page.goto(local_site)
        search = page.locator('.site-search')
        input_box = search.locator('input')
        button = search.locator('button')
        input_box.focus()
        assert search.evaluate('(element) => getComputedStyle(element).outlineStyle') == 'solid'
        assert search.evaluate('(element) => getComputedStyle(element).outlineWidth') == '2px'
        assert input_box.evaluate('(element) => getComputedStyle(element).outlineStyle') == 'none'
        input_bounds, button_bounds = input_box.bounding_box(), button.bounding_box()
        search_bounds = search.bounding_box()
        assert search_bounds['width'] <= 464.01
        assert abs(input_bounds['y'] - button_bounds['y']) < 1
        assert abs(input_bounds['height'] - button_bounds['height']) < 1
        assert abs(input_bounds['x'] + input_bounds['width'] - button_bounds['x']) < 1


@pytest.mark.parametrize('width', [1280, 375])
def test_search_results_are_safe_responsive_and_deep_linked(browser, local_site, width):
    with context_for(browser, viewport={'width': width, 'height': 812}) as context:
        page = context.new_page()
        page.goto(local_site + 'search.html?q=Psalm%2051%3A10')
        expect(page.locator('#search-status')).to_contain_text('result')
        scripture = page.locator('#search-results a[href*="#ledger-"]').first
        expect(scripture).to_be_visible()
        assert scripture.get_attribute('href').startswith('sermons/')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), overflow_details(page)
        page.goto(local_site + 'search.html?q=Hebrews%2012')
        expect(page.locator('#search-results a[href*="#ledger-"]').first).to_be_visible()
        page.goto(local_site + 'search.html?q=version%20of%20the%20truth')
        expect(page.locator('.result-excerpt').first).to_contain_text('version of the truth')
        assert page.locator('.result-excerpt').first.locator('xpath=..').locator('a').get_attribute('href').endswith('#s1')
        page.goto(local_site + 'search.html?q=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E')
        expect(page.locator('#search-status')).to_have_text('0 results')
        assert page.locator('#search-results img').count() == 0
        assert page.locator('text=<img src=x onerror=alert(1)>').count() == 0


def test_keyboard_numeric_anchor_print_and_large_text(browser, local_site):
    with context_for(browser, color_scheme='dark', viewport={'width': 1280, 'height': 900}) as context:
        page = context.new_page()
        page.goto(local_site + 'sermons/2026-08-24-start-with-me.html')
        page.keyboard.press('Tab')
        assert page.locator('.skip-link').evaluate('(el) => el === document.activeElement')
        assert page.locator('.skip-link').bounding_box()['x'] >= 0
        page.keyboard.press('Enter')
        assert page.locator('main').evaluate('(el) => el === document.activeElement')
        for selector in ('.timestamp', '.scripture-tag', '.month-return', '.theme-toggle'):
            element = page.locator(selector).first
            element.focus()
            assert element.evaluate('(el) => getComputedStyle(el).outlineStyle') == 'solid'
        page.goto(local_site + 'sermons/2026-08-24-start-with-me.html#1.1')
        assert page.locator('[id="1.1"]').evaluate('(el) => el.matches(":target")')
        page.emulate_media(media='print')
        assert background(page) == 'rgb(255, 255, 255)'
        assert page.locator('body').evaluate('(el) => getComputedStyle(el).fontSize') == '16px'
        assert not page.locator('.video-block').is_visible()
        assert page.locator('thead').evaluate('(el) => getComputedStyle(el).display') == 'table-header-group'
        assert page.locator('.outline-node').first.evaluate('(el) => getComputedStyle(el).breakInside') == 'avoid'
        page.emulate_media(media='screen')
        page.set_viewport_size({'width': 375, 'height': 812})
        page.add_style_tag(content='html { font-size: 200%; }')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), overflow_details(page)


@pytest.mark.parametrize('width', [375, 414])
@pytest.mark.parametrize('path', [path for path in render.build() if path.endswith('.html')])
def test_large_text_reflows_on_every_surface(browser, local_site, path, width):
    with context_for(browser, color_scheme='dark', viewport={'width': width, 'height': 812}) as context:
        page = context.new_page()
        page.goto(local_site + path)
        page.add_style_tag(content='html { font-size: 200%; }')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), overflow_details(page)


def test_unavailable_storage_keeps_theme_usable(browser, local_site):
    with context_for(browser, color_scheme='dark') as context:
        context.add_init_script('Object.defineProperty(window, "localStorage", { get() { throw new Error("unavailable"); } });')
        page = context.new_page()
        page.goto(local_site)
        page.get_by_role('button', name='Switch to light theme').click()
        assert background(page) == 'rgb(250, 250, 246)'


def test_actual_http_verification_on_every_surface(local_site):
    expected = render.build()
    assert verify(local_site, expected, render.records(), attempts=1) == expected
