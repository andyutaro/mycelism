import re
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
