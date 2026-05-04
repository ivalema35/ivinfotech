"""Basic CSS/JS minifier for IV Infotech assets.
Creates .min.css and .min.js files in the same directories.
"""
import re, os


def minify_css(text):
    """Remove comments, collapse whitespace, strip unnecessary semicolons/spaces."""
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Collapse runs of whitespace (space, tab, newline) into single space
    text = re.sub(r'\s+', ' ', text)
    # Remove spaces around : ; , { } ( > + ~ )
    text = re.sub(r'\s*([:;,{}()>\+~])\s*', r'\1', text)
    # Remove space before !important
    text = re.sub(r'\s+!important', '!important', text)
    # Remove last semicolon before closing brace
    text = re.sub(r';}', '}', text)
    # Strip leading/trailing space
    text = text.strip()
    return text


def minify_js(text):
    """Remove single/multi-line comments, collapse whitespace minimally."""
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove single-line comments (careful with // inside strings)
    # A simple approach: remove // comments not inside quotes
    lines = text.split('\n')
    out_lines = []
    for line in lines:
        # Simple heuristic: if line contains // outside of quotes, strip from //
        in_string = False
        string_char = None
        for i, ch in enumerate(line):
            if ch in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                    string_char = ch
                elif ch == string_char and (i == 0 or line[i-1] != '\\'):
                    in_string = False
            elif ch == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                line = line[:i].rstrip()
                break
        out_lines.append(line)
    text = '\n'.join(out_lines)
    # Collapse runs of whitespace (but keep newlines for semicolon insertion)
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove spaces around certain tokens
    text = re.sub(r'\s*([=+\-*/%<>!&|^~?:;,{}()\[\]])\s*', r'\1', text)
    # But keep space after keywords: if, else, for, while, function, return, etc.
    text = re.sub(r'\b(function|if|else|for|while|do|switch|case|return|throw|catch|finally|try|typeof|instanceof|new|delete|void|with)\s*\(', r'\1(', text)
    # Remove extra newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()
    return text


def main():
    base = os.path.dirname(os.path.abspath(__file__))

    # Minify CSS
    css_path = os.path.join(base, 'assets', 'css', 'style.css')
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        minified = minify_css(raw)
        out_path = os.path.join(base, 'assets', 'css', 'style.min.css')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        orig_kb = len(raw) / 1024
        new_kb = len(minified) / 1024
        print(f'CSS: {css_path} -> {out_path}')
        print(f'     {orig_kb:.1f}KB -> {new_kb:.1f}KB  ({100 - (new_kb/orig_kb*100):.1f}% reduction)')
    else:
        print(f'Skipping CSS: {css_path} not found')

    # Minify JS
    js_path = os.path.join(base, 'assets', 'js', 'main.js')
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        minified = minify_js(raw)
        out_path = os.path.join(base, 'assets', 'js', 'main.min.js')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        orig_kb = len(raw) / 1024
        new_kb = len(minified) / 1024
        print(f'JS:  {js_path} -> {out_path}')
        print(f'     {orig_kb:.1f}KB -> {new_kb:.1f}KB  ({100 - (new_kb/orig_kb*100):.1f}% reduction)')
    else:
        print(f'Skipping JS: {js_path} not found')

    print('\nDone.')


if __name__ == '__main__':
    main()
