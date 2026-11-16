"""Align script sentences to a voiceover using its pauses (no speech model needed).

Usage: python3 align.py gaps.txt SCRIPT.txt DURATION out_sent.json

gaps.txt is ffmpeg silencedetect output. Speech is cut into segments at each pause;
dynamic programming assigns each sentence a run of consecutive segments so that the
run's speech time matches the sentence's expected time (by character count), and
sentence ends prefer longer pauses. Prints the average timing error per sentence,
which is a check that the recording matches the script.
"""
import json
import re
import sys


def load_segments(gaps_path, duration):
    txt = open(gaps_path).read()
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", txt)]
    segs, t = [], 0.0
    for s, e in zip(starts, ends):
        if s - t > 0.05:
            segs.append([t, s, e - s])  # speech start, speech end, pause after
        t = e
    if duration - t > 0.05:
        segs.append([t, duration, 1.0])
    return segs


def load_sentences(path):
    body = "\n".join(l for l in open(path).read().splitlines() if not l.lstrip().startswith("["))
    out = []
    for pi, p in enumerate(x for x in re.split(r"\n\s*\n", body) if x.strip()):
        for s in re.split(r"(?<=[.!?])\s+", p.replace("\n", " ").strip()):
            if s.strip():
                out.append({"para": pi, "text": s.strip()})
    return out


def align(segs, sents):
    n, m = len(sents), len(segs)
    weight = [len(re.sub(r"[^A-Za-z]", "", s["text"])) + 2 for s in sents]
    speech = [0.0]
    for a, b, _ in segs:
        speech.append(speech[-1] + (b - a))
    rate = speech[-1] / sum(weight)
    exp = [w * rate for w in weight]
    INF = 1e18
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(i, m - (n - i) + 1):
            pause = segs[j - 1][2]
            bonus = -0.6 * min(pause, 1.0)  # sentence ends like long pauses
            best, arg = INF, 0
            for k in range(max(i - 1, j - 14), j):
                if cost[i - 1][k] >= INF:
                    continue
                d = (speech[j] - speech[k]) - exp[i - 1]
                c = cost[i - 1][k] + d * d / max(exp[i - 1], 1.0) + bonus
                if c < best:
                    best, arg = c, k
            cost[i][j], back[i][j] = best, arg
    j, cuts = m, []
    for i in range(n, 0, -1):
        k = back[i][j]
        cuts.append((k, j))
        j = k
    cuts.reverse()
    err = 0.0
    for s, (k, j), e in zip(sents, cuts, exp):
        s["start"], s["end"] = round(segs[k][0], 3), round(segs[j - 1][1], 3)
        s["pause_after"] = round(segs[j - 1][2], 3)
        err += abs((speech[j] - speech[k]) - e)
    return err / n


def main():
    gaps, script, duration, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    segs, sents = load_segments(gaps, duration), load_sentences(script)
    err = align(segs, sents)
    json.dump(sents, open(out, "w"), indent=1)
    print(f"{len(sents)} sentences, {len(segs)} speech segments, mean timing error {err:.2f}s per sentence")


if __name__ == "__main__":
    main()
