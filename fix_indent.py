import pathlib, re

path = pathlib.Path("scripts/xrpl.testnet.bootstrap.py")
text = path.read_text(encoding="utf8").splitlines(True)

# Lines we need to fix (from your scan)
bad_lines = {
    45, 62, 78, 79, 80, 102, 103, 112, 113, 114, 115, 116, 153
}

def fix_indent(line):
    """Normalize indentation to the nearest multiple of 4 spaces."""
    stripped = line.lstrip(" ")
    leading = len(line) - len(stripped)
    # Convert odd widths to next lower multiple of 4
    new_leading = (leading // 4) * 4
    return (" " * new_leading) + stripped

new_text = []
for lineno, line in enumerate(text, 1):
    if lineno in bad_lines and line.startswith(" "):
        fixed = fix_indent(line)
        new_text.append(fixed)
    else:
        new_text.append(line)

path.write_text("".join(new_text), encoding="utf8")

print("Fixed indentation on lines:", sorted(bad_lines))
