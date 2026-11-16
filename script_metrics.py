"""Score a TTS script on the FE humanization targets.

Usage: python3 script_metrics.py SCRIPT [SCRIPT2 ...]

Measures what can be measured without a language model:
- Burstiness: spread of sentence lengths (coefficient of variation), share of short
  and long sentences, longest run of similar-length sentences.
- Complexity: vocabulary diversity (moving-average type-token ratio), repeated
  sentence starters per paragraph, stock AI transitions and descriptors.
- TTS safety: ellipses, questions, 1-2 word sentences, em-dashes.
Perplexity itself needs a language model, so it is not scored here; temporal anchors
(years, dates, event numbers) are counted as a stand-in.
Marker lines starting with "[" are ignored, so the build version can be scored too.
"""
import re
import statistics
import sys
from collections import Counter

STOCK = ["furthermore", "moreover", "consequently", "in conclusion", "in summary", "as such",
         "hence", "thus", "therefore", "accordingly", "additionally", "it may seem",
         "on the other hand", "it remains to be seen", "while it is true", "some might argue",
         "it is important to note", "at the end of the day", "needless to say",
         "it goes without saying", "remarkable", "significant", "substantial", "profound",
         "essential", "vital", "plethora", "myriad", "invaluable", "pivotal", "dynamic",
         "seamless", "transformative", "groundbreaking", "comprehensive", "innovative"]
GENERIC_START = {"but", "and", "so", "then"}
MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"

TARGETS = {
    "length CV": (0.45, "≥"),
    "short (<8 words) %": (12, "≥"),
    "long (>25 words) %": (15, "≥"),
    "similar-length run": (3, "≤"),
    "MATTR (50-word)": (0.72, "≥"),
}


def sentences(text):
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("["))
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out = []
    for i, p in enumerate(paras):
        for s in re.split(r"(?<=[.!?])\s+", p.replace("\n", " ")):
            if s.strip():
                out.append((i, s.strip()))
    return body, out


def mattr(words, w=50):
    if len(words) <= w:
        return len(set(words)) / max(len(words), 1)
    return statistics.mean(len(set(words[i:i + w])) / w for i in range(len(words) - w + 1))


def score(path):
    text = open(path).read()
    body, sents = sentences(text)
    lens = [len(s.split()) for _, s in sents]
    words = re.findall(r"[a-z']+", body.lower())
    run = best = 1
    for a, b in zip(lens, lens[1:]):
        run = run + 1 if abs(a - b) <= 5 else 1
        best = max(best, run)
    starters = Counter()
    for p, s in sents:
        starters[(p, s.split()[0].strip(",").lower())] += 1
    para_repeats = [f"para {p + 1}: '{w}' x{n}" for (p, w), n in starters.items() if n > 2]
    low = body.lower().replace("significant strikes", "")  # official MMA stat, not filler
    stock = {t: len(re.findall(r"\b" + re.escape(t) + r"\b", low)) for t in STOCK}
    stock = {k: v for k, v in stock.items() if v}
    generic = sum(1 for _, s in sents if s.split()[0].strip(",").lower() in GENERIC_START)
    anchors = len(re.findall(r"\b(?:nineteen|two thousand)\b", low)) + len(re.findall(r"\b(?:%s)\b" % MONTHS, low))
    m = {
        "words": len(words), "sentences": len(lens),
        "mean length": round(statistics.mean(lens), 1),
        "length CV": round(statistics.pstdev(lens) / statistics.mean(lens), 2),
        "short (<8 words) %": round(100 * sum(l < 8 for l in lens) / len(lens)),
        "long (>25 words) %": round(100 * sum(l > 25 for l in lens) / len(lens)),
        "longest sentence": max(lens),
        "similar-length run": best,
        "MATTR (50-word)": round(mattr(words), 3),
        "temporal anchors": anchors,
        "generic starters (But/And/So/Then)": generic,
        "stock AI words": stock or "none",
        "paragraphs with a starter used 3+ times": para_repeats or "none",
        "1-2 word sentences": sum(l <= 2 for l in lens),
        "ellipses": body.count("…") + body.count("..."),
        "questions": body.count("?"),
        "em-dashes": body.count("—"),
    }
    return m


def main():
    for path in sys.argv[1:]:
        print(f"\n== {path}")
        for k, v in score(path).items():
            t = TARGETS.get(k)
            flag = ""
            if t:
                ok = v >= t[0] if t[1] == "≥" else v <= t[0]
                flag = f"   target {t[1]} {t[0]}  {'OK' if ok else 'MISS'}"
            print(f"  {k:42} {v}{flag}")


if __name__ == "__main__":
    main()
