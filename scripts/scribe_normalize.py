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
    text = re.sub(r'\n{12,}', '\n' * 11, text).strip() + '\n'
    return fm + text


def br_fidelity(text):
    """空行を <br> 行に変換して本数を保持（--- 罫線の前後の空行は実空行で残す）。"""
    text = text.rstrip('\n')
    lines = text.split('\n'); n = len(lines); out = []
    for i, ln in enumerate(lines):
        if ln == '':
            prev_hr = i > 0 and lines[i-1].strip() == '---'
            next_hr = i < n - 1 and lines[i+1].strip() == '---'
            out.append('' if (prev_hr or next_hr) else '<br>')
        else:
            out.append(ln)
    return '\n'.join(out) + '\n'
