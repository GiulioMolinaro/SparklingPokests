"""Builds the publishable site into dist/.

Usage: python build.py
Minifies index.html (comments and whitespace in HTML, CSS and JS) and copies
only the folders the page needs. The output folder can be uploaded as is.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / 'dist'
ASSET_DIRS = ['assets', 'video']


def minify_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};,>])\s*', r'\1', css)
    css = re.sub(r':\s+', ':', css)
    css = css.replace(';}', '}')
    return css.strip()


def minify_js(js):
    js = re.sub(r'^\s*/\*.*?\*/\s*$', '', js, flags=re.S | re.M)
    lines = [line.strip() for line in js.splitlines()]
    return '\n'.join(line for line in lines if line)


def minify_html(html):
    html = re.sub(r'<style>(.*?)</style>', lambda m: '<style>' + minify_css(m.group(1)) + '</style>', html, flags=re.S)
    html = re.sub(r'<script>(.*?)</script>', lambda m: '<script>' + minify_js(m.group(1)) + '</script>', html, flags=re.S)
    html = re.sub(r'<!--(?!\[).*?-->', '', html, flags=re.S)
    html = re.sub(r'>\s*\n\s*<', '>\n<', html)
    html = re.sub(r'\n{2,}', '\n', html)
    return html.strip() + '\n'


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    out = minify_html(src)
    (DIST / 'index.html').write_text(out, encoding='utf-8')
    for d in ASSET_DIRS:
        shutil.copytree(ROOT / d, DIST / d)
    size = sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())
    print(f'index.html {len(src.encode()) // 1024} KB -> {len(out.encode()) // 1024} KB')
    print(f'dist/ pronta: {size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
