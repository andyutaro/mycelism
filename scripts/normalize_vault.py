import re, sys, pathlib, difflib, os

URL = re.compile(r"(?<![\(<])(https?://[A-Za-z0-9\-._~:/?#@!$&'()*+,;=%]+)")
FENCE = chr(96) * 3

def normalize(text):
    fm = ""
    m = re.match(r'\A(---\n.*?\n---\n)', text, re.S)
    if m:
        fm, text = m.group(1), text[m.end():]
    out, in_code = [], False
    for ln in text.split('\n'):
        s = ln.lstrip()
        if s.startswith(FENCE) or s.startswith('~~~'):
            in_code = not in_code; out.append(ln); continue
        if in_code or '|' in ln:
            out.append(ln); continue
        ln = re.sub(r'[ \t]*-{3,}[ \t]*', '\n\n---\n\n', ln)
        ln = URL.sub(r'\n\n\1\n\n', ln)
        out.append(ln)
    text = '\n'.join(out)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
    return fm + text

args = sys.argv[1:]
target = next((a for a in args if not a.startswith('--')), os.path.expanduser('~/quartz/content/notes'))
apply = '--apply' in args
changed = 0
for p in sorted(pathlib.Path(target).rglob('*.md')):
    src = p.read_text(encoding='utf-8'); dst = normalize(src)
    if dst != src:
        changed += 1
        if apply:
            p.write_text(dst, encoding='utf-8')
        else:
            print('\n=== ' + str(p))
            print('\n'.join(list(difflib.unified_diff(src.splitlines(), dst.splitlines(), lineterm='', n=0))[:6]))
print('\n%d files %s / %s' % (changed, 'changed' if apply else 'would change', target))
