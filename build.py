"""Builds the publishable site into dist/ and dist.zip.

Usage: python build.py
Minifies index.html (comments and whitespace in HTML, CSS and JS), copies
only the folders the page needs, then zips the result with index.html at the
root, ready for the 0sei Digital gestionale upload (max 50 MB, 300 files).
"""
import os
import re
import shutil
import stat
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / 'dist'
ZIP = ROOT / 'dist.zip'
ASSET_DIRS = ['assets', 'video']
MAX_ZIP_BYTES = 50 * 1000 * 1000
MAX_FILES = 300


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


def _make_writable(func, path, _exc):
    # OneDrive marks synced folders read-only, which blocks deletion on Windows
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_dist():
    # OneDrive or a local server can hold files for a moment, so retry briefly
    for attempt in range(10):
        try:
            if DIST.exists():
                shutil.rmtree(DIST, onexc=_make_writable)
            return
        except PermissionError:
            time.sleep(1)
    sys.exit('Impossibile svuotare dist/: chiudi i programmi che la stanno usando e riprova.')


def main():
    remove_dist()
    DIST.mkdir()
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    out = minify_html(src)
    (DIST / 'index.html').write_text(out, encoding='utf-8')
    for d in ASSET_DIRS:
        shutil.copytree(ROOT / d, DIST / d)
    files = sorted(f for f in DIST.rglob('*') if f.is_file())
    print(f'index.html {len(src.encode()) // 1024} KB -> {len(out.encode()) // 1024} KB')

    # images and videos are already compressed, so they are stored as is
    with zipfile.ZipFile(ZIP, 'w') as z:
        for f in files:
            rel = f.relative_to(DIST).as_posix()
            kind = zipfile.ZIP_DEFLATED if f.suffix in {'.html', '.css', '.js', '.svg'} else zipfile.ZIP_STORED
            z.write(f, rel, compress_type=kind)
    zip_size = ZIP.stat().st_size
    print(f'dist.zip: {zip_size / 1e6:.1f} MB, {len(files)} file')

    problems = []
    if zip_size > MAX_ZIP_BYTES:
        problems.append(f'lo zip supera 50 MB ({zip_size / 1e6:.1f} MB)')
    if len(files) > MAX_FILES:
        problems.append(f'troppi file ({len(files)} su {MAX_FILES})')
    if problems:
        sys.exit('ATTENZIONE: ' + '; '.join(problems))
    print('OK per il gestionale: sotto 50 MB e 300 file')


if __name__ == '__main__':
    main()
