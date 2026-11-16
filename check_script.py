"""Scan a script for FE blocklist phrases.

Usage: python3 check_script.py SCRIPT.md [blocklist.txt]
Prints each hit with its line number; exits 1 if any hit is found.
"""
import re
import sys
from pathlib import Path


def patterns(blocklist_path):
    in_words = False
    for raw in Path(blocklist_path).read_text().splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_words = "single words" in line.lower()
            continue
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\[[^\]]+\]", line)
        body = r".{1,60}?".join(re.escape(p.strip()) for p in parts if p.strip())
        body = body.replace(r"\ ", r"\s+").replace("'", "['’]")
        if in_words:
            body += r"\w*"  # catch word forms: delves, fostering, elevated, unlocks
        yield line, re.compile(r"\b" + body, re.IGNORECASE)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    script = Path(sys.argv[1]).read_text()
    blocklist = sys.argv[2] if len(sys.argv) > 2 else Path(__file__).with_name("blocklist.txt")
    hits = 0
    for phrase, rx in patterns(blocklist):
        for m in rx.finditer(script):
            lineno = script.count("\n", 0, m.start()) + 1
            print(f"line {lineno}: '{m.group(0)}'  (blocked: {phrase})")
            hits += 1
    print(f"{hits} blocked phrase(s) found." if hits else "Clean: no blocked phrases.")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
