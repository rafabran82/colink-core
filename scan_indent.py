import sys, pathlib

path = pathlib.Path("scripts/xrpl.testnet.bootstrap.py")

print("=== Scanning indentation ===")

bad = []
with open(path, "r", encoding="utf8") as fh:
    for lineno, line in enumerate(fh, 1):
        if line.startswith(" "):
            spaces = len(line) - len(line.lstrip(" "))
            if spaces % 4 != 0:
                bad.append((lineno, spaces, line.rstrip()))
        if "\t" in line:
            bad.append((lineno, "TAB", line.rstrip()))

print("Found issues:", len(bad))
for entry in bad:
    print(entry)
